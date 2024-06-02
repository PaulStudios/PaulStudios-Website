import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from googleapiclient.discovery import build
from lyrics_extractor import SongLyrics

from PaulStudios import settings
from base.tasks import increase_progress, update_progress
from songdownloader.models import YouTubeSong, YouTubePlaylist
from songdownloader.services.downloader import process_image

logger = logging.getLogger("Services.Youtube")
GCS_API_KEY = settings.GCS_API_KEY
GCS_ENGINE_ID = settings.GCS_ENGINE_ID
api_key = settings.YT_API_KEY


class HashTable:
    def __init__(self):
        self.table = {}

    def insert(self, word):
        self.table[word] = True

    def lookup(self, word):
        return word in self.table


word_list = HashTable()


def set_word_list():
    r1 = requests.get('https://raw.githubusercontent.com/dolph/dictionary/master/enable1.txt')
    r2 = requests.get('https://raw.githubusercontent.com/wordnik/wordlist/main/wordlist-20210729.txt')
    r3 = requests.get('https://raw.githubusercontent.com/dwyl/english-words/master/words.txt')
    r4 = requests.get(
        'https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english.txt')
    r5 = requests.get('https://raw.githubusercontent.com/sindresorhus/word-list/main/words.txt')
    if r1.status_code != 200 or r2.status_code != 200 or r3.status_code != 200 or r4.status_code != 200 or r5.status_code != 200:
        logger.error("Error getting word list")
        raise Exception("Error getting word list")
    text = r1.text + r2.text + r3.text + r4.text + r5.text
    words_array = text.split('\n')
    for word in words_array:
        word_list.insert(word)


def _extract_artist(title, description, tags):
    # Extract artist from description first
    description_patterns = [
        r"artist: (.+)",  # Look for "Artist: Artist Name"
        r"singer: (.+)",  # Look for "Singer: Artist1, Artist2"
        r"singer : (.+)",  # Look for "SINGER : Artist Name"
        r"singer - (.+)",  # Look for "SINGER - Artist Name"
        r"music: (.+)",  # Look for "MUSIC: Artist Name"
        r"music : (.+)",  # Look for "Music : Artist Name"
        r"by (.+)",  # Look for "by Artist" in description
    ]

    description_lines = description.split('\n')
    for line in description_lines:
        for pattern in description_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                artist_name = match.group(1).strip()
                for word in artist_name.split(' '):
                    if word_list.lookup(word.lower()):
                        return "Unknown"      # Return None if artist name is a common English word
                    return artist_name

    # Attempt to extract artist from the title using various patterns
    title_patterns = [
        r"(.+) \| (.+)$",  # Pattern like 'Title | Artist'
        r"(.+) \| (.+) \| (.+)",  # Pattern like 'Title | Artist1 | Artist2'
        r"(.+) \| (.+) \| t-series",  # Pattern like 'Title | Artist | T-Series'
        r"\"(.+)\" by (.+)",  # Pattern like '"Song" by Artist'
        r"(.+): (.+)",  # Pattern like 'Artist: Title'
        r" - (.+)$",  # Common pattern "Title - Artist"
        r"(.+) - topic",  # YouTube's autogenerated format 'Artist - Topic'
        r"(.+) - topic",  # YouTube's autogenerated format 'Artist - Topic'
    ]

    for pattern in title_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            artist_name = match.group(2).strip() if len(match.groups()) == 2 else match.group(1).strip()
            for word in artist_name.split(' '):
                if word_list.lookup(word.lower()):
                    return "Unknown"  # Return None if artist name is a common English word
                return artist_name

        # Use tags if available
    for tag in tags:
        if "artist" in tag.lower():
            artist_name = tag.strip()
            for word in artist_name.split(' '):
                if word_list.lookup(word.lower()):
                    return "Unknown"  # Return None if artist name is a common English word
                return artist_name

    return "Unknown"  # Return None if artist name extraction fails


def _get_thumbnail_url(thumbnails):
    if not thumbnails:
        return None
    return (
            thumbnails.get('high') or
            thumbnails.get('medium') or
            thumbnails.get('default')
    )['url']


