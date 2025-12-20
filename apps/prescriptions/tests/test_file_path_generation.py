"""
Test suite for file path generation utilities.

Following TDD principles: These tests are written FIRST and WILL FAIL.
The utils.py module will be implemented to make these tests pass.

CRITICAL: DO NOT modify these tests to make them pass - fix the implementation instead.
"""
import pytest
from django.utils import timezone
from datetime import datetime
import re


@pytest.mark.unit
class TestUniquePathGeneration:
    """Test unique file path generation."""
    
    def test_generates_path_with_user_id(self):
        """Should include user ID in generated path."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 123
        filename = "prescription.jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        assert str(user_id) in path
        assert path.startswith("prescriptions/")
    
    def test_generates_path_with_timestamp(self):
        """Should include timestamp in generated path."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 456
        filename = "prescription.jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        # Should contain a timestamp pattern (YYYYMMDD_HHMMSS)
        assert re.search(r'\d{8}_\d{6}', path) is not None
    
    def test_generates_path_with_uuid(self):
        """Should include UUID for uniqueness."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 789
        filename = "prescription.jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        # Should contain a UUID-like pattern (hexadecimal)
        assert re.search(r'[0-9a-f]{8}', path) is not None
    
    def test_includes_original_filename(self):
        """Should include sanitized original filename."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 100
        filename = "my_prescription.jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        assert "my_prescription" in path or "prescription" in path
        assert path.endswith(".jpg")
    
    def test_generates_unique_paths_for_same_filename(self):
        """Should generate different paths for same filename."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 200
        filename = "prescription.jpg"
        
        path1 = generate_prescription_path(user_id, filename)
        path2 = generate_prescription_path(user_id, filename)
        
        # Paths should be different due to UUID/timestamp
        assert path1 != path2
    
    def test_path_format_structure(self):
        """Should follow expected path structure."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 300
        filename = "test.jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        # Expected format: prescriptions/{user_id}/{timestamp}_{uuid}_{filename}
        parts = path.split('/')
        assert len(parts) >= 3
        assert parts[0] == "prescriptions"
        assert parts[1] == str(user_id)


@pytest.mark.unit
class TestFilenameSanitization:
    """Test filename sanitization logic."""
    
    def test_removes_special_characters(self):
        """Should remove special characters from filename."""
        from prescriptions.utils import sanitize_filename
        
        filename = "my@prescription#2024!.jpg"
        sanitized = sanitize_filename(filename)
        
        # Should not contain special characters
        assert "@" not in sanitized
        assert "#" not in sanitized
        assert "!" not in sanitized
        assert sanitized.endswith(".jpg")
    
    def test_replaces_spaces_with_underscores(self):
        """Should replace spaces with underscores."""
        from prescriptions.utils import sanitize_filename
        
        filename = "my prescription file.jpg"
        sanitized = sanitize_filename(filename)
        
        assert " " not in sanitized
        assert "_" in sanitized
        assert sanitized.endswith(".jpg")
    
    def test_handles_unicode_characters(self):
        """Should handle Unicode characters safely."""
        from prescriptions.utils import sanitize_filename
        
        filename = "प्रिस्क्रिप्शन.jpg"
        sanitized = sanitize_filename(filename)
        
        # Should produce a valid filename
        assert sanitized is not None
        assert len(sanitized) > 0
        assert sanitized.endswith(".jpg")
    
    def test_truncates_long_filenames(self):
        """Should truncate very long filenames."""
        from prescriptions.utils import sanitize_filename
        
        # Create a very long filename
        long_name = "a" * 200 + ".jpg"
        sanitized = sanitize_filename(long_name)
        
        # Should be truncated to reasonable length
        assert len(sanitized) <= 100
        assert sanitized.endswith(".jpg")
    
    def test_preserves_file_extension(self):
        """Should always preserve file extension."""
        from prescriptions.utils import sanitize_filename
        
        filenames = [
            "test.jpg",
            "test.jpeg",
            "test.png",
            "test.pdf",
        ]
        
        for filename in filenames:
            sanitized = sanitize_filename(filename)
            original_ext = filename.split('.')[-1]
            assert sanitized.endswith(f".{original_ext}")
    
    def test_handles_multiple_dots(self):
        """Should handle filenames with multiple dots."""
        from prescriptions.utils import sanitize_filename
        
        filename = "my.prescription.v2.jpg"
        sanitized = sanitize_filename(filename)
        
        # Should preserve extension and handle dots
        assert sanitized.endswith(".jpg")
        assert sanitized is not None
    
    def test_removes_path_traversal_attempts(self):
        """Should remove path traversal attempts."""
        from prescriptions.utils import sanitize_filename
        
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "test/../../../secret.jpg",
        ]
        
        for filename in malicious_filenames:
            sanitized = sanitize_filename(filename)
            
            # Should not contain path traversal sequences
            assert ".." not in sanitized
            assert "/" not in sanitized or sanitized.count("/") == 0
            assert "\\" not in sanitized


