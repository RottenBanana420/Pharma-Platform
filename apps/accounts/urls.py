"""
URL configuration for accounts app.

Provides endpoints for:
- Token obtain (login)
- Token refresh
- Token verify
- Logout
- Protected endpoint (testing)
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    protected_view,
)

urlpatterns = [
    # JWT Token endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Logout endpoint
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Protected endpoint for testing
    path('protected/', protected_view, name='protected'),
]
