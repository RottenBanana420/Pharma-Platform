"""
Test suite for Prescription model.

Following TDD principles: These tests are written FIRST and should FAIL.
The model implementation will be written to make these tests pass.
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from tests.factories import PrescriptionFactory, UserFactory, PharmacyAdminFactory


@pytest.mark.django_db
class TestPrescriptionCreation:
    """Test prescription creation with valid data."""
    
    def test_create_prescription_with_valid_data(self):
        """Should successfully create a prescription with all required fields."""
        patient = UserFactory(user_type='patient')
        prescription = PrescriptionFactory(
            patient=patient,
            prescription_image_path='s3://bucket/prescriptions/123/rx.jpg',
            status='pending_verification'
        )
        
        assert prescription.id is not None
        assert prescription.patient == patient
        assert prescription.prescription_image_path == 's3://bucket/prescriptions/123/rx.jpg'
        assert prescription.status == 'pending_verification'
        assert prescription.uploaded_at is not None
        assert prescription.verifier is None
        assert prescription.verified_at is None
        assert prescription.rejection_reason == ''
    
    def test_prescription_string_representation(self):
        """Should return patient email and status as string representation."""
        patient = UserFactory(email='patient@example.com')
        prescription = PrescriptionFactory(patient=patient, status='verified')
        
        expected = f"Prescription for {patient.email} - verified"
        assert str(prescription) == expected
    
    def test_uploaded_at_auto_set(self):
        """Should automatically set uploaded_at timestamp on creation."""
        prescription = PrescriptionFactory()
        assert prescription.uploaded_at is not None
        # Should be very recent (within last minute)
        assert timezone.now() - prescription.uploaded_at < timedelta(minutes=1)


@pytest.mark.django_db
class TestPrescriptionStatusChoices:
    """Test prescription status field choices."""
    
    def test_pending_verification_status(self):
        """Should accept pending_verification status."""
        prescription = PrescriptionFactory(status='pending_verification')
        prescription.full_clean()  # Should not raise
        assert prescription.status == 'pending_verification'
    
    def test_verified_status(self):
        """Should accept verified status."""
        prescription = PrescriptionFactory(status='verified')
        prescription.full_clean()  # Should not raise
        assert prescription.status == 'verified'
    
    def test_rejected_status(self):
        """Should accept rejected status."""
        prescription = PrescriptionFactory(status='rejected', rejection_reason='Unclear image')
        prescription.full_clean()  # Should not raise
        assert prescription.status == 'rejected'
    
    def test_invalid_status_rejected(self):
        """Should reject invalid status values."""
        prescription = PrescriptionFactory.build(status='invalid_status')
        
        with pytest.raises(ValidationError) as exc_info:
            prescription.full_clean()
        
        assert 'status' in exc_info.value.error_dict


@pytest.mark.django_db
class TestPrescriptionRejectionValidation:
    """Test rejection reason validation rules."""
    
    def test_rejection_requires_rejection_reason(self):
        """Should require rejection_reason when status is rejected."""
        prescription = PrescriptionFactory.build(
            status='rejected',
            rejection_reason=''
        )
        
        with pytest.raises(ValidationError) as exc_info:
            prescription.full_clean()
        
        assert 'rejection_reason' in exc_info.value.error_dict
        assert 'required when status is rejected' in str(exc_info.value.error_dict['rejection_reason']).lower()
    
    def test_rejection_with_reason_accepted(self):
        """Should accept rejection with valid rejection_reason."""
        prescription = PrescriptionFactory(
            status='rejected',
            rejection_reason='Image is too blurry to read'
        )
        prescription.full_clean()  # Should not raise
        assert prescription.rejection_reason == 'Image is too blurry to read'
    
    def test_verified_should_not_have_rejection_reason(self):
        """Should not allow rejection_reason when status is verified."""
        prescription = PrescriptionFactory.build(
            status='verified',
            rejection_reason='Some reason'
        )
        
        with pytest.raises(ValidationError) as exc_info:
            prescription.full_clean()
        
        assert 'rejection_reason' in exc_info.value.error_dict
    
    def test_pending_should_not_have_rejection_reason(self):
        """Should not allow rejection_reason when status is pending_verification."""
        prescription = PrescriptionFactory.build(
            status='pending_verification',
            rejection_reason='Some reason'
        )
        
        with pytest.raises(ValidationError) as exc_info:
            prescription.full_clean()
        
        assert 'rejection_reason' in exc_info.value.error_dict


@pytest.mark.django_db
class TestPrescriptionForeignKeyRelationships:
    """Test foreign key relationships and cascade behaviors."""
    
    def test_patient_foreign_key_required(self):
        """Should require patient foreign key."""
        prescription = PrescriptionFactory.build(patient=None)
        
        with pytest.raises(ValidationError):
            prescription.full_clean()
    
    def test_patient_cascade_delete(self):
        """Should delete prescription when patient is deleted (CASCADE)."""
        patient = UserFactory()
        prescription = PrescriptionFactory(patient=patient)
        prescription_id = prescription.id
        
        patient.delete()
        
        from prescriptions.models import Prescription
        assert not Prescription.objects.filter(id=prescription_id).exists()
    
    def test_verifier_can_be_null(self):
        """Should allow verifier to be null."""
        prescription = PrescriptionFactory(verifier=None)
        prescription.full_clean()  # Should not raise
        assert prescription.verifier is None
    
    def test_verifier_set_null_on_delete(self):
        """Should set verifier to null when verifier user is deleted (SET_NULL)."""
        verifier = PharmacyAdminFactory()
        prescription = PrescriptionFactory(
            status='verified',
            verifier=verifier,
            verified_at=timezone.now()
        )
        
        verifier.delete()
        prescription.refresh_from_db()
        
        assert prescription.verifier is None
        # Prescription should still exist
        assert prescription.id is not None
    
    def test_patient_related_name(self):
        """Should access prescriptions via patient.prescriptions."""
        patient = UserFactory()
        prescription1 = PrescriptionFactory(patient=patient)
        prescription2 = PrescriptionFactory(patient=patient)
        
        assert prescription1 in patient.prescriptions.all()
        assert prescription2 in patient.prescriptions.all()
        assert patient.prescriptions.count() == 2
    
    def test_verifier_related_name(self):
        """Should access verified prescriptions via verifier.verified_prescriptions."""
        verifier = PharmacyAdminFactory()
        prescription1 = PrescriptionFactory(
            status='verified',
            verifier=verifier,
            verified_at=timezone.now()
        )
        prescription2 = PrescriptionFactory(
            status='verified',
            verifier=verifier,
            verified_at=timezone.now()
        )
        
        assert prescription1 in verifier.verified_prescriptions.all()
        assert prescription2 in verifier.verified_prescriptions.all()
        assert verifier.verified_prescriptions.count() == 2


@pytest.mark.django_db
class TestPrescriptionStatusTransitions:
    """Test status transition validation."""
    
    def test_cannot_transition_from_rejected_to_pending(self):
        """Should prevent transition from rejected back to pending_verification."""
        prescription = PrescriptionFactory(
            status='rejected',
            rejection_reason='Unclear image'
        )
        prescription.save()
        
        # Try to change status back to pending
        prescription.status = 'pending_verification'
        prescription.rejection_reason = ''
        
        with pytest.raises(ValidationError) as exc_info:
            prescription.full_clean()
        
        assert 'status' in exc_info.value.error_dict
        assert 'cannot transition' in str(exc_info.value.error_dict['status']).lower()
    
    def test_cannot_transition_from_verified_to_pending(self):
        """Should prevent transition from verified back to pending_verification."""
        verifier = PharmacyAdminFactory()
        prescription = PrescriptionFactory(
            status='verified',
            verifier=verifier,
            verified_at=timezone.now()
        )
        prescription.save()
        
        # Try to change status back to pending
        prescription.status = 'pending_verification'
        
        with pytest.raises(ValidationError) as exc_info:
            prescription.full_clean()
        
        assert 'status' in exc_info.value.error_dict
    
    def test_can_transition_from_pending_to_verified(self):
        """Should allow transition from pending_verification to verified."""
        prescription = PrescriptionFactory(status='pending_verification')
        prescription.save()
        
        verifier = PharmacyAdminFactory()
        prescription.status = 'verified'
        prescription.verifier = verifier
        prescription.verified_at = timezone.now()
        
        prescription.full_clean()  # Should not raise
        prescription.save()
        assert prescription.status == 'verified'
    
    def test_can_transition_from_pending_to_rejected(self):
        """Should allow transition from pending_verification to rejected."""
        prescription = PrescriptionFactory(status='pending_verification')
        prescription.save()
        
        prescription.status = 'rejected'
        prescription.rejection_reason = 'Image quality too poor'
        
        prescription.full_clean()  # Should not raise
        prescription.save()
        assert prescription.status == 'rejected'


@pytest.mark.django_db
class TestPrescriptionIndexes:
    """Test database indexes for prescription model."""
    
    def test_patient_is_indexed(self):
        """Should have index on patient field."""
        from prescriptions.models import Prescription
        
        indexes = Prescription._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['patient'] in index_fields or ('patient',) in index_fields
    
    def test_status_is_indexed(self):
        """Should have index on status field."""
        from prescriptions.models import Prescription
        
        indexes = Prescription._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['status'] in index_fields or ('status',) in index_fields


@pytest.mark.django_db
class TestPrescriptionOrdering:
    """Test default ordering of prescriptions."""
    
    def test_ordered_by_uploaded_at_descending(self):
        """Should order prescriptions by uploaded_at in descending order (newest first)."""
        # Create prescriptions with slight time differences
        old_prescription = PrescriptionFactory()
        # Small delay to ensure different timestamps
        import time
        time.sleep(0.01)
        new_prescription = PrescriptionFactory()
        
        from prescriptions.models import Prescription
        prescriptions = list(Prescription.objects.all())
        
        # Newest should come first
        assert prescriptions[0].id == new_prescription.id
        assert prescriptions[1].id == old_prescription.id


@pytest.mark.django_db
class TestPrescriptionEdgeCases:
    """Test edge cases and boundary values."""
    
    def test_very_long_s3_path(self):
        """Should accept S3 paths up to 500 characters."""
        # 12 (prefix) + 471 ('a's) + 17 (suffix) = 500
        long_path = 's3://bucket/' + 'a' * 471 + '/prescription.jpg'
        prescription = PrescriptionFactory(prescription_image_path=long_path)
        prescription.full_clean()  # Should not raise
        assert len(prescription.prescription_image_path) <= 500
    
    def test_s3_path_exceeding_max_length_rejected(self):
        """Should reject S3 paths exceeding 500 characters."""
        # 12 + 472 + 17 = 501 characters
        too_long_path = 's3://bucket/' + 'a' * 472 + '/prescription.jpg'
        prescription = PrescriptionFactory.build(prescription_image_path=too_long_path)
        
        with pytest.raises(ValidationError) as exc_info:
            prescription.full_clean()
        
        assert 'prescription_image_path' in exc_info.value.error_dict
    
    def test_very_long_rejection_reason(self):
        """Should accept very long rejection reasons."""
        long_reason = 'Rejected because ' + 'a' * 5000
        prescription = PrescriptionFactory(
            status='rejected',
            rejection_reason=long_reason
        )
        prescription.full_clean()  # Should not raise
        assert prescription.rejection_reason == long_reason
    
    def test_empty_prescription_image_path_rejected(self):
        """Should reject empty prescription_image_path."""
        prescription = PrescriptionFactory.build(prescription_image_path='')
        
        with pytest.raises(ValidationError) as exc_info:
            prescription.full_clean()
        
        assert 'prescription_image_path' in exc_info.value.error_dict
    
    def test_prescription_without_verifier_but_verified_status(self):
        """Should allow verified status without verifier (edge case for system verification)."""
        # This might be allowed if system auto-verifies in some cases
        # Or it might be invalid - test will determine the business rule
        prescription = PrescriptionFactory.build(
            status='verified',
            verifier=None,
            verified_at=timezone.now()
        )
        
        # This test will help determine if verifier is required for verified status
        # Adjust model based on business requirements
        prescription.full_clean()  # Behavior to be determined by model implementation
