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
]
