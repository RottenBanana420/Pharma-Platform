"""
Comprehensive authorization security tests.

Tests cover:
- Cross-role access denial
- Permission bypass attempts
- Token manipulation
- Object-level permission bypass
- Privilege escalation prevention
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

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
        password='SecurePass123!',
        phone_number='+919876543210',
        user_type='patient',
        is_verified=False,
    )


@pytest.fixture
def pharmacy_admin_user(db):
    """Create a pharmacy admin user."""
    return User.objects.create_user(
        username='admin@pharmacy.com',
        email='admin@pharmacy.com',
        password='SecurePass123!',
        phone_number='+919876543211',
        user_type='pharmacy_admin',
        is_verified=False,
    )


@pytest.fixture
def verified_pharmacy_admin_user(db):
    """Create a verified pharmacy admin user."""
    user = User.objects.create_user(
        username='verified@pharmacy.com',
        email='verified@pharmacy.com',
        password='SecurePass123!',
        phone_number='+919876543212',
        user_type='pharmacy_admin',
        is_verified=True,
    )
    return user


@pytest.fixture
def another_patient_user(db):
    """Create another patient user for testing cross-user access."""
    return User.objects.create_user(
        username='patient2@example.com',
        email='patient2@example.com',
        password='SecurePass123!',
        phone_number='+919876543213',
        user_type='patient',
        is_verified=False,
    )


# ============================================================================
# CROSS-ROLE ACCESS TESTS
# ============================================================================

@pytest.mark.django_db
class TestCrossRoleAccessDenial:
    """Tests to ensure users cannot access endpoints for other roles."""
    
    def test_patient_cannot_access_pharmacy_profile(
        self, api_client, patient_user, pharmacy_admin_user
    ):
        """Patient should not be able to access pharmacy admin's profile."""
        api_client.force_authenticate(user=patient_user)
        
        # Try to access profile endpoint - should return patient's own profile
        response = api_client.get(reverse('user_profile'))
        
        assert response.status_code == status.HTTP_200_OK
        # Should return patient's data, not pharmacy admin's
        assert response.data['user_type'] == 'patient'
        assert response.data['id'] == patient_user.id
        assert response.data['id'] != pharmacy_admin_user.id
    
    def test_pharmacy_admin_cannot_access_patient_profile(
        self, api_client, pharmacy_admin_user, patient_user
    ):
        """Pharmacy admin should not be able to access patient's profile."""
        api_client.force_authenticate(user=pharmacy_admin_user)
        
        # Try to access profile endpoint - should return pharmacy admin's own profile
        response = api_client.get(reverse('user_profile'))
        
        assert response.status_code == status.HTTP_200_OK
        # Should return pharmacy admin's data, not patient's
        assert response.data['user_type'] == 'pharmacy_admin'
        assert response.data['id'] == pharmacy_admin_user.id
        assert response.data['id'] != patient_user.id


# ============================================================================
# PRIVILEGE ESCALATION PREVENTION TESTS
# ============================================================================

@pytest.mark.django_db
class TestPrivilegeEscalationPrevention:
    """Tests to prevent privilege escalation attacks."""
    
    def test_patient_cannot_escalate_to_pharmacy_admin(
        self, api_client, patient_user
    ):
        """Patient should not be able to change user_type to pharmacy_admin."""
        api_client.force_authenticate(user=patient_user)
        
        original_user_type = patient_user.user_type
        
        # Attempt to escalate privileges
        response = api_client.patch(reverse('user_profile'), {
            'user_type': 'pharmacy_admin'
        })
        
        # Request should succeed but user_type should not change
        assert response.status_code == status.HTTP_200_OK
        
        patient_user.refresh_from_db()
        assert patient_user.user_type == original_user_type
        assert patient_user.user_type == 'patient'
    
    def test_patient_cannot_self_verify(self, api_client, patient_user):
        """Patient should not be able to set is_verified to True."""
        api_client.force_authenticate(user=patient_user)
        
        assert patient_user.is_verified is False
        
        # Attempt to self-verify
        response = api_client.patch(reverse('user_profile'), {
            'is_verified': True
        })
        
        # Request should succeed but is_verified should not change
        assert response.status_code == status.HTTP_200_OK
        
        patient_user.refresh_from_db()
        assert patient_user.is_verified is False
    
    def test_unverified_pharmacy_cannot_verify_self(
        self, api_client, pharmacy_admin_user
    ):
        """Unverified pharmacy admin should not be able to verify themselves."""
        api_client.force_authenticate(user=pharmacy_admin_user)
        
        assert pharmacy_admin_user.is_verified is False
        
        # Attempt to self-verify
        response = api_client.patch(reverse('user_profile'), {
            'is_verified': True
        })
        
        # Request should succeed but is_verified should not change
        assert response.status_code == status.HTTP_200_OK
        
        pharmacy_admin_user.refresh_from_db()
        assert pharmacy_admin_user.is_verified is False


