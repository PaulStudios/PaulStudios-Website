from django.http import HttpResponse
from django.shortcuts import redirect

from .models import UserProfile


def index(request):
    return HttpResponse("Hello, world. You're at the profile index.")


def detail(request, username):
    return HttpResponse("You're looking at the profile of %s." % username)


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

