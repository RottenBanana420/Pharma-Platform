"""
Comprehensive tests for user profile endpoints.

Tests cover:
- Profile retrieval with authentication
- Profile retrieval without authentication
- Profile update with valid data
- Profile update for restricted fields
- Object-level permissions (users can only access own data)
- Field-level validation
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
def patient_user(db):
    """Create a patient user."""
    return User.objects.create_user(
        username='patient@example.com',
        email='patient@example.com',
        password='SecurePass123!',
        phone_number='+919876543210',
        user_type='patient',
        first_name='John',
        last_name='Doe',
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
        first_name='Jane',
        last_name='Smith',
    )


@pytest.fixture
def profile_url():
    """URL for user profile endpoint."""
    return reverse('user_profile')


# ============================================================================
# PROFILE RETRIEVAL TESTS
# ============================================================================

@pytest.mark.django_db
class TestProfileRetrieval:
    """Tests for profile retrieval endpoint."""
    
    def test_authenticated_user_can_retrieve_profile(self, api_client, patient_user, profile_url):
        """Authenticated user should be able to retrieve their own profile."""
        api_client.force_authenticate(user=patient_user)
        
        response = api_client.get(profile_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == patient_user.id
        assert response.data['email'] == patient_user.email
        assert response.data['phone_number'] == patient_user.phone_number
        assert response.data['user_type'] == patient_user.user_type
        assert response.data['is_verified'] == patient_user.is_verified
        assert response.data['first_name'] == patient_user.first_name
        assert response.data['last_name'] == patient_user.last_name
        assert 'date_joined' in response.data
    
    def test_profile_does_not_include_password(self, api_client, patient_user, profile_url):
        """Profile response should never include password."""
        api_client.force_authenticate(user=patient_user)
        
        response = api_client.get(profile_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'password' not in response.data
    
    def test_profile_does_not_include_username(self, api_client, patient_user, profile_url):
        """Profile response should not include internal username field."""
        api_client.force_authenticate(user=patient_user)
        
        response = api_client.get(profile_url)
        
        assert response.status_code == status.HTTP_200_OK
        # Username is internal, should not be exposed
        assert 'username' not in response.data
    
    def test_unauthenticated_user_cannot_retrieve_profile(self, api_client, profile_url):
        """Unauthenticated user should get 401."""
        response = api_client.get(profile_url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_pharmacy_admin_can_retrieve_own_profile(self, api_client, pharmacy_admin_user, profile_url):
        """Pharmacy admin should be able to retrieve their own profile."""
        api_client.force_authenticate(user=pharmacy_admin_user)
        
        response = api_client.get(profile_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user_type'] == 'pharmacy_admin'
        assert response.data['email'] == pharmacy_admin_user.email


# ============================================================================
# PROFILE UPDATE TESTS
# ============================================================================

@pytest.mark.django_db
class TestProfileUpdate:
    """Tests for profile update endpoint."""
    
    def test_user_can_update_phone_number(self, api_client, patient_user, profile_url):
        """User should be able to update their phone number."""
        api_client.force_authenticate(user=patient_user)
        
        new_phone = '+919999999999'
        response = api_client.patch(profile_url, {'phone_number': new_phone})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['phone_number'] == new_phone
        
        # Verify in database
        patient_user.refresh_from_db()
        assert patient_user.phone_number == new_phone
    
    def test_user_can_update_first_name(self, api_client, patient_user, profile_url):
        """User should be able to update their first name."""
        api_client.force_authenticate(user=patient_user)
        
        new_first_name = 'Michael'
        response = api_client.patch(profile_url, {'first_name': new_first_name})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == new_first_name
        
        # Verify in database
        patient_user.refresh_from_db()
        assert patient_user.first_name == new_first_name
    
    def test_user_can_update_last_name(self, api_client, patient_user, profile_url):
        """User should be able to update their last name."""
        api_client.force_authenticate(user=patient_user)
        
        new_last_name = 'Johnson'
        response = api_client.patch(profile_url, {'last_name': new_last_name})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['last_name'] == new_last_name
        
        # Verify in database
        patient_user.refresh_from_db()
        assert patient_user.last_name == new_last_name
    
    def test_user_can_update_multiple_fields(self, api_client, patient_user, profile_url):
        """User should be able to update multiple fields at once."""
        api_client.force_authenticate(user=patient_user)
        
        update_data = {
            'phone_number': '+919888888888',
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        response = api_client.patch(profile_url, update_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['phone_number'] == update_data['phone_number']
        assert response.data['first_name'] == update_data['first_name']
        assert response.data['last_name'] == update_data['last_name']
        
        # Verify in database
        patient_user.refresh_from_db()
        assert patient_user.phone_number == update_data['phone_number']
        assert patient_user.first_name == update_data['first_name']
        assert patient_user.last_name == update_data['last_name']
    
    def test_unauthenticated_user_cannot_update_profile(self, api_client, profile_url):
        """Unauthenticated user should get 401."""
        response = api_client.patch(profile_url, {'first_name': 'Hacker'})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# RESTRICTED FIELDS TESTS
# ============================================================================

@pytest.mark.django_db
class TestRestrictedFieldUpdates:
    """Tests to ensure restricted fields cannot be updated via profile endpoint."""
    
    def test_user_cannot_update_email(self, api_client, patient_user, profile_url):
        """User should not be able to update email via profile endpoint."""
        api_client.force_authenticate(user=patient_user)
        
        original_email = patient_user.email
        new_email = 'newemail@example.com'
        
        response = api_client.patch(profile_url, {'email': new_email})
        
        # Should either succeed but ignore email, or return 200 with original email
        assert response.status_code == status.HTTP_200_OK
        
        # Email should NOT have changed
        patient_user.refresh_from_db()
        assert patient_user.email == original_email
        assert patient_user.email != new_email
    
    def test_user_cannot_update_user_type(self, api_client, patient_user, profile_url):
        """User should not be able to update user_type (privilege escalation prevention)."""
        api_client.force_authenticate(user=patient_user)
        
        original_user_type = patient_user.user_type
        
        response = api_client.patch(profile_url, {'user_type': 'pharmacy_admin'})
        
        # Should either succeed but ignore user_type, or return 200 with original type
        assert response.status_code == status.HTTP_200_OK
        
        # User type should NOT have changed
        patient_user.refresh_from_db()
        assert patient_user.user_type == original_user_type
        assert patient_user.user_type != 'pharmacy_admin'
    
    def test_user_cannot_update_is_verified(self, api_client, patient_user, profile_url):
        """User should not be able to self-verify (admin-only field)."""
        api_client.force_authenticate(user=patient_user)
        
        original_verified_status = patient_user.is_verified
        assert original_verified_status is False  # Should start unverified
        
        response = api_client.patch(profile_url, {'is_verified': True})
        
        # Should either succeed but ignore is_verified, or return 200 with original status
        assert response.status_code == status.HTTP_200_OK
        
        # Verification status should NOT have changed
        patient_user.refresh_from_db()
        assert patient_user.is_verified == original_verified_status
        assert patient_user.is_verified is False
    
    def test_user_cannot_update_multiple_restricted_fields(self, api_client, patient_user, profile_url):
        """User should not be able to update any restricted fields."""
        api_client.force_authenticate(user=patient_user)
        
        original_email = patient_user.email
        original_user_type = patient_user.user_type
        original_verified = patient_user.is_verified
        
        # Try to update all restricted fields
        response = api_client.patch(profile_url, {
            'email': 'hacker@example.com',
            'user_type': 'pharmacy_admin',
            'is_verified': True,
        })
        
        # Should succeed but ignore all restricted fields
        assert response.status_code == status.HTTP_200_OK
        
        # None of the restricted fields should have changed
        patient_user.refresh_from_db()
        assert patient_user.email == original_email
        assert patient_user.user_type == original_user_type
        assert patient_user.is_verified == original_verified
    
    def test_user_can_update_allowed_fields_with_restricted_fields_in_request(
        self, api_client, patient_user, profile_url
    ):
        """User should be able to update allowed fields even if restricted fields are in request."""
        api_client.force_authenticate(user=patient_user)
        
        original_email = patient_user.email
        new_first_name = 'ValidUpdate'
        
        # Mix allowed and restricted fields
        response = api_client.patch(profile_url, {
            'first_name': new_first_name,
            'email': 'hacker@example.com',  # Should be ignored
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Allowed field should update, restricted field should not
        patient_user.refresh_from_db()
        assert patient_user.first_name == new_first_name
        assert patient_user.email == original_email


# ============================================================================
# FIELD VALIDATION TESTS
# ============================================================================

@pytest.mark.django_db
class TestProfileFieldValidation:
    """Tests for field-level validation on profile updates."""
    
    def test_invalid_phone_number_format_rejected(self, api_client, patient_user, profile_url):
        """Invalid phone number format should return 400."""
        api_client.force_authenticate(user=patient_user)
        
        invalid_phones = [
            '9876543210',  # Missing +91
            '+1234567890',  # Wrong country code
            '+91987654321',  # Too short
            '+919876543210123',  # Too long
            '+91abcdefghij',  # Non-numeric
        ]
        
        for invalid_phone in invalid_phones:
            response = api_client.patch(profile_url, {'phone_number': invalid_phone})
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'phone_number' in response.data
    
    def test_duplicate_phone_number_rejected(self, api_client, patient_user, pharmacy_admin_user, profile_url):
        """Phone number already used by another user should be rejected."""
        api_client.force_authenticate(user=patient_user)
        
        # Try to use pharmacy admin's phone number
        response = api_client.patch(profile_url, {
            'phone_number': pharmacy_admin_user.phone_number
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'phone_number' in response.data
    
    def test_user_can_keep_same_phone_number(self, api_client, patient_user, profile_url):
        """User should be able to update profile without changing phone number."""
        api_client.force_authenticate(user=patient_user)
        
        # Update other fields while keeping same phone
        response = api_client.patch(profile_url, {
            'phone_number': patient_user.phone_number,  # Same phone
            'first_name': 'NewName',
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'NewName'
    
    def test_empty_first_name_rejected(self, api_client, patient_user, profile_url):
        """Empty first name should be rejected if provided."""
        api_client.force_authenticate(user=patient_user)
        
        response = api_client.patch(profile_url, {'first_name': ''})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'first_name' in response.data
    
    def test_empty_last_name_rejected(self, api_client, patient_user, profile_url):
        """Empty last name should be rejected if provided."""
        api_client.force_authenticate(user=patient_user)
        
        response = api_client.patch(profile_url, {'last_name': ''})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'last_name' in response.data
    
    def test_whitespace_trimmed_from_names(self, api_client, patient_user, profile_url):
        """Leading/trailing whitespace should be trimmed from names."""
        api_client.force_authenticate(user=patient_user)
        
        response = api_client.patch(profile_url, {
            'first_name': '  Trimmed  ',
            'last_name': '  Name  ',
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Trimmed'
        assert response.data['last_name'] == 'Name'


# ============================================================================
# OBJECT-LEVEL PERMISSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestObjectLevelPermissions:
    """Tests to ensure users can only access their own profile."""
    
    def test_user_cannot_access_another_users_profile_by_id(self, api_client, patient_user, pharmacy_admin_user):
        """User should not be able to access another user's profile by changing ID in URL."""
        # Note: This test assumes URL pattern like /api/accounts/profile/{id}/
        # If we use /api/accounts/profile/ (current user), this test may not apply
        # We'll test the general principle that the endpoint returns current user's data
        
        api_client.force_authenticate(user=patient_user)
        
        # Get profile - should return patient's data, not pharmacy admin's
        profile_url = reverse('user_profile')
        response = api_client.get(profile_url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == patient_user.id
        assert response.data['id'] != pharmacy_admin_user.id
        assert response.data['email'] == patient_user.email
    
    def test_profile_endpoint_always_returns_current_user(self, api_client, patient_user, pharmacy_admin_user):
        """Profile endpoint should always return the authenticated user's data."""
        # Test with patient
        api_client.force_authenticate(user=patient_user)
        response1 = api_client.get(reverse('user_profile'))
        assert response1.status_code == status.HTTP_200_OK
        assert response1.data['id'] == patient_user.id
        
        # Test with pharmacy admin
        api_client.force_authenticate(user=pharmacy_admin_user)
        response2 = api_client.get(reverse('user_profile'))
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data['id'] == pharmacy_admin_user.id
        
        # Responses should be different
        assert response1.data['id'] != response2.data['id']
    
    def test_user_update_only_affects_own_profile(self, api_client, patient_user, pharmacy_admin_user):
        """User update should only affect their own profile, not others."""
        api_client.force_authenticate(user=patient_user)
        
        original_pharmacy_name = pharmacy_admin_user.first_name
        
        # Update patient's profile
        response = api_client.patch(reverse('user_profile'), {
            'first_name': 'PatientUpdated'
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Patient's profile should be updated
        patient_user.refresh_from_db()
        assert patient_user.first_name == 'PatientUpdated'
        
        # Pharmacy admin's profile should NOT be affected
        pharmacy_admin_user.refresh_from_db()
        assert pharmacy_admin_user.first_name == original_pharmacy_name


# ============================================================================
# PARTIAL UPDATE TESTS (PATCH behavior)
# ============================================================================

@pytest.mark.django_db
class TestPartialUpdates:
    """Tests to ensure PATCH allows partial updates."""
    
    def test_patch_updates_only_provided_fields(self, api_client, patient_user, profile_url):
        """PATCH should only update fields that are provided."""
        api_client.force_authenticate(user=patient_user)
        
        original_phone = patient_user.phone_number
        original_last_name = patient_user.last_name
        
        # Update only first name
        response = api_client.patch(profile_url, {'first_name': 'OnlyFirst'})
        
        assert response.status_code == status.HTTP_200_OK
        
        # Only first name should change
        patient_user.refresh_from_db()
        assert patient_user.first_name == 'OnlyFirst'
        assert patient_user.phone_number == original_phone
        assert patient_user.last_name == original_last_name
    
    def test_empty_patch_request_succeeds(self, api_client, patient_user, profile_url):
        """Empty PATCH request should succeed without changing anything."""
        api_client.force_authenticate(user=patient_user)
        
        original_first_name = patient_user.first_name
        original_last_name = patient_user.last_name
        original_phone = patient_user.phone_number
        
        response = api_client.patch(profile_url, {})
        
        assert response.status_code == status.HTTP_200_OK
        
        # Nothing should change
        patient_user.refresh_from_db()
        assert patient_user.first_name == original_first_name
        assert patient_user.last_name == original_last_name
        assert patient_user.phone_number == original_phone
