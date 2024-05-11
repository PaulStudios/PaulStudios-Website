from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("info/<str:username>/", views.detail, name="profile_info"),
    path('activate/<str:code>/', views.activate_user_view, name='activate')
]