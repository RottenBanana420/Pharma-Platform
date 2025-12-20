"""
Test environment variable configuration and loading.

This test follows TDD principles - it should FAIL if the configuration is incorrect.
DO NOT modify this test to make it pass - fix the configuration instead.
"""

import pytest
import os
from django.conf import settings


@pytest.mark.unit
class TestPythonDecoupleInstallation:
    """Test that python-decouple is properly installed and configured."""
    
    def test_decouple_can_be_imported(self):
        """Verify python-decouple can be imported."""
        from decouple import config
        assert config is not None
    
    def test_decouple_config_function_works(self):
        """Verify decouple config function works."""
        from decouple import config
        
        # Set a test environment variable
        os.environ['TEST_VAR'] = 'test_value'
        
        # Retrieve it using decouple
        value = config('TEST_VAR', default='default')
        assert value == 'test_value'
        
        # Clean up
        del os.environ['TEST_VAR']
    
    def test_decouple_default_values(self):
        """Verify decouple returns default values when env var is missing."""
        from decouple import config
        
        # Try to get a non-existent variable with default
        value = config('NON_EXISTENT_VAR_12345', default='default_value')
        assert value == 'default_value'


@pytest.mark.unit
class TestEnvironmentVariableTypeCasting:
    """Test that environment variables are properly type-cast."""
    
    def test_boolean_casting(self):
        """Test boolean type casting."""
        from decouple import config, Csv
        
        # Test True values
        os.environ['TEST_BOOL_TRUE'] = 'True'
        assert config('TEST_BOOL_TRUE', default=False, cast=bool) is True
        
        os.environ['TEST_BOOL_TRUE'] = 'true'
        assert config('TEST_BOOL_TRUE', default=False, cast=bool) is True
        
        os.environ['TEST_BOOL_TRUE'] = '1'
        assert config('TEST_BOOL_TRUE', default=False, cast=bool) is True
        
        # Test False values
        os.environ['TEST_BOOL_FALSE'] = 'False'
        assert config('TEST_BOOL_FALSE', default=True, cast=bool) is False
        
        os.environ['TEST_BOOL_FALSE'] = 'false'
        assert config('TEST_BOOL_FALSE', default=True, cast=bool) is False
        
        os.environ['TEST_BOOL_FALSE'] = '0'
        assert config('TEST_BOOL_FALSE', default=True, cast=bool) is False
        
        # Clean up
        del os.environ['TEST_BOOL_TRUE']
        del os.environ['TEST_BOOL_FALSE']
    
    def test_integer_casting(self):
        """Test integer type casting."""
        from decouple import config
        
        os.environ['TEST_INT'] = '42'
        value = config('TEST_INT', default=0, cast=int)
        assert value == 42
        assert isinstance(value, int)
        
        # Clean up
        del os.environ['TEST_INT']
    
    def test_csv_casting(self):
        """Test CSV (comma-separated values) casting."""
        from decouple import config, Csv
        
        os.environ['TEST_CSV'] = 'value1,value2,value3'
        value = config('TEST_CSV', default='', cast=Csv())
        assert value == ['value1', 'value2', 'value3']
        assert isinstance(value, list)
        
        # Clean up
        del os.environ['TEST_CSV']


@pytest.mark.unit
class TestDjangoSettingsEnvironmentVariables:
    """Test that Django settings properly load environment variables."""
    
    def test_secret_key_loaded_from_env(self):
        """Verify SECRET_KEY is loaded from environment or has default."""
        assert hasattr(settings, 'SECRET_KEY')
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0
        # Should not be the default insecure key in production
        if os.getenv('DJANGO_ENVIRONMENT') == 'production':
            assert 'django-insecure' not in settings.SECRET_KEY
    
    def test_debug_is_boolean(self):
        """Verify DEBUG is a boolean value."""
        assert hasattr(settings, 'DEBUG')
        assert isinstance(settings.DEBUG, bool)
    
    def test_allowed_hosts_is_list(self):
        """Verify ALLOWED_HOSTS is a list."""
        assert hasattr(settings, 'ALLOWED_HOSTS')
        assert isinstance(settings.ALLOWED_HOSTS, list)
    
    def test_database_settings_loaded(self):
        """Verify database settings are loaded from environment."""
        assert hasattr(settings, 'DATABASES')
        assert 'default' in settings.DATABASES
        
        db_config = settings.DATABASES['default']
        assert 'ENGINE' in db_config
        assert 'NAME' in db_config
        
        # In testing, we might use SQLite, but structure should be correct
        assert db_config['ENGINE'] is not None
        assert db_config['NAME'] is not None


