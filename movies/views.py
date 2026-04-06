"""
Views for the AI Movie Generator application.

This module contains all views for movies, series, and API endpoints.
"""

from openai import OpenAI
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST, require_GET

from .models import Movie, Series, Episode
from .forms import MovieCreationForm, SeriesCreationForm
from .tasks import generate_movie_task, generate_episode_task, upload_to_youtube_task


@login_required
@require_POST
def improve_description_api(request):
    """Call Groq to enhance a rough movie description into a compelling pitch."""
    try:
        data = json.loads(request.body)
        rough = data.get('description', '').strip()
        genre = data.get('genre', 'drama').strip()
        title = data.get('title', '').strip()
        
        if not rough:
            return JsonResponse({'error': 'No description provided.'}, status=400)
            
        # Initialize Groq client using the OpenAI SDK
        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        
        system_instructions = (
            "You are a professional Hollywood pitch writer. "
            "You rewrite rough movie ideas into compelling, vivid 3-5 sentence pitches. "
            "Return only the improved description text, no other commentary."
        )
        
        user_prompt = f"""Rewrite this rough {genre} movie idea titled "{title}".
Idea: "{rough}"

Make it cinema-ready, focusing on tone, characters, and stakes. Match the {genre} style perfect."""

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.85,
            max_tokens=512
        )
        
        improved = response.choices[0].message.content.strip()
        return JsonResponse({'improved': improved})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
        
    except requests.RequestException as e:
        return JsonResponse({'error': f'AI service unavailable: {str(e)}'}, status=503)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



