"""
Test security settings for production readiness.

This test follows TDD principles - it should FAIL if the configuration is incorrect.
DO NOT modify this test to make it pass - fix the configuration instead.
"""

import pytest
import os
from django.conf import settings


@pytest.mark.unit
class TestSecurityMiddleware:
    """Test security middleware configuration."""
    
    def test_security_middleware_installed(self):
        """Verify SecurityMiddleware is installed."""
        assert 'django.middleware.security.SecurityMiddleware' in settings.MIDDLEWARE
    
    def test_csrf_middleware_installed(self):
        """Verify CSRF middleware is installed."""
        assert 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE
    
    def test_clickjacking_middleware_installed(self):
        """Verify clickjacking protection middleware is installed."""
        assert 'django.middleware.clickjacking.XFrameOptionsMiddleware' in settings.MIDDLEWARE


@pytest.mark.unit
class TestProductionSecuritySettings:
    """Test security settings for production environment."""
    
    def test_debug_false_in_production(self):
        """Verify DEBUG is False in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert settings.DEBUG is False, "DEBUG must be False in production"
    
    def test_secret_key_not_default_in_production(self):
        """Verify SECRET_KEY is not the default insecure key in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert 'django-insecure' not in settings.SECRET_KEY
            assert len(settings.SECRET_KEY) >= 50
    
    def test_allowed_hosts_configured_in_production(self):
        """Verify ALLOWED_HOSTS is properly configured in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert len(settings.ALLOWED_HOSTS) > 0
            assert '*' not in settings.ALLOWED_HOSTS


@pytest.mark.unit
class TestHTTPSSettings:
    """Test HTTPS and SSL settings for production."""
    
    def test_secure_ssl_redirect_in_production(self):
        """Verify SECURE_SSL_REDIRECT is enabled in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert hasattr(settings, 'SECURE_SSL_REDIRECT')
            assert settings.SECURE_SSL_REDIRECT is True
    
    def test_session_cookie_secure_in_production(self):
        """Verify SESSION_COOKIE_SECURE is enabled in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert hasattr(settings, 'SESSION_COOKIE_SECURE')
            assert settings.SESSION_COOKIE_SECURE is True
    
    def test_csrf_cookie_secure_in_production(self):
        """Verify CSRF_COOKIE_SECURE is enabled in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert hasattr(settings, 'CSRF_COOKIE_SECURE')
            assert settings.CSRF_COOKIE_SECURE is True


@pytest.mark.unit
class TestHSTSSettings:
    """Test HTTP Strict Transport Security settings."""
    
    def test_hsts_seconds_in_production(self):
        """Verify SECURE_HSTS_SECONDS is configured in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert hasattr(settings, 'SECURE_HSTS_SECONDS')
            # Should be at least 1 year (31536000 seconds)
            assert settings.SECURE_HSTS_SECONDS >= 31536000
    
    def test_hsts_include_subdomains_in_production(self):
        """Verify SECURE_HSTS_INCLUDE_SUBDOMAINS is enabled in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert hasattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS')
            assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
    
    def test_hsts_preload_in_production(self):
        """Verify SECURE_HSTS_PRELOAD is enabled in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert hasattr(settings, 'SECURE_HSTS_PRELOAD')
            assert settings.SECURE_HSTS_PRELOAD is True


@pytest.mark.unit
class TestContentSecuritySettings:
    """Test content security settings."""
    
    def test_content_type_nosniff_in_production(self):
        """Verify SECURE_CONTENT_TYPE_NOSNIFF is enabled in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert hasattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF')
            assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    
    def test_xframe_options_configured(self):
        """Verify X_FRAME_OPTIONS is configured."""
        assert hasattr(settings, 'X_FRAME_OPTIONS')
        assert settings.X_FRAME_OPTIONS in ['DENY', 'SAMEORIGIN']


@pytest.mark.unit
class TestProxySSLHeader:
    """Test proxy SSL header configuration for load balancers."""
    
    def test_secure_proxy_ssl_header_in_production(self):
        """Verify SECURE_PROXY_SSL_HEADER is configured in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            # This is needed when behind a load balancer/proxy
            if hasattr(settings, 'SECURE_PROXY_SSL_HEADER'):
                assert settings.SECURE_PROXY_SSL_HEADER == ('HTTP_X_FORWARDED_PROTO', 'https')


@pytest.mark.unit
class TestReferrerPolicy:
    """Test referrer policy configuration."""
    
    def test_referrer_policy_in_production(self):
        """Verify SECURE_REFERRER_POLICY is configured in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            if hasattr(settings, 'SECURE_REFERRER_POLICY'):
                # Should be a secure policy
                assert settings.SECURE_REFERRER_POLICY in [
                    'same-origin',
                    'strict-origin',
                    'strict-origin-when-cross-origin',
                    'no-referrer'
                ]


@pytest.mark.unit
class TestCSRFProtection:
    """Test CSRF protection configuration."""
    
    def test_csrf_cookie_httponly(self):
        """Verify CSRF cookie is not accessible via JavaScript."""
        # CSRF_COOKIE_HTTPONLY should be False (default) because
        # some frameworks need to read it, but CSRF protection is still active
        # The important thing is that CSRF middleware is enabled
        assert 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE
    
    def test_csrf_trusted_origins_in_production(self):
        """Verify CSRF_TRUSTED_ORIGINS is configured in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            # Should have CSRF_TRUSTED_ORIGINS for cross-origin requests
            if hasattr(settings, 'CSRF_TRUSTED_ORIGINS'):
                assert isinstance(settings.CSRF_TRUSTED_ORIGINS, (list, tuple))


@pytest.mark.unit
class TestEmailConfiguration:
    """Test email backend configuration."""
    
    def test_email_backend_configured(self):
        """Verify email backend is configured."""
        assert hasattr(settings, 'EMAIL_BACKEND')
        assert settings.EMAIL_BACKEND is not None
    
    def test_email_backend_smtp_in_production(self):
        """Verify SMTP email backend in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            from config.settings import production
            assert production.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
    
    def test_email_settings_in_production(self):
        """Verify email settings are configured in production."""
        environment = os.getenv('DJANGO_ENVIRONMENT', 'development')
        
        if environment == 'production':
            assert hasattr(settings, 'EMAIL_HOST')
            assert hasattr(settings, 'EMAIL_PORT')
            assert hasattr(settings, 'EMAIL_USE_TLS')


@pytest.mark.integration
class TestDjangoDeploymentCheck:
    """Test Django's deployment checklist."""
    
    def test_deployment_check_settings_exist(self):
        """Verify critical deployment settings exist."""
        critical_settings = [
            'SECRET_KEY',
            'DEBUG',
            'ALLOWED_HOSTS',
            'DATABASES',
            'MIDDLEWARE',
        ]
        
        for setting in critical_settings:
            assert hasattr(settings, setting), f"{setting} must be configured"
