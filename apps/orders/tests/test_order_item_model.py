"""
Test suite for OrderItem model.

Following TDD principles: These tests are written FIRST and should FAIL.
The model implementation will be written to make these tests pass.
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from tests.factories import OrderItemFactory, OrderFactory, MedicineFactory


@pytest.mark.django_db
class TestOrderItemCreation:
    """Test order item creation with valid data."""
    
    def test_create_order_item_with_valid_data(self):
        """Should successfully create an order item with all required fields."""
        order = OrderFactory()
        medicine = MedicineFactory()
        
        order_item = OrderItemFactory(
            order=order,
            medicine=medicine,
            quantity=5,
            unit_price=Decimal('25.50')
        )
        
        assert order_item.id is not None
        assert order_item.order == order
        assert order_item.medicine == medicine
        assert order_item.quantity == 5
        assert order_item.unit_price == Decimal('25.50')
    
    def test_order_item_string_representation(self):
        """Should return medicine name and quantity as string representation."""
        medicine = MedicineFactory(commercial_name='Aspirin')
        order_item = OrderItemFactory(medicine=medicine, quantity=3)
        
        expected = f"{medicine.commercial_name} x 3"
        assert str(order_item) == expected
    
    def test_subtotal_calculation(self):
        """Should calculate subtotal as quantity * unit_price."""
        order_item = OrderItemFactory(
            quantity=10,
            unit_price=Decimal('15.75')
        )
        
        expected_subtotal = Decimal('157.50')
        assert order_item.subtotal == expected_subtotal


@pytest.mark.django_db
class TestOrderItemQuantityValidation:
    """Test quantity validation rules."""
    
    def test_quantity_must_be_positive(self):
        """Should require quantity to be at least 1."""
        order_item = OrderItemFactory(quantity=5)
        order_item.full_clean()  # Should not raise
        assert order_item.quantity == 5
    
    def test_zero_quantity_rejected(self):
        """Should reject zero quantity."""
        order_item = OrderItemFactory.build(quantity=0)
        
        with pytest.raises(ValidationError) as exc_info:
            order_item.full_clean()
        
        assert 'quantity' in exc_info.value.error_dict
    
    def test_negative_quantity_rejected(self):
        """Should reject negative quantity."""
        order_item = OrderItemFactory.build(quantity=-5)
        
        with pytest.raises(ValidationError) as exc_info:
            order_item.full_clean()
        
        assert 'quantity' in exc_info.value.error_dict


@pytest.mark.django_db
class TestOrderItemForeignKeyRelationships:
    """Test foreign key relationships and cascade behaviors."""
    
    def test_order_foreign_key_required(self):
        """Should require order foreign key."""
        order_item = OrderItemFactory.build(order=None)
        
        with pytest.raises(ValidationError):
            order_item.full_clean()
    
    def test_medicine_foreign_key_required(self):
        """Should require medicine foreign key."""
        order_item = OrderItemFactory.build(medicine=None)
        
        with pytest.raises(ValidationError):
            order_item.full_clean()
    
    def test_order_cascade_delete(self):
        """Should delete order items when order is deleted (CASCADE)."""
        order = OrderFactory()
        order_item1 = OrderItemFactory(order=order)
        order_item2 = OrderItemFactory(order=order)
        item1_id = order_item1.id
        item2_id = order_item2.id
        
        order.delete()
        
        from orders.models import OrderItem
        assert not OrderItem.objects.filter(id=item1_id).exists()
        assert not OrderItem.objects.filter(id=item2_id).exists()
    
    def test_medicine_protect_delete(self):
        """Should prevent medicine deletion when order items exist (PROTECT)."""
        medicine = MedicineFactory()
        order_item = OrderItemFactory(medicine=medicine)
        
        from django.db.models import ProtectedError
        with pytest.raises(ProtectedError):
            medicine.delete()
    
    def test_order_related_name(self):
        """Should access order items via order.items."""
        order = OrderFactory()
        item1 = OrderItemFactory(order=order)
        item2 = OrderItemFactory(order=order)
        
        assert item1 in order.items.all()
        assert item2 in order.items.all()
        assert order.items.count() == 2
    
    def test_medicine_related_name(self):
        """Should access order items via medicine.order_items."""
        medicine = MedicineFactory()
        item1 = OrderItemFactory(medicine=medicine)
        item2 = OrderItemFactory(medicine=medicine)
        
        assert item1 in medicine.order_items.all()
        assert item2 in medicine.order_items.all()
        assert medicine.order_items.count() == 2


@pytest.mark.django_db
class TestOrderItemDecimalPrecision:
    """Test decimal precision for unit_price field."""
    
    def test_unit_price_with_two_decimal_places(self):
        """Should accept prices with two decimal places."""
        order_item = OrderItemFactory(unit_price=Decimal('99.99'))
        order_item.full_clean()  # Should not raise
        assert order_item.unit_price == Decimal('99.99')
    
    def test_unit_price_minimum_value(self):
        """Should accept minimum price of 0.01."""
        order_item = OrderItemFactory(unit_price=Decimal('0.01'))
        order_item.full_clean()  # Should not raise
        assert order_item.unit_price == Decimal('0.01')
    
    def test_unit_price_zero_rejected(self):
        """Should reject zero unit price."""
        order_item = OrderItemFactory.build(unit_price=Decimal('0.00'))
        
        with pytest.raises(ValidationError) as exc_info:
            order_item.full_clean()
        
        assert 'unit_price' in exc_info.value.error_dict
    
    def test_unit_price_negative_rejected(self):
        """Should reject negative unit price."""
        order_item = OrderItemFactory.build(unit_price=Decimal('-10.00'))
        
        with pytest.raises(ValidationError) as exc_info:
            order_item.full_clean()
        
        assert 'unit_price' in exc_info.value.error_dict
    
    def test_subtotal_precision(self):
        """Should maintain decimal precision in subtotal calculation."""
        order_item = OrderItemFactory(
            quantity=3,
            unit_price=Decimal('10.33')
        )
        
        expected_subtotal = Decimal('30.99')
        assert order_item.subtotal == expected_subtotal


@pytest.mark.django_db
class TestOrderItemEdgeCases:
    """Test edge cases and boundary values."""
    
    def test_very_large_quantity(self):
        """Should accept very large quantities."""
        order_item = OrderItemFactory(quantity=10000)
        order_item.full_clean()  # Should not raise
        assert order_item.quantity == 10000
    
    def test_large_unit_price(self):
        """Should accept large unit prices up to 9999.99."""
        order_item = OrderItemFactory(unit_price=Decimal('9999.99'))
        order_item.full_clean()  # Should not raise
        assert order_item.unit_price == Decimal('9999.99')
    
    def test_large_subtotal_calculation(self):
        """Should handle large subtotal calculations."""
        order_item = OrderItemFactory(
            quantity=1000,
            unit_price=Decimal('999.99')
        )
        
        expected_subtotal = Decimal('999990.00')
        assert order_item.subtotal == expected_subtotal
    
    def test_multiple_items_same_order(self):
        """Should allow multiple items in the same order."""
        order = OrderFactory()
        item1 = OrderItemFactory(order=order)
        item2 = OrderItemFactory(order=order)
        item3 = OrderItemFactory(order=order)
        
        assert order.items.count() == 3
    
    def test_same_medicine_multiple_orders(self):
        """Should allow same medicine in multiple orders."""
        medicine = MedicineFactory()
        order1 = OrderFactory()
        order2 = OrderFactory()
        
        item1 = OrderItemFactory(order=order1, medicine=medicine)
        item2 = OrderItemFactory(order=order2, medicine=medicine)
        
        assert medicine.order_items.count() == 2
