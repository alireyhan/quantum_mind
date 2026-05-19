from django.db import models
from apps.core.models import TimeStampedModel


class CreditTransaction(TimeStampedModel):
    """Immutable ledger of all credit movements for a user."""

    TYPE_CHOICES = [
        ('free_allocation', 'Free Allocation'),
        ('purchase', 'Purchase'),
        ('session_use', 'Session Use'),
        ('refund', 'Refund'),
        ('bonus', 'Bonus'),
    ]

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='credit_transactions',
    )
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    minutes_amount = models.IntegerField(
        help_text='Positive = credit added, Negative = credit used.'
    )
    description = models.CharField(max_length=255)
    session = models.ForeignKey(
        'therapy_sessions.TherapySession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_transactions',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Credit Transaction'
        verbose_name_plural = 'Credit Transactions'

    def __str__(self):
        sign = '+' if self.minutes_amount >= 0 else ''
        return f'{self.user.email} {sign}{self.minutes_amount}min [{self.transaction_type}]'


class CreditPackage(TimeStampedModel):
    """Available credit packages for purchase. Managed via Django Admin."""

    name = models.CharField(max_length=100)
    minutes = models.PositiveIntegerField(help_text='Number of session minutes included.')
    price_cents = models.PositiveIntegerField(help_text='Price in cents (e.g. 999 = $9.99).')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'price_cents']
        verbose_name = 'Credit Package'
        verbose_name_plural = 'Credit Packages'

    def __str__(self):
        return f'{self.name} — {self.minutes}min @ ${self.price_cents / 100:.2f}'

    @property
    def price_dollars(self):
        return self.price_cents / 100
