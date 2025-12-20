"""
Test suite for Pharmacy model.

Following TDD principles: These tests are written FIRST and should FAIL.
The model implementation will be written to make these tests pass.
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Index

from tests.factories import PharmacyFactory


@pytest.mark.django_db
class TestPharmacyCreation:
    """Test pharmacy creation with valid data."""
    
    def test_create_pharmacy_with_valid_data(self):
        """Should successfully create a pharmacy with all required fields."""
        pharmacy = PharmacyFactory(
            name='HealthPlus Pharmacy',
            license_number='LIC123456',
            contact_email='contact@healthplus.com',
            street_address='123 Main Street',
            city='Mumbai',
            state='Maharashtra',
            postal_code='400001',
            phone_number='+919876543210'
        )
        
        assert pharmacy.id is not None
        assert pharmacy.name == 'HealthPlus Pharmacy'
        assert pharmacy.license_number == 'LIC123456'
        assert pharmacy.contact_email == 'contact@healthplus.com'
        assert pharmacy.city == 'Mumbai'
        assert pharmacy.state == 'Maharashtra'
        assert pharmacy.phone_number == '+919876543210'
    
    def test_pharmacy_string_representation(self):
        """Should return pharmacy name as string representation."""
        pharmacy = PharmacyFactory(name='Test Pharmacy')
        assert str(pharmacy) == 'Test Pharmacy'


@pytest.mark.django_db
class TestPharmacyValidation:
    """Test pharmacy field validation."""
    
    def test_license_number_is_required(self):
        """Should raise ValidationError when license_number is missing."""
        pharmacy = PharmacyFactory.build(license_number='')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'license_number' in exc_info.value.error_dict
    
    def test_contact_email_is_required(self):
        """Should raise ValidationError when contact_email is missing."""
        pharmacy = PharmacyFactory.build(contact_email='')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'contact_email' in exc_info.value.error_dict
    
    def test_invalid_email_format_rejected(self):
        """Should raise ValidationError for invalid email format."""
        pharmacy = PharmacyFactory.build(contact_email='not-an-email')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'contact_email' in exc_info.value.error_dict
    
    def test_phone_number_is_required(self):
        """Should raise ValidationError when phone_number is missing."""
        pharmacy = PharmacyFactory.build(phone_number='')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'phone_number' in exc_info.value.error_dict
    
    def test_phone_number_validation_indian_format(self):
        """Should accept valid Indian phone number format (+91XXXXXXXXXX)."""
        pharmacy = PharmacyFactory(phone_number='+919876543210')
        pharmacy.full_clean()  # Should not raise
        assert pharmacy.phone_number == '+919876543210'
    
    def test_invalid_phone_number_format_rejected(self):
        """Should reject phone numbers not in Indian format."""
        invalid_numbers = [
            '9876543210',  # Missing +91
            '+91987654321',  # Only 9 digits
            '+9198765432100',  # 11 digits
            '+1234567890123',  # Wrong country code
            'invalid',  # Not a number
        ]
        
        for invalid_number in invalid_numbers:
            pharmacy = PharmacyFactory.build(phone_number=invalid_number)
            
            with pytest.raises(ValidationError) as exc_info:
                pharmacy.full_clean()
            
            assert 'phone_number' in exc_info.value.error_dict
    
    def test_name_is_required(self):
        """Should raise ValidationError when name is missing."""
        pharmacy = PharmacyFactory.build(name='')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'name' in exc_info.value.error_dict
    
    def test_street_address_is_required(self):
        """Should raise ValidationError when street_address is missing."""
        pharmacy = PharmacyFactory.build(street_address='')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'street_address' in exc_info.value.error_dict
    
    def test_city_is_required(self):
        """Should raise ValidationError when city is missing."""
        pharmacy = PharmacyFactory.build(city='')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'city' in exc_info.value.error_dict
    
    def test_state_is_required(self):
        """Should raise ValidationError when state is missing."""
        pharmacy = PharmacyFactory.build(state='')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'state' in exc_info.value.error_dict
    
    def test_postal_code_is_required(self):
        """Should raise ValidationError when postal_code is missing."""
        pharmacy = PharmacyFactory.build(postal_code='')
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'postal_code' in exc_info.value.error_dict


@pytest.mark.django_db
class TestPharmacyUniqueConstraints:
    """Test unique constraints on pharmacy fields."""
    
    def test_license_number_must_be_unique(self):
        """Should prevent duplicate license numbers."""
        PharmacyFactory(license_number='LIC123456')
        
        with pytest.raises(IntegrityError):
            PharmacyFactory(license_number='LIC123456')
    
    def test_contact_email_must_be_unique(self):
        """Should prevent duplicate contact emails."""
        PharmacyFactory(contact_email='test@pharmacy.com')
        
        with pytest.raises(IntegrityError):
            PharmacyFactory(contact_email='test@pharmacy.com')
    
    def test_different_pharmacies_can_have_same_name(self):
        """Should allow different pharmacies to have the same name."""
        PharmacyFactory(name='Apollo Pharmacy')
        pharmacy2 = PharmacyFactory(name='Apollo Pharmacy')
        
        assert pharmacy2.id is not None


@pytest.mark.django_db
class TestPharmacyDefaults:
    """Test default values for pharmacy fields."""
    
    def test_is_verified_defaults_to_false(self):
        """Should default is_verified to False for new pharmacies."""
        pharmacy = PharmacyFactory()
        assert pharmacy.is_verified is False
    
    def test_registered_at_auto_set(self):
        """Should automatically set registered_at timestamp on creation."""
        pharmacy = PharmacyFactory()
        assert pharmacy.registered_at is not None


@pytest.mark.django_db
class TestPharmacyIndexes:
    """Test database indexes for pharmacy model."""
    
    def test_license_number_is_indexed(self):
        """Should have index on license_number field."""
        from pharmacies.models import Pharmacy
        
        indexes = Pharmacy._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['license_number'] in index_fields
    
    def test_city_state_composite_index(self):
        """Should have composite index on city and state fields."""
        from pharmacies.models import Pharmacy
        
        indexes = Pharmacy._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['city', 'state'] in index_fields
    
    def test_is_verified_is_indexed(self):
        """Should have index on is_verified field."""
        from pharmacies.models import Pharmacy
        
        indexes = Pharmacy._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['is_verified'] in index_fields


@pytest.mark.django_db
class TestPharmacyEdgeCases:
    """Test edge cases and boundary values."""
    
    def test_maximum_name_length(self):
        """Should accept names up to 200 characters."""
        long_name = 'A' * 200
        pharmacy = PharmacyFactory(name=long_name)
        pharmacy.full_clean()  # Should not raise
        assert len(pharmacy.name) == 200
    
    def test_name_exceeding_max_length_rejected(self):
        """Should reject names exceeding 200 characters."""
        too_long_name = 'A' * 201
        pharmacy = PharmacyFactory.build(name=too_long_name)
        
        with pytest.raises(ValidationError) as exc_info:
            pharmacy.full_clean()
        
        assert 'name' in exc_info.value.error_dict
    
    def test_maximum_license_number_length(self):
        """Should accept license numbers up to 50 characters."""
        long_license = 'L' * 50
        pharmacy = PharmacyFactory(license_number=long_license)
        pharmacy.full_clean()  # Should not raise
        assert len(pharmacy.license_number) == 50
    
    def test_whitespace_in_fields_preserved(self):
        """Should preserve whitespace in text fields."""
        pharmacy = PharmacyFactory(
            name='  Test Pharmacy  ',
            street_address='  123 Main St  '
        )
        # Note: Django doesn't auto-trim by default
        assert pharmacy.name == '  Test Pharmacy  '
        assert pharmacy.street_address == '  123 Main St  '
    
    def test_email_case_sensitivity(self):
        """Should treat emails as case-insensitive for uniqueness."""
        PharmacyFactory(contact_email='Test@Pharmacy.com')
        
        # This should fail because emails should be case-insensitive
        with pytest.raises(IntegrityError):
            PharmacyFactory(contact_email='test@pharmacy.com')
