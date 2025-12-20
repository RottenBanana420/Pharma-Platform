"""
Django admin configuration for Pharmacy and Medicine models.
"""
from django.contrib import admin
from .models import Pharmacy, Medicine


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    """Admin interface for Pharmacy model."""
    
    list_display = [
        'name',
        'license_number',
        'city',
        'state',
        'is_verified',
        'registered_at'
    ]
    list_filter = ['is_verified', 'state', 'city']
    search_fields = ['name', 'license_number', 'contact_email', 'city']
    readonly_fields = ['registered_at']
    
    fieldsets = (
        ('Business Information', {
            'fields': ('name', 'license_number', 'contact_email')
        }),
        ('Address', {
            'fields': ('street_address', 'city', 'state', 'postal_code')
        }),
        ('Contact', {
            'fields': ('phone_number',)
        }),
        ('Status', {
            'fields': ('is_verified', 'registered_at')
        }),
    )


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    """Admin interface for Medicine model."""
    
    list_display = [
        'commercial_name',
        'generic_name',
        'manufacturer',
        'pharmacy',
        'price',
        'stock_quantity',
        'created_at'
    ]
    list_filter = ['pharmacy', 'manufacturer', 'created_at']
    search_fields = ['commercial_name', 'generic_name', 'manufacturer']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Medicine Information', {
            'fields': ('commercial_name', 'generic_name', 'manufacturer')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock_quantity')
        }),
        ('Pharmacy', {
            'fields': ('pharmacy',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
