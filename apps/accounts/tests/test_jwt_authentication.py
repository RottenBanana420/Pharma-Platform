"""
Comprehensive JWT authentication tests following TDD principles.

Tests cover:
- Token obtain with various credentials
- Token refresh and rotation
- Token expiration
- Token validation and security
- Protected endpoints
- Token blacklisting and logout
- Rate limiting
- Password validation
- Custom claims
- Security vulnerabilities
"""
import pytest
import jwt
import time
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from freezegun import freeze_time
from django.conf import settings
from django.core.cache import cache

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide API client for tests."""
    return APIClient()


@pytest.fixture
def user_data():
    """Provide valid user data for testing."""
    return {
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'phone_number': '+919876543210',
        'user_type': 'patient',
        'is_verified': True,
    }


@pytest.fixture
def create_user(db, user_data):
    """Factory to create test users."""
    def _create_user(**kwargs):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        data = user_data.copy()
        data.update(kwargs)
        password = data.pop('password')
        
        # Validate password before creating user
        user = User(**data)
        try:
            validate_password(password, user=user)
        except DjangoValidationError as e:
            # Re-raise as generic Exception for test assertions
            raise Exception(str(e))
        
        # Create user with validated password
        user = User.objects.create_user(
            username=data['email'],
            **data
        )
        user.set_password(password)
        user.save()
        return user
    return _create_user


@pytest.fixture
def authenticated_user(create_user):
    """Create and return an authenticated user."""
    return create_user()


@pytest.fixture
def obtain_token_url():
    """URL for obtaining JWT token."""
    return reverse('token_obtain_pair')


@pytest.fixture
def refresh_token_url():
    """URL for refreshing JWT token."""
    return reverse('token_refresh')


@pytest.fixture
def verify_token_url():
    """URL for verifying JWT token."""
    return reverse('token_verify')


@pytest.fixture
def logout_url():
    """URL for logout (blacklisting token)."""
    return reverse('logout')


@pytest.fixture
def protected_endpoint_url():
    """URL for a protected endpoint (using user detail as example)."""
    # We'll create a simple protected view for testing
    return '/api/auth/protected/'


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test to ensure rate limiting tests are isolated."""
    cache.clear()
    yield
    cache.clear()


# ============================================================================
# TOKEN OBTAIN TESTS
# ============================================================================

