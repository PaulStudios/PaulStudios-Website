from django.contrib.auth.views import LogoutView, LoginView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("info/", views.detail, name="profile_info"),
    path('activate/<str:code>/', views.activate_user_view, name='activate'),
    path('login/', LoginView.as_view(template_name='profiles/login.html'), name ='login'),
    path('logout/', views.user_logout, name ='logout'),
    path('register/', views.Register, name ='register'),
]