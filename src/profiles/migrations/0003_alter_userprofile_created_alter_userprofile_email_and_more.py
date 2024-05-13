# Generated by Django 5.0.6 on 2024-05-13 03:05

import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_alter_userprofile_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='created',
            field=models.DateTimeField(db_default=django.db.models.functions.datetime.Now(), verbose_name='Registration Date-Time'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='email',
            field=models.EmailField(error_messages={'unique': 'A user with that email already exists.'}, max_length=70, unique=True, verbose_name='Email'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='username',
            field=models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=100, unique=True, verbose_name='Username'),
        ),
    ]