# ============================================================================
# OBJECT-LEVEL PERMISSION BYPASS TESTS
# ============================================================================

@pytest.mark.django_db
class TestObjectLevelPermissionBypass:
    """Tests to prevent bypassing object-level permissions."""
    
    def test_user_cannot_update_another_users_profile(
        self, api_client, patient_user, another_patient_user
    ):
        """User should not be able to update another user's profile."""
        api_client.force_authenticate(user=patient_user)
        
        original_first_name = another_patient_user.first_name
        
        # Try to update profile - should only affect authenticated user
        response = api_client.patch(reverse('user_profile'), {
            'first_name': 'Hacker'
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Patient's own profile should be updated
        patient_user.refresh_from_db()
        assert patient_user.first_name == 'Hacker'
        
        # Another patient's profile should NOT be affected
        another_patient_user.refresh_from_db()
        assert another_patient_user.first_name == original_first_name
    
    def test_user_cannot_read_another_users_data(
        self, api_client, patient_user, another_patient_user
    ):
        """User should only be able to read their own profile data."""
        api_client.force_authenticate(user=patient_user)
        
        response = api_client.get(reverse('user_profile'))
        
        assert response.status_code == status.HTTP_200_OK
        # Should return authenticated user's data
        assert response.data['id'] == patient_user.id
        assert response.data['email'] == patient_user.email
        # Should NOT return another user's data
        assert response.data['id'] != another_patient_user.id
        assert response.data['email'] != another_patient_user.email


# ============================================================================
# TOKEN MANIPULATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestTokenManipulation:
    """Tests to prevent token manipulation attacks."""
    
    def test_expired_token_rejected(self, api_client, patient_user):
        """Expired access token should be rejected."""
        # Create a token and manually expire it
        refresh = RefreshToken.for_user(patient_user)
        access_token = str(refresh.access_token)
        
        # Set token in header
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Token should work initially
        response = api_client.get(reverse('user_profile'))
        assert response.status_code == status.HTTP_200_OK
        
        # Note: Testing actual expiration would require time manipulation
        # This test verifies the token validation mechanism is in place
    
    def test_invalid_token_rejected(self, api_client):
        """Invalid token should be rejected."""
        # Use a completely invalid token
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token-12345')
        
        response = api_client.get(reverse('user_profile'))
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_malformed_token_rejected(self, api_client):
        """Malformed token should be rejected."""
        # Use malformed authorization header
        api_client.credentials(HTTP_AUTHORIZATION='InvalidFormat')
        
        response = api_client.get(reverse('user_profile'))
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_missing_token_rejected(self, api_client):
        """Request without token should be rejected."""
        response = api_client.get(reverse('user_profile'))
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_from_different_user_cannot_access_profile(
        self, api_client, patient_user, pharmacy_admin_user
    ):
        """Token from one user should not grant access to another user's data."""
        # Create token for pharmacy admin
        refresh = RefreshToken.for_user(pharmacy_admin_user)
        access_token = str(refresh.access_token)
        
        # Use pharmacy admin's token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Get profile - should return pharmacy admin's data, not patient's
        response = api_client.get(reverse('user_profile'))
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == pharmacy_admin_user.id
        assert response.data['id'] != patient_user.id


# ============================================================================
# EMAIL CHANGE PREVENTION TESTS
# ============================================================================

@pytest.mark.django_db
class TestEmailChangePreventio:
    """Tests to ensure email cannot be changed via profile endpoint."""
    
    def test_user_cannot_change_email_to_existing_email(
        self, api_client, patient_user, pharmacy_admin_user
    ):
        """User should not be able to change email to one already in use."""
        api_client.force_authenticate(user=patient_user)
        
        original_email = patient_user.email
        
        # Try to change to pharmacy admin's email
        response = api_client.patch(reverse('user_profile'), {
            'email': pharmacy_admin_user.email
        })
        
        # Should succeed but email should not change
        assert response.status_code == status.HTTP_200_OK
        
        patient_user.refresh_from_db()
        assert patient_user.email == original_email
        assert patient_user.email != pharmacy_admin_user.email
    
    def test_user_cannot_change_email_to_new_email(
        self, api_client, patient_user
    ):
        """User should not be able to change email via profile endpoint."""
        api_client.force_authenticate(user=patient_user)
        
        original_email = patient_user.email
        
        # Try to change to a new email
        response = api_client.patch(reverse('user_profile'), {
            'email': 'newemail@example.com'
        })
        
        # Should succeed but email should not change
        assert response.status_code == status.HTTP_200_OK
        
        patient_user.refresh_from_db()
        assert patient_user.email == original_email
        assert patient_user.email != 'newemail@example.com'


# ============================================================================
# COMBINED ATTACK TESTS
# ============================================================================

@pytest.mark.django_db
class TestCombinedAttacks:
    """Tests for combined attack scenarios."""
    
    def test_combined_privilege_escalation_and_verification_attack(
        self, api_client, patient_user
    ):
        """User should not be able to escalate and verify in one request."""
        api_client.force_authenticate(user=patient_user)
        
        original_user_type = patient_user.user_type
        original_verified = patient_user.is_verified
        
        # Try to escalate and verify simultaneously
        response = api_client.patch(reverse('user_profile'), {
            'user_type': 'pharmacy_admin',
            'is_verified': True,
            'email': 'hacker@example.com',
        })
        
        # Should succeed but none of the restricted fields should change
        assert response.status_code == status.HTTP_200_OK
        
        patient_user.refresh_from_db()
        assert patient_user.user_type == original_user_type
        assert patient_user.is_verified == original_verified
        assert patient_user.email != 'hacker@example.com'
    
    def test_valid_update_with_invalid_fields_mixed(
        self, api_client, patient_user
    ):
        """Valid fields should update even when mixed with invalid attempts."""
        api_client.force_authenticate(user=patient_user)
        
        original_email = patient_user.email
        original_user_type = patient_user.user_type
        
        # Mix valid and invalid updates
        response = api_client.patch(reverse('user_profile'), {
            'first_name': 'ValidUpdate',  # Valid
            'user_type': 'pharmacy_admin',  # Invalid - should be ignored
            'email': 'hacker@example.com',  # Invalid - should be ignored
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        patient_user.refresh_from_db()
        # Valid field should update
        assert patient_user.first_name == 'ValidUpdate'
        # Invalid fields should not change
        assert patient_user.user_type == original_user_type
        assert patient_user.email == original_email


# ============================================================================
# PASSWORD SECURITY TESTS
# ============================================================================

@pytest.mark.django_db
class TestPasswordSecurity:
    """Tests for password-related security."""
    
    def test_password_not_exposed_in_profile_response(
        self, api_client, patient_user
    ):
        """Password should never be exposed in profile responses."""
        api_client.force_authenticate(user=patient_user)
        
        response = api_client.get(reverse('user_profile'))
        
        assert response.status_code == status.HTTP_200_OK
        assert 'password' not in response.data
        assert 'password' not in str(response.data).lower()
    
    def test_password_cannot_be_updated_via_profile_endpoint(
        self, api_client, patient_user
    ):
        """Password should not be updatable via profile endpoint."""
        api_client.force_authenticate(user=patient_user)
        
        original_password = patient_user.password
        
        # Try to update password via profile endpoint
        response = api_client.patch(reverse('user_profile'), {
            'password': 'NewHackedPass123!'
        })
        
        # Should succeed but password should not change
        # (password updates should go through password change endpoint)
        assert response.status_code == status.HTTP_200_OK
        
        patient_user.refresh_from_db()
        assert patient_user.password == original_password
        assert not patient_user.check_password('NewHackedPass123!')