@pytest.mark.django_db
class TestTokenObtain:
    """Tests for obtaining JWT tokens."""
    
    def test_obtain_token_with_valid_credentials(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Valid credentials should return access and refresh tokens."""
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert isinstance(response.data['access'], str)
        assert isinstance(response.data['refresh'], str)
    
    def test_obtain_token_with_invalid_password(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Invalid password should return 401."""
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': 'WrongPassword123!',
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'access' not in response.data
    
    def test_obtain_token_with_invalid_email(
        self, api_client, obtain_token_url
    ):
        """Non-existent email should return 401."""
        response = api_client.post(obtain_token_url, {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!',
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_obtain_token_with_missing_credentials(
        self, api_client, obtain_token_url
    ):
        """Missing credentials should return 400."""
        # Missing password
        response = api_client.post(obtain_token_url, {
            'email': 'test@example.com',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Missing email
        response = api_client.post(obtain_token_url, {
            'password': 'SomePassword123!',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Missing both
        response = api_client.post(obtain_token_url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_obtain_token_with_inactive_user(
        self, api_client, create_user, obtain_token_url, user_data
    ):
        """Inactive user should not be able to obtain token."""
        user = create_user(is_active=False)
        
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_structure_and_claims(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Token should contain expected claims."""
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Decode access token without verification to check claims
        access_token = response.data['access']
        decoded = jwt.decode(
            access_token,
            options={"verify_signature": False}
        )
        
        # Standard claims
        assert 'user_id' in decoded
        assert 'exp' in decoded
        assert 'iat' in decoded
        assert 'jti' in decoded
        
        # Custom claims
        assert 'user_type' in decoded
        assert decoded['user_type'] == 'patient'
        assert 'is_verified' in decoded
        assert decoded['is_verified'] is True
        assert 'email' in decoded
        assert decoded['email'] == user_data['email']


# ============================================================================
# TOKEN REFRESH TESTS
# ============================================================================

@pytest.mark.django_db
class TestTokenRefresh:
    """Tests for refreshing JWT tokens."""
    
    def test_refresh_token_with_valid_refresh_token(
        self, api_client, authenticated_user, obtain_token_url, 
        refresh_token_url, user_data
    ):
        """Valid refresh token should return new access token."""
        # First obtain tokens
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        refresh_token = obtain_response.data['refresh']
        
        # Now refresh
        response = api_client.post(refresh_token_url, {
            'refresh': refresh_token,
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    
    def test_refresh_token_with_invalid_refresh_token(
        self, api_client, refresh_token_url
    ):
        """Invalid refresh token should return 401."""
        response = api_client.post(refresh_token_url, {
            'refresh': 'invalid.token.here',
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_with_expired_refresh_token(
        self, api_client, authenticated_user, obtain_token_url,
        refresh_token_url, user_data
    ):
        """Expired refresh token should return 401."""
        # Obtain token
        with freeze_time("2024-01-01 12:00:00"):
            obtain_response = api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
            refresh_token = obtain_response.data['refresh']
        
        # Try to refresh after expiration (8 days later)
        with freeze_time("2024-01-09 12:00:01"):
            response = api_client.post(refresh_token_url, {
                'refresh': refresh_token,
            })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_rotation(
        self, api_client, authenticated_user, obtain_token_url,
        refresh_token_url, user_data
    ):
        """Old refresh token should be invalidated after refresh."""
        # Obtain tokens
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        old_refresh_token = obtain_response.data['refresh']
        
        # Refresh once
        refresh_response = api_client.post(refresh_token_url, {
            'refresh': old_refresh_token,
        })
        assert refresh_response.status_code == status.HTTP_200_OK
        
        # Try to use old refresh token again - should fail
        response = api_client.post(refresh_token_url, {
            'refresh': old_refresh_token,
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token_returns_new_refresh_token(
        self, api_client, authenticated_user, obtain_token_url,
        refresh_token_url, user_data
    ):
        """Refresh should return a new refresh token when rotation is enabled."""
        # Obtain tokens
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        old_refresh_token = obtain_response.data['refresh']
        
        # Refresh
        refresh_response = api_client.post(refresh_token_url, {
            'refresh': old_refresh_token,
        })
        
        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'refresh' in refresh_response.data
        assert refresh_response.data['refresh'] != old_refresh_token


# ============================================================================
# TOKEN EXPIRATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTokenExpiration:
    """Tests for token expiration behavior."""
    
    def test_access_with_expired_access_token(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Expired access token should return 401."""
        # Obtain token
        with freeze_time("2024-01-01 12:00:00"):
            obtain_response = api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
            access_token = obtain_response.data['access']
        
        # Try to access after expiration (16 minutes later)
        with freeze_time("2024-01-01 12:16:01"):
            api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_before_token_expiration(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Valid token should allow access."""
        # Obtain token
        with freeze_time("2024-01-01 12:00:00"):
            obtain_response = api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
            access_token = obtain_response.data['access']
        
        # Access within validity period (14 minutes later)
        with freeze_time("2024-01-01 12:14:00"):
            api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_token_expiration_time_validation(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Token exp claim should be 15 minutes from issue."""
        with freeze_time("2024-01-01 12:00:00") as frozen_time:
            response = api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
            
            access_token = response.data['access']
            decoded = jwt.decode(
                access_token,
                options={"verify_signature": False}
            )
            
            # Calculate expected expiration
            issued_at = decoded['iat']
            expiration = decoded['exp']
            lifetime_seconds = expiration - issued_at
            
            # Should be 15 minutes (900 seconds)
            assert lifetime_seconds == 900


# ============================================================================
# TOKEN VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTokenValidation:
    """Tests for token validation and security."""
    
    def test_access_without_token(
        self, api_client, protected_endpoint_url
    ):
        """Request without token should return 401."""
        response = api_client.get(protected_endpoint_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_with_malformed_token(
        self, api_client, protected_endpoint_url
    ):
        """Malformed token should return 401."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer malformed.token')
        response = api_client.get(protected_endpoint_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_with_tampered_token(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Token with modified payload should fail signature verification."""
        # Obtain valid token
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        access_token = obtain_response.data['access']
        
        # Decode, modify, and re-encode without re-signing
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        decoded['user_id'] = 99999  # Tamper with user_id
        
        # Re-encode without proper signing
        tampered_token = jwt.encode(
            decoded,
            'wrong-secret-key',
            algorithm='HS256'
        )
        
        # Try to use tampered token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
        response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_with_none_algorithm(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Token with 'none' algorithm should be rejected."""
        # Obtain valid token to get structure
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        access_token = obtain_response.data['access']
        
        # Decode and create token with 'none' algorithm
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        
        # Create token with none algorithm
        none_token = jwt.encode(
            decoded,
            '',
            algorithm='none'
        )
        
        # Try to use none-algorithm token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {none_token}')
        response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_with_wrong_signing_key(
        self, api_client, protected_endpoint_url
    ):
        """Token signed with wrong key should fail verification."""
        # Create token with wrong signing key
        payload = {
            'user_id': 1,
            'exp': timezone.now() + timedelta(minutes=15),
            'iat': timezone.now(),
        }
        
        wrong_token = jwt.encode(
            payload,
            'completely-wrong-secret-key',
            algorithm='HS256'
        )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {wrong_token}')
        response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_with_missing_bearer_prefix(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Token without 'Bearer' prefix should be rejected."""
        # Obtain valid token
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        access_token = obtain_response.data['access']
        
        # Send without Bearer prefix
        api_client.credentials(HTTP_AUTHORIZATION=access_token)
        response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# PROTECTED ENDPOINT TESTS
# ============================================================================

@pytest.mark.django_db
class TestProtectedEndpoints:
    """Tests for accessing protected endpoints."""
    
    def test_protected_endpoint_without_auth(
        self, api_client, protected_endpoint_url
    ):
        """Protected endpoint without auth should return 401."""
        response = api_client.get(protected_endpoint_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_protected_endpoint_with_valid_token(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Protected endpoint with valid token should return 200."""
        # Obtain token
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        access_token = obtain_response.data['access']
        
        # Access protected endpoint
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_protected_endpoint_with_expired_token(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Protected endpoint with expired token should return 401."""
        # Obtain token
        with freeze_time("2024-01-01 12:00:00"):
            obtain_response = api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
            access_token = obtain_response.data['access']
        
        # Try to access after expiration
        with freeze_time("2024-01-01 12:16:01"):
            api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
            response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# TOKEN BLACKLISTING & LOGOUT TESTS
# ============================================================================

@pytest.mark.django_db
class TestTokenBlacklisting:
    """Tests for token blacklisting and logout functionality."""
    
    def test_logout_blacklists_refresh_token(
        self, api_client, authenticated_user, obtain_token_url,
        logout_url, refresh_token_url, user_data
    ):
        """Logout should blacklist the refresh token."""
        # Obtain tokens
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        refresh_token = obtain_response.data['refresh']
        
        # Logout
        logout_response = api_client.post(logout_url, {
            'refresh': refresh_token,
        })
        
        assert logout_response.status_code == status.HTTP_200_OK
        
        # Try to use blacklisted token
        refresh_response = api_client.post(refresh_token_url, {
            'refresh': refresh_token,
        })
        
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_blacklisted_token_cannot_refresh(
        self, api_client, authenticated_user, obtain_token_url,
        logout_url, refresh_token_url, user_data
    ):
        """Blacklisted refresh token should not work."""
        # Obtain tokens
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        refresh_token = obtain_response.data['refresh']
        
        # Logout (blacklist)
        api_client.post(logout_url, {
            'refresh': refresh_token,
        })
        
        # Try to refresh with blacklisted token
        response = api_client.post(refresh_token_url, {
            'refresh': refresh_token,
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_with_invalid_token(
        self, api_client, logout_url
    ):
        """Logout with invalid token should return 400."""
        response = api_client.post(logout_url, {
            'refresh': 'invalid.token.here',
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_logout_without_token(
        self, api_client, logout_url
    ):
        """Logout without token should return 400."""
        response = api_client.post(logout_url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_access_token_still_valid_after_logout(
        self, api_client, authenticated_user, obtain_token_url,
        logout_url, protected_endpoint_url, user_data
    ):
        """Access tokens should work until expiration even after logout."""
        # Obtain tokens
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        access_token = obtain_response.data['access']
        refresh_token = obtain_response.data['refresh']
        
        # Logout
        api_client.post(logout_url, {
            'refresh': refresh_token,
        })
        
        # Access token should still work
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================

@pytest.mark.django_db
class TestRateLimiting:
    """Tests for rate limiting on authentication endpoints."""
    
    def test_rate_limit_on_token_obtain(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Exceeding rate limit on token obtain should return 429."""
        # Make requests up to the limit (5 per minute)
        for i in range(5):
            response = api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
            # First 5 should succeed or fail normally
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_400_BAD_REQUEST
            ]
        
        # 6th request should be rate limited
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_rate_limit_on_token_refresh(
        self, api_client, authenticated_user, obtain_token_url,
        refresh_token_url, user_data
    ):
        """Exceeding rate limit on token refresh should return 429."""
        # Obtain token first
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        refresh_token = obtain_response.data['refresh']
        
        # Make requests up to the limit (10 per minute)
        for i in range(10):
            response = api_client.post(refresh_token_url, {
                'refresh': refresh_token,
            })
            # Update refresh token for next iteration if rotation is on
            if response.status_code == status.HTTP_200_OK and 'refresh' in response.data:
                refresh_token = response.data['refresh']
        
        # 11th request should be rate limited
        response = api_client.post(refresh_token_url, {
            'refresh': refresh_token,
        })
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_rate_limit_reset_after_window(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Rate limit should reset after time window."""
        # Exhaust rate limit
        with freeze_time("2024-01-01 12:00:00"):
            for i in range(5):
                api_client.post(obtain_token_url, {
                    'email': user_data['email'],
                    'password': user_data['password'],
                })
            
            # Should be rate limited
            response = api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        
        # After 61 seconds, should work again
        with freeze_time("2024-01-01 12:01:01"):
            response = api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED
            ]
    
    def test_rate_limit_includes_retry_after_header(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """429 response should include Retry-After header."""
        # Exhaust rate limit
        for i in range(5):
            api_client.post(obtain_token_url, {
                'email': user_data['email'],
                'password': user_data['password'],
            })
        
        # Should be rate limited with Retry-After header
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'Retry-After' in response


# ============================================================================
# PASSWORD VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestPasswordValidation:
    """Tests for password validation rules."""
    
    def test_password_without_uppercase_rejected(self, create_user):
        """Password without uppercase should be rejected."""
        with pytest.raises(Exception):  # ValidationError
            create_user(password='securepass123!')
    
    def test_password_without_number_rejected(self, create_user):
        """Password without number should be rejected."""
        with pytest.raises(Exception):  # ValidationError
            create_user(password='SecurePass!')
    
    def test_password_without_special_char_rejected(self, create_user):
        """Password without special character should be rejected."""
        with pytest.raises(Exception):  # ValidationError
            create_user(password='SecurePass123')
    
    def test_password_too_short_rejected(self, create_user):
        """Password shorter than 8 characters should be rejected."""
        with pytest.raises(Exception):  # ValidationError
            create_user(password='Sec1!')
    
    def test_strong_password_accepted(self, create_user):
        """Strong password should be accepted."""
        user = create_user(password='SecurePass123!')
        assert user is not None
        assert user.check_password('SecurePass123!')


# ============================================================================
# CUSTOM CLAIMS TESTS
# ============================================================================

@pytest.mark.django_db
class TestCustomClaims:
    """Tests for custom JWT claims."""
    
    def test_token_contains_user_type_claim(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Token should contain user_type claim."""
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        access_token = response.data['access']
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        
        assert 'user_type' in decoded
        assert decoded['user_type'] == 'patient'
    
    def test_token_contains_is_verified_claim(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Token should contain is_verified claim."""
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        access_token = response.data['access']
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        
        assert 'is_verified' in decoded
        assert decoded['is_verified'] is True
    
    def test_token_contains_email_claim(
        self, api_client, authenticated_user, obtain_token_url, user_data
    ):
        """Token should contain email claim."""
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        access_token = response.data['access']
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        
        assert 'email' in decoded
        assert decoded['email'] == user_data['email']
    
    def test_custom_claims_reflect_user_data(
        self, api_client, create_user, obtain_token_url, user_data
    ):
        """Custom claims should match user model data."""
        # Create user with specific attributes
        user = create_user(
            user_type='pharmacy_admin',
            is_verified=False
        )
        
        response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        
        access_token = response.data['access']
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        
        assert decoded['user_type'] == 'pharmacy_admin'
        assert decoded['is_verified'] is False


# ============================================================================
# SECURITY VULNERABILITY TESTS
# ============================================================================

@pytest.mark.django_db
class TestSecurityVulnerabilities:
    """Tests for common JWT security vulnerabilities."""
    
    def test_algorithm_confusion_attack_prevented(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Changing algorithm header should fail validation."""
        # Obtain valid token
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        access_token = obtain_response.data['access']
        
        # Decode and change algorithm
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        
        # Try to create token with different algorithm
        confused_token = jwt.encode(
            decoded,
            'some-key',
            algorithm='HS512'  # Different algorithm
        )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {confused_token}')
        response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_signature_stripping_prevented(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Removing signature should fail validation."""
        # Obtain valid token
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        access_token = obtain_response.data['access']
        
        # Remove signature (keep header and payload only)
        parts = access_token.split('.')
        if len(parts) == 3:
            stripped_token = f"{parts[0]}.{parts[1]}."
            
            api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {stripped_token}')
            response = api_client.get(protected_endpoint_url)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_tampering_detected(
        self, api_client, authenticated_user, obtain_token_url,
        protected_endpoint_url, user_data
    ):
        """Modifying token claims should fail signature check."""
        # Obtain valid token
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        access_token = obtain_response.data['access']
        
        # Decode, modify, re-encode
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        decoded['user_type'] = 'pharmacy_admin'  # Tamper
        
        tampered_token = jwt.encode(
            decoded,
            'wrong-key',
            algorithm='HS256'
        )
        
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')
        response = api_client.get(protected_endpoint_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_replay_attack_with_blacklisted_token(
        self, api_client, authenticated_user, obtain_token_url,
        logout_url, refresh_token_url, user_data
    ):
        """Blacklisted token should not be reusable."""
        # Obtain tokens
        obtain_response = api_client.post(obtain_token_url, {
            'email': user_data['email'],
            'password': user_data['password'],
        })
        refresh_token = obtain_response.data['refresh']
        
        # Blacklist token
        api_client.post(logout_url, {
            'refresh': refresh_token,
        })
        
        # Try to replay blacklisted token
        response = api_client.post(refresh_token_url, {
            'refresh': refresh_token,
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
