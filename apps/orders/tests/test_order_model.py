"""
Test suite for Order model.

Following TDD principles: These tests are written FIRST and should FAIL.
The model implementation will be written to make these tests pass.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from tests.factories import (
    OrderFactory, PrescriptionFactory, UserFactory,
    PharmacyFactory, PharmacyAdminFactory
)


@pytest.mark.django_db
class TestOrderCreation:
    """Test order creation with valid data."""
    
    def test_create_order_with_valid_data(self):
        """Should successfully create an order with all required fields."""
        patient = UserFactory(user_type='patient')
        pharmacy = PharmacyFactory()
        verifier = PharmacyAdminFactory()
        prescription = PrescriptionFactory(
            patient=patient,
            status='verified',
            verifier=verifier,
            verified_at=timezone.now()
        )
        
        order = OrderFactory(
            patient=patient,
            pharmacy=pharmacy,
            prescription=prescription,
            total_amount=Decimal('150.50'),
            status='placed'
        )
        
        assert order.id is not None
        assert order.patient == patient
        assert order.pharmacy == pharmacy
        assert order.prescription == prescription
        assert order.total_amount == Decimal('150.50')
        assert order.status == 'placed'
        assert order.created_at is not None
        assert order.payment_reference_id == ''
        assert order.tracking_number == ''
    
    def test_order_string_representation(self):
        """Should return order ID and patient as string representation."""
        patient = UserFactory(email='patient@example.com')
        order = OrderFactory(patient=patient)
        
        expected = f"Order #{order.id} - {patient.email}"
        assert str(order) == expected
    
    def test_created_at_auto_set(self):
        """Should automatically set created_at timestamp on creation."""
        order = OrderFactory()
        assert order.created_at is not None


@pytest.mark.django_db
class TestOrderBusinessRules:
    """Test business rule: prescription must be verified."""
    
    def test_cannot_create_order_with_pending_prescription(self):
        """Should prevent order creation when prescription is pending verification."""
        prescription = PrescriptionFactory(status='pending_verification')
        order = OrderFactory.build(prescription=prescription)
        
        with pytest.raises(ValidationError) as exc_info:
            order.full_clean()
        
        assert 'prescription' in exc_info.value.error_dict
        assert 'must be verified' in str(exc_info.value.error_dict['prescription']).lower()
    
    def test_cannot_create_order_with_rejected_prescription(self):
        """Should prevent order creation when prescription is rejected."""
        prescription = PrescriptionFactory(
            status='rejected',
            rejection_reason='Unclear image'
        )
        order = OrderFactory.build(prescription=prescription)
        
        with pytest.raises(ValidationError) as exc_info:
            order.full_clean()
        
        assert 'prescription' in exc_info.value.error_dict
    
    def test_can_create_order_with_verified_prescription(self):
        """Should allow order creation when prescription is verified."""
        verifier = PharmacyAdminFactory()
        prescription = PrescriptionFactory(
            status='verified',
            verifier=verifier,
            verified_at=timezone.now()
        )
        order = OrderFactory(prescription=prescription)
        
        order.full_clean()  # Should not raise
        assert order.id is not None


@pytest.mark.django_db
class TestOrderStatusChoices:
    """Test order status field choices."""
    
    def test_placed_status(self):
        """Should accept placed status."""
        order = OrderFactory(status='placed')
        order.full_clean()  # Should not raise
        assert order.status == 'placed'
    
    def test_confirmed_status(self):
        """Should accept confirmed status."""
        order = OrderFactory(status='confirmed')
        order.full_clean()  # Should not raise
        assert order.status == 'confirmed'
    
    def test_shipped_status(self):
        """Should accept shipped status."""
        order = OrderFactory(status='shipped', tracking_number='TRACK123')
        order.full_clean()  # Should not raise
        assert order.status == 'shipped'
    
    def test_delivered_status(self):
        """Should accept delivered status."""
        order = OrderFactory(status='delivered', tracking_number='TRACK123')
        order.full_clean()  # Should not raise
        assert order.status == 'delivered'
    
    def test_invalid_status_rejected(self):
        """Should reject invalid status values."""
        order = OrderFactory.build(status='invalid_status')
        
        with pytest.raises(ValidationError) as exc_info:
            order.full_clean()
        
        assert 'status' in exc_info.value.error_dict


@pytest.mark.django_db
class TestOrderStatusTransitions:
    """Test status transition validation."""
    
    def test_cannot_skip_from_placed_to_delivered(self):
        """Should prevent skipping states (placed -> delivered)."""
        order = OrderFactory(status='placed')
        order.save()
        
        order.status = 'delivered'
        order.tracking_number = 'TRACK123'
        
        with pytest.raises(ValidationError) as exc_info:
            order.full_clean()
        
        assert 'status' in exc_info.value.error_dict
        assert 'cannot transition' in str(exc_info.value.error_dict['status']).lower()
    
    def test_cannot_skip_from_placed_to_shipped(self):
        """Should prevent skipping confirmed state (placed -> shipped)."""
        order = OrderFactory(status='placed')
        order.save()
        
        order.status = 'shipped'
        order.tracking_number = 'TRACK123'
        
        with pytest.raises(ValidationError) as exc_info:
            order.full_clean()
        
        assert 'status' in exc_info.value.error_dict
    
    def test_can_transition_placed_to_confirmed(self):
        """Should allow transition from placed to confirmed."""
        order = OrderFactory(status='placed')
        order.save()
        
        order.status = 'confirmed'
        order.full_clean()  # Should not raise
        order.save()
        assert order.status == 'confirmed'
    
    def test_can_transition_confirmed_to_shipped(self):
        """Should allow transition from confirmed to shipped."""
        order = OrderFactory(status='confirmed')
        order.save()
        
        order.status = 'shipped'
        order.tracking_number = 'TRACK123'
        order.full_clean()  # Should not raise
        order.save()
        assert order.status == 'shipped'
    
    def test_can_transition_shipped_to_delivered(self):
        """Should allow transition from shipped to delivered."""
        order = OrderFactory(status='shipped', tracking_number='TRACK123')
        order.save()
        
        order.status = 'delivered'
        order.full_clean()  # Should not raise
        order.save()
        assert order.status == 'delivered'
    
    def test_shipped_requires_tracking_number(self):
        """Should require tracking number when status is shipped."""
        order = OrderFactory.build(status='shipped', tracking_number='')
        
        with pytest.raises(ValidationError) as exc_info:
            order.full_clean()
        
        assert 'tracking_number' in exc_info.value.error_dict


@pytest.mark.django_db
class TestOrderForeignKeyRelationships:
    """Test foreign key relationships and cascade behaviors."""
    
    def test_patient_foreign_key_required(self):
        """Should require patient foreign key."""
        order = OrderFactory.build(patient=None)
        
        with pytest.raises(ValidationError):
            order.full_clean()
    
    def test_patient_cascade_delete(self):
        """Should delete order when patient is deleted (CASCADE)."""
        patient = UserFactory()
        order = OrderFactory(patient=patient)
        order_id = order.id
        
        patient.delete()
        
        from orders.models import Order
        assert not Order.objects.filter(id=order_id).exists()
    
    def test_pharmacy_protect_delete(self):
        """Should prevent pharmacy deletion when orders exist (PROTECT)."""
        pharmacy = PharmacyFactory()
        order = OrderFactory(pharmacy=pharmacy)
        
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            pharmacy.delete()
    
    def test_prescription_protect_delete(self):
        """Should prevent prescription deletion when orders exist (PROTECT)."""
        prescription = PrescriptionFactory(
            status='verified',
            verifier=PharmacyAdminFactory(),
            verified_at=timezone.now()
        )
        order = OrderFactory(prescription=prescription)
        
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            prescription.delete()
    
    def test_patient_related_name(self):
        """Should access orders via patient.orders."""
        patient = UserFactory()
        order1 = OrderFactory(patient=patient)
        order2 = OrderFactory(patient=patient)
        
        assert order1 in patient.orders.all()
        assert order2 in patient.orders.all()
        assert patient.orders.count() == 2
    
    def test_pharmacy_related_name(self):
        """Should access orders via pharmacy.orders."""
        pharmacy = PharmacyFactory()
        order1 = OrderFactory(pharmacy=pharmacy)
        order2 = OrderFactory(pharmacy=pharmacy)
        
        assert order1 in pharmacy.orders.all()
        assert order2 in pharmacy.orders.all()
        assert pharmacy.orders.count() == 2


@pytest.mark.django_db
class TestOrderDecimalPrecision:
    """Test decimal precision for total_amount field."""
    
    def test_total_amount_with_two_decimal_places(self):
        """Should accept amounts with two decimal places."""
        order = OrderFactory(total_amount=Decimal('99.99'))
        order.full_clean()  # Should not raise
        assert order.total_amount == Decimal('99.99')
    
    def test_total_amount_minimum_value(self):
        """Should accept minimum amount of 0.01."""
        order = OrderFactory(total_amount=Decimal('0.01'))
        order.full_clean()  # Should not raise
        assert order.total_amount == Decimal('0.01')
    
    def test_total_amount_zero_rejected(self):
        """Should reject zero total amount."""
        order = OrderFactory.build(total_amount=Decimal('0.00'))
        
        with pytest.raises(ValidationError) as exc_info:
            order.full_clean()
        
        assert 'total_amount' in exc_info.value.error_dict
    
    def test_total_amount_negative_rejected(self):
        """Should reject negative total amount."""
        order = OrderFactory.build(total_amount=Decimal('-10.00'))
        
        with pytest.raises(ValidationError) as exc_info:
            order.full_clean()
        
        assert 'total_amount' in exc_info.value.error_dict
    
    def test_large_total_amount(self):
        """Should accept large amounts up to 999999.99."""
        order = OrderFactory(total_amount=Decimal('999999.99'))
        order.full_clean()  # Should not raise
        assert order.total_amount == Decimal('999999.99')


@pytest.mark.django_db
class TestOrderIndexes:
    """Test database indexes for order model."""
    
    def test_patient_is_indexed(self):
        """Should have index on patient field."""
        from orders.models import Order
        
        indexes = Order._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['patient'] in index_fields or ('patient',) in index_fields
    
    def test_pharmacy_is_indexed(self):
        """Should have index on pharmacy field."""
        from orders.models import Order
        
        indexes = Order._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['pharmacy'] in index_fields or ('pharmacy',) in index_fields
    
    def test_status_is_indexed(self):
        """Should have index on status field."""
        from orders.models import Order
        
        indexes = Order._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['status'] in index_fields or ('status',) in index_fields
    
    def test_prescription_is_indexed(self):
        """Should have index on prescription field."""
        from orders.models import Order
        
        indexes = Order._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['prescription'] in index_fields or ('prescription',) in index_fields


@pytest.mark.django_db
class TestOrderOrdering:
    """Test default ordering of orders."""
    
    def test_ordered_by_created_at_descending(self):
        """Should order orders by created_at in descending order (newest first)."""
        import time
        old_order = OrderFactory()
        time.sleep(0.01)
        new_order = OrderFactory()
        
        from orders.models import Order
        orders = list(Order.objects.all())
        
        # Newest should come first
        assert orders[0].id == new_order.id
        assert orders[1].id == old_order.id


@pytest.mark.django_db
class TestOrderEdgeCases:
    """Test edge cases and boundary values."""
    
    def test_very_long_payment_reference_id(self):
        """Should accept payment reference IDs up to 100 characters."""
        long_ref = 'PAY' + 'X' * 97
        order = OrderFactory(payment_reference_id=long_ref)
        order.full_clean()  # Should not raise
        assert len(order.payment_reference_id) == 100
    
    def test_very_long_tracking_number(self):
        """Should accept tracking numbers up to 100 characters."""
        long_tracking = 'TRACK' + 'X' * 95
        order = OrderFactory(status='shipped', tracking_number=long_tracking)
        order.full_clean()  # Should not raise
        assert len(order.tracking_number) == 100
    
    def test_optional_payment_reference_id(self):
        """Should allow empty payment_reference_id."""
        order = OrderFactory(payment_reference_id='')
        order.full_clean()  # Should not raise
        assert order.payment_reference_id == ''
    
    def test_optional_tracking_number_for_non_shipped_orders(self):
        """Should allow empty tracking_number for non-shipped orders."""
        order = OrderFactory(status='placed', tracking_number='')
        order.full_clean()  # Should not raise
        assert order.tracking_number == ''
