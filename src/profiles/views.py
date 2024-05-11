from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import LoginForm
from .models import UserProfile


def index(request):
    name = request.user.full_name
    return HttpResponse("Hello %s. You're at the profile index."% name)


def detail(request):
    return HttpResponse("You're looking at the profile of %s." % request.user.username)

def Login(request):
    if request.method == "POST":
        form = LoginForm()
        if form.is_valid():
            username = form.username
            password = form.password
            user = authenticate(username=username, password=password)
            if user is not None:
                redirect("/info")

    form = LoginForm()
    context = {'form': form}
    return render(request, "profiles/login.html", context)

def Register(request):
    return HttpResponse("You're looking at the profile of ")

def activate_user_view(request, code=None, *args, **kwargs):
    if code:
        qs = UserProfile.objects.filter(activation_key=code)
        if qs.exists() and qs.count() == 1:
            profile = qs.first()
            if not profile.activated:
                profile.activated=True
                profile.activation_key=None
                profile.save()
                return redirect("/login")
    return redirect("/login")

