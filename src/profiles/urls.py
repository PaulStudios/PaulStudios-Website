from django.contrib.auth.views import LoginView
from django.urls import path

from . import views

app_name = "profiles"
urlpatterns = [
    path("", views.index, name="index"),
    path("info/", views.detail, name="info"),
    path('send-activation-mail', views.send_activation_mail, name="send-activation-mail"),
    path('activate/<str:code>/', views.activate_user_view, name='activate'),
    path('login/', LoginView.as_view(
        template_name='profiles/login.html',
        redirect_authenticated_user=True), name='login'
         ),
    path('error/<str:type>', views.error_page, name="error_page"),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.Register, name='register'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('reset_password/<uidb64>/<token>/', views.password_reset_action, name='reset_password_action'),
]
