"""
Celery Background Tasks for AI Movie Generator.

This module contains all background tasks for movie and episode generation.
"""

import os
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from .models import Movie, Episode, Scene
from .services import (
    generate_script,
    generate_episode_script,
    generate_audio,
    generate_image,
    merge_scene,
    concat_scenes,
    add_music,
    get_music,
    upload_video_to_youtube,
)


@shared_task(bind=True, max_retries=3)
def generate_movie_task(self, movie_id: int) -> None:
    """
    Celery task to generate a complete movie.

    This task runs the entire movie generation pipeline:
    1. Generate script using Ollama/LLaMA3
    2. Download background music
    3. For each scene:
       - Generate image using Hugging Face
       - Generate audio using edge-tts
       - Merge into video clip using FFmpeg
    4. Concatenate all clips
    5. Add background music
    6. Save final video

    Args:
        movie_id: ID of the Movie object to generate

    Raises:
        Exception: If any step fails (movie status is set to 'failed')
    """
    try:
        movie = Movie.objects.get(id=movie_id)
        movie.status = 'processing'
        movie.save()

        # Step 1: Generate script
        scenes_data = generate_script(
            movie.genre,
            movie.title,
            movie.description,
            movie.total_scenes
        )

        # Step 2: Get background music
        music_dir = os.path.join(settings.MEDIA_ROOT, 'music')
        os.makedirs(music_dir, exist_ok=True)
        music_path = os.path.join(music_dir, f'movie_{movie_id}.mp3')

        try:
            get_music(movie.genre, music_path)
        except Exception as e:
            # Continue without music if download fails
            print(f'Warning: Could not download music: {e}')
            music_path = None

        # Step 3: Process each scene
        clips_dir = os.path.join(settings.MEDIA_ROOT, 'clips')
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(clips_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        scene_clips = []
        total_scenes = len(scenes_data)

        for i, scene_data in enumerate(scenes_data):
            # Update progress
            movie.current_scene = i + 1
            movie.save(update_fields=['current_scene'])

            scene_number = scene_data.get('scene', i + 1)
            description = scene_data.get('description', '')
            narration = scene_data.get('narration', '')

            # File paths
            img_path = os.path.join(clips_dir, f'img_{movie_id}_{i}.png')
            audio_path = os.path.join(audio_dir, f'audio_{movie_id}_{i}.mp3')
            clip_path = os.path.join(clips_dir, f'clip_{movie_id}_{i}.mp4')

            try:
                # Generate image
                generate_image(description, img_path, genre=movie.genre)

                # Generate audio
                generate_audio(narration, audio_path, genre=movie.genre)

                # Merge into clip
                merge_scene(img_path, audio_path, clip_path)

                # Save scene to database
                Scene.objects.create(
                    movie=movie,
                    scene_number=scene_number,
                    description=description,
                    narration=narration,
                    image_path=img_path,
                    audio_path=audio_path,
                    clip_path=clip_path,
                    duration_seconds=30
                )

                scene_clips.append(clip_path)

            except Exception as e:
                # Log error but continue with remaining scenes
                print(f'Error processing scene {scene_number}: {e}')
                continue

        # Step 4: Assemble final movie
        movies_dir = os.path.join(settings.MEDIA_ROOT, 'movies')
        os.makedirs(movies_dir, exist_ok=True)

        temp_path = os.path.join(movies_dir, f'temp_{movie_id}.mp4')
        final_path = os.path.join(movies_dir, f'movie_{movie_id}.mp4')

        # Concatenate all clips
        if scene_clips:
            concat_scenes(scene_clips, temp_path)

            # Add background music if available
            if music_path and os.path.exists(music_path):
                add_music(temp_path, music_path, final_path)
                os.unlink(temp_path)
            else:
                os.rename(temp_path, final_path)

            # Save video file to movie
            movie.video_file = final_path
            movie.status = 'done'
            movie.completed_at = timezone.now()
            movie.save()

        else:
            raise Exception('No scenes were successfully generated')

    except Movie.DoesNotExist:
        raise Exception(f'Movie with id {movie_id} does not exist')

    except Exception as e:
        # Mark movie as failed
        try:
            movie = Movie.objects.get(id=movie_id)
            movie.status = 'failed'
            movie.save()
        except:
            pass
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def generate_episode_task(self, episode_id: int) -> None:
    """
    Celery task to generate a complete episode with story continuity.

    This task generates an episode while maintaining story continuity
    from the previous episode in the series.

    Args:
        episode_id: ID of the Episode object to generate

    Raises:
        Exception: If any step fails
    """
    try:
        episode = Episode.objects.get(id=episode_id)
        series = episode.series

        episode.status = 'processing'
        episode.save()

        # Get previous episode for continuity
        previous = Episode.objects.filter(
            series=series,
            episode_number=episode.episode_number - 1
        ).first()

        previous_summary = previous.story_summary if previous else 'This is episode 1.'
        previous_cliffhanger = previous.cliffhanger if previous else 'The adventure begins.'

        # Step 1: Generate episode script with continuity
        scenes_data, summary, cliffhanger = generate_episode_script(
            series_title=series.title,
            genre=series.genre,
            series_description=series.description,
            episode_number=episode.episode_number,
            total_episodes=series.total_episodes,
            previous_summary=previous_summary,
            previous_cliffhanger=previous_cliffhanger,
            num_scenes=episode.total_scenes
        )

        # Step 2: Get background music
        music_dir = os.path.join(settings.MEDIA_ROOT, 'music')
        os.makedirs(music_dir, exist_ok=True)
        music_path = os.path.join(music_dir, f'episode_{episode_id}.mp3')

        try:
            get_music(series.genre, music_path)
        except Exception as e:
            print(f'Warning: Could not download music: {e}')
            music_path = None

        # Step 3: Process each scene
        clips_dir = os.path.join(settings.MEDIA_ROOT, 'clips')
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        os.makedirs(clips_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        scene_clips = []
        total_scenes = len(scenes_data)

        for i, scene_data in enumerate(scenes_data):
            # Update progress
            episode.current_scene = i + 1
            episode.save(update_fields=['current_scene'])

            scene_number = scene_data.get('scene', i + 1)
            description = scene_data.get('description', '')
            narration = scene_data.get('narration', '')

            # File paths
            img_path = os.path.join(clips_dir, f'ep_{episode_id}_img_{i}.png')
            audio_path = os.path.join(audio_dir, f'ep_{episode_id}_audio_{i}.mp3')
            clip_path = os.path.join(clips_dir, f'ep_{episode_id}_clip_{i}.mp4')

            try:
                # Generate image
                generate_image(description, img_path, genre=series.genre)

                # Generate audio
                generate_audio(narration, audio_path, genre=series.genre)

                # Merge into clip
                merge_scene(img_path, audio_path, clip_path)

                # Save scene to database
                Scene.objects.create(
                    episode=episode,
                    scene_number=scene_number,
                    description=description,
                    narration=narration,
                    image_path=img_path,
                    audio_path=audio_path,
                    clip_path=clip_path,
                    duration_seconds=30
                )

                scene_clips.append(clip_path)

            except Exception as e:
                print(f'Error processing scene {scene_number}: {e}')
                continue

        # Step 4: Assemble final episode
        episodes_dir = os.path.join(settings.MEDIA_ROOT, 'episodes')
        os.makedirs(episodes_dir, exist_ok=True)

        temp_path = os.path.join(episodes_dir, f'temp_{episode_id}.mp4')
        final_path = os.path.join(episodes_dir, f'episode_{episode_id}.mp4')

        if scene_clips:
            concat_scenes(scene_clips, temp_path)

            if music_path and os.path.exists(music_path):
                add_music(temp_path, music_path, final_path)
                os.unlink(temp_path)
            else:
                os.rename(temp_path, final_path)

            # Update episode
            episode.video_file = final_path
            episode.story_summary = summary
            episode.cliffhanger = cliffhanger
            episode.status = 'done'
            episode.completed_at = timezone.now()
            episode.save()

        else:
            raise Exception('No scenes were successfully generated')

    except Episode.DoesNotExist:
        raise Exception(f'Episode with id {episode_id} does not exist')

    except Exception as e:
        try:
            episode = Episode.objects.get(id=episode_id)
            episode.status = 'failed'
            episode.save()
        except:
            pass
        raise self.retry(exc=e, countdown=60)


@shared_task
def cleanup_temp_files_task(movie_id: int = None, episode_id: int = None) -> None:
    """
    Clean up temporary files after movie/episode generation.

    Removes temporary scene clips and audio files to save disk space.

    Args:
        movie_id: ID of movie to clean up (optional)
        episode_id: ID of episode to clean up (optional)
    """
    clips_dir = os.path.join(settings.MEDIA_ROOT, 'clips')
    audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')

    if movie_id:
        # Clean up movie temp files
        pattern = f'_{movie_id}_'
        for filename in os.listdir(clips_dir):
            if pattern in filename:
                os.unlink(os.path.join(clips_dir, filename))
        for filename in os.listdir(audio_dir):
            if pattern in filename:
                os.unlink(os.path.join(audio_dir, filename))

    elif episode_id:
        # Clean up episode temp files
        pattern = f'_ep_{episode_id}_'
        for filename in os.listdir(clips_dir):
            if pattern in filename:
                os.unlink(os.path.join(clips_dir, filename))
        for filename in os.listdir(audio_dir):
            if pattern in filename:
                os.unlink(os.path.join(audio_dir, filename))


@shared_task
def generate_all_series_episodes_task(series_id: int) -> None:
    """
    Generate all episodes for a series in sequence.

    Queues up episode generation tasks one at a time to maintain
    story continuity between episodes.

    Args:
        series_id: ID of the Series to generate episodes for
    """
    from .models import Series

    try:
        series = Series.objects.get(id=series_id)

        # Create all episodes
        for ep_num in range(1, series.total_episodes + 1):
            Episode.objects.get_or_create(
                series=series,
                episode_number=ep_num,
                defaults={
                    'title': f'Episode {ep_num}',
                    'status': 'pending'
                }
            )

        # Queue episode generation tasks
        episodes = series.episodes.all().order_by('episode_number')
        for episode in episodes:
            generate_episode_task.delay(episode.id)

    except Series.DoesNotExist:
        raise Exception(f'Series with id {series_id} does not exist')

@shared_task
def upload_to_youtube_task(movie_id: int) -> None:
    """
    Celery task to upload a compiled movie to YouTube.
    """
    movie = Movie.objects.get(id=movie_id)
    if not movie.video_file:
        return
        
    try:
        video_path = movie.video_file.path
        tags = [movie.genre, "AI generated", "Movie"]
        
        youtube_id = upload_video_to_youtube(
            video_path=video_path,
            title=movie.title,
            description=movie.description,
            tags=tags,
            user=movie.user
        )
        
        if youtube_id:
            movie.youtube_id = youtube_id
            movie.youtube_url = f"https://youtu.be/{youtube_id}"
            movie.save()
            
    except Exception as e:
        print(f"Error uploading to YouTube: {e}")
        # Could retry or log failure