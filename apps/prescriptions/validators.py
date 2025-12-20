"""
File validation utilities for prescription uploads.

This module provides comprehensive validation for prescription file uploads including:
- File size validation
- File extension validation
- MIME type validation
- File integrity/corruption detection
"""
import magic
from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image
from io import BytesIO
import os


def validate_file_size(file, max_size_mb=None):
    """
    Validate file size against maximum allowed size.
    
    Args:
        file: Django UploadedFile object
        max_size_mb: Maximum size in MB (defaults to settings.FILE_UPLOAD_MAX_MEMORY_SIZE)
    
    Raises:
        ValidationError: If file is too large or empty
    """
    if max_size_mb is None:
        # Get from settings (already in bytes)
        max_size_bytes = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)
    else:
        max_size_bytes = max_size_mb * 1024 * 1024
    
    # Check if file is empty
    if file.size == 0:
        raise ValidationError("File is empty. Please upload a valid prescription file.")
    
    # Check if file exceeds size limit
    if file.size > max_size_bytes:
        max_size_mb_display = max_size_bytes / (1024 * 1024)
        actual_size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f"File size ({actual_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb_display:.0f} MB)."
        )


def validate_file_extension(file):
    """
    Validate file extension against whitelist of allowed extensions.
    
    Args:
        file: Django UploadedFile object
    
    Raises:
        ValidationError: If file extension is not allowed
    """
    allowed_extensions = getattr(
        settings,
        'ALLOWED_PRESCRIPTION_EXTENSIONS',
        ['.jpg', '.jpeg', '.png', '.pdf']
    )
    
    # Get file extension
    filename = file.name
    if not filename:
        raise ValidationError("Filename is missing.")
    
    # Extract extension (case-insensitive)
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    if not ext:
        raise ValidationError("File must have a valid extension (.jpg, .jpeg, .png, or .pdf).")
    
    # Check against whitelist
    if ext not in allowed_extensions:
        allowed_str = ", ".join(allowed_extensions)
        raise ValidationError(
            f"File extension '{ext}' is not allowed. Allowed extensions: {allowed_str}"
        )


def validate_mime_type(file):
    """
    Validate file MIME type using python-magic to detect actual file type.
    
    This prevents MIME type spoofing where a malicious file has wrong extension.
    
    Args:
        file: Django UploadedFile object
    
    Raises:
        ValidationError: If MIME type is not allowed or doesn't match extension
    """
    allowed_mime_types = getattr(
        settings,
        'ALLOWED_PRESCRIPTION_MIME_TYPES',
        ['image/jpeg', 'image/png', 'application/pdf']
    )
    
    # Read file content for MIME type detection
    file.seek(0)
    file_content = file.read(2048)  # Read first 2KB for detection
    file.seek(0)  # Reset file pointer
    
    # Detect MIME type using python-magic
    try:
        mime = magic.from_buffer(file_content, mime=True)
    except Exception as e:
        raise ValidationError(f"Unable to determine file type: {str(e)}")
    
    # Check against whitelist
    if mime not in allowed_mime_types:
        allowed_str = ", ".join(allowed_mime_types)
        raise ValidationError(
            f"File type '{mime}' is not allowed. Allowed types: {allowed_str}"
        )
    
    # Check for MIME type spoofing - extension should match detected MIME type
    filename = file.name.lower()
    extension_mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.pdf': 'application/pdf',
    }
    
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    if ext in extension_mime_map:
        expected_mime = extension_mime_map[ext]
        if mime != expected_mime:
            raise ValidationError(
                f"File extension '{ext}' does not match detected file type '{mime}'. "
                f"Possible MIME type spoofing detected."
            )


def validate_file_integrity(file):
    """
    Validate file integrity to detect corrupted or invalid files.
    
    For images: Attempts to open with PIL
    For PDFs: Checks for valid PDF header
    
    Args:
        file: Django UploadedFile object
    
    Raises:
        ValidationError: If file is corrupted or invalid
    """
    filename = file.name.lower()
    file.seek(0)
    
    # Validate image files
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        try:
            img = Image.open(file)
            img.verify()  # Verify it's a valid image
            file.seek(0)  # Reset after verify
            
            # Try to load the image to catch truncated files
            img = Image.open(file)
            img.load()
            file.seek(0)
        except Exception as e:
            raise ValidationError(
                f"Image file is corrupted or invalid: {str(e)}"
            )
    
    # Validate PDF files
    elif filename.endswith('.pdf'):
        file.seek(0)
        header = file.read(5)
        file.seek(0)
        
        # PDF files must start with %PDF-
        if not header.startswith(b'%PDF-'):
            raise ValidationError(
                "PDF file is invalid or corrupted. Missing PDF header."
            )
    
    file.seek(0)


def validate_prescription_file(file):
    """
    Complete validation pipeline for prescription files.
    
    Runs all validation checks:
    1. File size validation
    2. File extension validation
    3. MIME type validation
    4. File integrity validation
    
    Args:
        file: Django UploadedFile object
    
    Raises:
        ValidationError: If any validation check fails
    """
    # Run all validations in order
    validate_file_size(file)
    validate_file_extension(file)
    validate_mime_type(file)
    validate_file_integrity(file)
    
    # Reset file pointer after all validations
    file.seek(0)
