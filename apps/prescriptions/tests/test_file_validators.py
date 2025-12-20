"""
Test suite for file validation utilities.

Following TDD principles: These tests are written FIRST and WILL FAIL.
The validators.py module will be implemented to make these tests pass.

CRITICAL: DO NOT modify these tests to make them pass - fix the implementation instead.
"""
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image


@pytest.mark.unit
class TestFileSizeValidation:
    """Test file size validation logic."""
    
    def test_valid_file_size_accepted(self):
        """Should accept files within size limit."""
        from prescriptions.validators import validate_file_size
        
        # Create a 5MB file (within 10MB limit)
        content = b"x" * (5 * 1024 * 1024)
        file = SimpleUploadedFile("test.jpg", content, content_type="image/jpeg")
        
        # Should not raise
        validate_file_size(file)
    
    def test_file_at_exact_size_limit_accepted(self):
        """Should accept file at exactly 10MB."""
        from prescriptions.validators import validate_file_size
        
        # Create exactly 10MB file
        content = b"x" * (10 * 1024 * 1024)
        file = SimpleUploadedFile("test.jpg", content, content_type="image/jpeg")
        
        # Should not raise
        validate_file_size(file)
    
    def test_oversized_file_rejected(self):
        """Should reject files exceeding size limit."""
        from prescriptions.validators import validate_file_size
        
        # Create an 11MB file (exceeds 10MB limit)
        content = b"x" * (11 * 1024 * 1024)
        file = SimpleUploadedFile("test.jpg", content, content_type="image/jpeg")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(file)
        
        error_message = str(exc_info.value)
        assert "size" in error_message.lower()
        assert "10" in error_message  # Should mention the limit
    
    def test_empty_file_rejected(self):
        """Should reject empty files (0 bytes)."""
        from prescriptions.validators import validate_file_size
        
        file = SimpleUploadedFile("test.jpg", b"", content_type="image/jpeg")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_size(file)
        
        error_message = str(exc_info.value)
        assert "empty" in error_message.lower()
    
    def test_custom_size_limit(self):
        """Should respect custom size limits."""
        from prescriptions.validators import validate_file_size
        
        # Create a 3MB file
        content = b"x" * (3 * 1024 * 1024)
        file = SimpleUploadedFile("test.jpg", content, content_type="image/jpeg")
        
        # Should raise with 2MB limit
        with pytest.raises(ValidationError):
            validate_file_size(file, max_size_mb=2)
        
        # Should not raise with 5MB limit
        validate_file_size(file, max_size_mb=5)


@pytest.mark.unit
class TestFileExtensionValidation:
    """Test file extension validation logic."""
    
    def test_allowed_jpg_extension(self):
        """Should accept .jpg files."""
        from prescriptions.validators import validate_file_extension
        
        file = SimpleUploadedFile("prescription.jpg", b"content", content_type="image/jpeg")
        validate_file_extension(file)  # Should not raise
    
    def test_allowed_jpeg_extension(self):
        """Should accept .jpeg files."""
        from prescriptions.validators import validate_file_extension
        
        file = SimpleUploadedFile("prescription.jpeg", b"content", content_type="image/jpeg")
        validate_file_extension(file)  # Should not raise
    
    def test_allowed_png_extension(self):
        """Should accept .png files."""
        from prescriptions.validators import validate_file_extension
        
        file = SimpleUploadedFile("prescription.png", b"content", content_type="image/png")
        validate_file_extension(file)  # Should not raise
    
    def test_allowed_pdf_extension(self):
        """Should accept .pdf files."""
        from prescriptions.validators import validate_file_extension
        
        file = SimpleUploadedFile("prescription.pdf", b"content", content_type="application/pdf")
        validate_file_extension(file)  # Should not raise
    
    def test_case_insensitive_extension_check(self):
        """Should accept extensions regardless of case."""
        from prescriptions.validators import validate_file_extension
        
        file1 = SimpleUploadedFile("prescription.JPG", b"content", content_type="image/jpeg")
        file2 = SimpleUploadedFile("prescription.Pdf", b"content", content_type="application/pdf")
        file3 = SimpleUploadedFile("prescription.PNG", b"content", content_type="image/png")
        
        validate_file_extension(file1)  # Should not raise
        validate_file_extension(file2)  # Should not raise
        validate_file_extension(file3)  # Should not raise
    
    def test_dangerous_extension_rejected(self):
        """Should reject dangerous file extensions."""
        from prescriptions.validators import validate_file_extension
        
        dangerous_files = [
            SimpleUploadedFile("malware.exe", b"content"),
            SimpleUploadedFile("script.sh", b"content"),
            SimpleUploadedFile("batch.bat", b"content"),
            SimpleUploadedFile("code.py", b"content"),
            SimpleUploadedFile("script.js", b"content"),
            SimpleUploadedFile("page.html", b"content"),
        ]
        
        for file in dangerous_files:
            with pytest.raises(ValidationError) as exc_info:
                validate_file_extension(file)
            
            error_message = str(exc_info.value)
            assert "extension" in error_message.lower() or "type" in error_message.lower()
    
    def test_no_extension_rejected(self):
        """Should reject files without extension."""
        from prescriptions.validators import validate_file_extension
        
        file = SimpleUploadedFile("prescription", b"content")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_extension(file)
        
        error_message = str(exc_info.value)
        assert "extension" in error_message.lower()


