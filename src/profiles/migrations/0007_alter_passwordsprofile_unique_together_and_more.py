# Generated by Django 5.0.6 on 2024-06-18 12:13

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_passwordsprofile'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='passwordsprofile',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='passwordsprofile',
            name='previous_passwords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255), default=list, size=None),
        ),
        migrations.RemoveField(
            model_name='passwordsprofile',
            name='token',
        ),
        migrations.RemoveField(
            model_name='passwordsprofile',
            name='token_updated',
        ),
    ]