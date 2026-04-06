"""
Models for the AI Movie Generator application.

This module defines the database models for movies, series, episodes, and scenes.
"""

from django.db import models
from django.contrib.auth.models import User


class Movie(models.Model):
    """
    Model for standalone movies.

    Stores all information about a single movie including its generation status,
    script, and final video file.
    """

    GENRE_CHOICES = [
        ('action', 'Action'),
        ('thriller', 'Thriller'),
        ('sci_fi', 'Sci-Fi'),
        ('horror', 'Horror'),
        ('kids_animation', 'Kids Animation'),
        ('fairy_tale', 'Fairy Tale'),
        ('educational', 'Educational'),
        ('romantic', 'Romantic'),
        ('romantic_comedy', 'Romantic Comedy'),
        ('drama', 'Drama'),
        ('historical', 'Historical'),
        ('mystery', 'Mystery'),
        ('adventure', 'Adventure'),
        ('comedy', 'Comedy'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movies')
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    script = models.TextField(blank=True, help_text='Full JSON script')
    video_file = models.FileField(upload_to='movies/', blank=True, null=True)
    youtube_id = models.CharField(max_length=100, blank=True, null=True, help_text='YouTube Video ID')
    youtube_url = models.URLField(max_length=200, blank=True, null=True)
    duration_minutes = models.IntegerField(default=30)
    total_scenes = models.IntegerField(default=60)
    current_scene = models.IntegerField(default=0, help_text='Current scene being processed')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Movie'
        verbose_name_plural = 'Movies'

    def __str__(self):
        return f"{self.title} ({self.get_genre_display()})"

    @property
    def progress_percentage(self):
        """Calculate the percentage of completion."""
        if self.status == 'done':
            return 100
        if self.status == 'pending':
            return 0
        if self.total_scenes > 0:
            return int((self.current_scene / self.total_scenes) * 100)
        return 0


class Series(models.Model):
    """
    Model for TV-style series containing multiple episodes.

    Stores the series premise and main characters for story continuity
    across episodes.
    """

    GENRE_CHOICES = Movie.GENRE_CHOICES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='series')
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES)
    description = models.TextField(help_text='Series premise and main characters')
    total_episodes = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Series'
        verbose_name_plural = 'Series'

    def __str__(self):
        return f"{self.title} ({self.total_episodes} episodes)"

    @property
    def episodes_completed(self):
        """Return the number of completed episodes."""
        return self.episodes.filter(status='done').count()


class Episode(models.Model):
    """
    Model for individual episodes within a series.

    Each episode belongs to a series and stores story continuity data
    (summary and cliffhanger) for the next episode.
    """

    STATUS_CHOICES = Movie.STATUS_CHOICES

    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='episodes')
    episode_number = models.IntegerField()
    title = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    video_file = models.FileField(upload_to='episodes/', blank=True, null=True)
    youtube_id = models.CharField(max_length=100, blank=True, null=True, help_text='YouTube Video ID')
    youtube_url = models.URLField(max_length=200, blank=True, null=True)
    story_summary = models.TextField(blank=True, help_text='Summary of this episode events')
    cliffhanger = models.TextField(blank=True, help_text='Ending hook for next episode')
    duration_minutes = models.IntegerField(default=30)
    current_scene = models.IntegerField(default=0)
    total_scenes = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['series', 'episode_number']
        verbose_name = 'Episode'
        verbose_name_plural = 'Episodes'
        unique_together = ['series', 'episode_number']

    def __str__(self):
        return f"{self.series.title} - Episode {self.episode_number}: {self.title}"

    def save(self, *args, **kwargs):
        """Auto-generate title if not provided."""
        if not self.title:
            self.title = f"Episode {self.episode_number}"
        super().save(*args, **kwargs)

    @property
    def progress_percentage(self):
        """Calculate the percentage of completion."""
        if self.status == 'done':
            return 100
        if self.status == 'pending':
            return 0
        if self.total_scenes > 0:
            return int((self.current_scene / self.total_scenes) * 100)
        return 0


class Scene(models.Model):
    """
    Model for individual scenes within a movie or episode.

    Each scene has its own image, audio, and video clip that are
    assembled into the final video.
    """

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True, related_name='scenes')
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, null=True, blank=True, related_name='scenes')
    scene_number = models.IntegerField()
    description = models.TextField(help_text='Visual description for image generation')
    narration = models.TextField(help_text='Text for voiceover')
    image_path = models.CharField(max_length=500, blank=True)
    audio_path = models.CharField(max_length=500, blank=True)
    clip_path = models.CharField(max_length=500, blank=True)
    duration_seconds = models.IntegerField(default=30)

    class Meta:
        ordering = ['movie', 'episode', 'scene_number']
        verbose_name = 'Scene'
        verbose_name_plural = 'Scenes'

    def __str__(self):
        if self.movie:
            return f"{self.movie.title} - Scene {self.scene_number}"
        elif self.episode:
            return f"{self.episode.title} - Scene {self.scene_number}"
        return f"Scene {self.scene_number}"

    @property
    def parent(self):
        """Return the parent movie or episode."""
        return self.movie or self.episode