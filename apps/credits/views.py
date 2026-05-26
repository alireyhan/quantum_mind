from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.conf import settings
import stripe
from .models import CreditTransaction, CreditPackage
from .serializers import (
    CreditTransactionSerializer,
    CreditPackageSerializer,
    CreditBalanceSerializer,
    StripePaymentVerifySerializer,
)
from .services import CreditService


class CreditBalanceView(APIView):
    """GET /api/credits/balance/ — Return the user's current credit balance."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        free_remaining = max(0, settings.FREE_TIER_MINUTES - user.free_minutes_used)
        data = {
            'free_minutes_total': settings.FREE_TIER_MINUTES,
            'free_minutes_used': user.free_minutes_used,
            'free_minutes_remaining': free_remaining,
            'purchased_credits': user.purchased_credits,
            'total_available': free_remaining + user.purchased_credits,
        }
        serializer = CreditBalanceSerializer(data)
        return Response(serializer.data)


class CreditTransactionListView(generics.ListAPIView):
    """GET /api/credits/transactions/ — Paginated credit transaction history."""
    serializer_class = CreditTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CreditTransaction.objects.filter(user=self.request.user)


class CreditPackageListView(generics.ListAPIView):
    """GET /api/credits/packages/ — List available credit packages for purchase."""
    serializer_class = CreditPackageSerializer
    permission_classes = [IsAuthenticated]
    queryset = CreditPackage.objects.filter(is_active=True)


class VerifyStripePaymentView(APIView):
    """POST /api/credits/verify-payment/ — Verify a Stripe Checkout Session or
    PaymentIntent and add purchased credits to the user's account.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StripePaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stripe_session_id = serializer.validated_data['stripe_session_id']
        package_id = serializer.validated_data['package_id']

        try:
            package = CreditPackage.objects.get(id=package_id, is_active=True)
        except CreditPackage.DoesNotExist:
            return Response({'error': True, 'detail': 'Invalid package.'}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.STRIPE_SECRET_KEY:
            return Response({'error': True, 'detail': 'Stripe not configured on server.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        payment_completed = False
        if stripe_session_id.startswith('cs_'):
            try:
                session = stripe.checkout.Session.retrieve(stripe_session_id)
                payment_status = getattr(session, 'payment_status', None)
                if payment_status == 'paid' or getattr(session, 'status', None) == 'complete':
                    payment_completed = True
                else:
                    # Try verifying the PaymentIntent as a fallback
                    payment_intent_id = getattr(session, 'payment_intent', None)
                    if payment_intent_id:
                        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                        if intent.status == 'succeeded':
                            payment_completed = True
            except Exception as e:
                return Response({'error': True, 'detail': f'Stripe lookup failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        elif stripe_session_id.startswith('pi_'):
            try:
                intent = stripe.PaymentIntent.retrieve(stripe_session_id)
                if intent.status == 'succeeded':
                    payment_completed = True
            except Exception as e:
                return Response({'error': True, 'detail': f'Stripe lookup failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': True, 'detail': 'Invalid Stripe ID format. Must start with cs_ or pi_.'}, status=status.HTTP_400_BAD_REQUEST)

        if not payment_completed:
            return Response({'error': True, 'detail': 'Payment not completed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Add purchased credits
        credit_service = CreditService()
        credit_service.add_credits(
            request.user,
            package.minutes,
            transaction_type='purchase',
            description=f'Purchase via Stripe ID {stripe_session_id} (package {package.id})',
        )

        return Response({'ok': True, 'minutes_added': package.minutes}, status=status.HTTP_200_OK)
