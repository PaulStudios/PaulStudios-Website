from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import reverse_lazy

activation_required = user_passes_test(lambda user: user.activated, login_url=reverse_lazy("profiles:error_page", kwargs={'type':'mail_verify'}))
def activated_user_required(view_func):
    decorated_view_func = login_required(activation_required(view_func))
    return decorated_view_func

