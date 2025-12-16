"""
Pharmacy and Medicine models for the Pharma Platform.

This module contains models for managing pharmacies and their medicine inventory.
"""
from decimal import Decimal
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models


class Pharmacy(models.Model):
    """
    Model representing a pharmacy business.
    
    Stores complete business identification, address, and contact information
    for pharmacies registered on the platform.
    """
    
    # Business Identification
    name = models.CharField(
        max_length=200,
        blank=False,
        help_text="Pharmacy business name"
    )
    
    license_number = models.CharField(
        max_length=50,
        unique=True,
        blank=False,
        help_text="Unique pharmacy license number"
    )
    
    contact_email = models.EmailField(
        unique=True,
        blank=False,
        help_text="Primary contact email for the pharmacy"
    )
    
    # Address Fields
    street_address = models.CharField(
        max_length=255,
        blank=False,
        help_text="Street address of the pharmacy"
    )
    
    city = models.CharField(
        max_length=100,
        blank=False,
        help_text="City where pharmacy is located"
    )
    
    state = models.CharField(
        max_length=100,
        blank=False,
        help_text="State where pharmacy is located"
    )
    
    postal_code = models.CharField(
        max_length=10,
        blank=False,
        help_text="Postal/ZIP code"
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+91\d{10}$',
        message="Phone number must be in format: '+91XXXXXXXXXX' (Indian numbers only)"
    )
    
    phone_number = models.CharField(
        max_length=13,
        validators=[phone_regex],
        blank=False,
        help_text="Indian phone number in format: +91XXXXXXXXXX"
    )
    
    # Status Tracking
    is_verified = models.BooleanField(
        default=False,
        help_text="Designates whether this pharmacy has been verified"
    )
    
    registered_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when pharmacy was registered"
    )
    
    class Meta:
        verbose_name = 'pharmacy'
        verbose_name_plural = 'pharmacies'
        indexes = [
            models.Index(fields=['license_number']),
            models.Index(fields=['city', 'state']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        """Return pharmacy name as string representation."""
        return self.name
    
    def clean(self):
        """
        Validate the model fields.
        
        Ensures all required fields are provided.
        Normalizes email to lowercase for case-insensitive uniqueness.
        """
        from django.core.exceptions import ValidationError
        
        # Normalize email to lowercase for case-insensitive uniqueness
        if self.contact_email:
            self.contact_email = self.contact_email.lower()
        
        errors = {}
        
        # Validate required fields
        if not self.name:
            errors['name'] = 'Pharmacy name is required.'
        
        if not self.license_number:
            errors['license_number'] = 'License number is required.'
        
        if not self.contact_email:
            errors['contact_email'] = 'Contact email is required.'
        
        if not self.street_address:
            errors['street_address'] = 'Street address is required.'
        
        if not self.city:
            errors['city'] = 'City is required.'
        
        if not self.state:
            errors['state'] = 'State is required.'
        
        if not self.postal_code:
            errors['postal_code'] = 'Postal code is required.'
        
        if not self.phone_number:
            errors['phone_number'] = 'Phone number is required.'
        
        if errors:
            raise ValidationError(errors)
        
        super().clean()
    
    def save(self, *args, **kwargs):
        """Override save to normalize email before saving."""
        if self.contact_email:
            self.contact_email = self.contact_email.lower()
        super().save(*args, **kwargs)


class Medicine(models.Model):
    """
    Model representing a medicine in a pharmacy's inventory.
    
    Stores medicine identification, pricing, stock information,
    and relationship to the pharmacy.
    """
    
    # Identification
    commercial_name = models.CharField(
        max_length=200,
        blank=False,
        help_text="Commercial/brand name of the medicine"
    )
    
    generic_name = models.CharField(
        max_length=200,
        blank=False,
        help_text="Generic/scientific name of the medicine"
    )
    
    manufacturer = models.CharField(
        max_length=200,
        blank=False,
        help_text="Manufacturer of the medicine"
    )
    
    # Pricing and Stock
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per unit (minimum 0.01)"
    )
    
    stock_quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Current stock quantity (non-negative)"
    )
    
    # Relationships
    pharmacy = models.ForeignKey(
        'Pharmacy',
        on_delete=models.PROTECT,
        related_name='medicines',
        help_text="Pharmacy that stocks this medicine"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when medicine was added"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when medicine was last updated"
    )
    
    class Meta:
        verbose_name = 'medicine'
        verbose_name_plural = 'medicines'
        constraints = [
            models.UniqueConstraint(
                fields=['commercial_name', 'pharmacy'],
                name='unique_medicine_per_pharmacy'
            )
        ]
        indexes = [
            models.Index(fields=['commercial_name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['pharmacy', 'stock_quantity']),
        ]
    
    def __str__(self):
        """Return commercial name as string representation."""
        return self.commercial_name
    
    def clean(self):
        """
        Validate the model fields.
        
        Ensures all required fields are provided and business rules are met.
        """
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Validate required fields
        if not self.commercial_name:
            errors['commercial_name'] = 'Commercial name is required.'
        
        if not self.generic_name:
            errors['generic_name'] = 'Generic name is required.'
        
        if not self.manufacturer:
            errors['manufacturer'] = 'Manufacturer is required.'
        
        if self.price is None:
            errors['price'] = 'Price is required.'
        elif self.price <= 0:
            errors['price'] = 'Price must be greater than 0.'
        
        if self.stock_quantity is None:
            errors['stock_quantity'] = 'Stock quantity is required.'
        elif self.stock_quantity < 0:
            errors['stock_quantity'] = 'Stock quantity cannot be negative.'
        
        if not self.pharmacy_id:
            errors['pharmacy'] = 'Pharmacy is required.'
        
        if errors:
            raise ValidationError(errors)
        
        super().clean()
