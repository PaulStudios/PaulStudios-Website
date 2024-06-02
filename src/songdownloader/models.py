import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.functions import Now

User = get_user_model()


class UserLogRecent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id = models.UUIDField(editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    mode = models.CharField(max_length=120)
    type = models.CharField(max_length=120)
    service_id = models.CharField(max_length=120)
    created = models.DateTimeField("Creation Date-Time", db_default=Now(), auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.mode}: {self.type} - {self.name}"

    class Meta:
        verbose_name = 'User Logs (Recent)'
        verbose_name_plural = 'User Logs (Recent)'


class SpotifySong(models.Model):
    id = models.CharField(max_length=120, primary_key=True)
    name = models.CharField(max_length=120)
    artists = models.CharField(db_column="artists", max_length=500)
    image = models.ImageField(upload_to="songs")
    youtube_video_id = models.CharField(max_length=120)
    created = models.DateTimeField("Creation Date-Time", db_default=Now(), auto_now_add=True)

    def __str__(self):
        return f"{self.name}  -  [{self.id}]"

    class Meta:
        verbose_name = 'Spotify Song'


class SpotifyPlaylist(models.Model):
    id = models.CharField(max_length=120, primary_key=True)
    name = models.CharField(max_length=120)
    image = models.ImageField(upload_to="playlists")
    tracks = models.ManyToManyField(SpotifySong)
    created = models.DateTimeField("Creation Date-Time", db_default=Now(), auto_now_add=True)

    def __str__(self):
        return f"{self.name}  -  [{self.id}]"

    class Meta:
        verbose_name = 'Spotify Playlist'


class UserHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    mode = models.CharField(max_length=120)
    service_id = models.CharField(max_length=120)
    created = models.DateTimeField("Creation Date-Time", db_default=Now(), auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.mode}: {self.name}"

    class Meta:
        verbose_name = 'User History'
        verbose_name_plural = 'User History'


class YouTubeSong(models.Model):
    id = models.CharField(max_length=120, primary_key=True)
    name = models.CharField(max_length=120)
    artists = models.CharField(db_column="artists", max_length=500)
    image = models.ImageField(upload_to="songs")
    created = models.DateTimeField("Creation Date-Time", db_default=Now(), auto_now_add=True)

    def __str__(self):
        return f"{self.name}  -  [{self.id}]"

    class Meta:
        verbose_name = 'YouTube Song'


class YouTubePlaylist(models.Model):
    id = models.CharField(max_length=120, primary_key=True)
    name = models.CharField(max_length=120)
    image = models.ImageField(upload_to="playlists")
    tracks = models.ManyToManyField(YouTubeSong)
    created = models.DateTimeField("Creation Date-Time", db_default=Now(), auto_now_add=True)

    def __str__(self):
        return f"{self.name}  -  [{self.id}]"

    class Meta:
        verbose_name = 'YouTube Playlist'
