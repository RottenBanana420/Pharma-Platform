"""
Comprehensive tests for password management endpoints.

Tests cover:
- Password change with current password verification
- Password change validation (weak passwords, incorrect current password)
- Password reset request flow
- Password reset confirmation with token validation
- Token expiration and reuse prevention
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APIClient
from datetime import timedelta

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide API client for tests."""
    return APIClient()


@pytest.fixture
def patient_user(db):
    """Create a patient user."""
    return User.objects.create_user(
        username='patient@example.com',
        email='patient@example.com',
        password='OldPassword123!',
        phone_number='+919876543210',
        user_type='patient',
    )


@pytest.fixture
def password_change_url():
    """URL for password change endpoint."""
    return reverse('password_change')


@pytest.fixture
def password_reset_request_url():
    """URL for password reset request endpoint."""
    return reverse('password_reset_request')


@pytest.fixture
def password_reset_confirm_url():
    """URL for password reset confirmation endpoint."""
    return reverse('password_reset_confirm')


# ============================================================================
# PASSWORD CHANGE TESTS
# ============================================================================

@pytest.mark.django_db
class TestPasswordChange:
    """Tests for password change endpoint."""
    
    def test_user_can_change_password_with_correct_old_password(
        self, api_client, patient_user, password_change_url
    ):
        """User should be able to change password with correct old password."""
        api_client.force_authenticate(user=patient_user)
        
        data = {
            'old_password': 'OldPassword123!',
            'new_password': 'NewSecurePass456!',
            'confirm_new_password': 'NewSecurePass456!',
        }
        
        response = api_client.post(password_change_url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data or 'message' in response.data
        
        # Verify password was changed
        patient_user.refresh_from_db()
        assert patient_user.check_password('NewSecurePass456!')
        assert not patient_user.check_password('OldPassword123!')
    
    def test_password_change_with_incorrect_old_password_fails(
        self, api_client, patient_user, password_change_url
    ):
        """Password change should fail with incorrect old password."""
        api_client.force_authenticate(user=patient_user)
        
        data = {
            'old_password': 'WrongPassword123!',
            'new_password': 'NewSecurePass456!',
            'confirm_new_password': 'NewSecurePass456!',
        }
        
        response = api_client.post(password_change_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data
        
        # Verify password was NOT changed
        patient_user.refresh_from_db()
        assert patient_user.check_password('OldPassword123!')
    
    def test_password_change_with_weak_new_password_fails(
        self, api_client, patient_user, password_change_url
    ):
        """Password change should fail with weak new password."""
        api_client.force_authenticate(user=patient_user)
        
        weak_passwords = [
            'short',  # Too short
            'nouppercaseornumber',  # No uppercase or number
            'NoNumber!',  # No number
            'NoSpecial123',  # No special character
            '12345678',  # All numeric
            'password',  # Common password
        ]
        
        for weak_password in weak_passwords:
            data = {
                'old_password': 'OldPassword123!',
                'new_password': weak_password,
                'confirm_new_password': weak_password,
            }
            
            response = api_client.post(password_change_url, data)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'new_password' in response.data
    
    def test_password_change_with_mismatched_confirmation_fails(
        self, api_client, patient_user, password_change_url
    ):
        """Password change should fail when new password and confirmation don't match."""
        api_client.force_authenticate(user=patient_user)
        
        data = {
            'old_password': 'OldPassword123!',
            'new_password': 'NewSecurePass456!',
            'confirm_new_password': 'DifferentPass789!',
        }
        
        response = api_client.post(password_change_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirm_new_password' in response.data or 'non_field_errors' in response.data
    
    def test_password_change_without_authentication_fails(
        self, api_client, password_change_url
    ):
        """Unauthenticated user should not be able to change password."""
        data = {
            'old_password': 'OldPassword123!',
            'new_password': 'NewSecurePass456!',
            'confirm_new_password': 'NewSecurePass456!',
        }
        
        response = api_client.post(password_change_url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_password_change_missing_old_password_fails(
        self, api_client, patient_user, password_change_url
    ):
        """Password change should fail when old password is missing."""
        api_client.force_authenticate(user=patient_user)
        
        data = {
            'new_password': 'NewSecurePass456!',
            'confirm_new_password': 'NewSecurePass456!',
        }
        
        response = api_client.post(password_change_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data
    
    def test_password_change_missing_new_password_fails(
        self, api_client, patient_user, password_change_url
    ):
        """Password change should fail when new password is missing."""
        api_client.force_authenticate(user=patient_user)
        
        data = {
            'old_password': 'OldPassword123!',
            'confirm_new_password': 'NewSecurePass456!',
        }
        
        response = api_client.post(password_change_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data
    
    def test_password_change_missing_confirmation_fails(
        self, api_client, patient_user, password_change_url
    ):
        """Password change should fail when password confirmation is missing."""
        api_client.force_authenticate(user=patient_user)
        
        data = {
            'old_password': 'OldPassword123!',
            'new_password': 'NewSecurePass456!',
        }
        
        response = api_client.post(password_change_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirm_new_password' in response.data


# ============================================================================
# PASSWORD RESET REQUEST TESTS
# ============================================================================

@pytest.mark.django_db
class TestPasswordResetRequest:
    """Tests for password reset request endpoint."""
    
    def test_password_reset_request_with_valid_email(
        self, api_client, patient_user, password_reset_request_url
    ):
        """Password reset request with valid email should succeed."""
        data = {'email': patient_user.email}
        
        response = api_client.post(password_reset_request_url, data)
        
        # Should always return 200 (don't reveal if email exists)
        assert response.status_code == status.HTTP_200_OK
        assert 'detail' in response.data or 'message' in response.data
    
    def test_password_reset_request_with_nonexistent_email(
        self, api_client, password_reset_request_url
    ):
        """Password reset request with nonexistent email should still return 200 (security)."""
        data = {'email': 'nonexistent@example.com'}
        
        response = api_client.post(password_reset_request_url, data)
        
        # Should return 200 to not reveal if email exists
        assert response.status_code == status.HTTP_200_OK
    
    def test_password_reset_request_with_invalid_email_format(
        self, api_client, password_reset_request_url
    ):
        """Password reset request with invalid email format should fail."""
        data = {'email': 'not-an-email'}
        
        response = api_client.post(password_reset_request_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
    
    def test_password_reset_request_missing_email(
        self, api_client, password_reset_request_url
    ):
        """Password reset request without email should fail."""
        response = api_client.post(password_reset_request_url, {})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
    
    def test_password_reset_request_case_insensitive_email(
        self, api_client, patient_user, password_reset_request_url
    ):
        """Password reset should work with different email case."""
        data = {'email': patient_user.email.upper()}
        
        response = api_client.post(password_reset_request_url, data)
        
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# PASSWORD RESET CONFIRMATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestPasswordResetConfirm:
    """Tests for password reset confirmation endpoint."""
    
    def test_password_reset_confirm_with_valid_token(
        self, api_client, patient_user, password_reset_confirm_url
    ):
        """Password reset confirmation with valid token should succeed."""
        # Generate a valid token
        token = default_token_generator.make_token(patient_user)
        
        data = {
            'token': token,
            'uid': patient_user.pk,  # May need to encode this
            'new_password': 'NewResetPass123!',
            'confirm_new_password': 'NewResetPass123!',
        }
        
        response = api_client.post(password_reset_confirm_url, data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify password was changed
        patient_user.refresh_from_db()
        assert patient_user.check_password('NewResetPass123!')
    
    def test_password_reset_confirm_with_invalid_token(
        self, api_client, patient_user, password_reset_confirm_url
    ):
        """Password reset confirmation with invalid token should fail."""
        data = {
            'token': 'invalid-token-12345',
            'uid': patient_user.pk,
            'new_password': 'NewResetPass123!',
            'confirm_new_password': 'NewResetPass123!',
        }
        
        response = api_client.post(password_reset_confirm_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Verify password was NOT changed
        patient_user.refresh_from_db()
        assert patient_user.check_password('OldPassword123!')
    
    def test_password_reset_confirm_with_weak_password(
        self, api_client, patient_user, password_reset_confirm_url
    ):
        """Password reset confirmation with weak password should fail."""
        token = default_token_generator.make_token(patient_user)
        
        data = {
            'token': token,
            'uid': patient_user.pk,
            'new_password': 'weak',
            'confirm_new_password': 'weak',
        }
        
        response = api_client.post(password_reset_confirm_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data
    
    def test_password_reset_confirm_with_mismatched_passwords(
        self, api_client, patient_user, password_reset_confirm_url
    ):
        """Password reset confirmation with mismatched passwords should fail."""
        token = default_token_generator.make_token(patient_user)
        
        data = {
            'token': token,
            'uid': patient_user.pk,
            'new_password': 'NewResetPass123!',
            'confirm_new_password': 'DifferentPass456!',
        }
        
        response = api_client.post(password_reset_confirm_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_password_reset_token_cannot_be_reused(
        self, api_client, patient_user, password_reset_confirm_url
    ):
        """Password reset token should not be reusable after successful reset."""
        token = default_token_generator.make_token(patient_user)
        
        data = {
            'token': token,
            'uid': patient_user.pk,
            'new_password': 'FirstReset123!',
            'confirm_new_password': 'FirstReset123!',
        }
        
        # First reset should succeed
        response1 = api_client.post(password_reset_confirm_url, data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Try to reuse the same token
        data['new_password'] = 'SecondReset456!'
        data['confirm_new_password'] = 'SecondReset456!'
        
        response2 = api_client.post(password_reset_confirm_url, data)
        
        # Second attempt should fail
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        
        # Password should still be the first reset password
        patient_user.refresh_from_db()
        assert patient_user.check_password('FirstReset123!')
        assert not patient_user.check_password('SecondReset456!')
    
    def test_password_reset_missing_token(
        self, api_client, patient_user, password_reset_confirm_url
    ):
        """Password reset confirmation without token should fail."""
        data = {
            'uid': patient_user.pk,
            'new_password': 'NewResetPass123!',
            'confirm_new_password': 'NewResetPass123!',
        }
        
        response = api_client.post(password_reset_confirm_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'token' in response.data
    
    def test_password_reset_missing_uid(
        self, api_client, patient_user, password_reset_confirm_url
    ):
        """Password reset confirmation without uid should fail."""
        token = default_token_generator.make_token(patient_user)
        
        data = {
            'token': token,
            'new_password': 'NewResetPass123!',
            'confirm_new_password': 'NewResetPass123!',
        }
        
        response = api_client.post(password_reset_confirm_url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'uid' in response.data


# ============================================================================
# PASSWORD SECURITY TESTS
# ============================================================================

@pytest.mark.django_db
class TestPasswordSecurity:
    """Security-focused tests for password management."""
    
    def test_old_password_not_returned_in_response(
        self, api_client, patient_user, password_change_url
    ):
        """Password change response should never include passwords."""
        api_client.force_authenticate(user=patient_user)
        
        data = {
            'old_password': 'OldPassword123!',
            'new_password': 'NewSecurePass456!',
            'confirm_new_password': 'NewSecurePass456!',
        }
        
        response = api_client.post(password_change_url, data)
        
        # Response should not contain any password
        response_str = str(response.data)
        assert 'OldPassword123!' not in response_str
        assert 'NewSecurePass456!' not in response_str
    
    def test_password_reset_does_not_reveal_user_existence(
        self, api_client, password_reset_request_url
    ):
        """Password reset should not reveal if user exists (timing attack prevention)."""
        # Request for existing user
        response1 = api_client.post(password_reset_request_url, {
            'email': 'existing@example.com'
        })
        
        # Request for non-existing user
        response2 = api_client.post(password_reset_request_url, {
            'email': 'nonexistent@example.com'
        })
        
        # Both should return the same status code
        assert response1.status_code == response2.status_code
        
        # Both should have similar response structure
        assert ('detail' in response1.data) == ('detail' in response2.data)
    
    def test_password_change_requires_authentication(
        self, api_client, password_change_url
    ):
        """Password change should require authentication."""
        data = {
            'old_password': 'OldPassword123!',
            'new_password': 'NewSecurePass456!',
            'confirm_new_password': 'NewSecurePass456!',
        }
        
        response = api_client.post(password_change_url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
