from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse


def send_mail(request):
    request.user.send_activation_email(request)
    messages.info(request, "Mail has been sent")
    return redirect(reverse("profiles:info"))
