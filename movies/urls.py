"""
URL configuration for the movies app.

AI Movie Generator - Movie and Series URL routing.
"""

from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Movies
    path('movies/create/', views.create_movie, name='create_movie'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('movies/<int:pk>/download/', views.movie_download, name='movie_download'),
    path('movies/<int:pk>/youtube/', views.movie_youtube_upload, name='movie_youtube_upload'),
    path('movies/<int:pk>/delete/', views.movie_delete, name='movie_delete'),
    path('movies/<int:pk>/retry/', views.movie_retry, name='movie_retry'),


    # Series
    path('series/create/', views.create_series, name='create_series'),
    path('series/<int:pk>/', views.series_detail, name='series_detail'),
    path('series/<int:pk>/generate/', views.generate_episode, name='generate_episode'),

    # Episodes
    path('episodes/<int:pk>/', views.episode_detail, name='episode_detail'),
    path('episodes/<int:pk>/download/', views.episode_download, name='episode_download'),

    # API endpoints
    path('api/status/<int:pk>/', views.movie_status_api, name='movie_status_api'),
    path('api/episode/status/<int:pk>/', views.episode_status_api, name='episode_status_api'),
    path('api/improve-description/', views.improve_description_api, name='improve_description_api'),
]