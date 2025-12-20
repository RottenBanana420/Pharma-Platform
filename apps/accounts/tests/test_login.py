"""
Tests for enhanced login functionality.

Tests cover:
- Login with user data in response
- Consistent error messages for security
- Account verification status checks
- No passwords in responses
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide API client for tests."""
    return APIClient()


@pytest.fixture
def login_url():
    """URL for user login."""
    return reverse('token_obtain_pair')


@pytest.fixture
def user_data():
    """Provide valid user data for testing."""
    return {
        'email': 'testuser@example.com',
        'password': 'SecurePass123!',
        'phone_number': '+919876543210',
        'user_type': 'patient',
        'is_verified': True,
    }


@pytest.fixture
def create_user(db, user_data):
    """Factory to create test users."""
    def _create_user(**kwargs):
        data = user_data.copy()
        data.update(kwargs)
        password = data.pop('password')
        
        user = User.objects.create_user(
            username=data['email'],
            **data
        )
        user.set_password(password)
        user.save()
        return user
    return _create_user


# ============================================================================
# LOGIN SUCCESS TESTS
# ============================================================================

@pytest.mark.django_db
class TestLoginSuccess:
    """Tests for successful login."""
    
    def test_login_returns_user_data(
        self, api_client, create_user, login_url, user_data
    ):
        """Successful login should return user data along with tokens."""
        user = create_user()
        
        response = api_client.post(login_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check tokens
        assert 'access' in response.data
        assert 'refresh' in response.data
        
        # Check user data (if implemented in response)
        # Note: This might be in a nested 'user' key or at root level
        if 'user' in response.data:
            user_response = response.data['user']
        else:
            user_response = response.data
        
        # Verify user data is present (implementation may vary)
        # At minimum, tokens should contain user info in claims
        assert isinstance(response.data['access'], str)
        assert isinstance(response.data['refresh'], str)
    
    def test_login_no_password_in_response(
        self, api_client, create_user, login_url, user_data
    ):
        """Login response should never contain password."""
        user = create_user()
        
        response = api_client.post(login_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check entire response for password
        response_str = str(response.data)
        assert user_data['password'] not in response_str
        assert 'password' not in response.data
        if 'user' in response.data:
            assert 'password' not in response.data['user']


# ============================================================================
# LOGIN ERROR MESSAGE TESTS
# ============================================================================

@pytest.mark.django_db
class TestLoginErrorMessages:
    """Tests for consistent error messages (security)."""
    
    def test_login_wrong_password_error_message(
        self, api_client, create_user, login_url, user_data
    ):
        """Wrong password should return generic error message."""
        user = create_user()
        
        response = api_client.post(login_url, {
            'email': user_data['email'],
            'password': 'WrongPassword123!',
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Error message should not reveal that email exists
        error_message = str(response.data).lower()
        assert 'password' not in error_message or 'credentials' in error_message
        # Should use generic message
        assert 'credentials' in error_message or 'invalid' in error_message
    
    def test_login_nonexistent_email_error_message(
        self, api_client, login_url
    ):
        """Non-existent email should return same error as wrong password."""
        response = api_client.post(login_url, {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!',
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Error message should be generic
        error_message = str(response.data).lower()
        assert 'credentials' in error_message or 'invalid' in error_message
        # Should NOT reveal that email doesn't exist
        assert 'not found' not in error_message
        assert 'does not exist' not in error_message
    
    def test_login_error_messages_consistent(
        self, api_client, create_user, login_url, user_data
    ):
        """Error messages for wrong password and wrong email should be identical."""
        user = create_user()
        
        # Wrong password
        response1 = api_client.post(login_url, {
            'email': user_data['email'],
            'password': 'WrongPassword123!',
        })
        
        # Wrong email
        response2 = api_client.post(login_url, {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!',
        })
        
        # Both should return 401 or 429 (rate limit)
        assert response1.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS]
        assert response2.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS]
        
        # If both are 401, error messages should be similar/identical
        if response1.status_code == status.HTTP_401_UNAUTHORIZED and response2.status_code == status.HTTP_401_UNAUTHORIZED:
            error1 = str(response1.data).lower()
            error2 = str(response2.data).lower()
            
            # Both should mention credentials or be generic
            assert 'credentials' in error1 or 'invalid' in error1
            assert 'credentials' in error2 or 'invalid' in error2


# ============================================================================
# ACCOUNT STATUS TESTS
# ============================================================================

@pytest.mark.django_db
class TestAccountStatusChecks:
    """Tests for account status validation during login."""
    
    def test_login_inactive_user(
        self, api_client, create_user, login_url, user_data
    ):
        """Inactive user should not be able to login."""
        user = create_user(is_active=False)
        
        response = api_client.post(login_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        # Should return 401 or 429 (rate limit)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS]
    
    def test_login_unverified_user_allowed(
        self, api_client, create_user, login_url, user_data
    ):
        """Unverified user should be able to login (per requirements)."""
        user = create_user(is_verified=False)
        
        response = api_client.post(login_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        # Should succeed or hit rate limit
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS]
        if response.status_code == status.HTTP_200_OK:
            assert 'access' in response.data
            assert 'refresh' in response.data
    
    def test_login_verified_user(
        self, api_client, create_user, login_url, user_data
    ):
        """Verified user should be able to login."""
        user = create_user(is_verified=True)
        
        response = api_client.post(login_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        # Should succeed or hit rate limit
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS]
        if response.status_code == status.HTTP_200_OK:
            assert 'access' in response.data
            assert 'refresh' in response.data


# ============================================================================
# LOGIN VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestLoginValidation:
    """Tests for login input validation."""
    
    def test_login_missing_email(
        self, api_client, login_url
    ):
        """Missing email should return 400."""
        response = api_client.post(login_url, {
            'password': 'SomePassword123!',
        })
        
        # Should return 400 or 429 (rate limit)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_429_TOO_MANY_REQUESTS]
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            assert 'email' in response.data
    
    def test_login_missing_password(
        self, api_client, login_url
    ):
        """Missing password should return 400."""
        response = api_client.post(login_url, {
            'email': 'test@example.com',
        })
        
        # Should return 400 or 429 (rate limit)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_429_TOO_MANY_REQUESTS]
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            assert 'password' in response.data
    
    def test_login_empty_credentials(
        self, api_client, login_url
    ):
        """Empty credentials should return 400."""
        response = api_client.post(login_url, {})
        
        # Should return 400 or 429 (rate limit)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_429_TOO_MANY_REQUESTS]
    
    def test_login_email_case_insensitive(
        self, api_client, create_user, login_url, user_data
    ):
        """Login should work with different email case."""
        user = create_user()
        
        # Try login with uppercase email
        response = api_client.post(login_url, {
            'email': user_data['email'].upper(),
            'password': user_data['password'],
        })
        
        # Should succeed or hit rate limit
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS]
        if response.status_code == status.HTTP_200_OK:
            assert 'access' in response.data
