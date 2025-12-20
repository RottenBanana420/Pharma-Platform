"""
Custom permission classes for role-based access control.

Provides:
- IsPatient: Restricts access to patient users only
- IsPharmacyAdmin: Restricts access to pharmacy administrator users only
- IsVerifiedPharmacy: Restricts access to verified pharmacy administrators only
"""
from rest_framework import permissions


class IsPatient(permissions.BasePermission):
    """
    Permission class that allows access only to users with patient user type.
    
    Used for patient-specific endpoints such as prescription uploads.
    """
    
    message = "Only patients can access this resource."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and has patient user type.
        
        Args:
            request: HTTP request object
            view: View being accessed
            
        Returns:
            bool: True if user is authenticated patient, False otherwise
        """
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'user_type') and
            request.user.user_type == 'patient'
        )


class IsPharmacyAdmin(permissions.BasePermission):
    """
    Permission class that allows access only to pharmacy administrator users.
    
    Used for pharmacy management endpoints.
    Does not require verification status.
    """
    
    message = "Only pharmacy administrators can access this resource."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and has pharmacy_admin user type.
        
        Args:
            request: HTTP request object
            view: View being accessed
            
        Returns:
            bool: True if user is authenticated pharmacy admin, False otherwise
        """
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'user_type') and
            request.user.user_type == 'pharmacy_admin'
        )


class IsVerifiedPharmacy(permissions.BasePermission):
    """
    Permission class that allows access only to verified pharmacy administrators.
    
    Requires both:
    - user_type must be 'pharmacy_admin'
    - is_verified must be True
    
    Used for sensitive pharmacy operations like order fulfillment.
    """
    
    message = "Only verified pharmacy administrators can access this resource."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated, pharmacy admin, and verified.
        
        Args:
            request: HTTP request object
            view: View being accessed
            
        Returns:
            bool: True if user is verified pharmacy admin, False otherwise
        """
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'user_type') and
            request.user.user_type == 'pharmacy_admin' and
            hasattr(request.user, 'is_verified') and
            request.user.is_verified is True
        )
