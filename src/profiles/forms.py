from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

from profiles.models import UserProfile

user = UserProfile


class RegistrationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password-input'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput()
    )
    password_strength = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
    )
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-3 mb-0'),
                Column('email', css_class='form-group col-md-5 mb-0'),
                Column('country', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(Column('captcha', css_class='form-group col-md-4 mb-0 bg-transparent'), css_class='form-row'),
            Submit('submit', 'Register')
        )

    class Meta:
        model = user
        fields = ["first_name", "last_name",
                  "username",
                  "email", "country", ]


class OTPLoginForm(forms.Form):
    input_data = forms.CharField(label="Username/ Email")


class EnterOTPForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        label='Enter your verification code',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '6-digit code'
        })
    )
