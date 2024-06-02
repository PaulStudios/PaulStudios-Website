import base64
import concurrent
import logging
import os
import tempfile

import requests
from django.core.files import File
from lyrics_extractor import SongLyrics
from youtube_search import YoutubeSearch

from PaulStudios import settings
from base.tasks import increase_progress, update_progress
from songdownloader.models import SpotifyPlaylist, SpotifySong
from songdownloader.services.downloader import process_image

# Replace these with your own Spotify credentials
CLIENT_ID = settings.SONGDOWNLOADER_SPOTIFY_CLIENT_ID
CLIENT_SECRET = settings.SONGDOWNLOADER_SPOTIFY_CLIENT_SECRET
GCS_API_KEY = settings.GCS_API_KEY
GCS_ENGINE_ID = settings.GCS_ENGINE_ID

logger = logging.getLogger("Services.Spotify")


def get_track_details(track):
    try:
        track_id = track['id']
        track_name = track['name']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        album_image = track['album']['images'][0]['url']
        return track_id, track_name, album_image, artists
    except Exception as e:
        logger.warning(e)


def parse_songs(track, counter, total_tracks):
    try:
        track_id, track_name, album_image, artists = get_track_details(track['track'])
        logger.info(f"Parsing track: {track_name}  ({counter}/{total_tracks})")
        name = track_name
        if len(track_name) > 40: name = track_name[:40]
        song_name = f"{str(counter)}. {name} [{artists.split(', ')[0]}]"
        track_data = {
            'track_id': track_id,
            "url": search_song(song_name),
            'name': song_name,
            'track_name': track_name,
            'album_image': album_image,
            'artists': artists,
        }
        return track_data
    except Exception as e:
        logger.warning(e)


class Spotify:
    def __init__(self, mode, url):
        logger.info('Spotify initialized')
        self.id = self.parse_id(url)
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.access_token = self._get_access_token()
        self._extract_lyrics = SongLyrics(GCS_API_KEY, GCS_ENGINE_ID)
        if mode == 'Playlist':
            self.data = self._SpotifyPlaylist(self.id, self.access_token)
        elif mode == 'Track':
            self.data = self._SpotifyTrack(self.id, self.access_token)

    @staticmethod
    def parse_id(id):
        try:
            return id.split("/")[-1].split("?")[0]
        except AttributeError as e:
            return id.split("/")[-1]

    def _get_access_token(self):
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_headers = {
            'Authorization': 'Basic ' + base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        }
        auth_data = {
            'grant_type': 'client_credentials'
        }
        response = requests.post(auth_url, headers=auth_headers, data=auth_data)
        response_data = response.json()
        return response_data['access_token']

    def _get_lyrics(self, track_name):
        return self._extract_lyrics.get_lyrics(track_name)

    class _SpotifyTrack:
        def __init__(self, id: str, token: str):
            logger.info('Track mode selected')
            self.track_id = id
            self.access_token = token

        def get_track_data(self, playlist_id: str):
            playlist_url = f"https://api.spotify.com/v1/tracks/{playlist_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            response = requests.get(playlist_url, headers=headers)
            return response.json()

        @property
        def name(self) -> str:
            return self.get_track_data(self.track_id)['name']

    class _SpotifyPlaylist:
        def __init__(self, id: str, token: str):
            logger.info('Playlist Mode selected')
            self.playlist_id = id
            self.access_token = token
            self.track_list = []

        def get_tracks_list(self):
            logger.info('Getting list of tracks')
            playlist_url = f"https://api.spotify.com/v1/playlists/{self.playlist_id}/tracks"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            response = requests.get(playlist_url, headers=headers)
            res = response.json()
            items = res['items']
            # if res['next'] is None: return items
            while res['next']:
                response = requests.get(res['next'], headers=headers)
                res = response.json()
                items.extend(res['items'])
            res = [i for n, i in enumerate(items) if i not in items[:n]]
            for item in res:
                try:
                    if not item['track']['name'] == "":
                        self.track_list.append(item)
                except Exception as e:
                    print(e)
            return None

        @property
        def name(self):
            playlist_url = f"https://api.spotify.com/v1/playlists/{self.playlist_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            response = requests.get(playlist_url, headers=headers)
            return response.json()['name']

        @property
        def image(self):
            playlist_url = f"https://api.spotify.com/v1/playlists/{self.playlist_id}/images"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            response = requests.get(playlist_url, headers=headers)
            image_url = response.json()[0]['url']

            return image_url


def search_song(song_name):
    results = YoutubeSearch(song_name, max_results=1).to_dict()

    if results:
        video_id = results[0]['id']
        return video_id
    else:
        return None


def make_playlist(playlist_id, playlist_data, song_list, task_id):
    song_objects = []
    total_tracks = len(song_list)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_track, track['track'], counter, total_tracks, playlist_data.name, task_id)
                   for counter, track in enumerate(song_list, 1)]
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                song_objects.append(future.result())
    logger.info(f"Creating Playlist: {playlist_data.name}")
    increase_progress(task_id)
    playlist = SpotifyPlaylist.objects.create(
        id=playlist_id,
        name=playlist_data.name,
    )
    process_image(playlist, playlist_data.image)
    playlist.tracks.set(song_objects)


def process_track(track, counter, total_tracks, playlist_name, task_id):
    try:
        track_id, track_name, album_image, artists = get_track_details(track)
        logger.info(f"Parsing track: {track_name} ({counter}/{total_tracks}) [{playlist_name}]")
        name = track_name
        if len(track_name) > 40:
            name = track_name[:40]
        if SpotifySong.objects.filter(id=track_id).exists():
            song = SpotifySong.objects.get(id=track_id)
        else:
            x = search_song(f"{name}")
            if not x:
                return "None"
            song = SpotifySong.objects.create(
                id=track_id,
                name=track_name,
                artists=artists,
                youtube_video_id=x
            )
            process_image(song, album_image)
        update_progress(song.name, task_id, song.image.url)
        return song
    except Exception as e:
        logger.error(e)
        increase_progress(task_id)
        return