@pytest.mark.unit
class TestMimeTypeValidation:
    """Test MIME type validation logic."""
    
    def test_valid_jpeg_mime_type(self):
        """Should accept valid JPEG MIME type."""
        from prescriptions.validators import validate_mime_type
        
        # Create actual JPEG image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        file = SimpleUploadedFile("test.jpg", img_bytes.read(), content_type="image/jpeg")
        validate_mime_type(file)  # Should not raise
    
    def test_valid_png_mime_type(self):
        """Should accept valid PNG MIME type."""
        from prescriptions.validators import validate_mime_type
        
        # Create actual PNG image
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        file = SimpleUploadedFile("test.png", img_bytes.read(), content_type="image/png")
        validate_mime_type(file)  # Should not raise
    
    def test_valid_pdf_mime_type(self):
        """Should accept valid PDF MIME type."""
        from prescriptions.validators import validate_mime_type
        
        # Create PDF-like content with proper header
        pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"
        file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        
        validate_mime_type(file)  # Should not raise
    
    def test_mime_type_spoofing_detected(self):
        """Should detect MIME type spoofing (wrong extension for content)."""
        from prescriptions.validators import validate_mime_type
        
        # Create a JPEG image but name it .pdf
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # File claims to be PDF but is actually JPEG
        file = SimpleUploadedFile("fake.pdf", img_bytes.read(), content_type="application/pdf")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_mime_type(file)
        
        error_message = str(exc_info.value)
        assert "mime" in error_message.lower() or "type" in error_message.lower()
    
    def test_text_file_rejected(self):
        """Should reject text files."""
        from prescriptions.validators import validate_mime_type
        
        file = SimpleUploadedFile("test.txt", b"This is text content", content_type="text/plain")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_mime_type(file)
        
        error_message = str(exc_info.value)
        assert "mime" in error_message.lower() or "type" in error_message.lower()


