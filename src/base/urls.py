from django.contrib.auth.views import LoginView
from django.urls import path

from . import views

app_name = "backend"

urlpatterns = [
    path("task-progress/<str:task_id>", views.task_progress, name="task_progress")
]