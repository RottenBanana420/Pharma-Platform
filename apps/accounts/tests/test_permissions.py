"""
Comprehensive tests for custom permission classes.

Tests cover:
- IsPatient permission class
- IsPharmacyAdmin permission class
- IsVerifiedPharmacy permission class
- Permission error messages
- Cross-role access denial
- Unauthenticated access
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Import permissions - these don't exist yet, tests will fail (TDD RED phase)
from apps.accounts.permissions import (
    IsPatient,
    IsPharmacyAdmin,
    IsVerifiedPharmacy,
)

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide API client for tests."""
    return APIClient()


@pytest.fixture
def request_factory():
    """Provide request factory for permission testing."""
    return APIRequestFactory()


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


# ============================================================================
# TEST VIEW CLASSES (for testing permissions in context)
# ============================================================================

class PatientOnlyView(APIView):
    """Test view that requires IsPatient permission."""
    permission_classes = [IsPatient]
    
    def get(self, request):
        return Response({'message': 'Patient access granted'})


class PharmacyAdminOnlyView(APIView):
    """Test view that requires IsPharmacyAdmin permission."""
    permission_classes = [IsPharmacyAdmin]
    
    def get(self, request):
        return Response({'message': 'Pharmacy admin access granted'})


class VerifiedPharmacyOnlyView(APIView):
    """Test view that requires IsVerifiedPharmacy permission."""
    permission_classes = [IsVerifiedPharmacy]
    
    def get(self, request):
        return Response({'message': 'Verified pharmacy access granted'})


# ============================================================================
# IsPatient PERMISSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestIsPatientPermission:
    """Tests for IsPatient permission class."""
    
    def test_patient_user_has_permission(self, request_factory, patient_user):
        """Patient user should have permission."""
        permission = IsPatient()
        request = request_factory.get('/test/')
        request.user = patient_user
        
        # Create a mock view
        view = PatientOnlyView()
        
        assert permission.has_permission(request, view) is True
    
    def test_pharmacy_admin_denied_permission(self, request_factory, pharmacy_admin_user):
        """Pharmacy admin should be denied permission."""
        permission = IsPatient()
        request = request_factory.get('/test/')
        request.user = pharmacy_admin_user
        
        view = PatientOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_verified_pharmacy_admin_denied_permission(self, request_factory, verified_pharmacy_admin_user):
        """Verified pharmacy admin should be denied permission."""
        permission = IsPatient()
        request = request_factory.get('/test/')
        request.user = verified_pharmacy_admin_user
        
        view = PatientOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_unauthenticated_user_denied_permission(self, request_factory):
        """Unauthenticated user should be denied permission."""
        from django.contrib.auth.models import AnonymousUser
        
        permission = IsPatient()
        request = request_factory.get('/test/')
        request.user = AnonymousUser()
        
        view = PatientOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_permission_has_custom_message(self):
        """IsPatient should have a custom error message."""
        permission = IsPatient()
        
        assert hasattr(permission, 'message')
        assert 'patient' in permission.message.lower()


# ============================================================================
# IsPharmacyAdmin PERMISSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestIsPharmacyAdminPermission:
    """Tests for IsPharmacyAdmin permission class."""
    
    def test_pharmacy_admin_has_permission(self, request_factory, pharmacy_admin_user):
        """Pharmacy admin should have permission."""
        permission = IsPharmacyAdmin()
        request = request_factory.get('/test/')
        request.user = pharmacy_admin_user
        
        view = PharmacyAdminOnlyView()
        
        assert permission.has_permission(request, view) is True
    
    def test_verified_pharmacy_admin_has_permission(self, request_factory, verified_pharmacy_admin_user):
        """Verified pharmacy admin should have permission (verification not required)."""
        permission = IsPharmacyAdmin()
        request = request_factory.get('/test/')
        request.user = verified_pharmacy_admin_user
        
        view = PharmacyAdminOnlyView()
        
        assert permission.has_permission(request, view) is True
    
    def test_patient_denied_permission(self, request_factory, patient_user):
        """Patient should be denied permission."""
        permission = IsPharmacyAdmin()
        request = request_factory.get('/test/')
        request.user = patient_user
        
        view = PharmacyAdminOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_unauthenticated_user_denied_permission(self, request_factory):
        """Unauthenticated user should be denied permission."""
        from django.contrib.auth.models import AnonymousUser
        
        permission = IsPharmacyAdmin()
        request = request_factory.get('/test/')
        request.user = AnonymousUser()
        
        view = PharmacyAdminOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_permission_has_custom_message(self):
        """IsPharmacyAdmin should have a custom error message."""
        permission = IsPharmacyAdmin()
        
        assert hasattr(permission, 'message')
        assert 'pharmacy' in permission.message.lower()


# ============================================================================
# IsVerifiedPharmacy PERMISSION TESTS
# ============================================================================