@pytest.mark.unit
class TestFileCorruptionDetection:
    """Test file corruption detection logic."""
    
    def test_valid_image_not_corrupted(self):
        """Should accept valid, non-corrupted images."""
        from prescriptions.validators import validate_file_integrity
        
        # Create valid image
        img = Image.new('RGB', (100, 100), color='green')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        file = SimpleUploadedFile("test.jpg", img_bytes.read(), content_type="image/jpeg")
        validate_file_integrity(file)  # Should not raise
    
    def test_corrupted_image_rejected(self):
        """Should reject corrupted image files."""
        from prescriptions.validators import validate_file_integrity
        
        # Create corrupted image data
        corrupted_content = b"\xFF\xD8\xFF\xE0" + b"corrupted data"
        file = SimpleUploadedFile("corrupted.jpg", corrupted_content, content_type="image/jpeg")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_integrity(file)
        
        error_message = str(exc_info.value)
        assert "corrupt" in error_message.lower() or "invalid" in error_message.lower()
    
    def test_truncated_image_rejected(self):
        """Should reject truncated image files."""
        from prescriptions.validators import validate_file_integrity
        
        # Create valid image then truncate it
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Take only first 100 bytes (truncated)
        truncated_content = img_bytes.read(100)
        file = SimpleUploadedFile("truncated.jpg", truncated_content, content_type="image/jpeg")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_integrity(file)
        
        error_message = str(exc_info.value)
        assert "corrupt" in error_message.lower() or "invalid" in error_message.lower()
    
    def test_valid_pdf_not_corrupted(self):
        """Should accept valid PDF files."""
        from prescriptions.validators import validate_file_integrity
        
        # Create minimal valid PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        
        validate_file_integrity(file)  # Should not raise
    
    def test_invalid_pdf_rejected(self):
        """Should reject invalid PDF files."""
        from prescriptions.validators import validate_file_integrity
        
        # PDF without proper header
        invalid_pdf = b"This is not a PDF"
        file = SimpleUploadedFile("invalid.pdf", invalid_pdf, content_type="application/pdf")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_integrity(file)
        
        error_message = str(exc_info.value)
        assert "corrupt" in error_message.lower() or "invalid" in error_message.lower()


@pytest.mark.unit
class TestCompleteFileValidation:
    """Test complete file validation pipeline."""
    
    def test_valid_prescription_image_passes_all_checks(self):
        """Should pass all validation checks for valid prescription image."""
        from prescriptions.validators import validate_prescription_file
        
        # Create valid JPEG image
        img = Image.new('RGB', (800, 600), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        file = SimpleUploadedFile("prescription.jpg", img_bytes.read(), content_type="image/jpeg")
        
        # Should not raise
        validate_prescription_file(file)
    
    def test_valid_prescription_pdf_passes_all_checks(self):
        """Should pass all validation checks for valid prescription PDF."""
        from prescriptions.validators import validate_prescription_file
        
        # Create minimal valid PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"
        file = SimpleUploadedFile("prescription.pdf", pdf_content, content_type="application/pdf")
        
        # Should not raise
        validate_prescription_file(file)
    
    def test_oversized_file_fails_validation(self):
        """Should fail validation for oversized files."""
        from prescriptions.validators import validate_prescription_file
        
        # Create 11MB file
        content = b"x" * (11 * 1024 * 1024)
        file = SimpleUploadedFile("large.jpg", content, content_type="image/jpeg")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_prescription_file(file)
        
        error_message = str(exc_info.value)
        assert "size" in error_message.lower()
    
    def test_wrong_extension_fails_validation(self):
        """Should fail validation for wrong file extension."""
        from prescriptions.validators import validate_prescription_file
        
        file = SimpleUploadedFile("malware.exe", b"content", content_type="application/x-msdownload")
        
        with pytest.raises(ValidationError):
            validate_prescription_file(file)
    
    def test_corrupted_file_fails_validation(self):
        """Should fail validation for corrupted files."""
        from prescriptions.validators import validate_prescription_file
        
        corrupted_content = b"\xFF\xD8\xFF\xE0" + b"corrupted"
        file = SimpleUploadedFile("corrupted.jpg", corrupted_content, content_type="image/jpeg")
        
        with pytest.raises(ValidationError):
            validate_prescription_file(file)
    
    def test_validation_error_messages_are_descriptive(self):
        """Should provide descriptive error messages."""
        from prescriptions.validators import validate_prescription_file
        
        # Test with oversized file
        large_file = SimpleUploadedFile("large.jpg", b"x" * (11 * 1024 * 1024), content_type="image/jpeg")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_prescription_file(large_file)
        
        error_message = str(exc_info.value)
        # Should mention specific issue
        assert len(error_message) > 10
        assert "size" in error_message.lower() or "large" in error_message.lower()
