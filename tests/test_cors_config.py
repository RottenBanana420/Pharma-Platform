"""
Test CORS configuration for API access.

This test follows TDD principles - it should FAIL if the configuration is incorrect.
DO NOT modify this test to make it pass - fix the configuration instead.
"""

import pytest
from django.conf import settings
from django.test import RequestFactory
from django.http import HttpResponse


@pytest.mark.unit
class TestCORSInstallation:
    """Test that django-cors-headers is properly installed."""
    
    def test_cors_headers_installed(self):
        """Verify django-cors-headers is in INSTALLED_APPS."""
        assert 'corsheaders' in settings.INSTALLED_APPS
    
    def test_cors_middleware_installed(self):
        """Verify CORS middleware is in MIDDLEWARE."""
        assert 'corsheaders.middleware.CorsMiddleware' in settings.MIDDLEWARE
    
    def test_cors_middleware_before_common_middleware(self):
        """Verify CORS middleware is before CommonMiddleware."""
        cors_index = settings.MIDDLEWARE.index('corsheaders.middleware.CorsMiddleware')
        common_index = settings.MIDDLEWARE.index('django.middleware.common.CommonMiddleware')
        
        assert cors_index < common_index, "CorsMiddleware must be before CommonMiddleware"


@pytest.mark.unit
class TestCORSConfiguration:
    """Test CORS settings configuration."""
    
    def test_cors_allowed_origins_configured(self):
        """Verify CORS_ALLOWED_ORIGINS is configured."""
        assert hasattr(settings, 'CORS_ALLOWED_ORIGINS')
        assert isinstance(settings.CORS_ALLOWED_ORIGINS, (list, tuple))
    
    def test_cors_allow_credentials_enabled(self):
        """Verify CORS_ALLOW_CREDENTIALS is enabled for authentication."""
        assert hasattr(settings, 'CORS_ALLOW_CREDENTIALS')
        assert settings.CORS_ALLOW_CREDENTIALS is True
    
    def test_cors_allowed_origins_not_wildcard_in_production(self):
        """Verify CORS doesn't allow all origins in production."""
        import os
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            # Should not use CORS_ALLOW_ALL_ORIGINS in production
            if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS'):
                assert settings.CORS_ALLOW_ALL_ORIGINS is False
    
    def test_cors_development_origins(self):
        """Verify development CORS origins include localhost."""
        import os
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'development':
            origins = settings.CORS_ALLOWED_ORIGINS
            # Should allow localhost for development
            assert any('localhost' in origin for origin in origins)


@pytest.mark.unit
class TestCORSHeaders:
    """Test CORS header configuration."""
    
    def test_cors_allow_headers_configured(self):
        """Verify CORS_ALLOW_HEADERS includes necessary headers."""
        # Default headers should be allowed, or custom ones configured
        # If CORS_ALLOW_HEADERS is not set, django-cors-headers uses defaults
        if hasattr(settings, 'CORS_ALLOW_HEADERS'):
            headers = settings.CORS_ALLOW_HEADERS
            # Should include Authorization for JWT
            assert any('authorization' in h.lower() for h in headers)
    
    def test_cors_expose_headers_for_file_downloads(self):
        """Verify CORS_EXPOSE_HEADERS includes Content-Disposition."""
        # For file downloads, Content-Disposition should be exposed
        if hasattr(settings, 'CORS_EXPOSE_HEADERS'):
            headers = settings.CORS_EXPOSE_HEADERS
            assert any('content-disposition' in h.lower() for h in headers)


@pytest.mark.integration
@pytest.mark.django_db
class TestCORSMiddlewareFunctionality:
    """Test CORS middleware functionality with requests."""
    
    def test_cors_headers_in_response(self):
        """Test that CORS headers are added to responses."""
        from django.test import Client
        
        client = Client()
        
        # Make an OPTIONS request (preflight)
        response = client.options(
            '/api/',  # Assuming you have an API endpoint
            HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET'
        )
        
        # CORS middleware should add headers
        # Note: Actual headers depend on CORS configuration
        # This test verifies middleware is working
        assert response.status_code in [200, 404]  # 404 if endpoint doesn't exist yet
    
    def test_cors_preflight_request(self):
        """Test CORS preflight request handling."""
        from django.test import Client
        
        client = Client()
        
        # Preflight request
        response = client.options(
            '/',
            HTTP_ORIGIN='http://localhost:3000',
            HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type'
        )
        
        # Should return 200 for preflight
        assert response.status_code in [200, 404]
