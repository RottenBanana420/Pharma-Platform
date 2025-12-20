"""
Custom storage backends for AWS S3.

This module provides custom storage classes for handling prescription files
with private access, pre-signed URLs, metadata, and encryption.
"""

import os
import mimetypes
from django.conf import settings
from django.core.exceptions import ValidationError
from storages.backends.s3boto3 import S3Boto3Storage
from botocore.exceptions import ClientError, BotoCoreError
import logging

logger = logging.getLogger(__name__)


class PrivatePrescriptionStorage(S3Boto3Storage):
    """
    Custom S3 storage backend for prescription files.
    
    Features:
    - Private file access (not publicly readable)
    - Pre-signed URLs with configurable expiration
    - Custom file path structure
    - File overwrite protection
    - Metadata support (upload user, timestamp, original filename)
    - Content-Type detection and setting
    - Server-side encryption (SSE-S3)
    - Comprehensive error handling
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
        
        # Enable server-side encryption
        self.object_parameters = {
            'ServerSideEncryption': 'AES256',
        }
    
    def _get_content_type(self, name):
        """
        Detect and return appropriate Content-Type for file.
        
        Args:
            name: File name/path
        
        Returns:
            Content-Type string
        """
        # Get extension
        _, ext = os.path.splitext(name)
        ext = ext.lower()
        
        # Map extensions to MIME types
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.pdf': 'application/pdf',
        }
        
        # Return mapped type or use mimetypes library
        if ext in content_type_map:
            return content_type_map[ext]
        
        content_type, _ = mimetypes.guess_type(name)
        return content_type or 'application/octet-stream'
    
    def _save(self, name, content):
        """
        Save file with metadata and proper Content-Type.
        
        Args:
            name: File path
            content: File content
        
        Returns:
            Saved file path
        """
        # Set Content-Type
        content_type = self._get_content_type(name)
        
        # Update object parameters with Content-Type
        params = self.object_parameters.copy()
        params['ContentType'] = content_type
        
        # Add metadata if available
        # Metadata can be set via content.metadata if it exists
        if hasattr(content, 'metadata'):
            params['Metadata'] = content.metadata
        
        # Temporarily update object_parameters
        original_params = self.object_parameters
        self.object_parameters = params
        
        try:
            # Call parent _save method
            saved_name = super()._save(name, content)
            return saved_name
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 ClientError during upload: {error_code} - {str(e)}")
            
            if error_code == 'NoSuchBucket':
                raise ValidationError(
                    "S3 bucket not found. Please check your AWS configuration."
                )
            elif error_code == 'AccessDenied':
                raise ValidationError(
                    "Access denied to S3 bucket. Please check your AWS permissions."
                )
            else:
                raise ValidationError(
                    f"Failed to upload file to S3: {str(e)}"
                )
        except BotoCoreError as e:
            logger.error(f"BotoCoreError during upload: {str(e)}")
            raise ValidationError(
                "Network error occurred while uploading to S3. Please try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            raise ValidationError(
                f"Unexpected error during file upload: {str(e)}"
            )
        finally:
            # Restore original parameters
            self.object_parameters = original_params
    
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
        
        try:
            return super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise ValidationError(
                "Failed to generate file access URL. Please try again."
            )
    
    def delete(self, name):
        """
        Delete file from S3 with error handling.
        
        Args:
            name: File path to delete
        """
        try:
            super().delete(name)
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            # Don't raise error for delete failures - log and continue
        except Exception as e:
            logger.error(f"Unexpected error deleting file: {str(e)}")
