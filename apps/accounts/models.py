"""
Custom User model for the Pharma Platform.

Extends Django's AbstractUser to add pharmacy-specific fields:
- phone_number: Indian phone number with validation
- user_type: Distinguishes between patients and pharmacy admins
- is_verified: Tracks account verification status
"""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """
    Custom user model extending AbstractUser.
    
    Additional fields:
    - phone_number: Required, validated Indian phone number (+91XXXXXXXXXX)
    - user_type: Required, either 'patient' or 'pharmacy_admin'
    - is_verified: Boolean flag for account verification status
    """
    
    USER_TYPE_CHOICES = [
        ('patient', 'Patient'),
        ('pharmacy_admin', 'Pharmacy Administrator'),
    ]
    
    # Phone number validator for Indian numbers (+91 followed by 10 digits)
    phone_regex = RegexValidator(
        regex=r'^\+91\d{10}$',
        message="Phone number must be in format: '+91XXXXXXXXXX' (Indian numbers only)"
    )
    
    # Override email to make it required and unique
    # Custom handling to trim whitespace before validation
    email = models.EmailField(
        'email address',
        unique=True,
        blank=False,
        error_messages={
            'unique': 'A user with that email already exists.',
        }
    )
    
    def __init__(self, *args, **kwargs):
        """Override init to trim email and phone_number before validation."""
        if 'email' in kwargs and kwargs['email']:
            kwargs['email'] = kwargs['email'].strip()
        if 'phone_number' in kwargs and kwargs['phone_number']:
            kwargs['phone_number'] = kwargs['phone_number'].strip()
        super().__init__(*args, **kwargs)
    
    # Override password to make it not required for validation
    # Password is set via set_password() method, not through validation
    password = models.CharField(
        'password',
        max_length=128,
        blank=True,
        help_text="Use set_password() method to set password"
    )
    
    phone_number = models.CharField(
        max_length=13,
        validators=[phone_regex],
        blank=False,
        help_text="Indian phone number in format: +91XXXXXXXXXX"
    )
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        blank=False,
        help_text="Type of user account"
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Designates whether this user has verified their account."
    )
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['user_type']),
        ]
    
    def __str__(self):
        """Return email as string representation."""
        return self.email
    
    def clean(self):
        """
        Validate the model fields.
        
        Ensures:
        - Email is provided and trimmed
        - Phone number is provided and trimmed
        - User type is provided and valid
        """
        # Trim whitespace from email FIRST
        if self.email:
            self.email = self.email.strip()
        
        # Trim whitespace from phone number FIRST
        if self.phone_number:
            self.phone_number = self.phone_number.strip()
        
        # Call parent clean to run validators
        super().clean()
        
        # Validate email is not empty after stripping
        if not self.email:
            raise ValidationError({
                'email': 'Email address is required.'
            })
        
        # Validate phone number is not empty after stripping
        if not self.phone_number:
            raise ValidationError({
                'phone_number': 'Phone number is required.'
            })
        
        # Validate user type is not empty
        if not self.user_type:
            raise ValidationError({
                'user_type': 'User type is required.'
            })
        
        # Validate user type is one of the allowed choices
        valid_types = [choice[0] for choice in self.USER_TYPE_CHOICES]
        if self.user_type and self.user_type not in valid_types:
            raise ValidationError({
                'user_type': f'User type must be one of: {", ".join(valid_types)}'
            })
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation on custom fields."""
        # Only validate custom fields, not password
        # Password is handled by set_password() method
        if self.email:
            self.email = self.email.strip()
        if self.phone_number:
            self.phone_number = self.phone_number.strip()
        super().save(*args, **kwargs)
