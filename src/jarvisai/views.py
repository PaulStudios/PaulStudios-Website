import requests.exceptions
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from profiles.decorators import activated_user_required
from .chatbot import Bot
from .models import ChatMessage

bot = Bot()


@csrf_exempt
@login_required
@activated_user_required
def chat_view(request):
    user = request.user
    return render(request, 'jarvisai/chat.html', {'username': user.first_name, 'first_name': user.first_name})


@login_required
@csrf_exempt
def bot_response(request):
    if request.method == 'POST':
        message = request.POST.get("msg1", "")
        if message:
            try:
                response = bot.process(message)
            except requests.exceptions.ReadTimeout as e:
                response = "Sorry, PaulStudios Servers are currently down. Please check again after some time."
            ChatMessage.objects.create(
                user=request.user,
                message=message,
                response=response
            )
            # Keep only the last 20 messages per user
            user_chat_logs = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')
            if user_chat_logs.count() > 20:
                user_chat_logs[20:].delete()
            return JsonResponse({'response': response})
        else:
            return JsonResponse({'error': 'Message not provided'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@csrf_exempt
def chat_history(request):
    chats = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')
    chat_list = [{'id': chat.id, 'user_message': chat.message, 'bot_response': chat.response, 'timestamp': chat.timestamp} for chat in chats]
    return JsonResponse(chat_list, safe=False)

@login_required
@csrf_exempt
def chat_detail(request, chat_id):
    chat = get_object_or_404(ChatMessage, id=chat_id, user=request.user)
    messages = [
        {'sender': request.user.first_name, 'message': chat.message},
        {'sender': 'JarvisAI', 'message': chat.response}
    ]
    return JsonResponse({'messages': messages})