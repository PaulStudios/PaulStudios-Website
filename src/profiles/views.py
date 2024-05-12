from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render


from .models import UserProfile


def index(request):
    return render(request,'profiles/index.html', {})


def handler404(request, exception, template_name="profiles/404.html"):
    response = render(template_name)
    response.status_code = 404
    return response

@login_required
def detail(request):
    return render(request,'profiles/info.html')

@login_required
def user_logout(request):
    logout(request)
    return render(request,'profiles/logged_out.html', {})


def Register(request):
    return HttpResponse("You're looking at the profile of ")


def activate_user_view(request, *args, code=None, **kwargs):
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
