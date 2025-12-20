"""
Rate limiting middleware for authentication endpoints.

Implements IP-based rate limiting to prevent brute-force attacks.
"""
import time
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status


class RateLimitMiddleware:
    """
    Middleware to implement rate limiting on authentication endpoints.
    
    Rate limits:
    - /api/auth/token/: 5 requests per minute
    - /api/auth/token/refresh/: 10 requests per minute
    """
    
    # Rate limit configurations (requests per minute)
    RATE_LIMITS = {
        '/api/auth/token/': 5,
        '/api/auth/token/refresh/': 10,
    }
    
    # Time window in seconds
    WINDOW = 60
    
    def __init__(self, get_response):
        """Initialize middleware."""
        self.get_response = get_response
    
    def __call__(self, request):
        """
        Process request and apply rate limiting.
        
        Args:
            request: HTTP request
            
        Returns:
            HTTP response or 429 if rate limited
        """
        # Check if this is a rate-limited endpoint
        path = request.path
        if path in self.RATE_LIMITS:
            # Get client IP
            ip_address = self.get_client_ip(request)
            
            # Create cache key
            cache_key = f'rate_limit:{path}:{ip_address}'
            
            # Get current request count
            request_count = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if request_count >= self.RATE_LIMITS[path]:
                return JsonResponse(
                    {
                        'detail': 'Rate limit exceeded. Please try again later.',
                        'retry_after': self.WINDOW
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={'Retry-After': str(self.WINDOW)}
                )
            
            # Increment counter
            cache.set(cache_key, request_count + 1, self.WINDOW)
        
        # Process request
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """
        Get client IP address from request.
        
        Args:
            request: HTTP request
            
        Returns:
            Client IP address as string
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
