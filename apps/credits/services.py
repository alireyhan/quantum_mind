import logging
from django.db import transaction
from django.conf import settings
from .models import CreditTransaction

logger = logging.getLogger(__name__)


class CreditService:
    """
    All credit balance operations. Deductions and additions are atomic
    and always recorded in the CreditTransaction ledger.
    """

    def get_available_credits(self, user) -> int:
        """Total minutes available: remaining free tier + purchased credits."""
        free_remaining = max(0, settings.FREE_TIER_MINUTES - user.free_minutes_used)
        return free_remaining + user.purchased_credits

    def has_sufficient_credits(self, user, minutes: int) -> bool:
        return self.get_available_credits(user) >= minutes

    @transaction.atomic
    def deduct_credits(
        self,
        user,
        minutes: int,
        transaction_type: str = 'session_use',
        session=None,
    ):
        """
        Deduct session minutes. Always consumes free tier first,
        then falls back to purchased credits.
        Records separate ledger entries for free vs paid usage.
        """
        # Re-fetch user inside the transaction for row-level consistency
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.select_for_update().get(pk=user.pk)

        free_remaining = max(0, settings.FREE_TIER_MINUTES - user.free_minutes_used)

        if free_remaining >= minutes:
            # Consume entirely from free tier
            user.free_minutes_used += minutes
            CreditTransaction.objects.create(
                user=user,
                transaction_type='free_allocation',
                minutes_amount=-minutes,
                description='Free tier session usage',
                session=session,
            )
        else:
            # Consume remaining free + required purchased
            free_used = free_remaining
            purchased_needed = minutes - free_used

            user.free_minutes_used += free_used
            user.purchased_credits = max(0, user.purchased_credits - purchased_needed)

            if free_used > 0:
                CreditTransaction.objects.create(
                    user=user,
                    transaction_type='free_allocation',
                    minutes_amount=-free_used,
                    description='Free tier session usage (partial)',
                    session=session,
                )

            CreditTransaction.objects.create(
                user=user,
                transaction_type='session_use',
                minutes_amount=-purchased_needed,
                description='Paid credit session usage',
                session=session,
            )

        user.save()
        logger.info(
            'Deducted %d minutes from user %s (free_used=%d, purchased_balance=%d)',
            minutes, user.id, user.free_minutes_used, user.purchased_credits,
        )

    @transaction.atomic
    def add_credits(
        self,
        user,
        minutes: int,
        transaction_type: str,
        description: str,
    ):
        """Add purchased or bonus credits to a user's account."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.select_for_update().get(pk=user.pk)

        user.purchased_credits += minutes
        user.save()

        CreditTransaction.objects.create(
            user=user,
            transaction_type=transaction_type,
            minutes_amount=minutes,
            description=description,
        )
        logger.info('Added %d credits (%s) to user %s', minutes, transaction_type, user.id)

    @transaction.atomic
    def refund_credits(self, user, session, reason: str):
        """
        Refund credits that were deducted for a failed session.
        Returns the exact minutes used by that session.
        """
        if not session or not session.credits_used:
            return

        minutes = session.credits_used
        self.add_credits(
            user,
            minutes,
            transaction_type='refund',
            description=f'Refund for failed session #{session.id}: {reason}',
        )
        logger.info('Refunded %d credits to user %s for session %s', minutes, user.id, session.id)
