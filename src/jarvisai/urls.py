from django.urls import path

from . import views

app_name = "jarvisai"

urlpatterns = [
    path("chat", views.chat_view, name="chat"),
    path("chat/bot_response", views.bot_response, name="bot_response"),
    path('chat/history', views.chat_history, name='chat_history'),
    path('chat/history/<int:chat_id>', views.chat_detail, name='chat_detail'),
]
