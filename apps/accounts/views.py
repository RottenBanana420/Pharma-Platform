"""
Authentication views for JWT token management.

Provides views for:
- Token obtain (login)
- Token refresh
- Logout (token blacklisting)
- Protected endpoint (for testing)
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model

from .serializers import CustomTokenObtainPairSerializer

User = get_user_model()
logger = logging.getLogger('accounts.authentication')


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view with logging.
    
    Logs successful and failed authentication attempts.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Handle token obtain request.
        
        Args:
            request: HTTP request with email and password
            
        Returns:
            Response with access and refresh tokens or error
        """
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            # Log successful authentication
            email = request.data.get('email', 'unknown')
            ip_address = self.get_client_ip(request)
            logger.info(
                f"Successful authentication for user: {email} from IP: {ip_address}"
            )
        else:
            # Log failed authentication
            email = request.data.get('email', 'unknown')
            ip_address = self.get_client_ip(request)
            logger.warning(
                f"Failed authentication attempt for user: {email} from IP: {ip_address}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view with logging.
    
    Logs token refresh events.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Handle token refresh request.
        
        Args:
            request: HTTP request with refresh token
            
        Returns:
            Response with new access token
        """
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            ip_address = self.get_client_ip(request)
            logger.info(f"Token refreshed from IP: {ip_address}")
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    Logout view that blacklists the refresh token.
    
    Requires refresh token in request body.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Blacklist the refresh token.
        
        Args:
            request: HTTP request with refresh token
            
        Returns:
            Success response or error
        """
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'detail': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist the token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Log logout
            ip_address = self.get_client_ip(request)
            logger.info(f"User logged out from IP: {ip_address}")
            
            return Response(
                {'detail': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
            
        except TokenError as e:
            return Response(
                {'detail': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {'detail': 'An error occurred during logout.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    """
    Protected endpoint for testing authentication.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        request: HTTP request with Authorization header
        
    Returns:
        User data if authenticated
    """
    user = request.user
    return Response({
        'user_id': user.id,
        'email': user.email,
        'user_type': user.user_type,
        'is_verified': user.is_verified,
    }, status=status.HTTP_200_OK)
