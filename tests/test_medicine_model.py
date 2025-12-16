"""
Test suite for Medicine model.

Following TDD principles: These tests are written FIRST and should FAIL.
The model implementation will be written to make these tests pass.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.utils import timezone

from tests.factories import PharmacyFactory, MedicineFactory


@pytest.mark.django_db
class TestMedicineCreation:
    """Test medicine creation with valid data."""
    
    def test_create_medicine_with_valid_data(self):
        """Should successfully create a medicine with all required fields."""
        pharmacy = PharmacyFactory()
        medicine = MedicineFactory(
            commercial_name='Paracetamol 500mg',
            generic_name='Acetaminophen',
            manufacturer='PharmaCorp',
            price=Decimal('25.50'),
            stock_quantity=100,
            pharmacy=pharmacy
        )
        
        assert medicine.id is not None
        assert medicine.commercial_name == 'Paracetamol 500mg'
        assert medicine.generic_name == 'Acetaminophen'
        assert medicine.manufacturer == 'PharmaCorp'
        assert medicine.price == Decimal('25.50')
        assert medicine.stock_quantity == 100
        assert medicine.pharmacy == pharmacy
    
    def test_medicine_string_representation(self):
        """Should return commercial name as string representation."""
        medicine = MedicineFactory(commercial_name='Aspirin 100mg')
        assert str(medicine) == 'Aspirin 100mg'


@pytest.mark.django_db
class TestMedicinePriceValidation:
    """Test price field validation."""
    
    def test_negative_price_rejected(self):
        """Should reject negative prices."""
        medicine = MedicineFactory.build(price=Decimal('-10.00'))
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'price' in exc_info.value.error_dict
    
    def test_zero_price_rejected(self):
        """Should reject zero price."""
        medicine = MedicineFactory.build(price=Decimal('0.00'))
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'price' in exc_info.value.error_dict
    
    def test_minimum_valid_price(self):
        """Should accept minimum valid price of 0.01."""
        medicine = MedicineFactory(price=Decimal('0.01'))
        medicine.full_clean()  # Should not raise
        assert medicine.price == Decimal('0.01')
    
    def test_price_decimal_precision(self):
        """Should store price with 2 decimal places."""
        medicine = MedicineFactory(price=Decimal('99.99'))
        medicine.full_clean()
        assert medicine.price == Decimal('99.99')
    
    def test_large_price_accepted(self):
        """Should accept large prices up to max_digits limit."""
        # max_digits=10, decimal_places=2 means up to 99,999,999.99
        large_price = Decimal('99999999.99')
        medicine = MedicineFactory(price=large_price)
        medicine.full_clean()
        assert medicine.price == large_price
    
    def test_price_exceeding_max_digits_rejected(self):
        """Should reject prices exceeding max_digits limit."""
        # This would be 100,000,000.00 which exceeds 10 digits total
        too_large_price = Decimal('100000000.00')
        medicine = MedicineFactory.build(price=too_large_price)
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'price' in exc_info.value.error_dict
    
    def test_price_is_required(self):
        """Should raise ValidationError when price is missing."""
        medicine = MedicineFactory.build(price=None)
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'price' in exc_info.value.error_dict


@pytest.mark.django_db
class TestMedicineStockValidation:
    """Test stock quantity field validation."""
    
    def test_negative_stock_rejected(self):
        """Should reject negative stock quantities."""
        medicine = MedicineFactory.build(stock_quantity=-1)
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'stock_quantity' in exc_info.value.error_dict
    
    def test_zero_stock_allowed(self):
        """Should allow zero stock (out of stock scenario)."""
        medicine = MedicineFactory(stock_quantity=0)
        medicine.full_clean()  # Should not raise
        assert medicine.stock_quantity == 0
    
    def test_maximum_stock_value(self):
        """Should accept large stock quantities."""
        large_stock = 999999
        medicine = MedicineFactory(stock_quantity=large_stock)
        medicine.full_clean()
        assert medicine.stock_quantity == large_stock
    
    def test_stock_quantity_is_required(self):
        """Should raise ValidationError when stock_quantity is missing."""
        medicine = MedicineFactory.build(stock_quantity=None)
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'stock_quantity' in exc_info.value.error_dict


@pytest.mark.django_db
class TestMedicineRequiredFields:
    """Test required field validation."""
    
    def test_commercial_name_is_required(self):
        """Should raise ValidationError when commercial_name is missing."""
        medicine = MedicineFactory.build(commercial_name='')
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'commercial_name' in exc_info.value.error_dict
    
    def test_generic_name_is_required(self):
        """Should raise ValidationError when generic_name is missing."""
        medicine = MedicineFactory.build(generic_name='')
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'generic_name' in exc_info.value.error_dict
    
    def test_manufacturer_is_required(self):
        """Should raise ValidationError when manufacturer is missing."""
        medicine = MedicineFactory.build(manufacturer='')
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'manufacturer' in exc_info.value.error_dict


@pytest.mark.django_db
class TestMedicinePharmacyRelationship:
    """Test foreign key relationship with Pharmacy."""
    
    def test_medicine_requires_pharmacy(self):
        """Should raise ValidationError when pharmacy is missing."""
        medicine = MedicineFactory.build(pharmacy=None)
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'pharmacy' in exc_info.value.error_dict
    
    def test_deleting_pharmacy_with_medicines_protected(self):
        """Should prevent deletion of pharmacy that has medicines (PROTECT behavior)."""
        pharmacy = PharmacyFactory()
        MedicineFactory(pharmacy=pharmacy)
        
        with pytest.raises(ProtectedError):
            pharmacy.delete()
    
    def test_deleting_pharmacy_without_medicines_allowed(self):
        """Should allow deletion of pharmacy with no medicines."""
        pharmacy = PharmacyFactory()
        pharmacy_id = pharmacy.id
        
        pharmacy.delete()
        
        from pharmacies.models import Pharmacy
        assert not Pharmacy.objects.filter(id=pharmacy_id).exists()
    
    def test_pharmacy_reverse_relationship(self):
        """Should access medicines from pharmacy using reverse relationship."""
        pharmacy = PharmacyFactory()
        medicine1 = MedicineFactory(pharmacy=pharmacy)
        medicine2 = MedicineFactory(pharmacy=pharmacy)
        
        medicines = pharmacy.medicines.all()
        assert medicines.count() == 2
        assert medicine1 in medicines
        assert medicine2 in medicines


@pytest.mark.django_db
class TestMedicineUniqueConstraints:
    """Test unique constraints on medicine fields."""
    
    def test_duplicate_medicine_same_pharmacy_rejected(self):
        """Should prevent duplicate medicine in the same pharmacy."""
        pharmacy = PharmacyFactory()
        MedicineFactory(
            commercial_name='Paracetamol 500mg',
            pharmacy=pharmacy
        )
        
        with pytest.raises(IntegrityError):
            MedicineFactory(
                commercial_name='Paracetamol 500mg',
                pharmacy=pharmacy
            )
    
    def test_same_medicine_different_pharmacies_allowed(self):
        """Should allow same medicine in different pharmacies."""
        pharmacy1 = PharmacyFactory()
        pharmacy2 = PharmacyFactory()
        
        medicine1 = MedicineFactory(
            commercial_name='Paracetamol 500mg',
            pharmacy=pharmacy1
        )
        medicine2 = MedicineFactory(
            commercial_name='Paracetamol 500mg',
            pharmacy=pharmacy2
        )
        
        assert medicine1.id != medicine2.id
        assert medicine1.commercial_name == medicine2.commercial_name


@pytest.mark.django_db
class TestMedicineTimestamps:
    """Test automatic timestamp fields."""
    
    def test_created_at_auto_set(self):
        """Should automatically set created_at timestamp on creation."""
        medicine = MedicineFactory()
        assert medicine.created_at is not None
        assert isinstance(medicine.created_at, timezone.datetime)
    
    def test_updated_at_auto_set(self):
        """Should automatically set updated_at timestamp on creation."""
        medicine = MedicineFactory()
        assert medicine.updated_at is not None
        assert isinstance(medicine.updated_at, timezone.datetime)
    
    def test_updated_at_auto_updates(self):
        """Should automatically update updated_at timestamp on save."""
        medicine = MedicineFactory()
        original_updated_at = medicine.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        medicine.stock_quantity = 50
        medicine.save()
        
        assert medicine.updated_at > original_updated_at
    
    def test_created_at_does_not_change_on_update(self):
        """Should not change created_at timestamp on updates."""
        medicine = MedicineFactory()
        original_created_at = medicine.created_at
        
        medicine.stock_quantity = 50
        medicine.save()
        
        assert medicine.created_at == original_created_at


@pytest.mark.django_db
class TestMedicineIndexes:
    """Test database indexes for medicine model."""
    
    def test_commercial_name_is_indexed(self):
        """Should have index on commercial_name field."""
        from pharmacies.models import Medicine
        
        indexes = Medicine._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['commercial_name'] in index_fields
    
    def test_generic_name_is_indexed(self):
        """Should have index on generic_name field."""
        from pharmacies.models import Medicine
        
        indexes = Medicine._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['generic_name'] in index_fields
    
    def test_manufacturer_is_indexed(self):
        """Should have index on manufacturer field."""
        from pharmacies.models import Medicine
        
        indexes = Medicine._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['manufacturer'] in index_fields
    
    def test_pharmacy_stock_composite_index(self):
        """Should have composite index on pharmacy and stock_quantity fields."""
        from pharmacies.models import Medicine
        
        indexes = Medicine._meta.indexes
        index_fields = [idx.fields for idx in indexes]
        
        assert ['pharmacy', 'stock_quantity'] in index_fields


@pytest.mark.django_db
class TestMedicineEdgeCases:
    """Test edge cases and boundary values."""
    
    def test_maximum_commercial_name_length(self):
        """Should accept commercial names up to 200 characters."""
        long_name = 'A' * 200
        medicine = MedicineFactory(commercial_name=long_name)
        medicine.full_clean()  # Should not raise
        assert len(medicine.commercial_name) == 200
    
    def test_commercial_name_exceeding_max_length_rejected(self):
        """Should reject commercial names exceeding 200 characters."""
        too_long_name = 'A' * 201
        medicine = MedicineFactory.build(commercial_name=too_long_name)
        
        with pytest.raises(ValidationError) as exc_info:
            medicine.full_clean()
        
        assert 'commercial_name' in exc_info.value.error_dict
    
    def test_multiple_medicines_zero_stock(self):
        """Should allow multiple medicines with zero stock."""
        pharmacy = PharmacyFactory()
        medicine1 = MedicineFactory(pharmacy=pharmacy, stock_quantity=0)
        medicine2 = MedicineFactory(pharmacy=pharmacy, stock_quantity=0)
        
        assert medicine1.stock_quantity == 0
        assert medicine2.stock_quantity == 0
