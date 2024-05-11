"""
Jarvis AI Models
"""

import uuid

from django.db import models
from django.db.models.functions import Now
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .utilities import countries_exist


def validate_country(name):
    if countries_exist(name):
        return name
    else:
        raise ValidationError(
            _("%(value)s is not a real country."),
            params={"value": name},
        )


class UserProfile(models.Model):
    """User Profile Model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField("First Name", max_length=30)
    last_name = models.CharField("Last Name", max_length=30)
    country = models.CharField("Country", max_length=50, validators=[validate_country])
    username = models.CharField("Username", max_length=100, unique=True)
    email = models.EmailField("Email", max_length=55, unique=True)
    password = models.CharField("Password", max_length=254)
    is_admin = models.BooleanField("Is ADMIN?", default=False)
    register_ip = models.GenericIPAddressField("IP Address during creation", protocol="IPv4")
    created = models.DateTimeField(
        "Registration Date-Time",
        db_comment="Date and Time when the user was first registered",
        db_default=Now()
    )

    def __str__(self):
        name = self.full_name + " | (" + self.username + ")"
        return name

    @property
    def full_name(self):
        """Returns the person's full name."""
        return f"{self.first_name} {self.last_name}"
