import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from profiles.decorators import activated_user_required
from .forms import ChatForm
from .chatbot import Bot
from .models import ChatMessage

bot = Bot()


@login_required
@activated_user_required
def chat_view(request):
    user = request.user
    return render(request, 'jarvisai/chat.html', {'username': user.first_name})


@login_required
@csrf_exempt
def bot_response(request):
    if request.method == 'POST':
        message = request.POST.get("msg1", "")
        if message:
            response = bot.process(message)
            ChatMessage.objects.create(
                user=request.user,
                message=message,
                response=bot_response
            )

            return JsonResponse({'response': response})
        else:
            return JsonResponse({'error': 'Message not provided'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def chat_history(request):
    chats = ChatMessage.objects.filter(user=request.user).order_by('-timestamp').values('id', 'message', 'timestamp')
    return JsonResponse(list(chats), safe=False)

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(ChatMessage, id=chat_id, user=request.user)
    messages = [
        {'sender': request.user.username, 'message': chat.message},
        {'sender': 'JarvisAI', 'message': chat.response}
    ]
    return JsonResponse({'messages': messages})