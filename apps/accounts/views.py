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


class UserProfileView(APIView):
    """
    User profile endpoint for retrieval and updates.
    
    GET: Retrieve current authenticated user's profile
    PATCH: Update current authenticated user's profile
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Retrieve current authenticated user's profile.
        
        Returns:
            200: User profile data
            401: Unauthorized
        """
        from .serializers import UserProfileSerializer
        
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """
        Update current authenticated user's profile.
        
        Allows updates to: phone_number, first_name, last_name
        Ignores: email, user_type, is_verified (security)
        
        Returns:
            200: Updated profile data
            400: Validation errors
            401: Unauthorized
        """
        from .serializers import UserProfileUpdateSerializer, UserProfileSerializer
        
        # Use update serializer for validation
        serializer = UserProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True  # Allow partial updates
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Return full profile using read serializer
            response_serializer = UserProfileSerializer(request.user)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    """
    Password change endpoint.
    
    Requires old password verification before allowing change.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Change password for authenticated user.
        
        Returns:
            200: Password changed successfully
            400: Validation errors
            401: Unauthorized
        """
        from .serializers import PasswordChangeSerializer
        
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Set new password
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            logger.info(f"Password changed for user: {request.user.email}")
            
            return Response(
                {'detail': 'Password changed successfully.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    Password reset request endpoint.
    
    Generates reset token and sends email (stubbed for now).
    Always returns success to not reveal if email exists.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Request password reset token.
        
        Returns:
            200: Always (security - don't reveal if email exists)
            400: Invalid email format
        """
        from .serializers import PasswordResetRequestSerializer
        from django.contrib.auth.tokens import default_token_generator
        
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Try to find user (case-insensitive)
            try:
                user = User.objects.get(email__iexact=email)
                
                # Generate reset token
                token = default_token_generator.make_token(user)
                
                # In production, send email with reset link
                # For now, log to console
                logger.info(
                    f"Password reset requested for {email}. "
                    f"Token: {token}, UID: {user.pk}"
                )
                
                # TODO: Send email with reset link
                # reset_url = f"{settings.FRONTEND_URL}/reset-password/{user.pk}/{token}/"
                # send_mail(...)
                
            except User.DoesNotExist:
                # Don't reveal that user doesn't exist
                logger.info(f"Password reset requested for non-existent email: {email}")
            
            # Always return success
            return Response(
                {'detail': 'If an account exists with this email, a password reset link has been sent.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation endpoint.
    
    Validates token and sets new password.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Confirm password reset with token.
        
        Returns:
            200: Password reset successfully
            400: Invalid token or validation errors
        """
        from .serializers import PasswordResetConfirmSerializer
        
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            # Get user from validated data
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            logger.info(f"Password reset completed for user: {user.email}")
            
            return Response(
                {'detail': 'Password has been reset successfully.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