def home(request):
    """Home page view."""
    if request.user.is_authenticated:
        return redirect('movies:dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """User dashboard showing their movies and series."""
    movies = Movie.objects.filter(user=request.user)
    series_list = Series.objects.filter(user=request.user)

    context = {
        'movies': movies,
        'series_list': series_list,
    }
    return render(request, 'movies/dashboard.html', context)


@login_required
def create_movie(request):
    """Create a new movie."""
    if request.method == 'POST':
        form = MovieCreationForm(request.POST)
        if form.is_valid():
            movie = form.save(commit=False)
            movie.user = request.user
            # Calculate scenes based on duration (30 seconds per scene)
            movie.total_scenes = movie.duration_minutes * 2
            movie.save()

            # Start background generation task
            generate_movie_task.delay(movie.id)

            messages.success(request, f'Movie "{movie.title}" is being generated!')
            return redirect('movies:movie_detail', pk=movie.id)
    else:
        form = MovieCreationForm()

    return render(request, 'movies/create.html', {'form': form, 'title': 'Create Movie'})


@login_required
def movie_detail(request, pk):
    """Movie detail view with video player and status."""
    movie = get_object_or_404(Movie, pk=pk, user=request.user)
    scenes = movie.scenes.all().order_by('scene_number')

    context = {
        'movie': movie,
        'scenes': scenes,
    }
    return render(request, 'movies/detail.html', context)


@login_required
def movie_download(request, pk):
    """Download the generated movie file."""
    movie = get_object_or_404(Movie, pk=pk, user=request.user)

    if movie.status != 'done' or not movie.video_file:
        messages.error(request, 'Movie is not ready for download.')
        return redirect('movies:movie_detail', pk=pk)

    response = FileResponse(
        open(movie.video_file.path, 'rb'),
        as_attachment=True,
        filename=f'{movie.title.replace(" ", "_")}.mp4'
    )
    return response

@login_required
@require_POST
def movie_retry(request, pk):
    """Retry generating a failed movie."""
    movie = get_object_or_404(Movie, pk=pk, user=request.user)
    
    if movie.status != 'failed':
        messages.error(request, 'Only failed movies can be retried.')
        return redirect('movies:dashboard')
        
    movie.status = 'processing'
    movie.current_scene = 0
    movie.save()
    
    # Restart the background task
    generate_movie_task.delay(movie.id)
    
    messages.success(request, f'Movie "{movie.title}" is being regenerated!')
    return redirect('movies:dashboard')
    


@login_required
@require_POST
def movie_delete(request, pk):
    """Delete a movie."""
    movie = get_object_or_404(Movie, pk=pk, user=request.user)
    movie.delete()
    messages.success(request, f'Movie "{movie.title}" has been deleted.')
    return redirect('movies:dashboard')

@login_required
@require_POST
def movie_youtube_upload(request, pk):
    """Trigger background upload to YouTube."""
    movie = get_object_or_404(Movie, pk=pk, user=request.user)
    
    if movie.status != 'done' or not movie.video_file:
        messages.error(request, 'Movie is not ready for upload.')
        return redirect('movies:movie_detail', pk=pk)
        
    upload_to_youtube_task.delay(movie.id)
    messages.info(request, f'YouTube upload started for "{movie.title}".')
    return redirect('movies:movie_detail', pk=pk)


@login_required
@require_GET
def movie_status_api(request, pk):
    """API endpoint for movie generation status."""
    movie = get_object_or_404(Movie, pk=pk, user=request.user)

    data = {
        'status': movie.status,
        'progress': movie.progress_percentage,
        'current_scene': movie.current_scene,
        'total_scenes': movie.total_scenes,
        'video_url': movie.video_file.url if movie.video_file and movie.status == 'done' else None,
    }

    return JsonResponse(data)


@login_required
def create_series(request):
    """Create a new series."""
    if request.method == 'POST':
        form = SeriesCreationForm(request.POST)
        if form.is_valid():
            series = form.save(commit=False)
            series.user = request.user
            series.save()

            messages.success(request, f'Series "{series.title}" has been created!')
            return redirect('movies:series_detail', pk=series.id)
    else:
        form = SeriesCreationForm()

    return render(request, 'movies/create_series.html', {'form': form, 'title': 'Create Series'})


@login_required
def series_detail(request, pk):
    """Series detail view with episode list."""
    series = get_object_or_404(Series, pk=pk, user=request.user)
    episodes = series.episodes.all().order_by('episode_number')

    context = {
        'series': series,
        'episodes': episodes,
    }
    return render(request, 'movies/series.html', context)


@login_required
@require_POST
def generate_episode(request, pk):
    """Generate the next episode for a series."""
    series = get_object_or_404(Series, pk=pk, user=request.user)

    # Find the next pending episode
    next_episode = series.episodes.filter(status='pending').order_by('episode_number').first()

    if not next_episode:
        messages.error(request, 'No pending episodes to generate.')
        return redirect('movies:series_detail', pk=pk)

    # Start background generation task
    generate_episode_task.delay(next_episode.id)

    messages.success(request, f'Episode {next_episode.episode_number} is being generated!')
    return redirect('movies:series_detail', pk=pk)


@login_required
def episode_detail(request, pk):
    """Episode detail view."""
    episode = get_object_or_404(Episode, pk=pk)
    # Verify user owns this episode
    if episode.series.user != request.user:
        return redirect('movies:dashboard')

    scenes = episode.scenes.all().order_by('scene_number')

    context = {
        'episode': episode,
        'series': episode.series,
        'scenes': scenes,
    }
    return render(request, 'movies/episode_detail.html', context)


@login_required
@require_GET
def episode_status_api(request, pk):
    """API endpoint for episode generation status."""
    episode = get_object_or_404(Episode, pk=pk)

    # Verify user owns this episode
    if episode.series.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    data = {
        'status': episode.status,
        'progress': episode.progress_percentage,
        'current_scene': episode.current_scene,
        'total_scenes': episode.total_scenes,
        'video_url': episode.video_file.url if episode.video_file and episode.status == 'done' else None,
    }

    return JsonResponse(data)


@login_required
def episode_download(request, pk):
    """Download the generated episode file."""
    episode = get_object_or_404(Episode, pk=pk)

    # Verify user owns this episode
    if episode.series.user != request.user:
        return redirect('movies:dashboard')

    if episode.status != 'done' or not episode.video_file:
        messages.error(request, 'Episode is not ready for download.')
        return redirect('movies:episode_detail', pk=pk)

    response = FileResponse(
        open(episode.video_file.path, 'rb'),
        as_attachment=True,
        filename=f'{episode.series.title.replace(" ", "_")}_E{episode.episode_number}.mp4'
    )
    return response