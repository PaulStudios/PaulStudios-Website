from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from profiles.decorators import activated_user_required


@csrf_exempt
@login_required
@activated_user_required
def game_view(request):
    user = request.user
    return render(request, 'cyberorb/index.html', {'username': user.first_name, 'first_name': user.first_name})