@pytest.mark.django_db
class TestIsVerifiedPharmacyPermission:
    """Tests for IsVerifiedPharmacy permission class."""
    
    def test_verified_pharmacy_admin_has_permission(self, request_factory, verified_pharmacy_admin_user):
        """Verified pharmacy admin should have permission."""
        permission = IsVerifiedPharmacy()
        request = request_factory.get('/test/')
        request.user = verified_pharmacy_admin_user
        
        view = VerifiedPharmacyOnlyView()
        
        assert permission.has_permission(request, view) is True
    
    def test_unverified_pharmacy_admin_denied_permission(self, request_factory, pharmacy_admin_user):
        """Unverified pharmacy admin should be denied permission."""
        permission = IsVerifiedPharmacy()
        request = request_factory.get('/test/')
        request.user = pharmacy_admin_user
        
        view = VerifiedPharmacyOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_patient_denied_permission(self, request_factory, patient_user):
        """Patient should be denied permission."""
        permission = IsVerifiedPharmacy()
        request = request_factory.get('/test/')
        request.user = patient_user
        
        view = VerifiedPharmacyOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_verified_patient_denied_permission(self, request_factory, patient_user):
        """Verified patient should still be denied permission (wrong user type)."""
        # Make patient verified
        patient_user.is_verified = True
        patient_user.save()
        
        permission = IsVerifiedPharmacy()
        request = request_factory.get('/test/')
        request.user = patient_user
        
        view = VerifiedPharmacyOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_unauthenticated_user_denied_permission(self, request_factory):
        """Unauthenticated user should be denied permission."""
        from django.contrib.auth.models import AnonymousUser
        
        permission = IsVerifiedPharmacy()
        request = request_factory.get('/test/')
        request.user = AnonymousUser()
        
        view = VerifiedPharmacyOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_permission_has_custom_message(self):
        """IsVerifiedPharmacy should have a custom error message."""
        permission = IsVerifiedPharmacy()
        
        assert hasattr(permission, 'message')
        assert 'verified' in permission.message.lower()
        assert 'pharmacy' in permission.message.lower()


# ============================================================================
# CROSS-ROLE ACCESS TESTS
# ============================================================================

@pytest.mark.django_db
class TestCrossRoleAccess:
    """Tests to ensure users cannot access endpoints for other roles."""
    
    def test_patient_cannot_access_pharmacy_endpoint(self, api_client, patient_user):
        """Patient should get 403 when accessing pharmacy-only endpoint."""
        # This test will need actual endpoints, but we'll test the permission directly
        permission = IsPharmacyAdmin()
        request_factory = APIRequestFactory()
        request = request_factory.get('/test/')
        request.user = patient_user
        
        view = PharmacyAdminOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_pharmacy_admin_cannot_access_patient_endpoint(self, api_client, pharmacy_admin_user):
        """Pharmacy admin should get 403 when accessing patient-only endpoint."""
        permission = IsPatient()
        request_factory = APIRequestFactory()
        request = request_factory.get('/test/')
        request.user = pharmacy_admin_user
        
        view = PatientOnlyView()
        
        assert permission.has_permission(request, view) is False
    
    def test_unverified_pharmacy_cannot_access_verified_endpoint(self, api_client, pharmacy_admin_user):
        """Unverified pharmacy admin should get 403 when accessing verified-only endpoint."""
        permission = IsVerifiedPharmacy()
        request_factory = APIRequestFactory()
        request = request_factory.get('/test/')
        request.user = pharmacy_admin_user
        
        view = VerifiedPharmacyOnlyView()
        
        assert permission.has_permission(request, view) is False


# ============================================================================
# PERMISSION ERROR MESSAGE TESTS
# ============================================================================

@pytest.mark.django_db
class TestPermissionErrorMessages:
    """Tests to ensure permission classes return appropriate error messages."""
    
    def test_is_patient_error_message_is_descriptive(self):
        """IsPatient should return a descriptive error message."""
        permission = IsPatient()
        
        assert hasattr(permission, 'message')
        assert len(permission.message) > 0
        assert isinstance(permission.message, str)
    
    def test_is_pharmacy_admin_error_message_is_descriptive(self):
        """IsPharmacyAdmin should return a descriptive error message."""
        permission = IsPharmacyAdmin()
        
        assert hasattr(permission, 'message')
        assert len(permission.message) > 0
        assert isinstance(permission.message, str)
    
    def test_is_verified_pharmacy_error_message_is_descriptive(self):
        """IsVerifiedPharmacy should return a descriptive error message."""
        permission = IsVerifiedPharmacy()
        
        assert hasattr(permission, 'message')
        assert len(permission.message) > 0
        assert isinstance(permission.message, str)
    
    def test_error_messages_are_unique(self):
        """Each permission class should have a unique error message."""
        is_patient = IsPatient()
        is_pharmacy_admin = IsPharmacyAdmin()
        is_verified_pharmacy = IsVerifiedPharmacy()
        
        messages = [
            is_patient.message,
            is_pharmacy_admin.message,
            is_verified_pharmacy.message,
        ]
        
        # All messages should be different
        assert len(set(messages)) == len(messages)
