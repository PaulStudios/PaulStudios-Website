from django.contrib.auth.views import LoginView
from django.urls import path

from . import views

app_name = "profiles"
urlpatterns = [
    path("", views.index, name="index"),
    path("info/", views.detail, name="info"),
    path('activate/<str:code>/', views.activate_user_view, name='activate'),
    path('login/', LoginView.as_view(
        template_name='profiles/login.html',
        redirect_authenticated_user=True), name='login'
         ),
    path('error/<str:type>', views.error_page, name="error_page"),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.Register, name='register'),
]
