from django.test import TestCase

from fake import FAKER

import django
django.setup()

from profiles.models import UserProfile, validate_country
from profiles.utilities import fake_country


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
        name = self.user.first_name + " " + self.user.last_name
        self.assertEqual(self.user.full_name, name)

    def test_countries_validation(self):
        self.assertEqual(validate_country(self.user.country), self.user.country)

