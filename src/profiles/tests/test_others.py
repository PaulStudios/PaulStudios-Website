from django.test import TestCase

from profiles.utilities import countries_exist


class UtilitiesTest(TestCase):
    def test_utilities_countries_exist(self):
        correct = "India"
        wrong = "something"
        self.assertEqual(countries_exist(correct), True)
        self.assertEqual(countries_exist(wrong), False)
