from django.urls import path

from . import views

app_name = "javascript_games.cyberorb"

urlpatterns = [
    path("", views.game_view, name="game"),
    ]