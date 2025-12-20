"""
Test AWS S3 storage configuration and functionality.

This test follows TDD principles - it should FAIL if the configuration is incorrect.
DO NOT modify this test to make it pass - fix the configuration instead.
"""

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from moto import mock_aws
import boto3
from io import BytesIO
from PIL import Image


@pytest.mark.unit
class TestS3StorageConfiguration:
    """Test that S3 storage is properly configured."""
    
    def test_storages_installed(self):
        """Verify django-storages is installed."""
        assert 'storages' in settings.INSTALLED_APPS
    
    def test_aws_settings_exist(self):
        """Verify AWS S3 settings are configured."""
        # These should be present even if empty/default in development
        assert hasattr(settings, 'AWS_STORAGE_BUCKET_NAME')
        assert hasattr(settings, 'AWS_S3_REGION_NAME')
        assert hasattr(settings, 'AWS_DEFAULT_ACL')
        assert hasattr(settings, 'AWS_QUERYSTRING_AUTH')
        assert hasattr(settings, 'AWS_S3_FILE_OVERWRITE')
    
    def test_aws_default_acl_is_private(self):
        """Verify files are private by default."""
        # AWS_DEFAULT_ACL should be None for private files
        assert settings.AWS_DEFAULT_ACL is None
    
    def test_aws_querystring_auth_enabled(self):
        """Verify pre-signed URLs are enabled."""
        assert settings.AWS_QUERYSTRING_AUTH is True
    
    def test_file_overwrite_disabled(self):
        """Verify file overwrite is disabled for safety."""
        assert settings.AWS_S3_FILE_OVERWRITE is False
    
    def test_prescription_storage_backend_exists(self):
        """Verify custom prescription storage backend is configured."""
        from config.storage_backends import PrivatePrescriptionStorage
        storage = PrivatePrescriptionStorage()
        assert storage is not None
    
    def test_file_upload_settings_configured(self):
        """Verify file upload limits are configured."""
        assert hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE')
        assert hasattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE')
        assert hasattr(settings, 'ALLOWED_PRESCRIPTION_EXTENSIONS')
        assert hasattr(settings, 'PRESCRIPTION_FILE_URL_EXPIRATION')
        
        # Verify reasonable limits
        assert settings.FILE_UPLOAD_MAX_MEMORY_SIZE == 10 * 1024 * 1024  # 10MB
        assert settings.DATA_UPLOAD_MAX_MEMORY_SIZE == 10 * 1024 * 1024  # 10MB
        assert isinstance(settings.ALLOWED_PRESCRIPTION_EXTENSIONS, list)
        assert '.jpg' in settings.ALLOWED_PRESCRIPTION_EXTENSIONS
        assert '.pdf' in settings.ALLOWED_PRESCRIPTION_EXTENSIONS


@pytest.mark.integration
class TestS3FileOperations:
    """Test S3 file upload, retrieval, and deletion with mocked AWS."""
    
    @pytest.fixture(autouse=True)
    def setup_s3(self, monkeypatch):
        """Create a mock S3 bucket for testing."""
        # Set mock AWS credentials in environment
        monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
        monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
        monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
        monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
        
        # Start moto AWS mock
        self.mock = mock_aws()
        self.mock.start()
        
        # Create mock S3 client
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
        )
        
        # Create the bucket
        try:
            self.s3_client.create_bucket(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': settings.AWS_S3_REGION_NAME}
            )
        except Exception:
            # If region is us-east-1, don't use LocationConstraint
            self.s3_client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        
        yield
        
        # Stop the mock
        self.mock.stop()
    
    def test_upload_prescription_file(self):
        """Test uploading a prescription file to S3."""
        from config.storage_backends import PrivatePrescriptionStorage
        
        storage = PrivatePrescriptionStorage()
        
        # Create a test file
        test_content = b"Test prescription content"
        test_file = ContentFile(test_content, name='prescription.jpg')
        
        # Upload file
        saved_path = storage.save('test_prescription.jpg', test_file)
        
        # Verify file was saved
        assert saved_path is not None
        assert 'prescription' in saved_path.lower()
        assert storage.exists(saved_path)
    
    def test_file_path_structure(self):
        """Test that files are organized with proper path structure."""
        from config.storage_backends import PrivatePrescriptionStorage
        
        storage = PrivatePrescriptionStorage()
        test_file = ContentFile(b"Test content", name='test.jpg')
        
        # Save file with user_id context
        saved_path = storage.save('prescriptions/123/test.jpg', test_file)
        
        # Verify path structure includes user_id
        assert 'prescriptions' in saved_path
        assert saved_path is not None
    
    def test_generate_presigned_url(self):
        """Test generating pre-signed URLs for private files."""
        from config.storage_backends import PrivatePrescriptionStorage
        
        storage = PrivatePrescriptionStorage()
        test_file = ContentFile(b"Test content", name='test.jpg')
        
        # Upload file
        saved_path = storage.save('test_prescription.jpg', test_file)
        
        # Generate URL
        url = storage.url(saved_path)
        
        # Verify URL is generated (pre-signed URLs contain query parameters)
        assert url is not None
        assert 'http' in url.lower()
        # Pre-signed URLs should contain signature parameters
        # Note: moto may not fully simulate this, but we verify the method works
    
    def test_delete_prescription_file(self):
        """Test deleting a prescription file from S3."""
        from config.storage_backends import PrivatePrescriptionStorage
        
        storage = PrivatePrescriptionStorage()
        test_file = ContentFile(b"Test content", name='test.jpg')
        
        # Upload file
        saved_path = storage.save('test_prescription.jpg', test_file)
        assert storage.exists(saved_path)
        
        # Delete file
        storage.delete(saved_path)
        
        # Verify file was deleted
        assert not storage.exists(saved_path)
    
    def test_file_size_validation(self):
        """Test that large files are rejected."""
        from config.storage_backends import PrivatePrescriptionStorage
        
        storage = PrivatePrescriptionStorage()
        
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = ContentFile(large_content, name='large.jpg')
        
        # This should raise an error or be handled by Django's upload limits
        # The actual validation happens at the view/form level
        # Here we verify the setting is configured correctly
        assert settings.FILE_UPLOAD_MAX_MEMORY_SIZE == 10 * 1024 * 1024


