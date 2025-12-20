"""
Tests for password validation endpoint.

Tests cover:
- Password strength validation
- Detailed error messages for weak passwords
- Success response for strong passwords
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Provide API client for tests."""
    return APIClient()


@pytest.fixture
def password_validation_url():
    """URL for password validation."""
    return reverse('validate_password')


# ============================================================================
# PASSWORD VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestPasswordValidation:
    """Tests for password validation endpoint."""
    
    def test_validate_strong_password(
        self, api_client, password_validation_url
    ):
        """Strong password should pass validation."""
        response = api_client.post(password_validation_url, {
            'password': 'SecurePass123!',
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'valid' in response.data or 'message' in response.data
    
    def test_validate_password_no_uppercase(
        self, api_client, password_validation_url
    ):
        """Password without uppercase should fail with specific error."""
        response = api_client.post(password_validation_url, {
            'password': 'weakpass123!',
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        # Should mention uppercase requirement
        error_message = str(response.data['password']).lower()
        assert 'uppercase' in error_message
    
    def test_validate_password_no_number(
        self, api_client, password_validation_url
    ):
        """Password without number should fail with specific error."""
        response = api_client.post(password_validation_url, {
            'password': 'WeakPassword!',
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        # Should mention digit requirement
        error_message = str(response.data['password']).lower()
        assert 'digit' in error_message or 'number' in error_message
    
    def test_validate_password_no_special_char(
        self, api_client, password_validation_url
    ):
        """Password without special character should fail with specific error."""
        response = api_client.post(password_validation_url, {
            'password': 'WeakPassword123',
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        # Should mention special character requirement
        error_message = str(response.data['password']).lower()
        assert 'special' in error_message
    
    def test_validate_password_too_short(
        self, api_client, password_validation_url
    ):
        """Password shorter than 8 characters should fail."""
        response = api_client.post(password_validation_url, {
            'password': 'Short1!',
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        # Should mention length requirement
        error_message = str(response.data['password']).lower()
        assert '8' in error_message or 'short' in error_message
    
    def test_validate_common_password(
        self, api_client, password_validation_url
    ):
        """Common password should fail."""
        response = api_client.post(password_validation_url, {
            'password': 'password',  # Very common password
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        # Should mention common password
        error_message = str(response.data['password']).lower()
        assert 'common' in error_message
    
    def test_validate_numeric_password(
        self, api_client, password_validation_url
    ):
        """Entirely numeric password should fail."""
        response = api_client.post(password_validation_url, {
            'password': '12345678',
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        # Should mention numeric-only issue
        error_message = str(response.data['password']).lower()
        assert 'numeric' in error_message or 'number' in error_message
    
    def test_validate_missing_password(
        self, api_client, password_validation_url
    ):
        """Missing password should return 400."""
        response = api_client.post(password_validation_url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
    
    def test_validate_empty_password(
        self, api_client, password_validation_url
    ):
        """Empty password should return 400."""
        response = api_client.post(password_validation_url, {
            'password': '',
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
    
    def test_validate_multiple_weak_passwords(
        self, api_client, password_validation_url
    ):
        """Multiple validation failures should return all errors."""
        response = api_client.post(password_validation_url, {
            'password': 'weak',  # Too short, no uppercase, no number, no special
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data
        # Should have multiple error messages
        errors = response.data['password']
        assert len(errors) > 1  # Multiple validation failures
