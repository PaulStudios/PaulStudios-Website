# Generated by Django 5.0.6 on 2024-05-30 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songdownloader', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userlog',
            name='task_id',
            field=models.UUIDField(default=0, editable=False),
            preserve_default=False,
        ),
    ]
