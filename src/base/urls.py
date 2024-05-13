from django.contrib.auth.views import LoginView
from django.urls import path

from . import views

app_name = "backend"

urlpatterns = [
    path('send-activation-mail', views.send_mail, name="send-activation-mail")
]