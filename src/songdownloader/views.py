import json
import time
from pathlib import Path

import redis
from celery.result import AsyncResult
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse

from PaulStudios import settings
from base.tasks import set_progress, update_celery_task_list
from profiles.views import user_check
from .forms import DataForm
from .tasks import spotify_playlist, spotify_track, youtube_playlist, youtube_track

redis_db = redis.from_url(settings.REDIS_URL, decode_responses=True)


def index(request):
    check = user_check(request)
    if check: return check
    if request.method == "POST":
        form = DataForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            service = form.cleaned_data['service']
            mode = form.cleaned_data['mode']
            url = form.cleaned_data['url']
            if service == "Spotify" and mode == "Playlist":
                t = spotify_playlist.delay(request.user.id, url)
            elif service == "Spotify" and mode == "Track":
                t = spotify_track.delay(request.user.id, url)
            elif service == "Youtube" and mode == "Playlist":
                t = youtube_playlist.delay(request.user.id, url)
            elif service == "Youtube" and mode == "Track":
                t = youtube_track.delay(request.user.id, url)
            print(t)
            update_celery_task_list.delay()
            set_progress(0, t)
            redis_db.set(f"total-{t}", 1000)
            redis_db.set(f"image-{t}", "/static/logo.png")
            return redirect(reverse("songdownloader:progress", kwargs={"task_id": t}))
    else:
        form = DataForm()
    return render(request, 'songdownloader/index.html', {'form': form})


def show_progress(request, task_id):
    update_celery_task_list.delay()
    task_list = json.loads(redis_db.get("task_list"))
    if task_id not in task_list:
        retries = int(redis_db.get(f"progress-retry-{request.user.id}-{task_id}") or 0)
        if retries > 3:
            redis_db.delete(f"progress-retry-{request.user.id}-{task_id}")
            raise Http404
        else:
            time.sleep(0.6)
            redis_db.set(f"progress-retry-{request.user.id}-{task_id}", retries + 1)
            return redirect(reverse("songdownloader:progress", kwargs={"task_id": task_id}))
    return render(request, 'songdownloader/progress.html', {'task_id': task_id})


def download_file(request, task_id):
    result = AsyncResult(task_id).info
    if not result['user'] == str(request.user.id):
        raise PermissionDenied("This file was requested by another user.")
    path = result['path']
    BASE_DIR = Path(__file__).resolve().parent.parent
    return FileResponse(open(BASE_DIR / path, "rb"))
