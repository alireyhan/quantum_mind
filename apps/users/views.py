from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
import random
from django.utils import timezone
from datetime import timedelta
from .models import EmailOTP
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, UserUpdateSerializer,
    SendOTPSerializer, ResetPasswordSerializer
)

User = get_user_model()


def generate_and_send_otp(email, purpose):
    otp = f"{random.randint(100000, 999999)}"
    expires_at = timezone.now() + timedelta(minutes=15)
    
    EmailOTP.objects.filter(email=email, purpose=purpose).delete()
    
    EmailOTP.objects.create(
        email=email,
        otp=otp,
        purpose=purpose,
        expires_at=expires_at
    )
    
    subject = "Your Verification Code - Quantum Mind"
    message = f"Your 6-digit verification code is: {otp}\nIt will expire in 15 minutes."
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


class SendOTPView(generics.GenericAPIView):
    """POST /api/users/send-otp/ — Send a 6-digit OTP for registration or password reset."""
    serializer_class = SendOTPSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']
        
        generate_and_send_otp(email, purpose)
        return Response({"detail": "OTP sent successfully."}, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    """POST /api/users/register/ — Create a new user account with OTP."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp = request.data.get('otp')
        
        otp_record = EmailOTP.objects.filter(email=email, otp=otp, purpose='registration').first()
        if not otp_record or otp_record.is_expired:
            return Response({"otp": ["Invalid or expired OTP."]}, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        otp_record.delete()
        
        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/users/profile/ — Retrieve, update, or delete the current user profile."""
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserProfileSerializer

    def perform_destroy(self, instance):
        # We can either hard-delete or soft-delete. Let's hard delete.
        instance.delete()


class ResetPasswordView(generics.GenericAPIView):
    """POST /api/users/reset-password/ — Reset the password using 6-digit OTP."""
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        otp_record = EmailOTP.objects.filter(email=email, otp=otp, purpose='password_reset').first()
        if not otp_record or otp_record.is_expired:
            return Response({"error": True, "detail": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            otp_record.delete()
            return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": True, "detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
