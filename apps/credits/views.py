from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.conf import settings
from .models import CreditTransaction, CreditPackage
from .serializers import (
    CreditTransactionSerializer,
    CreditPackageSerializer,
    CreditBalanceSerializer,
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
