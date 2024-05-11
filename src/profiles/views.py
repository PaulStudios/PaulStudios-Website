from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import LoginForm
from .models import UserProfile


def index(request):
    if request.user.is_authenticated:
        name = request.user.full_name
    else:
        name = "Anonymous"
    return HttpResponse("Hello %s. You're at the profile index."% name)

@login_required
def detail(request):
    return HttpResponse("You're looking at the profile of %s." % request.user.username)

@login_required
def user_logout(request):
    logout(request)
    return render(request,'profiles/logged_out.html', {})
def Register(request):
    return HttpResponse("You're looking at the profile of ")

def activate_user_view(request, code=None, *args, **kwargs):
    if code:
        qs = UserProfile.objects.filter(activation_key=code)
        if qs.exists() and qs.count() == 1:
            profile = qs.first()
            if not profile.activated:
                profile.activated=True
                profile.activation_key="DONE"
                profile.save()
                return redirect("/login")
    return redirect("/login")

