"""
Custom password validators for enhanced security.

Implements validators for:
- Uppercase letter requirement
- Number requirement
- Special character requirement
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    """
    Validate that the password contains at least one uppercase letter.
    """
    
    def validate(self, password, user=None):
        """
        Validate the password.
        
        Args:
            password: The password to validate
            user: Optional user instance
            
        Raises:
            ValidationError: If password doesn't contain uppercase letter
        """
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
    
    def get_help_text(self):
        """Return help text for this validator."""
        return _("Your password must contain at least one uppercase letter.")


class NumberValidator:
    """
    Validate that the password contains at least one digit.
    """
    
    def validate(self, password, user=None):
        """
        Validate the password.
        
        Args:
            password: The password to validate
            user: Optional user instance
            
        Raises:
            ValidationError: If password doesn't contain a digit
        """
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_number',
            )
    
    def get_help_text(self):
        """Return help text for this validator."""
        return _("Your password must contain at least one digit.")


class SpecialCharacterValidator:
    """
    Validate that the password contains at least one special character.
    """
    
    def validate(self, password, user=None):
        """
        Validate the password.
        
        Args:
            password: The password to validate
            user: Optional user instance
            
        Raises:
            ValidationError: If password doesn't contain special character
        """
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."),
                code='password_no_special',
            )
    
    def get_help_text(self):
        """Return help text for this validator."""
        return _("Your password must contain at least one special character (!@#$%^&*(),.?\":{}|<>).")
