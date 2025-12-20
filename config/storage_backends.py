"""
Custom storage backends for AWS S3.

This module provides custom storage classes for handling prescription files
with private access and pre-signed URLs.
"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PrivatePrescriptionStorage(S3Boto3Storage):
    """
    Custom S3 storage backend for prescription files.
    
    Features:
    - Private file access (not publicly readable)
    - Pre-signed URLs with configurable expiration
    - Custom file path structure
    - File overwrite protection
    """
    
    location = 'prescriptions'
    default_acl = None  # Private by default
    file_overwrite = False
    custom_domain = False
    
    def __init__(self, **settings_dict):
        """Initialize the storage backend with custom settings."""
        super().__init__(**settings_dict)
        
        # Set querystring auth to enable pre-signed URLs
        self.querystring_auth = True
        
        # Set URL expiration time from settings
        self.querystring_expire = getattr(
            settings,
            'PRESCRIPTION_FILE_URL_EXPIRATION',
            3600  # Default: 1 hour
        )
    
    def url(self, name, parameters=None, expire=None, http_method=None):
        """
        Generate a pre-signed URL for private file access.
        
        Args:
            name: File path/name
            parameters: Additional query parameters
            expire: Custom expiration time (seconds)
            http_method: HTTP method for the URL
        
        Returns:
            Pre-signed URL string
        """
        if expire is None:
            expire = self.querystring_expire
        
        return super().url(name, parameters=parameters, expire=expire, http_method=http_method)
