"""
Custom serializers for JWT authentication and user registration.

Provides:
- Custom token serializers with additional claims
- User registration serializer with comprehensive validation
- Password validation serializer for pre-submission checks
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles:
    - Email validation (format, uniqueness, normalization)
    - Password validation (strength requirements)
    - Password confirmation matching
    - Phone number validation (format, uniqueness)
    - User type validation
    - Secure password hashing
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'confirm_password',
            'phone_number', 'user_type', 'is_verified'
        ]
        read_only_fields = ['id', 'is_verified']
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': True},
            'user_type': {'required': True},
        }
    
    def validate_email(self, value):
        """
        Validate email field.
        
        - Trim whitespace
        - Convert to lowercase
        - Check uniqueness (case-insensitive)
        """
        if not value:
            raise serializers.ValidationError("Email address is required.")
        
        # Trim and normalize
        value = value.strip().lower()
        
        # Check uniqueness (case-insensitive)
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with that email already exists."
            )
        
        return value
    
    def validate_password(self, value):
        """
        Validate password strength using Django's password validators.
        """
        # Create a temporary user instance for validation
        user = User(
            email=self.initial_data.get('email', ''),
            phone_number=self.initial_data.get('phone_number', ''),
            user_type=self.initial_data.get('user_type', 'patient'),
        )
        
        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value
    
    def validate_phone_number(self, value):
        """
        Validate phone number field.
        
        - Trim whitespace
        - Check format (handled by model validator)
        - Check uniqueness
        """
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        # Trim whitespace
        value = value.strip()
        
        # Check uniqueness
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "A user with that phone number already exists."
            )
        
        return value
    
    def validate_user_type(self, value):
        """
        Validate user type is one of the allowed choices.
        """
        if not value:
            raise serializers.ValidationError("User type is required.")
        
        valid_types = [choice[0] for choice in User.USER_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"User type must be one of: {', '.join(valid_types)}"
            )
        
        return value
    
    def validate(self, attrs):
        """
        Object-level validation.
        
        - Ensure password and confirm_password match
        """
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        
        if password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """
        Create user with hashed password.
        
        - Remove confirm_password from data
        - Hash password securely
        - Set is_verified to False by default
        """
        # Remove confirm_password as it's not a model field
        validated_data.pop('confirm_password', None)
        
        # Extract password
        password = validated_data.pop('password')
        
        # Create user with username set to email
        user = User.objects.create_user(
            username=validated_data['email'],
            **validated_data
        )
        
        # Set password (hashes it)
        user.set_password(password)
        
        # Ensure is_verified is False for new users
        user.is_verified = False
        
        user.save()
        
        return user


class PasswordValidationSerializer(serializers.Serializer):
    """
    Serializer for validating password strength.
    
    Used for pre-submission validation to provide
    immediate feedback to users about password requirements.
    """
    
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
    )
    
    def validate_password(self, value):
        """
        Validate password against all Django password validators.
        """
        if not value:
            raise serializers.ValidationError("Password is required.")
        
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value


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
        
        # Try to get user by email (case-insensitive)
        try:
            user = User.objects.get(email__iexact=email)
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



class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile retrieval (read-only).
    
    Returns all relevant user fields except password.
    Used for GET requests to profile endpoint.
    """
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_number', 'user_type', 'is_verified',
            'first_name', 'last_name', 'date_joined'
        ]
        read_only_fields = fields  # All fields are read-only


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile updates.
    
    Allows updates to: phone_number, first_name, last_name
    Prevents updates to: email, user_type, is_verified (security)
    """
    
    class Meta:
        model = User
        fields = ['phone_number', 'first_name', 'last_name']
    
    def validate_phone_number(self, value):
        """
        Validate phone number field.
        
        - Trim whitespace
        - Check format (handled by model validator)
        - Check uniqueness (excluding current user)
        """
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        # Trim whitespace
        value = value.strip()
        
        # Check uniqueness (exclude current user)
        user = self.instance
        if user and User.objects.filter(phone_number=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                "A user with that phone number already exists."
            )
        
        return value
    
    def validate_first_name(self, value):
        """
        Validate first name is not empty if provided.
        """
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("First name cannot be empty.")
        return value
    
    def validate_last_name(self, value):
        """
        Validate last name is not empty if provided.
        """
        if value is not None:
            value = value.strip()
            if not value:
                raise serializers.ValidationError("Last name cannot be empty.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    
    Requires old password verification before allowing change.
    """
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
    )
    confirm_new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )
    
    def validate_old_password(self, value):
        """
        Validate that old password is correct.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        """
        Validate new password strength using Django's password validators.
        """
        user = self.context['request'].user
        
        try:
            validate_password(value, user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value
    
    def validate(self, attrs):
        """
        Object-level validation.
        
        - Ensure new password and confirmation match
        """
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')
        
        if new_password != confirm_new_password:
            raise serializers.ValidationError({
                'confirm_new_password': 'Passwords do not match.'
            })
        
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    
    Accepts email and generates reset token.
    Does not reveal if email exists (security).
    """
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """
        Validate email format and normalize.
        """
        if not value:
            raise serializers.ValidationError("Email address is required.")
        
        # Trim and normalize
        value = value.strip().lower()
        
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    
    Validates token and sets new password.
    """
    
    token = serializers.CharField(required=True)
    uid = serializers.IntegerField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
    )
    confirm_new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )
    
    def validate_new_password(self, value):
        """
        Validate new password strength.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value
    
    def validate(self, attrs):
        """
        Object-level validation.
        
        - Ensure passwords match
        - Validate token
        """
        new_password = attrs.get('new_password')
        confirm_new_password = attrs.get('confirm_new_password')
        
        if new_password != confirm_new_password:
            raise serializers.ValidationError({
                'confirm_new_password': 'Passwords do not match.'
            })
        
        # Validate token and get user
        from django.contrib.auth.tokens import default_token_generator
        
        uid = attrs.get('uid')
        token = attrs.get('token')
        
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'token': 'Invalid reset token.'
            })
        
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({
                'token': 'Invalid or expired reset token.'
            })
        
        # Store user for use in view
        attrs['user'] = user
        
        return attrs
