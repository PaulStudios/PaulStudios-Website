import redis
from django.contrib import messages
from django.contrib.auth import logout, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from PaulStudios import settings
from .forms import RegistrationForm, OTPLoginForm, EnterOTPForm
from .models import PasswordsProfile
from .tasks import send_activation_email, send_reset_password_email, send_login_email
from .utilities import is_base64, validateEmail

PRIVATE_IPS_PREFIX = ('10.', '172.', '192.', '127.')
redis_db = redis.from_url(settings.REDIS_URL, decode_responses=True)
User = get_user_model()


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


def user_check(request):
    user = request.user
    if not user.is_authenticated:
        messages.error(request, 'You are not logged in.', extra_tags="danger")
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")
    if not user.activated:
        messages.error(request, 'Your account is not activated. Please verify your mail first!', extra_tags="danger")
        return redirect(reverse("profiles:error_page", kwargs={'type': "mail_verify"}))
    return


def index(request):
    return render(request, 'profiles/index.html', {})


@login_required
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
                return redirect(
                    reverse("profiles:error_page", kwargs={'type': 'mail_verify'}))  # Redirect to the login page
            else:
                # Handle password mismatch error here
                form.add_error('password2', 'Passwords entered do not match')
        else:
            for key, error in list(form.errors.items()):
                if key == 'captcha' and error[0] == 'This field is required.':
                    messages.error(request, "You must pass the reCAPTCHA test", extra_tags="danger")
                    continue
                messages.error(request, error)
    else:
        form = RegistrationForm()
    return render(request, 'profiles/register.html', {'form': form})


@login_required
def error_page(request, *args, type=None, **kwargs):
    if type == "mail_verify":
        return render(request, 'profiles/errors/mail_verify.html')


def send_activation_mail(request):
    send_activation_email.apply_async(request.scheme, request.get_host(), request.user.id)
    messages.info(request, "Mail has been sent")
    if not PasswordsProfile.objects.filter(user=request.user).exists():
        profile = PasswordsProfile.objects.create(user=request.user)
        profile.old_passwords.append(request.user.password)
        profile.save()
    return redirect(reverse("profiles:info"))


def activate_user_view(request, *args, code=None, **kwargs):
    if code:
        if not is_base64(code):
            messages.error(request, "Your activation key is invalid.", extra_tags="danger")
            return redirect(reverse("profiles:login"))
        code = urlsafe_base64_decode(code).decode('utf-8')
        qs = User.objects.filter(activation_key=code)
        if qs.exists() and qs.count() == 1:
            profile = qs.first()
            if not redis_db.exists(profile.activation_key):
                messages.error(request, 'Your activation key has expired.', extra_tags="danger")
                return redirect(reverse("profiles:login"))
            if not profile.activated:
                profile.activated = True
                profile.activation_key = "DONE"
                profile.save()
                messages.success(request, "Profile activated. You now have complete access to all Apps & Services.")
                return redirect(reverse("profiles:login"))
            messages.success(request, "Profile already activated.")
            return redirect(reverse("profiles:info"))
        messages.error(request, "Your activation key is invalid.", extra_tags="danger")
        return redirect(reverse("profiles:login"))
    return redirect(reverse("profiles:info"))


def reset_password(request, *args, **kwargs):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['email']
            user = User.objects.filter(email=data)
            if user.exists():
                send_reset_password_email.apply_async(request.scheme, request.get_host(), user.first().id)
            messages.success(request, "If this email is associated with an account, a mail will be sent with "
                                      "instructions on how to reset your password.")
            return redirect(reverse("profiles:login"))
    else:
        form = PasswordResetForm()
    return render(request, "profiles/reset/reset.html", {"form": form})


def password_reset_action(request, uidb64=None, token=None):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save(commit=False)
                newpassword = form.cleaned_data['new_password1']
                try:
                    # Retrieve the PasswordsProfile instance for the user
                    profile = PasswordsProfile.objects.get(user=user)
                except PasswordsProfile.DoesNotExist:
                    return False

                    # Check if the entered password matches any of the previous passwords
                if not isinstance(profile.old_passwords, list):
                    profile.previous_passwords = []
                for old_password in profile.old_passwords:
                    if check_password(newpassword, old_password):
                        exists = True
                    else:
                        exists = False
                if exists:
                    messages.error(request, "You cannot use a previously used password.", extra_tags="danger")
                    return render(request, 'profiles/reset/confirm.html', {'form': form, 'validlink': True})
                else:
                    profile = PasswordsProfile.objects.get(user=user)
                    profile.old_passwords.append(user.password)
                    profile.save()
                    form.save()
                    messages.success(request, "Your password has been reset. Please login again.")
                return redirect(reverse("profiles:login"))
        else:
            form = SetPasswordForm(user)
        messages.success(request, "Your link is valid. Please set your new password.")
        return render(request, 'profiles/reset/confirm.html', {'form': form, 'validlink': True})
    else:
        messages.error(request, "Invalid Reset link. Link may have expired", extra_tags="danger")
        return render(request, 'profiles/reset/confirm.html', {'validlink': False})


def login_otp(request, page_type=None, code=None):
    if page_type == "1" and code == "step1":
        if request.method == "POST":
            form = OTPLoginForm(request.POST)
            if form.is_valid():
                user_info = form.cleaned_data['input_data']
                if validateEmail(user_info):
                    user = User.objects.filter(email=user_info)
                    user = user.first()
                else:
                    user = User.objects.filter(username=user_info)
                    user = user.first()
                if user is None:
                    messages.error(request, "The account information entered is invalid.", extra_tags="danger")
                    return render(request, 'profiles/login.html', {'form': form, 'mode': "otp"})
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                send_login_email.apply_async(user.pk)
                messages.success(request, "Your OTP has been sent to your registered email id.")
                return redirect(reverse("profiles:login_otp", kwargs={"page_type": "2", "code": uid}))
        else:
            form = OTPLoginForm()
            return render(request, 'profiles/login.html', {'form': form, 'mode': "otp"})
    elif page_type == "2" and code is not None:
        if request.method == "POST":
            form = EnterOTPForm(request.POST)
            uid = force_str(urlsafe_base64_decode(code))
            user = get_object_or_404(User, pk=uid)
            if form.is_valid():
                input_otp = form.cleaned_data['input_data']
                otp = cache.get(f'verification_code_{code}')
                if otp is None:
                    messages.error(request, "OTP has expired.", extra_tags="danger")
                    return redirect(reverse("profiles:login_otp", kwargs={"page_type": "1", "code": "step1"}))
                if input_otp == otp:
                    cache.delete(f'verification_code_{code}')
                    login(request, user)
                    messages.success(request, "You have been successfully logged in")
                    return redirect(reverse("profiles:info"))
                else:
                    messages.error(request, "Invalid OTP.", extra_tags="danger")
                    return redirect(reverse("profiles:login_otp", kwargs={"page_type": "1", "code": "step1"}))
        else:
            form = EnterOTPForm()
            return render(request, 'profiles/login.html', {'form': form, 'mode': "otp"})
    else:
        raise PermissionDenied("You do not have permission to perform this action.")

