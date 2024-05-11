from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the profile index.")


def detail(request, username):
    return HttpResponse("You're looking at the profile of %s." % username)

