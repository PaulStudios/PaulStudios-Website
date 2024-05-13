from django.test import TestCase

from django.urls import reverse
from fake import FAKER

from profiles.models import UserProfile
from profiles.utilities import fake_country


class InfoViewTests(TestCase):

    def setUp(self):
        self.user = UserProfile.objects.create(
            first_name=FAKER.first_name(),
            last_name=FAKER.last_name(),
            country=fake_country(),
            username=FAKER.username(),
            email=FAKER.email(),
            password=FAKER.slug(),
            is_admin=False,
            activated=True,
            register_ip=FAKER.ipv4()
        )

    def test_info_view_deny_anonymous(self):
        response = self.client.get(reverse("profiles:info"), follow=True)
        self.assertRedirects(
            response,
            reverse("profiles:login") + "?next=%2Fprofiles%2Finfo%2F"
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("profiles:info"), follow=True)
        self.assertRedirects(
            response,
            reverse("profiles:login") + "?next=%2Fprofiles%2Finfo%2F"
        )
        self.assertEqual(response.status_code, 200)

    def test_info_view_load(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("profiles:info"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/info.html')

    def test_info_view_post_blank(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("profiles:info"), {})  # blank data dictionary
        self.assertEqual(response.status_code, 200)


class LoginViewTests(TestCase):
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

    def test_login_view_load(self):
        response = self.client.get(reverse("profiles:login"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/login.html')

    def test_login_view_post_blank(self):
        response = self.client.post(reverse("profiles:login"), {})  # blank data dictionary
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', 'This field is required.')
        self.assertFormError(response.context['form'], 'password', 'This field is required.')

    def test_login_view_post_normal(self):
        response = self.client.post(reverse("profiles:login"),
                                    {"username": "abcdefgh", "password": "hi"})  # blank data dictionary
        self.assertEqual(response.status_code, 200)


class IndexViewTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(
            first_name=FAKER.first_name(),
            last_name=FAKER.last_name(),
            country=fake_country(),
            username="i_am_a_slug",
            email=FAKER.email(),
            password=FAKER.slug(),
            is_admin=False,
            register_ip=FAKER.ipv4()
        )

    def test_index_view_load(self):
        response = self.client.get(reverse("profiles:index"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/index.html')

    def test_index_view_anonymous(self):
        response = self.client.get(reverse("profiles:index"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Anonymous")

    def test_index_view_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("profiles:index"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "i_am_a_slug")