@pytest.mark.unit
class TestAWSEnvironmentVariables:
    """Test that AWS S3 settings are properly configured from environment."""
    
    def test_aws_storage_bucket_name_configured(self):
        """Verify AWS_STORAGE_BUCKET_NAME is configured."""
        assert hasattr(settings, 'AWS_STORAGE_BUCKET_NAME')
        assert settings.AWS_STORAGE_BUCKET_NAME is not None
        # In testing, this might be a test bucket name
        assert isinstance(settings.AWS_STORAGE_BUCKET_NAME, str)
    
    def test_aws_region_configured(self):
        """Verify AWS_S3_REGION_NAME is configured."""
        assert hasattr(settings, 'AWS_S3_REGION_NAME')
        assert settings.AWS_S3_REGION_NAME is not None
        # Should be a valid AWS region format
        assert isinstance(settings.AWS_S3_REGION_NAME, str)
        # Default should be ap-south-1 for India
        assert settings.AWS_S3_REGION_NAME == 'ap-south-1'
    
    def test_aws_credentials_structure(self):
        """Verify AWS credentials are configured (even if empty in testing)."""
        # These should exist as settings, even if empty in testing
        assert hasattr(settings, 'AWS_ACCESS_KEY_ID')
        assert hasattr(settings, 'AWS_SECRET_ACCESS_KEY')


@pytest.mark.unit
class TestFileUploadEnvironmentSettings:
    """Test file upload settings from environment variables."""
    
    def test_max_file_size_configured(self):
        """Verify maximum file size is configured."""
        assert hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE')
        assert isinstance(settings.FILE_UPLOAD_MAX_MEMORY_SIZE, int)
        assert settings.FILE_UPLOAD_MAX_MEMORY_SIZE > 0
    
    def test_prescription_url_expiration_configured(self):
        """Verify prescription URL expiration is configured."""
        assert hasattr(settings, 'PRESCRIPTION_FILE_URL_EXPIRATION')
        assert isinstance(settings.PRESCRIPTION_FILE_URL_EXPIRATION, int)
        assert settings.PRESCRIPTION_FILE_URL_EXPIRATION > 0


@pytest.mark.unit
class TestEnvironmentSpecificSettings:
    """Test that settings change based on DJANGO_ENVIRONMENT."""
    
    def test_environment_variable_exists(self):
        """Verify DJANGO_ENVIRONMENT is set."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        assert environment in ['development', 'production', 'testing']
    
    def test_debug_false_in_production(self):
        """Verify DEBUG is False in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        if environment == 'production':
            assert settings.DEBUG is False
    
    def test_allowed_hosts_configured_in_production(self):
        """Verify ALLOWED_HOSTS is properly configured in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        if environment == 'production':
            assert len(settings.ALLOWED_HOSTS) > 0
            # Should not contain wildcard in production
            assert '*' not in settings.ALLOWED_HOSTS


@pytest.mark.integration
class TestEnvFileLoading:
    """Test that .env file is properly loaded."""
    
    def test_env_file_exists_or_example_exists(self):
        """Verify .env.example file exists for reference."""
        import os
        from pathlib import Path
        
        base_dir = Path(settings.BASE_DIR)
        env_example = base_dir / '.env.example'
        
        # .env.example should always exist
        assert env_example.exists(), ".env.example file should exist for reference"
    
    def test_env_file_in_gitignore(self):
        """Verify .env is in .gitignore."""
        import os
        from pathlib import Path
        
        base_dir = Path(settings.BASE_DIR)
        gitignore = base_dir / '.gitignore'
        
        if gitignore.exists():
            content = gitignore.read_text()
            assert '.env' in content, ".env should be in .gitignore"


@pytest.mark.unit
class TestRequiredEnvironmentVariables:
    """Test that required environment variables are present."""
    
    def test_secret_key_not_empty(self):
        """Verify SECRET_KEY is not empty."""
        assert settings.SECRET_KEY
        assert len(settings.SECRET_KEY) > 10
    
    def test_database_name_not_empty(self):
        """Verify database name is configured."""
        db_name = settings.DATABASES['default']['NAME']
        assert db_name
        assert len(db_name) > 0
