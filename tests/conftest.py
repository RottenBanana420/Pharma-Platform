"""
Pytest configuration and fixtures for tests.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    This fixture is applied to all tests automatically.
    """
    pass


@pytest.fixture
def user_factory():
    """Fixture to provide UserFactory."""
    from tests.factories import UserFactory
    return UserFactory


@pytest.fixture
def pharmacy_admin_factory():
    """Fixture to provide PharmacyAdminFactory."""
    from tests.factories import PharmacyAdminFactory
    return PharmacyAdminFactory
