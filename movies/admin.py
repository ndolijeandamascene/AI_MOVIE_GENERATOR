"""
Admin configuration for the movies app.
"""

from django.contrib import admin
from .models import Movie, Series, Episode, Scene


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'genre', 'status', 'duration_minutes', 'created_at')
    list_filter = ('status', 'genre', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'completed_at', 'progress_percentage')


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'genre', 'total_episodes', 'created_at')
    list_filter = ('genre', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at',)


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'series', 'episode_number', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'series__title')
    readonly_fields = ('created_at', 'completed_at', 'progress_percentage')


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ('scene_number', 'parent', 'duration_seconds')
    list_filter = ('movie', 'episode')
    search_fields = ('description', 'narration')
