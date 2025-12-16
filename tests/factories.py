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


class PharmacyFactory(DjangoModelFactory):
    """Factory for creating Pharmacy instances in tests."""
    
    class Meta:
        model = 'pharmacies.Pharmacy'
    
    name = factory.Faker('company')
    license_number = factory.Sequence(lambda n: f'LIC{n:06d}')
    contact_email = factory.Sequence(lambda n: f'pharmacy{n}@example.com')
    street_address = factory.Faker('street_address')
    city = factory.Faker('city')
    state = factory.Faker('state')
    postal_code = factory.LazyFunction(lambda: fake.numerify(text='######'))
    phone_number = factory.LazyFunction(
        lambda: f'+91{fake.numerify(text="##########")}'
    )
    is_verified = False


class MedicineFactory(DjangoModelFactory):
    """Factory for creating Medicine instances in tests."""
    
    class Meta:
        model = 'pharmacies.Medicine'
    
    commercial_name = factory.Sequence(lambda n: f'Medicine-{n}')
    generic_name = factory.Faker('word')
    manufacturer = factory.Faker('company')
    price = factory.Faker(
        'pydecimal',
        left_digits=4,
        right_digits=2,
        positive=True,
        min_value=0.01,
        max_value=9999.99
    )
    stock_quantity = factory.Faker('random_int', min=0, max=10000)
    pharmacy = factory.SubFactory(PharmacyFactory)

