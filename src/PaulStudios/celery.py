from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PaulStudios.settings')

# Create the Celery app instance
app = Celery('PaulStudios')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.broker_connection_retry_on_startup = True


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
