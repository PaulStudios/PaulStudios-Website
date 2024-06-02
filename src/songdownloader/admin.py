from django.contrib import admin
from .models import SpotifySong, SpotifyPlaylist, UserHistory, YouTubeSong, YouTubePlaylist


class SongAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'artists', 'image')
    search_fields = ('name', 'id')


class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'image')
    search_fields = ('name', 'id')


admin.site.register(SpotifySong, SongAdmin)
admin.site.register(SpotifyPlaylist, PlaylistAdmin)
admin.site.register(YouTubeSong, SongAdmin)
admin.site.register(YouTubePlaylist, PlaylistAdmin)
admin.site.register(UserHistory)
