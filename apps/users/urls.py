from django.urls import path
from .views import RegisterView, ProfileView, SendOTPView, ResetPasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='user-register'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]