@pytest.mark.unit
class TestPathLengthValidation:
    """Test path length validation."""
    
    def test_generated_path_within_s3_limits(self):
        """Should generate paths within S3 key length limits (1024 chars)."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 999999
        # Very long filename
        filename = "a" * 200 + ".jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        # S3 key length limit is 1024 characters
        assert len(path) <= 1024
    
    def test_path_with_long_user_id(self):
        """Should handle very large user IDs."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 999999999999
        filename = "prescription.jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        assert str(user_id) in path
        assert len(path) <= 1024


@pytest.mark.unit
class TestCollisionPrevention:
    """Test that path generation prevents collisions."""
    
    def test_concurrent_uploads_same_user_different_paths(self):
        """Should generate different paths for concurrent uploads by same user."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 500
        filename = "prescription.jpg"
        
        # Simulate concurrent uploads
        paths = [generate_prescription_path(user_id, filename) for _ in range(10)]
        
        # All paths should be unique
        assert len(paths) == len(set(paths))
    
    def test_same_filename_different_users_different_paths(self):
        """Should generate different paths for same filename from different users."""
        from prescriptions.utils import generate_prescription_path
        
        filename = "prescription.jpg"
        
        path1 = generate_prescription_path(100, filename)
        path2 = generate_prescription_path(200, filename)
        
        assert path1 != path2
        assert "100" in path1
        assert "200" in path2
    
    def test_rapid_successive_uploads_unique_paths(self):
        """Should generate unique paths even for rapid successive uploads."""
        from prescriptions.utils import generate_prescription_path
        import time
        
        user_id = 600
        filename = "prescription.jpg"
        
        paths = []
        for _ in range(5):
            path = generate_prescription_path(user_id, filename)
            paths.append(path)
            time.sleep(0.001)  # Very small delay
        
        # All paths should be unique despite rapid generation
        assert len(paths) == len(set(paths))


@pytest.mark.unit
class TestExtractFilenameFromPath:
    """Test extracting original filename from generated path."""
    
    def test_extract_filename_from_path(self):
        """Should be able to extract original filename from path."""
        from prescriptions.utils import generate_prescription_path, extract_original_filename
        
        user_id = 700
        original_filename = "my_prescription.jpg"
        
        path = generate_prescription_path(user_id, original_filename)
        extracted = extract_original_filename(path)
        
        # Should extract something similar to original
        assert "prescription" in extracted.lower()
        assert extracted.endswith(".jpg")
    
    def test_extract_filename_preserves_extension(self):
        """Should preserve file extension when extracting."""
        from prescriptions.utils import extract_original_filename
        
        paths = [
            "prescriptions/123/20251220_abc123_test.jpg",
            "prescriptions/456/20251220_def456_test.png",
            "prescriptions/789/20251220_ghi789_test.pdf",
        ]
        
        for path in paths:
            extracted = extract_original_filename(path)
            original_ext = path.split('.')[-1]
            assert extracted.endswith(f".{original_ext}")


@pytest.mark.unit
class TestPathGenerationEdgeCases:
    """Test edge cases in path generation."""
    
    def test_empty_filename_handled(self):
        """Should handle empty filename gracefully."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 800
        filename = ""
        
        # Should either raise ValueError or generate default name
        try:
            path = generate_prescription_path(user_id, filename)
            # If it doesn't raise, should have generated a valid path
            assert path is not None
            assert len(path) > 0
        except ValueError:
            # Acceptable to raise ValueError for empty filename
            pass
    
    def test_filename_with_only_extension(self):
        """Should handle filename with only extension."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 900
        filename = ".jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        assert path is not None
        assert path.endswith(".jpg")
    
    def test_user_id_zero(self):
        """Should handle user ID of zero."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = 0
        filename = "prescription.jpg"
        
        path = generate_prescription_path(user_id, filename)
        
        assert "0" in path
        assert path.startswith("prescriptions/")
    
    def test_negative_user_id_rejected(self):
        """Should reject negative user IDs."""
        from prescriptions.utils import generate_prescription_path
        
        user_id = -1
        filename = "prescription.jpg"
        
        with pytest.raises(ValueError):
            generate_prescription_path(user_id, filename)