class Youtube:
    def __init__(self, mode, url):
        logger.info('Spotify initialized')
        self.api_key = settings.YT_API_KEY
        self._extract_lyrics = SongLyrics(GCS_API_KEY, GCS_ENGINE_ID)
        if mode == 'Playlist':
            self.id = self.parse_id_playlist(url)
            self.data = self.YoutubePlaylist(self.id, self.api_key)
        elif mode == 'Track':
            self.id = self.parse_id_track(url)
            self.data = self.YoutubeTrack(self.id, self.api_key)

    @staticmethod
    def parse_id_playlist(url):
        try:
            return url.split("list=")[-1].split("&")[0]
        except AttributeError as e:
            return url.split("list=")[-1]

    @staticmethod
    def parse_id_track(url):
        try:
            return url.split("v=")[-1].split("&")[0]
        except AttributeError as e:
            return url.split("v=")[-1]

    def _get_lyrics(self, track_name):
        return self._extract_lyrics.get_lyrics(track_name)

    class YoutubePlaylist:
        def __init__(self, playlist_id, api_key):
            self.playlist_id = playlist_id
            self._playlist_title = None
            self._playlist_thumbnail = None
            self.dataset = pd.DataFrame()
            self.snippet = dict()
            self._api_key = api_key
            self._api_client = build('youtube', 'v3', developerKey=self._api_key)

        def get_playlist_details(self):
            # Build the YouTube service
            youtube = self._api_client

            # Get playlist details
            playlist_request = youtube.playlists().list(
                part='snippet',
                id=self.playlist_id
            )
            playlist_response = playlist_request.execute()

            if not playlist_response['items']:
                raise ValueError("Invalid playlist ID or no items found in the playlist")

            self.snippet = playlist_response['items'][0]['snippet']

        @property
        def name(self):
            snippet = self.snippet
            playlist_title = snippet['title']
            return playlist_title

        @property
        def image(self):
            snippet = self.snippet
            playlist_thumbnails = snippet['thumbnails']
            playlist_thumbnail = (
                    playlist_thumbnails.get('high') or
                    playlist_thumbnails.get('medium') or
                    playlist_thumbnails.get('default')
            )['url']
            return playlist_thumbnail

        @property
        def num_of_tracks(self):
            youtube = self._api_client

            # Get playlist details
            playlist_request = youtube.playlists().list(
                part='contentDetails',
                id=self.playlist_id,
            )
            playlist_response = playlist_request.execute()
            n = playlist_response['items'][0]['contentDetails']['itemCount']

            return n

        def get_videos(self, task_id):
            youtube = self._api_client
            videos = []
            next_page_token = None

            while True:
                playlist_items_request = youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=self.playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                playlist_items_response = playlist_items_request.execute()

                if not playlist_items_response['items']:
                    break

                for item in playlist_items_response['items']:
                    video_title = item['snippet']['title']
                    video_id = item['contentDetails']['videoId']
                    video_thumbnail = _get_thumbnail_url(item['snippet'].get('thumbnails'))
                    video_url = f"https://www.youtube.com/watch?v={video_id}"

                    video_request = youtube.videos().list(
                        part='snippet',
                        id=video_id
                    )
                    video_response = video_request.execute()

                    # Check if the video response contains items
                    if not video_response['items']:
                        continue

                    video_description = video_response['items'][0]['snippet']['description']
                    video_tags = video_response['items'][0]['snippet'].get('tags', [])

                    artist = _extract_artist(video_title, video_description, video_tags)

                    videos.append((video_title, artist, video_thumbnail, video_url))
                    increase_progress(task_id)
                    print(video_title)


                next_page_token = playlist_items_response.get('nextPageToken')

                print(next_page_token)
                if not next_page_token:
                    break

            self.dataset = pd.DataFrame(videos, columns=['Song Title', 'Artists', 'Thumbnail', 'URL'])

    class YoutubeTrack:
        def __init__(self, track_id, api_key):
            self.video_id = track_id
            self.name = ""
            self.artist = ""
            self.thumbnail = ""
            self.snippet = dict()
            self._api_key = api_key
            self._api_client = build('youtube', 'v3', developerKey=self._api_key)

        def get_video_details(self):
            youtube = self._api_client

            request = youtube.videos().list(
                part='snippet',
                id=self.video_id
            )
            response = request.execute()
            if response['items']:
                video_info = response['items'][0]['snippet']
                self.name = video_info['title']
                self.thumbnail = _get_thumbnail_url(video_info['thumbnails'])
                return {
                    'title': video_info['title'],
                    'thumbnail': _get_thumbnail_url(video_info['thumbnails'])
                }
            else:
                return None

        def get_artists(self):
            youtube = self._api_client

            request = youtube.videos().list(
                part='snippet,contentDetails',
                id=self.video_id
            )
            response = request.execute()
            if response['items']:
                video_info = response['items'][0]['snippet']
                video_description = response['items'][0]['snippet']['description']
                video_tags = response['items'][0]['snippet'].get('tags', [])
                video_url = f"https://www.youtube.com/watch?v={self.video_id}"

                self.artist = _extract_artist(self.name, video_description, video_tags)



def parse_video_id(url):
    try:
        return url.split("v=")[-1].split("&")[0]
    except AttributeError as e:
        return url.split("v=")[-1]


def process_track(title, artists, thumbnail, url, counter, total, playlist_name, task_id):
    try:
        track_id = parse_video_id(url)
        track_name = title
        artists = artists
        logger.info(f"Parsing track: {track_name} ({counter}/{total}) [{playlist_name}]")
        if YouTubeSong.objects.filter(id=track_id).exists():
            song = YouTubeSong.objects.get(id=track_id)
        else:
            song = YouTubeSong.objects.create(
                id=track_id,
                name=track_name,
                artists=artists,
            )
            process_image(song, thumbnail)
        update_progress(song.name, task_id, song.image.url)
        return song
    except Exception as e:
        logger.error(e)
        increase_progress(task_id)
        return


def make_playlist(playlist_id, playlist_name, playlist_thumbnail, song_dataset, total_tracks, task_id):
    song_objects = []

    title = song_dataset["Song Title"]
    artists = song_dataset["Artists"]
    thumbnail = song_dataset["Thumbnail"]
    url = song_dataset["URL"]

    with ThreadPoolExecutor() as executor:
        tasks = []
        for counter, song in enumerate(range(total_tracks), 0):
            try:
                tasks.append(
                    executor.submit(process_track, title[counter],
                                    artists[counter], thumbnail[counter],
                                    url[counter], counter + 1,
                                    total_tracks, playlist_name,
                                    task_id))
            except KeyError as e:
                print(f"Failed Track: {e}")
                increase_progress(task_id)
        for task in as_completed(tasks):
            if task.result():
                song_objects.append(task.result())

    logger.info(f"Creating Playlist: {playlist_name}")
    playlist = YouTubePlaylist.objects.create(
        id=playlist_id,
        name=playlist_name,
    )
    process_image(playlist, playlist_thumbnail)

    playlist.tracks.set(song_objects)


set_word_list()
