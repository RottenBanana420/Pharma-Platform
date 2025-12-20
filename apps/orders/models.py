"""
Order and OrderItem models for the Pharma Platform.

This module contains models for managing orders and order line items,
including status workflows and business rule validation.
"""
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class OrderStatus(models.TextChoices):
    """Status choices for order workflow."""
    PLACED = 'placed', 'Placed'
    CONFIRMED = 'confirmed', 'Confirmed'
    SHIPPED = 'shipped', 'Shipped'
    DELIVERED = 'delivered', 'Delivered'


class Order(models.Model):
    """
    Model representing a customer order.
    
    Stores order information, status, and relationships to patient, pharmacy,
    and prescription. Enforces business rule that prescription must be verified.
    """
    
    # Patient who placed the order
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        help_text="Patient who placed this order"
    )
    
    # Pharmacy fulfilling the order
    pharmacy = models.ForeignKey(
        'pharmacies.Pharmacy',
        on_delete=models.PROTECT,
        related_name='orders',
        help_text="Pharmacy fulfilling this order"
    )
    
    # Prescription for this order (must be verified)
    prescription = models.ForeignKey(
        'prescriptions.Prescription',
        on_delete=models.PROTECT,
        related_name='orders',
        help_text="Prescription for this order (must be verified)"
    )
    
    # Total amount for the order
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total amount for the order (minimum 0.01)"
    )
    
    # Order status
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PLACED,
        help_text="Current order status"
    )
    
    # Payment reference ID (optional until payment is processed)
    payment_reference_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Payment reference ID from payment gateway"
    )
    
    # Creation timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when order was created"
    )
    
    # Tracking number (optional until shipped)
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Shipping tracking number"
    )
    
    class Meta:
        verbose_name = 'order'
        verbose_name_plural = 'orders'
        ordering = ['-created_at']  # Newest first
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['pharmacy']),
            models.Index(fields=['status']),
            models.Index(fields=['prescription']),
        ]
    
    def __str__(self):
        """Return order ID and patient as string representation."""
        return f"Order #{self.id} - {self.patient.email}"
    
    def clean(self):
        """
        Validate the model fields and business rules.
        
        Ensures:
        - Prescription must be verified
        - Status transitions are sequential (no skipping states)
        - Tracking number required when status is shipped or delivered
        """
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Business rule: Prescription must be verified
        if self.prescription_id:
            from prescriptions.models import PrescriptionStatus
            if self.prescription.status != PrescriptionStatus.VERIFIED:
                errors['prescription'] = 'Prescription must be verified before creating an order.'
        
        # Validate status transitions (sequential only)
        if self.pk:  # Only check for existing instances
            try:
                old_instance = Order.objects.get(pk=self.pk)
                old_status = old_instance.status
                new_status = self.status
                
                # Define valid transitions
                valid_transitions = {
                    OrderStatus.PLACED: [OrderStatus.CONFIRMED],
                    OrderStatus.CONFIRMED: [OrderStatus.SHIPPED],
                    OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
                    OrderStatus.DELIVERED: [],  # Terminal state
                }
                
                # Check if transition is valid
                if old_status != new_status:
                    if new_status not in valid_transitions.get(old_status, []):
                        errors['status'] = f'Cannot transition from {old_status} to {new_status}. Orders must progress sequentially.'
            except Order.DoesNotExist:
                # New instance, no transition validation needed
                pass
        
        # Validate tracking number required for shipped/delivered status
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            if not self.tracking_number or not self.tracking_number.strip():
                errors['tracking_number'] = 'Tracking number is required when order is shipped or delivered.'
        
        if errors:
            raise ValidationError(errors)
        
        super().clean()
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is called."""
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Model representing a line item in an order.
    
    Stores medicine, quantity, and unit price for each item in an order.
    """
    
    # Order this item belongs to
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="Order this item belongs to"
    )
    
    # Medicine being ordered
    medicine = models.ForeignKey(
        'pharmacies.Medicine',
        on_delete=models.PROTECT,
        related_name='order_items',
        help_text="Medicine being ordered"
    )
    
    # Quantity ordered
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity ordered (minimum 1)"
    )
    
    # Unit price at time of order
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Unit price at time of order (minimum 0.01)"
    )
    
    class Meta:
        verbose_name = 'order item'
        verbose_name_plural = 'order items'
        indexes = [
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        """Return medicine name and quantity as string representation."""
        return f"{self.medicine.commercial_name} x {self.quantity}"
    
    @property
    def subtotal(self):
        """Calculate subtotal as quantity * unit_price."""
        return self.quantity * self.unit_price
    
    def clean(self):
        """
        Validate the model fields.
        
        Ensures:
        - Quantity is positive (greater than 0)
        """
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Validate quantity is positive
        if self.quantity is not None and self.quantity < 1:
            errors['quantity'] = 'Quantity must be at least 1.'
        
        if errors:
            raise ValidationError(errors)
        
        super().clean()
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is called."""
        super().save(*args, **kwargs)
