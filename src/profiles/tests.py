from django.test import TestCase
from fake import FAKER

from .models import UserProfile, validate_country
from .utilities import fake_country


class UserProfileModelTests(TestCase):

    def setUp(self):
        self.user = UserProfile.objects.create(
            first_name=FAKER.first_name(),
            last_name=FAKER.last_name(),
            country=fake_country(),
            username=FAKER.username(),
            email=FAKER.email(),
            password=FAKER.slug(),
            is_admin=False,
            register_ip=FAKER.ipv4()
        )

    def test_full_name(self):
        self.assertEqual(self.user.full_name, self.user.first_name + " " + self.user.last_name)

    def test_countries_exist(self):
        self.assertEqual(validate_country(self.user.country), self.user.country)
