"""
Jarvis AI Models
"""

import uuid

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models.functions import Now
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .utilities import countries_exist, code_generator


def validate_country(name):
    if countries_exist(name):
        return name
    raise ValidationError(
        _("%(value)s is not a real country."),
        params={"value": name},
    )


class UserProfile(AbstractBaseUser, PermissionsMixin):
    """User Profile Model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField("First Name", max_length=40)
    last_name = models.CharField("Last Name", max_length=40)
    country = models.CharField("Country", max_length=50, validators=[validate_country])
    username = models.CharField("Username", max_length=100, unique=True)
    email = models.EmailField("Email", max_length=55, unique=True)
    password = models.CharField("Password", max_length=254)
    is_admin = models.BooleanField("Is ADMIN?", default=False)
    activation_key = models.CharField(max_length=120, blank=True, null=True)
    activated = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    register_ip = models.GenericIPAddressField("IP Address during creation", protocol="IPv4")
    created = models.DateTimeField("Registration Date-Time", db_default=Now())
    updated = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name", "country", "email", "password", "register_ip"]

    objects = UserManager()

    def __str__(self):
        name = self.full_name + " | (" + self.username + ")"
        return name

    @property
    def full_name(self):
        """Returns the person's full name."""
        return f"{self.first_name} {self.last_name}"

    def send_activation_email(self):
        if not self.activated:
            self.activation_key = code_generator()  # 'somekey' #gen key
            self.save()
            path_ = reverse('activate', kwargs={"code": self.activation_key})
            full_path = "https://muypicky.com" + path_
            subject = 'Activate Account'
            from_email = settings.DEFAULT_FROM_EMAIL
            message = f'Activate your account here: {full_path}'
            recipient_list = [self.user.email]
            html_message = f'<p>Activate your account here: {full_path}</p>'
            print(html_message)
            sent_mail = send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
                html_message=html_message)
            sent_mail = False
            return sent_mail
        return "FAILED"