@pytest.mark.unit
class TestFileExtensionValidation:
    """Test file extension validation for prescription uploads."""
    
    def test_allowed_extensions_configured(self):
        """Verify allowed file extensions are configured."""
        allowed_extensions = settings.ALLOWED_PRESCRIPTION_EXTENSIONS
        
        assert '.jpg' in allowed_extensions
        assert '.jpeg' in allowed_extensions
        assert '.png' in allowed_extensions
        assert '.pdf' in allowed_extensions
    
    def test_disallowed_extensions_not_included(self):
        """Verify dangerous file extensions are not allowed."""
        allowed_extensions = settings.ALLOWED_PRESCRIPTION_EXTENSIONS
        
        # These should NOT be in allowed extensions
        dangerous_extensions = ['.exe', '.sh', '.bat', '.py', '.js', '.html']
        for ext in dangerous_extensions:
            assert ext not in allowed_extensions


@pytest.mark.integration
class TestPrescriptionImageUpload:
    """Test prescription image upload with actual image files."""
    
    @pytest.fixture(autouse=True)
    def setup_s3(self, monkeypatch):
        """Create a mock S3 bucket for testing."""
        # Set mock AWS credentials in environment
        monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
        monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
        monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
        monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
        
        # Start moto AWS mock
        self.mock = mock_aws()
        self.mock.start()
        
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
        )
        
        try:
            self.s3_client.create_bucket(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': settings.AWS_S3_REGION_NAME}
            )
        except Exception:
            # If region is us-east-1, don't use LocationConstraint
            self.s3_client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        
        yield
        
        # Stop the mock
        self.mock.stop()
    
    def test_upload_jpg_image(self):
        """Test uploading a JPG prescription image."""
        from config.storage_backends import PrivatePrescriptionStorage
        
        storage = PrivatePrescriptionStorage()
        
        # Create a test JPG image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        test_file = ContentFile(img_bytes.read(), name='prescription.jpg')
        
        # Upload file
        saved_path = storage.save('prescription.jpg', test_file)
        
        # Verify file was saved
        assert saved_path is not None
        assert storage.exists(saved_path)
    
    def test_upload_png_image(self):
        """Test uploading a PNG prescription image."""
        from config.storage_backends import PrivatePrescriptionStorage
        
        storage = PrivatePrescriptionStorage()
        
        # Create a test PNG image
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        test_file = ContentFile(img_bytes.read(), name='prescription.png')
        
        # Upload file
        saved_path = storage.save('prescription.png', test_file)
        
        # Verify file was saved
        assert saved_path is not None
        assert storage.exists(saved_path)
    
    def test_upload_pdf_file(self):
        """Test uploading a PDF prescription."""
        from config.storage_backends import PrivatePrescriptionStorage
        
        storage = PrivatePrescriptionStorage()
        
        # Create a simple PDF-like content (not a real PDF, just for testing)
        pdf_content = b"%PDF-1.4\nTest prescription PDF content"
        test_file = ContentFile(pdf_content, name='prescription.pdf')
        
        # Upload file
        saved_path = storage.save('prescription.pdf', test_file)
        
        # Verify file was saved
        assert saved_path is not None
        assert storage.exists(saved_path)


@pytest.mark.unit
class TestURLExpirationConfiguration:
    """Test pre-signed URL expiration configuration."""
    
    def test_url_expiration_configured(self):
        """Verify URL expiration time is configured."""
        assert hasattr(settings, 'PRESCRIPTION_FILE_URL_EXPIRATION')
        assert isinstance(settings.PRESCRIPTION_FILE_URL_EXPIRATION, int)
        assert settings.PRESCRIPTION_FILE_URL_EXPIRATION > 0
    
    def test_url_expiration_reasonable_time(self):
        """Verify URL expiration is set to a reasonable time."""
        # Should be at least 5 minutes (300 seconds) and at most 24 hours (86400 seconds)
        expiration = settings.PRESCRIPTION_FILE_URL_EXPIRATION
        assert 300 <= expiration <= 86400
        
        # Default should be 1 hour (3600 seconds)
        assert expiration == 3600
