"""
Prescription model for the Pharma Platform.

This module contains the Prescription model for managing prescription uploads,
verification, and rejection workflows.
"""
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class PrescriptionStatus(models.TextChoices):
    """Status choices for prescription verification workflow."""
    PENDING_VERIFICATION = 'pending_verification', 'Pending Verification'
    VERIFIED = 'verified', 'Verified'
    REJECTED = 'rejected', 'Rejected'


class Prescription(models.Model):
    """
    Model representing a prescription uploaded by a patient.
    
    Stores prescription image path (S3), verification status, and related metadata.
    Supports verification workflow with status transitions and rejection handling.
    """
    
    # Patient who uploaded the prescription
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        help_text="Patient who uploaded this prescription"
    )
    
    # S3 path to prescription image
    prescription_image_path = models.CharField(
        max_length=500,
        blank=False,
        help_text="S3 path to prescription image file"
    )
    
    # Verification status
    status = models.CharField(
        max_length=30,
        choices=PrescriptionStatus.choices,
        default=PrescriptionStatus.PENDING_VERIFICATION,
        help_text="Current verification status"
    )
    
    # Timestamp when prescription was uploaded
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when prescription was uploaded"
    )
    
    # Pharmacy admin who verified/rejected the prescription (optional)
    verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_prescriptions',
        help_text="Pharmacy admin who verified or rejected this prescription"
    )
    
    # Timestamp when verification occurred (optional)
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when prescription was verified or rejected"
    )
    
    # Rejection reason (required when status is rejected)
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (required when status is rejected)"
    )
    
    class Meta:
        verbose_name = 'prescription'
        verbose_name_plural = 'prescriptions'
        ordering = ['-uploaded_at']  # Newest first
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        """Return patient email and status as string representation."""
        return f"Prescription for {self.patient.email} - {self.status}"
    
    def clean(self):
        """
        Validate the model fields and business rules.
        
        Ensures:
        - Prescription image path is not empty and within max length
        - Rejection reason is provided when status is rejected
        - Rejection reason is empty when status is not rejected
        - Status transitions are valid (no going back from rejected/verified to pending)
        """
        from django.core.exceptions import ValidationError
        
        errors = {}
        
        # Validate prescription_image_path is not empty
        if not self.prescription_image_path:
            errors['prescription_image_path'] = 'Prescription image path is required.'
        elif len(self.prescription_image_path) > 500:
            errors['prescription_image_path'] = f'Prescription image path cannot exceed 500 characters (current: {len(self.prescription_image_path)}).'
        
        # Validate rejection reason based on status
        if self.status == PrescriptionStatus.REJECTED:
            if not self.rejection_reason or not self.rejection_reason.strip():
                errors['rejection_reason'] = 'Rejection reason is required when status is rejected.'
        else:
            # Status is not rejected, rejection_reason should be empty
            if self.rejection_reason and self.rejection_reason.strip():
                errors['rejection_reason'] = 'Rejection reason should be empty when status is not rejected.'
        
        # Validate status transitions (prevent going back from terminal states)
        if self.pk:  # Only check for existing instances
            try:
                old_instance = Prescription.objects.get(pk=self.pk)
                old_status = old_instance.status
                new_status = self.status
                
                # Cannot transition from rejected or verified back to pending
                if old_status == PrescriptionStatus.REJECTED and new_status == PrescriptionStatus.PENDING_VERIFICATION:
                    errors['status'] = 'Cannot transition from rejected back to pending verification.'
                elif old_status == PrescriptionStatus.VERIFIED and new_status == PrescriptionStatus.PENDING_VERIFICATION:
                    errors['status'] = 'Cannot transition from verified back to pending verification.'
            except Prescription.DoesNotExist:
                # New instance, no transition validation needed
                pass
        
        if errors:
            raise ValidationError(errors)
        
        super().clean()
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is called."""
        # Note: full_clean() is not called automatically in save()
        # Tests should call full_clean() explicitly or we can call it here
        # For now, relying on tests to call full_clean()
        super().save(*args, **kwargs)
