from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    available_credits = serializers.SerializerMethodField()
    free_minutes_remaining = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'date_joined', 'is_premium', 'premium_expires_at',
            'free_minutes_used', 'purchased_credits',
            'available_credits', 'free_minutes_remaining',
        ]
        read_only_fields = [
            'id', 'email', 'date_joined', 'is_premium', 'premium_expires_at',
            'free_minutes_used', 'purchased_credits',
        ]

    def get_available_credits(self, obj):
        free_remaining = max(0, settings.FREE_TIER_MINUTES - obj.free_minutes_used)
        return free_remaining + obj.purchased_credits

    def get_free_minutes_remaining(self, obj):
        return max(0, settings.FREE_TIER_MINUTES - obj.free_minutes_used)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
