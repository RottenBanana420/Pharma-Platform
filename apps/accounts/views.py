"""
Authentication views for JWT token management and user registration.

Provides views for:
- User registration with validation
- Password validation
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
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    PasswordValidationSerializer,
)

User = get_user_model()
logger = logging.getLogger('accounts.authentication')


class UserRegistrationView(APIView):
    """
    User registration endpoint.
    
    Handles user registration with comprehensive validation:
    - Email format and uniqueness
    - Password strength requirements
    - Phone number format and uniqueness
    - User type validation
    
    Rate limited to prevent abuse.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'registration'
    
    def post(self, request):
        """
        Register a new user.
        
        Args:
            request: HTTP request with registration data
            
        Returns:
            201: User created successfully with user data (no password)
            400: Validation errors
        """
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Log registration
            ip_address = self.get_client_ip(request)
            logger.info(
                f"New user registered: {user.email} from IP: {ip_address}"
            )
            
            # Return user data (password excluded by serializer)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        # Return validation errors
        return Response(
            serializer.errors,
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


class PasswordValidationView(APIView):
    """
    Password validation endpoint.
    
    Validates password strength without creating a user.
    Useful for client-side validation before form submission.
    
    No rate limiting as this is a validation helper.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Validate password strength.
        
        Args:
            request: HTTP request with password
            
        Returns:
            200: Password is valid
            400: Password validation errors
        """
        serializer = PasswordValidationSerializer(data=request.data)
        
        if serializer.is_valid():
            return Response(
                {'valid': True, 'message': 'Password meets all requirements.'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain view with logging and rate limiting.
    
    Logs successful and failed authentication attempts.
    Rate limited to prevent brute force attacks.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    
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
    Custom token refresh view with logging and rate limiting.
    
    Logs token refresh events.
    Rate limited to prevent abuse.
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'token_refresh'
    
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
