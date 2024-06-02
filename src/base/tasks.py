import base64
import json
import os
import shutil
import time
from pathlib import Path

import redis
from celery import shared_task
from celery.signals import worker_ready, task_success
from celery.result import AsyncResult
from django.contrib.auth import get_user_model

from PaulStudios import settings
from PaulStudios.celery import app
from songdownloader.models import SpotifySong, SpotifyPlaylist, UserLogRecent, UserHistory

redis_db = redis.from_url(settings.REDIS_URL, decode_responses=True)
User = get_user_model()


def increase_progress(task_id):
    string = f"progress-{task_id}"
    redis_db.set(string, int(redis_db.get(string)) + 1)


def set_progress(progress, task_id):
    string = f"progress-{task_id}"
    redis_db.set(string, progress)

def update_progress(name, task_id, img = "/static/image_loading.svg"):
    redis_db.set(f"current-{task_id}", name)
    redis_db.set(f"image-{task_id}", img)
    increase_progress(task_id)

@shared_task
def delete_local_file(filename):
    try:
        os.remove(filename)
        print("Deleted media")
        print(f"Deleted file: {filename.split('/')[-1]} of user {filename.split('/')[2]}")
    except Exception as e:
        print(f"Error deleting file: {e}")
        raise


@shared_task
def delete_folder(folder):
    try:
        shutil.rmtree(folder)
        print(f"Deleted folder: {folder.split('/')[-1]} of user {folder.split('/')[2]}")
    except Exception as e:
        print(f"Error deleting folder: {e}")
        raise


@worker_ready.connect
def setup(sender, **kwargs):
    worker_list_upload.delay()


@app.task(bind=True)
def worker_list_upload(self):
    worker_list = [*app.control.inspect().stats().keys()]
    print(f"Active Workers: {worker_list}")
    redis_db.set("workers", json.dumps(worker_list))
    if redis_db.get("task_list") is None:
        redis_db.set("task_list", json.dumps([""]))


@app.task(bind=True)
def update_celery_task_list(self):
    scheduled_total = []
    active_total = []
    reserved_total = []
    worker_list = json.loads(redis_db.get("workers"))
    for worker in worker_list:
        celery_app = app.control.inspect([worker])
        if celery_app.scheduled():
            scheduled = celery_app.scheduled().get(worker)
            for task in scheduled:
                if "songdownloader.tasks" in task['request']['name']:
                    scheduled_total.append(task['request']['id'])
        if celery_app.active():
            active = celery_app.active().get(worker)
            for task in active:
                if "songdownloader.tasks" in task['name']:
                    active_total.append(task['id'])
        if celery_app.reserved():
            reserved = celery_app.reserved().get(worker)
            for task in reserved:
                if "songdownloader.tasks" in task['name']:
                    reserved_total.append(task['id'])
    total = []
    total.extend(scheduled_total)
    total.extend(active_total)
    total.extend(reserved_total)
    task_list = json.loads(redis_db.get("task_list"))
    task_list.extend(total)
    res = []
    [res.append(str(x)) for x in task_list if x not in res]
    redis_db.set("task_list", json.dumps(res))
    print("Task_List updated")
    return res


@app.task(bind=True)
def delete_task_data(self, userlog_id):
    userlog = UserLogRecent.objects.get(pk=userlog_id)
    task_id = str(userlog.task_id)

    task = AsyncResult(task_id)
    task_result = task.info
    path = task_result['path']
    BASE_DIR = Path(__file__).resolve().parent.parent
    task.forget()

    redis_db.delete(f"total-{task_id}")
    redis_db.delete(f"progress-{task_id}")
    redis_db.delete(f"name-{task_id}")
    redis_db.delete(f"current-{task_id}")
    redis_db.delete(f"image-{task_id}")
    task_list = json.loads(redis_db.get("task_list"))
    print(task_list)
    print(task_id, type(task_id))
    task_list.remove(task_id)
    redis_db.set("task_list", json.dumps(task_list))

    delete_local_file.delay(str(BASE_DIR / path))

    u = UserHistory.objects.create(
        user=userlog.user,
        name=userlog.name,
        mode=f"{userlog.type}-{userlog.mode}",
        service_id=userlog.service_id,
    )
    remove_db_data.apply_async((u.id,), countdown=24 * 3600)
    userlog.delete()
    print(f"Cleanup Successful of {task_result['name']}  [{task_id}]")


@app.task(bind=True)
def remove_db_data(self, userhistory_id):
    data = UserHistory.objects.get(pk=userhistory_id)
    service_id = data.service_id
    if data.mode.split("-")[-1] == "Playlist":
        playlist = SpotifyPlaylist.objects.get(pk=service_id)
        list_of_songs = playlist.tracks.all()
        playlist.image.delete()
        playlist.delete()
    elif data.mode.split("-")[-1] == "Track":
        try:
            list_of_songs = [SpotifySong.objects.get(pk=service_id)]
        except Exception as e:
            list_of_songs = []
            print(e)
    else:
        list_of_songs = []
    for song in list_of_songs:
        song.image.delete()
        song.delete()
