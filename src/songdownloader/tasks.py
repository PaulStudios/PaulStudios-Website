import concurrent
import os
import tempfile
from datetime import datetime

import redis
import requests
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.core.files import File

from PaulStudios import settings
from PaulStudios.celery import app
from base.tasks import delete_folder, increase_progress, set_progress, delete_task_data, update_progress
from .models import SpotifySong, SpotifyPlaylist, UserLogRecent, YouTubeSong, YouTubePlaylist
from .services.downloader import downloader, make_yt_link
from .services.spotify import Spotify, get_track_details, search_song
from .services import youtube, spotify
from .services.youtube import Youtube as YT, parse_video_id

logger = get_task_logger(__name__)
User = get_user_model()
redis_db = redis.from_url(settings.REDIS_URL, decode_responses=True)


@app.task(bind=True)
def spotify_playlist(self, user_id, url):
    user = User.objects.get(pk=user_id)
    spotify_object = Spotify("Playlist", url)
    set_progress(0, self.request.id)
    redis_db.set(f"image-{self.request.id}", "/static/image_loading.svg")
    redis_db.set(f"current-{self.request.id}", "loading")
    redis_db.set(f"name-{self.request.id}", spotify_object.data.name)

    userlog = UserLogRecent.objects.create(
        user=user,
        task_id=self.request.id,
        name=spotify_object.data.name,
        mode="Playlist",
        type="Spotify",
        service_id=spotify_object.id,
        created=datetime.now(),
    )
    state_meta = {
        "name": spotify_object.data.name,
        "mode": userlog.mode,
        "service": userlog.type,
        "id": spotify_object.id
    }
    self.update_state(state="Getting list of Tracks", meta=state_meta)
    spotify_object.data.get_tracks_list()
    list_of_songs = spotify_object.data.track_list

    total_steps = (len(list_of_songs) + 1) * 2
    redis_db.set(f"total-{self.request.id}", total_steps)

    self.update_state(state="Parsing Tracks", meta=state_meta)

    if not SpotifyPlaylist.objects.filter(id=spotify_object.id).exists():
        spotify.make_playlist(spotify_object.id, spotify_object.data, list_of_songs, self.request.id)
    else:
        playlist = SpotifyPlaylist.objects.get(id=spotify_object.id)
        id_list_local = [song['track']['id'] for song in list_of_songs]
        id_list_db = [song.id for song in playlist.tracks.all()]
        id_list_local = [i for n, i in enumerate(id_list_local) if i not in id_list_local[:n]]
        if not id_list_local.sort() == id_list_db.sort():
            playlist.delete()
            spotify.make_playlist(spotify_object.id, spotify_object.data, list_of_songs, self.request.id)

    set_progress((total_steps // 2), self.request.id)
    playlist = SpotifyPlaylist.objects.get(id=spotify_object.id)
    songs = playlist.tracks.all()

    redis_db.set(f"image-{self.request.id}", playlist.image.url)
    redis_db.set(f"current-{self.request.id}", "loading")
    increase_progress(self.request.id)

    self.update_state(state="Downloading and Zipping", meta=state_meta)

    logger.info(f"Creating download list for {playlist.name}")
    download_task_list = []
    for counter, song in enumerate(songs, 1):
        song_name = f"{str(counter)}. {song.name} [{song.artists.split(', ')[0]}]"
        task = {
            "url": make_yt_link(song.youtube_video_id),
            "name": song_name,
        }
        download_task_list.append(task)

    increase_progress(self.request.id)

    logger.info("Starting downloads")
    downloads, failures, filepath, folder = downloader(download_task_list, playlist.name, str(user_id), self.request.id)

    self.update_state(state="DONE", meta=state_meta)

    set_progress(total_steps, self.request.id)

    delete_folder.apply_async((os.path.join(folder, playlist.name),), countdown=10)
    delete_task_data.apply_async((userlog.id,), countdown=90 * 60)

    return {
        "user": str(user.id),
        "name": playlist.name,
        "path": filepath,
        "success": len(downloads),
        "fail": len(failures),
        "extra": {
            "successful_downloads": downloads,
            "failed_downloads": failures
        }
    }


@app.task(bind=True)
def spotify_track(self, user_id, url):
    user = User.objects.get(pk=user_id)
    spotify_object = Spotify("Track", url)

    set_progress(1, self.request.id)
    redis_db.set(f"total-{self.request.id}", 3)
    redis_db.set(f"image-{self.request.id}", "/static/image_loading.svg")
    redis_db.set(f"current-{self.request.id}", spotify_object.data.name)

    userlog = UserLogRecent.objects.create(
        user=user,
        task_id=self.request.id,
        name=spotify_object.data.name,
        mode="Track",
        type="Spotify",
        service_id=spotify_object.id,
        created=datetime.now(),
    )
    state_meta = {
        "name": spotify_object.data.name,
        "mode": userlog.mode,
        "service": userlog.type,
        "id": spotify_object.id
    }
    self.update_state(state="Parsing Tracks", meta=state_meta)

    logger.info('Starting Parsing process')
    track_raw = spotify_object.data.get_track_data(spotify_object.id)

    song = spotify.process_track(track_raw, 1, 1, "Single", self.request.id)

    song_name = f"{song.name} [{song.artists.split(', ')[0]}]"
    task = [{
        "url": make_yt_link(song.youtube_video_id),
        "name": song_name,
    }]

    self.update_state(state="Downloading", meta=state_meta)
    downloads, failures, filepath, folder = downloader(task, spotify_object.data.name, str(user_id), self.request.id)

    set_progress(3, self.request.id)

    delete_folder.apply_async((os.path.join(folder, song.name),), countdown=10)
    delete_task_data.apply_async((userlog.id,), countdown=90 * 60)

    return {
        "user": str(user.id),
        "name": spotify_object.data.name,
        "path": filepath,
        "success": len(downloads),
        "fail": len(failures),
        "extra": {
            "successful_downloads": downloads,
            "failed_downloads": failures
        }
    }


@app.task(bind=True)
def youtube_playlist(self, user_id, url):
    user = User.objects.get(pk=user_id)
    set_progress(0, self.request.id)
    youtube_object = YT("Playlist", url)
    youtube_object.data.get_playlist_details()
    redis_db.set(f"image-{self.request.id}", "/static/image_loading.svg")
    redis_db.set(f"current-{self.request.id}", "loading")
    redis_db.set(f"name-{self.request.id}", youtube_object.data.name)

    userlog = UserLogRecent.objects.create(
        user=user,
        task_id=self.request.id,
        name=youtube_object.data.name,
        mode="Playlist",
        type="Youtube",
        service_id=youtube_object.id,
        created=datetime.now(),
    )
    state_meta = {
        "name": youtube_object.data.name,
        "mode": userlog.mode,
        "service": userlog.type,
        "id": youtube_object.id
    }
    self.update_state(state="Getting list of Tracks", meta=state_meta)

    total_tracks = youtube_object.data.num_of_tracks
    steps = total_tracks * 2
    print(steps)

    redis_db.set(f"total-{self.request.id}", steps)
    increase_progress(self.request.id)

    self.update_state(state="Parsing Tracks", meta=state_meta)

    if not YouTubePlaylist.objects.filter(id=youtube_object.id).exists():
        youtube_object.data.get_videos(self.request.id)
        df = youtube_object.data.dataset
        #  df.dropna(inplace=True)
        df.drop_duplicates(inplace=True)
        dataset = df.to_dict()
        youtube.make_playlist(youtube_object.id, youtube_object.data.name,
                              youtube_object.data.image, dataset,
                              total_tracks, self.request.id)

    set_progress((total_tracks * 2) + 2, self.request.id)
    playlist = YouTubePlaylist.objects.get(id=youtube_object.id)
    songs = playlist.tracks.all()

    redis_db.set(f"image-{self.request.id}", playlist.image.url)
    redis_db.set(f"current-{self.request.id}", "loading")

    self.update_state(state="Downloading and Zipping", meta=state_meta)

    logger.info(f"Creating download list for {playlist.name}")
    download_task_list = []

    for counter, song in enumerate(songs, 1):
        song_name = f"{str(counter)}. {song.name} [{song.artists.split(', ')[0]}]"
        task = {
            "url": make_yt_link(song.id),
            "name": song_name,
        }
        download_task_list.append(task)

    set_progress(steps - len(download_task_list) - 1, self.request.id)
    logger.info("Starting downloads")
    downloads, failures, filepath, folder = downloader(download_task_list, playlist.name, str(user_id), self.request.id)

    self.update_state(state="DONE", meta=state_meta)

    set_progress(steps, self.request.id)

    delete_folder.apply_async((os.path.join(folder, playlist.name),), countdown=10)
    delete_task_data.apply_async((userlog.id,), countdown=90 * 60)

    return {
        "user": str(user.id),
        "name": playlist.name,
        "path": filepath,
        "success": len(downloads),
        "fail": len(failures),
        "extra": {
            "successful_downloads": downloads,
            "failed_downloads": failures
        }
    }


@app.task(bind=True)
def youtube_track(self, user_id, url):
    user = User.objects.get(pk=user_id)
    set_progress(0, self.request.id)
    youtube_object = YT("Track", url)
    redis_db.set(f"total-{self.request.id}", 3)
    youtube_object.data.get_video_details()

    redis_db.set(f"total-{self.request.id}", 3)
    redis_db.set(f"image-{self.request.id}", "/static/image_loading.svg")
    redis_db.set(f"current-{self.request.id}", youtube_object.data.name)

    userlog = UserLogRecent.objects.create(
        user=user,
        task_id=self.request.id,
        name=youtube_object.data.name,
        mode="Track",
        type="Youtube",
        service_id=youtube_object.id,
        created=datetime.now(),
    )
    state_meta = {
        "name": youtube_object.data.name,
        "mode": userlog.mode,
        "service": userlog.type,
        "id": youtube_object.id
    }
    self.update_state(state="Parsing Tracks", meta=state_meta)
    update_progress(youtube_object.data.name, self.request.id, youtube_object.data.thumbnail)
    logger.info('Starting Parsing process')
    youtube_object.data.get_artists()
    song = youtube_object.data

    task = [{
        "url": make_yt_link(song.video_id),
        "name": song.name,
    }]
    increase_progress(self.request.id)

    self.update_state(state="Downloading", meta=state_meta)

    downloads, failures, filepath, folder = downloader(task, youtube_object.data.name, str(user_id), self.request.id)

    set_progress(3, self.request.id)

    delete_folder.apply_async((os.path.join(folder, song.name),), countdown=10)
    delete_task_data.apply_async((userlog.id,), countdown=90 * 60)

    return {
        "user": str(user.id),
        "name": youtube_object.data.name,
        "path": filepath,
        "success": len(downloads),
        "fail": len(failures),
        "extra": {
            "successful_downloads": downloads,
            "failed_downloads": failures
        }
    }





    
