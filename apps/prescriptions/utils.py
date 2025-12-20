"""
Utility functions for prescription file handling.

This module provides utilities for:
- Generating unique file paths with collision prevention
- Sanitizing filenames
- Extracting original filenames from paths
"""
import os
import re
import uuid
from django.utils import timezone
from datetime import datetime
import unicodedata


def sanitize_filename(filename):
    """
    Sanitize filename to remove special characters and ensure safety.
    
    - Removes special characters
    - Replaces spaces with underscores
    - Handles Unicode characters
    - Truncates long filenames
    - Preserves file extension
    - Prevents path traversal attacks
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename string
    """
    if not filename:
        return "file"
    
    # Handle filenames that start with dot (e.g., ".jpg")
    if filename.startswith('.') and filename.count('.') == 1:
        # This is just an extension, add default name
        return f"file{filename}"
    
    # Split filename and extension
    name, ext = os.path.splitext(filename)
    
    # Remove path traversal attempts and path separators
    name = name.replace("..", "")
    name = name.replace("/", "")
    name = name.replace("\\", "")  # Remove backslashes
    
    # Also clean the extension part
    ext = ext.replace("..", "")
    ext = ext.replace("/", "")
    ext = ext.replace("\\", "")
    
    # Normalize Unicode characters
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')
    
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    
    # Remove special characters (keep only alphanumeric, underscore, hyphen)
    name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    
    # If name is empty after sanitization, use default
    if not name:
        name = "file"
    
    # Truncate long filenames (keep extension separate)
    max_name_length = 50
    if len(name) > max_name_length:
        name = name[:max_name_length]
    
    # Ensure extension is lowercase and starts with dot
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    ext = ext.lower()
    
    # Combine name and extension
    sanitized = f"{name}{ext}"
    
    # Final length check (total should be <= 100)
    if len(sanitized) > 100:
        # Truncate name further if needed
        available_for_name = 100 - len(ext)
        name = name[:available_for_name]
        sanitized = f"{name}{ext}"
    
    return sanitized


def generate_prescription_path(user_id, filename):
    """
    Generate unique S3 path for prescription file.
    
    Format: prescriptions/{user_id}/{timestamp}_{uuid}_{sanitized_filename}
    Example: prescriptions/123/20251220_183000_a1b2c3d4_prescription.jpg
    
    Args:
        user_id: User ID (must be non-negative integer)
        filename: Original filename
    
    Returns:
        Unique S3 path string
    
    Raises:
        ValueError: If user_id is negative
    """
    # Validate user_id
    if user_id < 0:
        raise ValueError("User ID must be non-negative")
    
    # Sanitize filename
    sanitized_filename = sanitize_filename(filename)
    
    # Generate timestamp (YYYYMMDD_HHMMSS format)
    now = timezone.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # Generate short UUID (first 8 characters)
    unique_id = str(uuid.uuid4().hex)[:8]
    
    # Construct path
    path = f"prescriptions/{user_id}/{timestamp}_{unique_id}_{sanitized_filename}"
    
    # Ensure path is within S3 limits (1024 characters)
    if len(path) > 1024:
        # Truncate filename if needed
        max_filename_length = 1024 - len(f"prescriptions/{user_id}/{timestamp}_{unique_id}_")
        if max_filename_length > 0:
            _, ext = os.path.splitext(sanitized_filename)
            name_part = sanitized_filename[:max_filename_length - len(ext)]
            sanitized_filename = f"{name_part}{ext}"
            path = f"prescriptions/{user_id}/{timestamp}_{unique_id}_{sanitized_filename}"
    
    return path


def extract_original_filename(path):
    """
    Extract original filename from generated S3 path.
    
    Args:
        path: S3 path (e.g., prescriptions/123/20251220_183000_a1b2c3d4_prescription.jpg)
    
    Returns:
        Extracted filename (e.g., prescription.jpg)
    """
    # Get the last part of the path (filename)
    filename = os.path.basename(path)
    
    # Remove timestamp and UUID prefix (format: YYYYMMDD_HHMMSS_UUID_filename)
    # Split by underscore and take everything after the UUID
    parts = filename.split('_')
    
    if len(parts) >= 4:
        # Join everything after timestamp and UUID
        original_filename = '_'.join(parts[3:])
        return original_filename
    
    # If format doesn't match expected, return as-is
    return filename
