"""
Django admin configuration for the accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin interface for User model."""
    
    # Fields to display in the list view
    list_display = (
        'email',
        'username',
        'phone_number',
        'user_type',
        'is_verified',
        'is_active',
        'is_staff',
        'date_joined',
    )
    
    # Filters in the sidebar
    list_filter = (
        'user_type',
        'is_verified',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    )
    
    # Search fields
    search_fields = (
        'email',
        'username',
        'phone_number',
        'first_name',
        'last_name',
    )
    
    # Ordering
    ordering = ('-date_joined',)
    
    # Fieldsets for the detail view
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('Account Type', {
            'fields': ('user_type', 'is_verified')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Fieldsets for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'phone_number',
                'user_type',
                'password1',
                'password2',
            ),
        }),
    )
