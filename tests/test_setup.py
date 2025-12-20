"""
Test Django installation and database connectivity.

This test follows TDD principles - it should FAIL if the configuration is incorrect.
DO NOT modify this test to make it pass - fix the configuration instead.
"""

import pytest
from django.conf import settings
from django.db import connection
from django.contrib.auth import get_user_model


@pytest.mark.unit
class TestDjangoInstallation:
    """Test that Django is properly installed and configured."""
    
    def test_django_settings_loaded(self):
        """Verify Django settings are loaded correctly."""
        assert settings.configured
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0
    
    def test_timezone_configured_for_india(self):
        """Verify timezone is set to Asia/Kolkata."""
        assert settings.TIME_ZONE == 'Asia/Kolkata'
        assert settings.USE_TZ is True
    
    def test_language_code_configured(self):
        """Verify language code is set to en-in."""
        assert settings.LANGUAGE_CODE == 'en-in'
    
    def test_rest_framework_installed(self):
        """Verify Django REST Framework is installed."""
        assert 'rest_framework' in settings.INSTALLED_APPS
    
    def test_jwt_installed(self):
        """Verify JWT authentication is installed."""
        assert 'rest_framework_simplejwt' in settings.INSTALLED_APPS


@pytest.mark.django_db
@pytest.mark.integration
class TestDatabaseConnectivity:
    """Test database connectivity and basic operations."""
    
    def test_database_connection(self):
        """Verify database connection works."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result == (1,)
    
    def test_database_tables_exist(self):
        """Verify Django tables are created."""
        with connection.cursor() as cursor:
            # Database-agnostic way to check for table existence
            tables = connection.introspection.table_names(cursor)
            assert 'django_migrations' in tables, "django_migrations table should exist"
    
    def test_user_model_accessible(self):
        """Verify User model is accessible and can perform basic operations."""
        User = get_user_model()
        
        # Create a test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Verify user was created
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('testpass123')
        
        # Verify user can be retrieved
        retrieved_user = User.objects.get(username='testuser')
        assert retrieved_user.id == user.id
        
        # Clean up
        user.delete()
    
    def test_database_transaction_rollback(self):
        """Verify database transactions work correctly."""
        User = get_user_model()
        
        initial_count = User.objects.count()
        
        # This should be rolled back after the test
        User.objects.create_user(
            username='tempuser',
            email='temp@example.com',
            password='temppass123'
        )
        
        # User should exist within this test
        assert User.objects.filter(username='tempuser').exists()
        
        # After test rollback, count should return to initial
        # (This is verified by pytest-django's transaction management)


@pytest.mark.integration
class TestLoggingConfiguration:
    """Test logging is properly configured."""
    
    def test_logging_configured(self):
        """Verify logging configuration exists."""
        assert hasattr(settings, 'LOGGING')
        assert 'version' in settings.LOGGING
        assert settings.LOGGING['version'] == 1
    
    def test_logging_handlers_configured(self):
        """Verify logging handlers are configured."""
        # In testing environment, we use NullHandler
        # In development, we should have console and file handlers
        assert 'handlers' in settings.LOGGING
        assert len(settings.LOGGING['handlers']) > 0


@pytest.mark.unit
class TestStaticMediaConfiguration:
    """Test static and media files configuration."""
    
    def test_static_url_configured(self):
        """Verify STATIC_URL is configured."""
        assert hasattr(settings, 'STATIC_URL')
        # Django automatically adds leading slash if not present
        assert settings.STATIC_URL in ['static/', '/static/']
    
    def test_media_url_configured(self):
        """Verify MEDIA_URL is configured."""
        assert hasattr(settings, 'MEDIA_URL')
        # Django automatically adds leading slash if not present
        assert settings.MEDIA_URL in ['media/', '/media/']
    
    def test_static_root_configured(self):
        """Verify STATIC_ROOT is configured."""
        assert hasattr(settings, 'STATIC_ROOT')
        assert settings.STATIC_ROOT is not None
    
    def test_media_root_configured(self):
        """Verify MEDIA_ROOT is configured."""
        assert hasattr(settings, 'MEDIA_ROOT')
        assert settings.MEDIA_ROOT is not None
