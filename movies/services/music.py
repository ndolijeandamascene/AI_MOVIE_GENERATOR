"""
Background Music Service.

This module handles fetching background music from Pixabay API.
Provides royalty-free music tracks for different genres.
"""

import os
import requests
from django.conf import settings


# Music search queries by genre
MUSIC_QUERIES = {
    'action': 'epic action cinematic',
    'thriller': 'suspense thriller dark',
    'sci_fi': 'futuristic electronic space',
    'horror': 'dark horror suspense',
    'kids_animation': 'happy cartoon kids',
    'fairy_tale': 'magical fairy tale',
    'educational': 'educational background',
    'romantic': 'romantic piano soft',
    'romantic_comedy': 'happy romantic upbeat',
    'drama': 'emotional dramatic orchestra',
    'historical': 'historical epic orchestra',
    'mystery': 'mysterious suspense jazz',
    'adventure': 'adventure epic journey',
    'comedy': 'funny comedy upbeat',
}


def get_music(genre: str, output_path: str) -> str:
    """
    Download background music for a given genre from Pixabay.

    Args:
        genre: Movie genre (determines music style)
        output_path: Path to save the music file

    Returns:
        Path to the downloaded music file

    Raises:
        Exception: If Pixabay API fails or no music found
    """
    if not settings.PIXABAY_API_KEY:
        # Return path to default music if no API key
        default_music = os.path.join(settings.MEDIA_ROOT, 'music', 'default.mp3')
        if os.path.exists(default_music):
            return default_music
        raise Exception('PIXABAY_API_KEY not configured and no default music available')

    # Get search query for genre
    query = MUSIC_QUERIES.get(genre, 'cinematic background')

    try:
        # Search Pixabay for music
        search_url = f'https://pixabay.com/api/music/'
        params = {
            'key': settings.PIXABAY_API_KEY,
            'q': query,
            'per_page': 10,
        }

        response = requests.get(search_url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data.get('hits'):
            raise Exception(f'No music found for genre: {genre}')

        # Get the first suitable music track
        for hit in data['hits']:
            # Prefer longer tracks (better for movies)
            music_url = hit.get('audio', '')

            if music_url:
                # Download the music file
                music_response = requests.get(music_url, timeout=60)
                music_response.raise_for_status()

                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Save the music file
                with open(output_path, 'wb') as f:
                    f.write(music_response.content)

                return output_path

        raise Exception('No downloadable music found')

    except requests.RequestException as e:
        raise Exception(f'Pixabay API request failed: {str(e)}')


def get_default_music_path(genre: str = None) -> str:
    """
    Get path to default music file for a genre.

    Falls back to a default file if genre-specific music is not available.

    Args:
        genre: Optional genre for specific default music

    Returns:
        Path to the default music file
    """
    music_dir = os.path.join(settings.MEDIA_ROOT, 'music')

    # Try genre-specific default
    if genre:
        genre_default = os.path.join(music_dir, f'{genre}_default.mp3')
        if os.path.exists(genre_default):
            return genre_default

    # Fall back to global default
    global_default = os.path.join(music_dir, 'default.mp3')
    if os.path.exists(global_default):
        return global_default

    return None


def download_music_tracks(genres: list = None, output_dir: str = None) -> dict:
    """
    Pre-download music tracks for all genres.

    Useful for caching music offline before movie generation.

    Args:
        genres: List of genres to download (default: all genres)
        output_dir: Directory to save music files

    Returns:
        Dictionary of genre -> file_path mappings
    """
    if genres is None:
        genres = list(MUSIC_QUERIES.keys())

    if output_dir is None:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'music')

    results = {}

    for genre in genres:
        try:
            output_path = os.path.join(output_dir, f'{genre}_default.mp3')
            results[genre] = get_music(genre, output_path)
        except Exception as e:
            results[genre] = f'Failed: {str(e)}'

    return results