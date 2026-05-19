from rest_framework import serializers
from .models import CreditTransaction, CreditPackage


class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = [
            'id', 'transaction_type', 'minutes_amount',
            'description', 'session_id', 'created_at',
        ]
        read_only_fields = fields


class CreditPackageSerializer(serializers.ModelSerializer):
    price_dollars = serializers.FloatField(read_only=True)

    class Meta:
        model = CreditPackage
        fields = ['id', 'name', 'minutes', 'price_cents', 'price_dollars', 'sort_order']


class CreditBalanceSerializer(serializers.Serializer):
    free_minutes_total = serializers.IntegerField()
    free_minutes_used = serializers.IntegerField()
    free_minutes_remaining = serializers.IntegerField()
    purchased_credits = serializers.IntegerField()
    total_available = serializers.IntegerField()
