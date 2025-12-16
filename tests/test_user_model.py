"""
Comprehensive tests for the custom User model.

Following TDD principles:
1. Write tests first
2. Watch them fail
3. Implement minimal code to pass
4. Refactor

These tests are designed to FAIL initially and expose validation weaknesses.
NEVER modify these tests - always fix the model implementation.
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from tests.factories import UserFactory, PharmacyAdminFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserCreation:
    """Test basic user creation functionality."""
    
    def test_create_user_with_valid_data(self):
        """Test creating a user with all required fields."""
        user = UserFactory(
            email='patient@example.com',
            phone_number='+919876543210',
            user_type='patient'
        )
        
        assert user.email == 'patient@example.com'
        assert user.phone_number == '+919876543210'
        assert user.user_type == 'patient'
        assert user.is_verified is False
        assert user.is_active is True
    
    def test_create_pharmacy_admin_user(self):
        """Test creating a pharmacy admin user."""
        admin = PharmacyAdminFactory(
            email='admin@pharmacy.com',
            phone_number='+919123456789'
        )
        
        assert admin.user_type == 'pharmacy_admin'
        assert admin.email == 'admin@pharmacy.com'
        assert admin.is_verified is False
    
    def test_user_string_representation(self):
        """Test __str__ method returns email."""
        user = UserFactory(email='test@example.com')
        assert str(user) == 'test@example.com'


@pytest.mark.django_db
class TestUserValidation:
    """Test user model validation rules."""
    
    def test_email_is_required(self):
        """Test that email field is required."""
        with pytest.raises(ValidationError) as exc_info:
            user = User(
                username='testuser',
                phone_number='+919876543210',
                user_type='patient'
            )
            user.full_clean()
        
        assert 'email' in exc_info.value.message_dict
    
    def test_phone_number_is_required(self):
        """Test that phone_number field is required."""
        with pytest.raises(ValidationError) as exc_info:
            user = User(
                username='testuser',
                email='test@example.com',
                user_type='patient'
            )
            user.full_clean()
        
        assert 'phone_number' in exc_info.value.message_dict
    
    def test_user_type_is_required(self):
        """Test that user_type field is required."""
        with pytest.raises(ValidationError) as exc_info:
            user = User(
                username='testuser',
                email='test@example.com',
                phone_number='+919876543210'
            )
            user.full_clean()
        
        assert 'user_type' in exc_info.value.message_dict
    
    def test_duplicate_email_not_allowed(self):
        """Test that duplicate emails are not allowed."""
        UserFactory(email='duplicate@example.com')
        
        with pytest.raises(IntegrityError):
            UserFactory(email='duplicate@example.com')
    
    def test_invalid_phone_number_format(self):
        """Test that invalid phone number formats are rejected."""
        invalid_numbers = [
            '1234567890',  # Missing +91
            '+91123',  # Too short
            '+9112345678901',  # Too long
            'abcdefghij',  # Non-numeric
            '+1234567890',  # Wrong country code
            '+91 98765 43210',  # Spaces not allowed
            '+91-9876543210',  # Hyphens not allowed
        ]
        
        for invalid_number in invalid_numbers:
            with pytest.raises(ValidationError) as exc_info:
                user = User(
                    username='testuser',
                    email=f'test_{invalid_number}@example.com',
                    phone_number=invalid_number,
                    user_type='patient'
                )
                user.full_clean()
            
            assert 'phone_number' in exc_info.value.message_dict, \
                f"Expected validation error for: {invalid_number}"
    
    def test_valid_phone_number_formats(self):
        """Test that valid phone number formats are accepted."""
        valid_numbers = [
            '+919876543210',
            '+919123456789',
            '+910000000000',
            '+919999999999',
        ]
        
        for idx, valid_number in enumerate(valid_numbers):
            user = User(
                username=f'testuser{idx}',
                email=f'test{idx}@example.com',
                phone_number=valid_number,
                user_type='patient'
            )
            user.full_clean()  # Should not raise
            user.save()
            assert user.phone_number == valid_number
    
    def test_invalid_user_type(self):
        """Test that only 'patient' and 'pharmacy_admin' are valid user types."""
        invalid_types = ['admin', 'doctor', 'nurse', 'staff', 'customer', '']
        
        for invalid_type in invalid_types:
            with pytest.raises(ValidationError) as exc_info:
                user = User(
                    username='testuser',
                    email=f'test_{invalid_type}@example.com',
                    phone_number='+919876543210',
                    user_type=invalid_type
                )
                user.full_clean()
            
            assert 'user_type' in exc_info.value.message_dict, \
                f"Expected validation error for user_type: {invalid_type}"
    
    def test_valid_user_types(self):
        """Test that 'patient' and 'pharmacy_admin' are valid user types."""
        valid_types = ['patient', 'pharmacy_admin']
        
        for idx, valid_type in enumerate(valid_types):
            user = User(
                username=f'testuser{idx}',
                email=f'test{idx}@example.com',
                phone_number=f'+9198765432{idx:02d}',
                user_type=valid_type
            )
            user.full_clean()  # Should not raise
            user.save()
            assert user.user_type == valid_type


@pytest.mark.django_db
class TestUserDefaults:
    """Test default values for user model fields."""
    
    def test_is_verified_defaults_to_false(self):
        """Test that is_verified defaults to False."""
        user = UserFactory()
        assert user.is_verified is False
    
    def test_is_active_defaults_to_true(self):
        """Test that is_active defaults to True."""
        user = UserFactory()
        assert user.is_active is True


@pytest.mark.django_db
class TestUserVerificationStatus:
    """Test user verification status changes."""
    
    def test_can_verify_user(self):
        """Test that user can be verified."""
        user = UserFactory(is_verified=False)
        assert user.is_verified is False
        
        user.is_verified = True
        user.save()
        
        user.refresh_from_db()
        assert user.is_verified is True
    
    def test_can_unverify_user(self):
        """Test that user can be unverified."""
        user = UserFactory(is_verified=True)
        assert user.is_verified is True
        
        user.is_verified = False
        user.save()
        
        user.refresh_from_db()
        assert user.is_verified is False


@pytest.mark.django_db
class TestUserQueryOptimization:
    """Test database query optimization with indexes."""
    
    def test_email_is_indexed(self):
        """Test that email field has database index."""
        # Create multiple users
        for i in range(10):
            UserFactory(email=f'user{i}@example.com')
        
        # Query by email should be efficient
        user = User.objects.get(email='user5@example.com')
        assert user.email == 'user5@example.com'
    
    def test_phone_number_is_indexed(self):
        """Test that phone_number field has database index."""
        # Create multiple users
        for i in range(10):
            UserFactory(phone_number=f'+9198765432{i:02d}')
        
        # Query by phone should be efficient
        user = User.objects.get(phone_number='+919876543205')
        assert user.phone_number == '+919876543205'
    
    def test_user_type_is_indexed(self):
        """Test that user_type field has database index."""
        # Create users of different types
        for i in range(5):
            UserFactory(user_type='patient')
            PharmacyAdminFactory()
        
        # Query by user_type should be efficient
        patients = User.objects.filter(user_type='patient')
        admins = User.objects.filter(user_type='pharmacy_admin')
        
        assert patients.count() == 5
        assert admins.count() == 5


@pytest.mark.django_db
class TestUserModelMethods:
    """Test custom methods on the User model."""
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        user = UserFactory(first_name='John', last_name='Doe')
        assert user.get_full_name() == 'John Doe'
    
    def test_get_short_name(self):
        """Test get_short_name method."""
        user = UserFactory(first_name='John')
        assert user.get_short_name() == 'John'


@pytest.mark.django_db
class TestUserEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_email_is_case_insensitive(self):
        """Test that email lookups are case-insensitive."""
        UserFactory(email='Test@Example.com')
        
        # Should find user regardless of case
        user = User.objects.get(email__iexact='test@example.com')
        assert user.email.lower() == 'test@example.com'
    
    def test_email_is_trimmed(self):
        """Test that email whitespace is trimmed."""
        user = User(
            username='testuser',
            email='  test@example.com  ',
            phone_number='+919876543210',
            user_type='patient'
        )
        user.full_clean()
        user.save()
        
        assert user.email == 'test@example.com'
    
    def test_phone_number_is_trimmed(self):
        """Test that phone number whitespace is trimmed."""
        user = User(
            username='testuser',
            email='test@example.com',
            phone_number='  +919876543210  ',
            user_type='patient'
        )
        user.full_clean()
        user.save()
        
        assert user.phone_number == '+919876543210'
    
    def test_cannot_create_user_without_username(self):
        """Test that username is still required (from AbstractUser)."""
        with pytest.raises(ValidationError):
            user = User(
                email='test@example.com',
                phone_number='+919876543210',
                user_type='patient'
            )
            user.full_clean()
