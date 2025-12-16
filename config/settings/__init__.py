"""
Settings module loader.
Dynamically loads the appropriate settings based on DJANGO_ENVIRONMENT variable.
"""

import os

# Default to development if not specified
environment = os.getenv('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *
elif environment == 'testing':
    from .testing import *
else:
    from .development import *
