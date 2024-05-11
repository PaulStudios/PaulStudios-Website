# Generated by Django 5.0.6 on 2024-05-11 03:57

import django.db.models.functions.datetime
import jarvisai.models
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=30, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=30, verbose_name='Last Name')),
                ('country', models.CharField(max_length=50, validators=[jarvisai.models.validate_country], verbose_name='Country')),
                ('username', models.CharField(max_length=100, unique=True, verbose_name='Username')),
                ('email', models.EmailField(max_length=55, unique=True, verbose_name='Email')),
                ('password', models.CharField(max_length=254, verbose_name='Password')),
                ('is_admin', models.BooleanField(default=False, verbose_name='Is ADMIN?')),
                ('register_ip', models.GenericIPAddressField(protocol='IPv4', verbose_name='IP Address during creation')),
                ('created', models.DateTimeField(db_comment='Date and Time when the user was first registered', db_default=django.db.models.functions.datetime.Now(), verbose_name='Registration Date-Time')),
            ],
        ),
    ]
