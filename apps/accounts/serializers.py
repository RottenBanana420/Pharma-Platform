"""
Custom serializers for JWT authentication.

Provides custom token serializers that add additional claims to JWT tokens.
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that adds user-specific claims to the token.
    
    Uses email instead of username for authentication.
    
    Additional claims:
    - user_type: Type of user (patient/pharmacy_admin)
    - is_verified: Account verification status
    - email: User's email address
    """
    
    # Override username_field to use email
    username_field = 'email'
    
    @classmethod
    def get_token(cls, user):
        """
        Generate token with custom claims.
        
        Args:
            user: User instance
            
        Returns:
            Token with additional claims
        """
        token = super().get_token(user)
        
        # Add custom claims
        token['user_type'] = user.user_type
        token['is_verified'] = user.is_verified
        token['email'] = user.email
        
        return token
    
    def validate(self, attrs):
        """
        Validate credentials and ensure user is active.
        
        Args:
            attrs: Dictionary with email and password
            
        Returns:
            Validated data with tokens
            
        Raises:
            AuthenticationFailed: If credentials are invalid or user is inactive
        """
        # Get email and password
        email = attrs.get('email')
        password = attrs.get('password')
        
        # Try to get user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('No active account found with the given credentials')
        
        # Check password
        if not user.check_password(password):
            raise AuthenticationFailed('No active account found with the given credentials')
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationFailed('User account is disabled.')
        
        # Set user for token generation
        self.user = user
        
        # Generate tokens
        refresh = self.get_token(user)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

