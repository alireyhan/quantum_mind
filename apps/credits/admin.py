from django.contrib import admin
from .models import CreditTransaction, CreditPackage


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'minutes_amount', 'description', 'created_at']
    list_filter = ['transaction_type']
    search_fields = ['user__email', 'description']
    readonly_fields = ['user', 'transaction_type', 'minutes_amount', 'description', 'session', 'created_at']

    def has_add_permission(self, request):
        return False  # Transactions are system-generated only

    def has_delete_permission(self, request, obj=None):
        return False  # Immutable ledger


@admin.register(CreditPackage)
class CreditPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'minutes', 'price_cents', 'price_dollars', 'is_active', 'sort_order']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order']
