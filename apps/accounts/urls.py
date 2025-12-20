"""
URL configuration for accounts app.

Provides endpoints for:
- User registration
- Password validation
- Token obtain (login)
- Token refresh
- Token verify
- Logout
- Protected endpoint (testing)
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    UserRegistrationView,
    PasswordValidationView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    protected_view,
    UserProfileView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    # Registration endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('validate-password/', PasswordValidationView.as_view(), name='validate_password'),
    
    # JWT Token endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Logout endpoint
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Protected endpoint for testing
    path('protected/', protected_view, name='protected'),
    
    # Profile endpoints
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    
    # Password management endpoints
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
