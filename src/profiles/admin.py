from django.contrib import admin

from .models import UserProfile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'username', 'country', 'email', 'activated', 'is_staff')
    search_fields = ('full_name', 'username', 'email')
    list_filter = ('activated', 'is_staff')


admin.site.register(UserProfile, ProfileAdmin)
