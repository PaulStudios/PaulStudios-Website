from django import forms

from django.contrib.auth import get_user_model

user = get_user_model()

class LoginForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    class Meta:
        model = user
        fields = ["username", "password"]