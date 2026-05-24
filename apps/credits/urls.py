from django.urls import path
from .views import (
    CreditBalanceView,
    CreditTransactionListView,
    CreditPackageListView,
    VerifyStripePaymentView,
)

urlpatterns = [
    path('balance/', CreditBalanceView.as_view(), name='credit-balance'),
    path('transactions/', CreditTransactionListView.as_view(), name='credit-transactions'),
    path('packages/', CreditPackageListView.as_view(), name='credit-packages'),
    path('verify-payment/', VerifyStripePaymentView.as_view(), name='credit-verify-payment'),
]
