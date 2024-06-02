from django.urls import path, include
from . import views

app_name = 'songdownloader'

urlpatterns = [
    path('', views.index, name='index'),
    path("<str:task_id>", views.show_progress, name='progress'),
    path("<str:task_id>/download", views.download_file, name='download'),
]