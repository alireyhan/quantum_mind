from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    otp = serializers.CharField(write_only=True, min_length=6, max_length=6)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm', 'age', 'occupation', 'pronouns', 'otp']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        validated_data.pop('otp', None)
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    available_credits = serializers.SerializerMethodField()
    free_minutes_remaining = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'age', 'occupation', 'pronouns',
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
        fields = ['first_name', 'last_name', 'age', 'occupation', 'pronouns']


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    # "registration" or "password_reset"
    purpose = serializers.ChoiceField(choices=['registration', 'password_reset'])

    def validate(self, data):
        email = data['email']
        purpose = data['purpose']

        if purpose == 'registration' and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "User with this email already exists."})
        if purpose == 'password_reset' and not User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "If an account exists, an OTP will be sent."})

        return data


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return data
