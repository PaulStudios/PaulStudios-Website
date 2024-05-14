from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .decorators import activated_user_required
from .forms import RegistrationForm
from .models import UserProfile

PRIVATE_IPS_PREFIX = ('10.', '172.', '192.', '127.')


def get_client_ip(request):
    """get the client ip from the request
    """
    remote_address = request.META.get('REMOTE_ADDR')
    # set the default value of the ip to be the REMOTE_ADDR if available
    # else None
    ip = remote_address
    # try to get the first non-proxy ip (not a private ip) from the
    # HTTP_X_FORWARDED_FOR
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        proxies = x_forwarded_for.split(',')
        # remove the private ips from the beginning
        while (len(proxies) > 0 and
               proxies[0].startswith(PRIVATE_IPS_PREFIX)):
            proxies.pop(0)
        # take the first ip which is not a private one (of a proxy)
        if len(proxies) > 0:
            ip = proxies[0]

    return ip


def index(request):
    return render(request, 'profiles/index.html', {})


def handler404(request, exception, template_name="profiles/404.html"):
    response = render(template_name)
    response.status_code = 404
    return response


@login_required
@activated_user_required
def detail(request):
    return render(request, 'profiles/info.html')


@login_required
def user_logout(request):
    logout(request)
    return render(request, 'profiles/logged_out.html', {})


def Register(request):
    if request.method == 'POST':
        # Create a form that has request.POST
        form = RegistrationForm(request.POST)
        print(form.errors)
        if form.is_valid():
            user = form.save(commit=False)
            # Set the user's password securely
            password = form.cleaned_data['password2']
            password1 = form.cleaned_data['password1']

            if password == password1:
                user.set_password(password)
                user.register_ip = get_client_ip(request)

                user.save()
                messages.success(request, "User registered. Please activate your profile by verifying your email.")
                return redirect(reverse("profiles:error_page", kwargs={'type':'mail_verify'})  # Redirect to the login page
            else:
                # Handle password mismatch error here
                form.add_error('password2', 'Passwords entered do not match')
    else:
        form = RegistrationForm()
    return render(request, 'profiles/register.html', {'form': form})


@login_required
def error_page(request, *args, type=None, **kwargs):
    if type == "mail_verify":
        return render(request, 'profiles/errors/mail_verify.html')

def activate_user_view(request, *args, code=None, **kwargs):
    if code:
        qs = UserProfile.objects.filter(activation_key=code)
        if qs.exists() and qs.count() == 1:
            profile = qs.first()
            if not profile.activated:
                profile.activated = True
                profile.activation_key = "DONE"
                profile.save()
                messages.success(request, "Profile activated. You now have complete access to all Apps.")
                return redirect(reverse("profiles:login"))
    return redirect(reverse("profiles:login"))
