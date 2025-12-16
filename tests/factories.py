"""
Factory classes for creating test data using factory_boy.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker

fake = Faker('en_IN')  # Indian locale for realistic test data


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances in tests."""
    
    class Meta:
        model = 'accounts.User'
        skip_postgeneration_save = True
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    phone_number = factory.LazyFunction(
        lambda: f'+91{fake.numerify(text="##########")}'
    )
    user_type = 'patient'
    is_verified = False
    is_active = True
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return
        
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('testpass123')


class PharmacyAdminFactory(UserFactory):
    """Factory for creating pharmacy admin users."""
    user_type = 'pharmacy_admin'
