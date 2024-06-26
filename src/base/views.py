import redis
from celery.result import AsyncResult
from django.http import JsonResponse
from django.shortcuts import render

from PaulStudios import settings

redis_db = redis.from_url(settings.REDIS_URL, decode_responses=True)


def task_progress(request, task_id):
    result = AsyncResult(task_id)
    try:
        response_data = {
            'progress': redis_db.get(f"progress-{task_id}"),
            'total': redis_db.get(f"total-{task_id}"),
            'image': redis_db.get(f"image-{task_id}"),
            'current': redis_db.get(f"current-{task_id}"),
            'name': redis_db.get(f"name-{task_id}"),
            'state': result.state,
            'details': result.info,
        }
        return JsonResponse(response_data)
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)})


def custom_403(request, exception):
    return render(request, 'base/403.html', status=403)


def custom_404(request, exception):
    return render(request, 'base/404.html', status=404)


def custom_500(request):
    return render(request, 'base/500.html', status=500)
