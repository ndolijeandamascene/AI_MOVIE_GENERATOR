# 🎬 AI Movie Generator

> A powerful Django web application that automatically generates full-length movies and multi-episode series using 100% free AI tools — no paid API subscriptions required.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
- [Supported Genres](#supported-genres)
- [Video Generation Pipeline](#video-generation-pipeline)
- [AI Script Prompts](#ai-script-prompts)
- [Free API Services](#free-api-services)
- [URL Structure](#url-structure)
- [Background Tasks (Celery)](#background-tasks-celery)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Requirements](#requirements)
- [Monetization Strategy](#monetization-strategy)
- [Quick AI Prompt Reference](#quick-ai-prompt-reference)

---

## Project Overview

AI Movie Generator lets users create complete 30-minute movies automatically. The user selects a genre, provides a title and description, and the system generates a full movie including script, voiceover, images, and final video — all assembled without any human editing.

The platform supports standalone movies and multi-episode series with story continuity between episodes. Everything runs on free tools so you can start building with zero budget.

---

## Key Features

| Feature | Description | Status |
|---|---|---|
| Movie Generation | Auto-generate full 30-min movies from a title | ✅ Core |
| Episode Series | Multi-episode series with story continuity | ✅ Core |
| All Genres | Action, Kids, Romance, Horror, Sci-Fi, Drama, etc. | ✅ Core |
| AI Script | LLaMA3 via Ollama generates full scripts locally | ✅ Core |
| AI Voiceover | edge-tts provides free high-quality narration | ✅ Core |
| AI Images | Hugging Face Stable Diffusion for scene images | ✅ Core |
| Video Assembly | FFmpeg merges all assets into final MP4 | ✅ Core |
| Background Music | Pixabay free music API per genre | ✅ Core |
| User Accounts | Register, login, manage movies | ✅ Core |
| Admin Dashboard | Django admin to manage all content | ✅ Core |
| Download Movies | Users can download generated MP4 files | ✅ Core |
| YouTube Upload | Auto-upload to YouTube via API | 🔜 Phase 2 |
| Payments | Stripe subscriptions for premium users | 🔜 Phase 2 |

---

## Technology Stack

> Everything below is 100% free. No credit card needed to start.

| Layer | Technology | Purpose |
|---|---|---|
| Backend Framework | Django 4.x + DRF | Web server, API, admin panel |
| Database | PostgreSQL | Store users, movies, scenes |
| Task Queue | Celery + Redis | Background video rendering |
| AI Script | Ollama + LLaMA3 | Generate movie scripts locally |
| Text-to-Speech | edge-tts (Microsoft) | Voiceover for all scenes |
| Image Generation | Hugging Face Inference API | AI images per scene |
| Video Assembly | FFmpeg | Merge audio, images, music |
| Background Music | Pixabay API | Royalty-free music per genre |
| File Storage | Local / Cloudflare R2 | Store generated videos |
| Hosting | Local server / Railway | Serve the web app |
| Frontend | Django Templates + Tailwind CSS | User interface |
| Payments (Phase 2) | Stripe | Subscription billing |

---

## Project Structure

```
movie_generator/
│
├── manage.py
├── requirements.txt
├── .env
│
├── config/                     # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── celery.py               # Background task config
│
├── users/                      # Authentication app
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/users/
│       ├── login.html
│       └── register.html
│
├── movies/                     # Core movie generation app
│   ├── models.py               # Movie, Series, Episode, Scene
│   ├── views.py                # Generate, list, detail views
│   ├── urls.py
│   ├── tasks.py                # Celery background tasks
│   ├── admin.py                # Django admin configuration
│   └── services/
│       ├── script_gen.py       # Ollama → script generation
│       ├── tts.py              # edge-tts → audio files
│       ├── image_gen.py        # Hugging Face → scene images
│       ├── video_gen.py        # FFmpeg → final video
│       └── music.py            # Pixabay → background music
│
├── templates/                  # HTML templates
│   ├── base.html
│   ├── home.html
│   └── movies/
│       ├── create.html         # Movie creation form
│       ├── list.html           # User's movie library
│       ├── detail.html         # Movie player + status
│       └── series.html         # Series + episode list
│
├── static/                     # CSS, JS, assets
│   ├── css/style.css
│   ├── js/app.js
│   └── music/                  # Default background music
│
└── media/                      # Generated files (git ignored)
    ├── movies/                 # Final movie MP4 files
    ├── episodes/               # Final episode MP4 files
    ├── clips/                  # Temporary scene clips
    └── audio/                  # Temporary audio files
```

---

## Database Models

### Movie Model
Stores all standalone movies.

```python
class Movie(models.Model):
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

    user             = models.ForeignKey(User, on_delete=models.CASCADE)
    title            = models.CharField(max_length=200)
    genre            = models.CharField(max_length=50, choices=GENRE_CHOICES)
    description      = models.TextField()
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    script           = models.TextField(blank=True)       # Full JSON script
    video_file       = models.FileField(upload_to='movies/', blank=True)
    duration_minutes = models.IntegerField(default=30)
    total_scenes     = models.IntegerField(default=60)
    created_at       = models.DateTimeField(auto_now_add=True)
    completed_at     = models.DateTimeField(null=True, blank=True)
```

### Series Model
Stores TV-style series containing multiple episodes.

```python
class Series(models.Model):
    user             = models.ForeignKey(User, on_delete=models.CASCADE)
    title            = models.CharField(max_length=200)
    genre            = models.CharField(max_length=50)
    description      = models.TextField()                 # Series premise + main characters
    total_episodes   = models.IntegerField(default=10)
    created_at       = models.DateTimeField(auto_now_add=True)
```

### Episode Model
Each episode belongs to a series and stores story continuity data.

```python
class Episode(models.Model):
    series           = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='episodes')
    episode_number   = models.IntegerField()
    title            = models.CharField(max_length=200)
    status           = models.CharField(max_length=20, default='pending')
    video_file       = models.FileField(upload_to='episodes/', blank=True)
    story_summary    = models.TextField(blank=True)       # Summary of this episode's events
    cliffhanger      = models.TextField(blank=True)       # Ending hook for next episode
    duration_minutes = models.IntegerField(default=30)
```

### Scene Model
Each movie/episode is divided into 60 scenes. Each scene has its own image, audio, and clip.

```python
class Scene(models.Model):
    movie            = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    episode          = models.ForeignKey(Episode, on_delete=models.CASCADE, null=True, blank=True)
    scene_number     = models.IntegerField()
    description      = models.TextField()                 # Visual description for image generation
    narration        = models.TextField()                 # Text for voiceover
    image_path       = models.CharField(max_length=500, blank=True)
    audio_path       = models.CharField(max_length=500, blank=True)
    clip_path        = models.CharField(max_length=500, blank=True)
    duration_seconds = models.IntegerField(default=30)
```

---

## Supported Genres

| Genre Key | Display Name | Description | Audience |
|---|---|---|---|
| `action` | Action | Heroes, villains, car chases, explosions | Adults 18+ |
| `thriller` | Thriller | Suspense, psychological tension, plot twists | Adults 18+ |
| `sci_fi` | Sci-Fi | Futuristic tech, space, robots, AI | All ages |
| `horror` | Horror | Scary, suspenseful, dark atmosphere | Adults 18+ |
| `kids_animation` | Kids Animation | Colorful, fun, moral lessons, animals | Kids 3-12 |
| `fairy_tale` | Fairy Tale | Classic fairy tales reimagined | Kids 3-10 |
| `educational` | Educational | Learning through stories | Kids 5-15 |
| `romantic` | Romantic | Love stories, emotional depth | Adults 18+ |
| `romantic_comedy` | Rom-Com | Funny and heartwarming romance | Adults 18+ |
| `drama` | Drama | Deep human emotional stories | Adults 18+ |
| `historical` | Historical | Stories set in past eras | All ages |
| `mystery` | Mystery | Detective stories, clues, reveals | Adults 18+ |
| `adventure` | Adventure | Exploration, discovery, journeys | All ages |
| `comedy` | Comedy | Funny situations and characters | All ages |

---

## Video Generation Pipeline

Video generation runs in the background using Celery. Users can close their browser and the job continues running.

```
User submits form (genre + title + description)
              │
              ▼
Django creates Movie record (status=pending)
              │
              ▼
Celery task triggered in background
              │
              ▼
┌─────────────────────────────────────┐
│         FOR EACH SCENE (60x)        │
│                                     │
│  Ollama LLaMA3 → JSON script        │
│         │                           │
│         ▼                           │
│  edge-tts → voiceover .mp3          │
│         │                           │
│         ▼                           │
│  Hugging Face → scene image .png    │
│         │                           │
│         ▼                           │
│  FFmpeg → merge into clip .mp4      │
└─────────────────────────────────────┘
              │
              ▼
FFmpeg concatenates all 60 clips
              │
              ▼
FFmpeg adds background music (10% volume)
              │
              ▼
Final MP4 saved → status = done
              │
              ▼
User notified → preview / download
```

### Estimated Generation Time

| Movie Length | Scenes | Est. Time (Local PC) | Est. Time (Server) |
|---|---|---|---|
| 10 minutes | 20 scenes | 10-15 minutes | 5-8 minutes |
| 30 minutes | 60 scenes | 30-45 minutes | 15-20 minutes |
| 60 minutes | 120 scenes | 60-90 minutes | 30-45 minutes |

---

## AI Script Prompts

### Standard Movie Prompt Template

```
You are a professional screenwriter. Write a {duration}-minute {genre} movie script.
Title: {title}
Description: {description}

Rules:
- Create exactly {num_scenes} scenes
- Each scene is approximately {seconds_per_scene} seconds long
- Each narration should be 2-4 sentences of spoken text
- Visual descriptions should be detailed for image generation
- Return ONLY a valid JSON array, no other text

Format:
[{"scene": 1, "description": "detailed visual description", "narration": "spoken narration text"}, ...]
```

### Genre-Specific Instructions

Add these to the prompt based on selected genre:

| Genre | Add to Prompt |
|---|---|
| Action | Include car chases, fights, explosions, a hero and villain. Build tension progressively. End with epic climax. |
| Kids Animation | Use friendly animal characters. Include humor, bright colors, a simple problem to solve, and a moral lesson. Age 3-8. |
| Romantic | Include meet-cute, misunderstanding, emotional separation, and happy reunion. Warm, emotional tone. |
| Horror | Build slow dread. Include jump-scare moments, dark environments, mysterious threat. Do not make it too graphic. |
| Sci-Fi | Include futuristic technology, space or advanced cities, a discovery or conflict, and scientific concepts. |
| Mystery | Include a crime or puzzle, clues, red herrings, suspects, and a satisfying reveal at the end. |
| Drama | Focus on human relationships, emotional conflict, personal growth. Realistic settings and dialogue. |
| Historical | Set in [era]. Use period-accurate descriptions, clothing, and language. Educational but engaging. |

### Episode Continuity Prompt

```
You are writing Episode {episode_number} of {total_episodes} of a series called '{series_title}'.
Genre: {genre}
Series description: {series_description}

Previous episode summary: {previous_summary}
Previous episode cliffhanger: {previous_cliffhanger}

Write this episode continuing from the cliffhanger above.
Rules:
- Create exactly 60 scenes
- Continue character development from previous episodes
- End with a new cliffhanger for the next episode
- After the JSON array, add:
  SUMMARY: [2-3 sentences summarizing this episode]
  CLIFFHANGER: [1 sentence ending hook for next episode]

Format:
[{"scene": 1, "description": "...", "narration": "..."}, ...]
SUMMARY: ...
CLIFFHANGER: ...
```

---

## Free API Services

### 1. Ollama — Script Generation (Local AI)

- **Website:** https://ollama.ai
- **Cost:** 100% free, runs on your computer
- **Best models:** `llama3`, `mistral`, `phi3`
- **API endpoint:** `http://localhost:11434/api/generate`

```bash
# Install
curl -fsSL https://ollama.ai/install.sh | sh

# Download model
ollama pull llama3
```

```python
# movies/services/script_gen.py
import requests, json

def generate_script(genre, title, description, num_scenes=60):
    prompt = build_prompt(genre, title, description, num_scenes)
    response = requests.post('http://localhost:11434/api/generate', json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    })
    raw = response.json()['response']
    return json.loads(raw)
```

### 2. edge-tts — Text to Speech (Free)

- **Cost:** 100% free, uses Microsoft Neural voices
- **No API key needed**
- **300+ voices in many languages**

```bash
pip install edge-tts
```

```python
# movies/services/tts.py
import edge_tts, asyncio

VOICES = {
    'action':    'en-US-GuyNeural',       # Deep, dramatic
    'horror':    'en-GB-RyanNeural',      # Dark tone
    'kids_animation': 'en-US-AnaNeural', # Cheerful
    'romantic':  'en-US-JennyNeural',    # Warm, emotional
    'drama':     'en-US-AriaNeural',     # Expressive
}

async def generate_audio(text, output_path, genre='action'):
    voice = VOICES.get(genre, 'en-US-GuyNeural')
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def tts(text, output_path, genre):
    asyncio.run(generate_audio(text, output_path, genre))
```

### 3. Hugging Face — Image Generation (Free)

- **Website:** https://huggingface.co
- **Cost:** Free tier with rate limits
- **Get free token:** https://huggingface.co/settings/tokens
- **Best free model:** `stabilityai/stable-diffusion-2`

```python
# movies/services/image_gen.py
import requests
from django.conf import settings

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"

def generate_image(description, output_path):
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_TOKEN}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": description})
    with open(output_path, 'wb') as f:
        f.write(response.content)
```

### 4. FFmpeg — Video Assembly (Free Forever)

- **Cost:** 100% free, open source
- **No limits — process unlimited videos**

```bash
# Install on Ubuntu
sudo apt install ffmpeg
```

```python
# movies/services/video_gen.py
import subprocess

def merge_scene(image_path, audio_path, output_path, duration=30):
    """Merge one image + audio into a video clip"""
    subprocess.run([
        'ffmpeg', '-loop', '1',
        '-i', image_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-t', str(duration),
        '-y', output_path
    ])

def concat_scenes(scene_clips, output_path):
    """Concatenate all scene clips into one movie"""
    list_file = '/tmp/scene_list.txt'
    with open(list_file, 'w') as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")
    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', list_file, '-c', 'copy', '-y', output_path
    ])

def add_music(video_path, music_path, output_path):
    """Mix background music at low volume"""
    subprocess.run([
        'ffmpeg',
        '-i', video_path,
        '-i', music_path,
        '-filter_complex', '[1:a]volume=0.08[music];[0:a][music]amix=inputs=2:duration=first',
        '-c:v', 'copy',
        '-y', output_path
    ])
```

### 5. Pixabay — Background Music (Free)

- **Website:** https://pixabay.com/api/docs/
- **Cost:** Free with API key
- **Get free key:** https://pixabay.com/api/docs/

```python
# movies/services/music.py
import requests
from django.conf import settings

MUSIC_QUERIES = {
    'action':         'epic action cinematic',
    'horror':         'dark horror suspense',
    'kids_animation': 'happy cartoon kids',
    'romantic':       'romantic piano soft',
    'drama':          'emotional dramatic orchestra',
    'sci_fi':         'futuristic electronic space',
    'mystery':        'mysterious suspense jazz',
}

def get_music(genre, output_path):
    query = MUSIC_QUERIES.get(genre, 'cinematic background')
    url = f"https://pixabay.com/api/videos/music/?key={settings.PIXABAY_API_KEY}&q={query}&per_page=3"
    results = requests.get(url).json()
    music_url = results['hits'][0]['audio']
    audio = requests.get(music_url).content
    with open(output_path, 'wb') as f:
        f.write(audio)
```

---

## URL Structure

```python
# config/urls.py
urlpatterns = [
    path('admin/',                          admin.site.urls),
    path('',                                views.home,              name='home'),
    path('register/',                       views.register,          name='register'),
    path('login/',                          views.login_view,        name='login'),
    path('logout/',                         views.logout_view,       name='logout'),
    path('dashboard/',                      views.dashboard,         name='dashboard'),

    # Standalone movies
    path('movies/create/',                  views.create_movie,      name='create_movie'),
    path('movies/<int:id>/',               views.movie_detail,      name='movie_detail'),
    path('movies/<int:id>/download/',      views.download_movie,    name='download_movie'),
    path('movies/<int:id>/delete/',        views.delete_movie,      name='delete_movie'),

    # Series and episodes
    path('series/create/',                  views.create_series,     name='create_series'),
    path('series/<int:id>/',               views.series_detail,     name='series_detail'),
    path('series/<int:id>/episode/next/',  views.gen_episode,       name='gen_episode'),

    # AJAX status polling
    path('api/status/<int:id>/',           views.movie_status_api,  name='movie_status'),
]
```

---

## Background Tasks (Celery)

```python
# movies/tasks.py
from celery import shared_task
from .models import Movie, Episode, Scene
from .services import script_gen, tts, image_gen, video_gen, music
import os

@shared_task
def generate_movie_task(movie_id):
    movie = Movie.objects.get(id=movie_id)
    movie.status = 'processing'
    movie.save()

    try:
        # Step 1: Generate script
        scenes_data = script_gen.generate_script(
            movie.genre, movie.title,
            movie.description, movie.total_scenes
        )

        # Step 2: Get background music
        music_path = f'media/music/movie_{movie_id}.mp3'
        music.get_music(movie.genre, music_path)

        # Step 3: Process each scene
        scene_clips = []
        for i, scene in enumerate(scenes_data):
            img_path   = f'media/clips/img_{movie_id}_{i}.png'
            audio_path = f'media/clips/audio_{movie_id}_{i}.mp3'
            clip_path  = f'media/clips/clip_{movie_id}_{i}.mp4'

            image_gen.generate_image(scene['description'], img_path)
            tts.tts(scene['narration'], audio_path, movie.genre)
            video_gen.merge_scene(img_path, audio_path, clip_path)

            scene_clips.append(clip_path)
            Scene.objects.create(
                movie=movie,
                scene_number=i + 1,
                description=scene['description'],
                narration=scene['narration'],
                image_path=img_path,
                audio_path=audio_path,
                clip_path=clip_path
            )

        # Step 4: Assemble final movie
        temp_path  = f'media/movies/temp_{movie_id}.mp4'
        final_path = f'media/movies/movie_{movie_id}.mp4'
        video_gen.concat_scenes(scene_clips, temp_path)
        video_gen.add_music(temp_path, music_path, final_path)

        # Step 5: Save and complete
        movie.video_file = final_path
        movie.status = 'done'
        movie.save()

        # Step 6: Cleanup temp files
        for clip in scene_clips:
            os.remove(clip)
        os.remove(temp_path)

    except Exception as e:
        movie.status = 'failed'
        movie.save()
        raise e


@shared_task
def generate_episode_task(episode_id):
    episode = Episode.objects.get(id=episode_id)
    series  = episode.series

    # Get previous episode for continuity
    previous = Episode.objects.filter(
        series=series,
        episode_number=episode.episode_number - 1
    ).first()

    previous_summary     = previous.story_summary if previous else 'This is episode 1.'
    previous_cliffhanger = previous.cliffhanger if previous else 'The adventure begins.'

    scenes_data, summary, cliffhanger = script_gen.generate_episode_script(
        series, episode.episode_number,
        previous_summary, previous_cliffhanger
    )

    # Same pipeline as generate_movie_task but saves to episode
    # ... (same scene loop) ...

    episode.story_summary = summary
    episode.cliffhanger   = cliffhanger
    episode.status        = 'done'
    episode.save()
```

### Task Summary

| Task | Triggered By | Description |
|---|---|---|
| `generate_movie_task` | Movie create form submit | Full pipeline for standalone movies |
| `generate_episode_task` | Episode generate button | Pipeline with story continuity for series |
| `generate_all_episodes_task` | Series creation | Queues all episodes in sequence |
| `cleanup_temp_files_task` | After movie completion | Deletes scene clips and temp audio |

---

## Installation & Setup

### Step 1 — Clone and Create Virtual Environment

```bash
git clone https://github.com/yourname/movie-generator
cd movie-generator
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Install System Dependencies

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install ffmpeg postgresql postgresql-contrib redis-server

# Install Ollama (local AI)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3
```

### Step 4 — Setup Database

```bash
sudo -u postgres psql
CREATE DATABASE moviedb;
CREATE USER movieuser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE moviedb TO movieuser;
\q
```

### Step 5 — Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Step 6 — Start All Services

Open 3 separate terminals:

```bash
# Terminal 1 — Django server
python manage.py runserver

# Terminal 2 — Celery worker
celery -A config worker --loglevel=info

# Terminal 3 — Redis
redis-server
```

Visit `http://127.0.0.1:8000` to open the app.

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://movieuser:yourpassword@localhost/moviedb

# Free APIs
HUGGINGFACE_TOKEN=your-free-hf-token-from-huggingface.co
PIXABAY_API_KEY=your-free-key-from-pixabay.com

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Storage
MEDIA_ROOT=/path/to/your/project/media
MEDIA_URL=/media/

# Phase 2 — Payments (optional)
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
```

---

## Requirements

```txt
# requirements.txt

# Core
django>=4.2
djangorestframework
python-dotenv
whitenoise

# Database
psycopg2-binary

# Background tasks
celery
redis
django-celery-results

# AI & Media
edge-tts
requests
pillow

# Storage
boto3
django-storages

# Payments (Phase 2)
stripe

# Utilities
python-decouple
django-crispy-forms
crispy-tailwind
```

---

## Monetization Strategy

### Phase 1 — Build Free (Months 1-2)

- Build and test the full app locally using free tools
- Generate sample movies in all genres for testing
- Create a YouTube Kids channel and upload kids animation videos
- Create separate channels for romantic movies and action movies
- Apply for YouTube monetization (need 1,000 subscribers + 4,000 watch hours)

### Phase 2 — First Revenue (Months 2-4)

- Offer movie generation as a Fiverr service ($5-$20 per video)
- Launch the app publicly with a free tier (2 movies/month free)
- Add Stripe payments for premium plans
- Start earning from YouTube ad revenue

### Phase 3 — Scale (Month 4+)

- Use YouTube earnings to upgrade to ElevenLabs for better voices
- Upgrade image generation to better APIs
- Add auto-YouTube-upload feature
- Target 100 paying subscribers at $15/month = $1,500/month recurring

### Pricing Plans

| Plan | Price | Movies/Month | Features |
|---|---|---|---|
| Free | $0 | 2 movies | All genres, 30 min, watermark |
| Basic | $9/month | 10 movies | All genres, 30 min, no watermark |
| Pro | $29/month | 50 movies | All genres, 60 min, series support |
| Unlimited | $59/month | Unlimited | Everything + YouTube auto-upload |

---

## Quick AI Prompt Reference

Use these prompts when asking an AI assistant to help you build each part of the project.

### Script Generation Service

```
Build a Django service in movies/services/script_gen.py that calls Ollama LLaMA3
at localhost:11434 to generate a movie script. Accept genre, title, description,
and num_scenes as parameters. Return a list of scene dicts with scene_number,
description, and narration fields. Use genre-specific prompt instructions.
Handle JSON parsing errors gracefully.
```

### TTS Service

```
Build a Django service in movies/services/tts.py using the edge-tts Python library.
Accept text, output_filepath, and genre as parameters. Select the appropriate
Microsoft Neural voice based on genre: en-US-GuyNeural for action/thriller,
en-US-AnaNeural for kids, en-US-JennyNeural for romantic, en-GB-RyanNeural for horror.
Use asyncio.run() to call the async edge-tts function synchronously.
```

### Image Generation Service

```
Build a Django service in movies/services/image_gen.py that calls the Hugging Face
Inference API to generate images using stabilityai/stable-diffusion-2. Accept a scene
description and output file path. Read the HuggingFace token from Django settings.
Save the returned image bytes to the output path. Add a retry mechanism for when
the model is loading (503 response).
```

### Video Assembly Service

```
Build a Django service in movies/services/video_gen.py using Python subprocess to
call FFmpeg. Include three functions:
1. merge_scene(image, audio, output, duration=30) — create a video clip from image + audio
2. concat_scenes(clip_list_file, output) — join all clips into one video
3. add_music(video, music, output) — mix background music at 8% volume using amix filter
All functions should use -y flag to overwrite output files without asking.
```

### Celery Task

```
Build a Celery task in movies/tasks.py called generate_movie_task that accepts a movie_id.
Steps: set movie status to processing → call script_gen to get scenes → loop through
scenes calling tts and image_gen for each → call video_gen to merge each scene into a clip
→ concat all clips → add background music → save final video path to the Movie model →
set status to done. Wrap in try/except and set status to failed on any exception.
Create a second task generate_episode_task that does the same but reads the previous
episode summary and cliffhanger for story continuity.
```

### Django Models

```
Build Django models in movies/models.py for a movie generator app. Create four models:
Movie (with genre choices for action/thriller/sci_fi/horror/kids_animation/fairy_tale/
educational/romantic/romantic_comedy/drama/historical/mystery/adventure/comedy,
status choices for pending/processing/done/failed, and fields for user, title,
description, script, video_file, duration_minutes, total_scenes, created_at, completed_at),
Series (user, title, genre, description, total_episodes),
Episode (ForeignKey to Series, episode_number, title, status, video_file,
story_summary for continuity, cliffhanger for next episode),
Scene (ForeignKey to either Movie or Episode, scene_number, description, narration,
image_path, audio_path, clip_path, duration_seconds).
```

### Status Polling (AJAX)

```
Build a Django view and JavaScript for real-time movie generation status updates.
The view at /api/status/<movie_id>/ should return JSON with fields: status, progress
percentage, current_scene, total_scenes, and video_url when done. The JavaScript
should poll this endpoint every 5 seconds using fetch(), update a progress bar,
and redirect to the movie detail page when status becomes done.
```

---

## Notes

- **Your fiber internet is a major advantage** — you can run Ollama and Stable Diffusion locally and serve to the world with no bandwidth limits slowing you down.
- **Kids Animation is the most profitable YouTube niche** — start there first for fastest monetization.
- **One Celery worker handles one video at a time** — scale by adding more workers as you grow.
- **All temp files (clips, audio) are deleted after final movie is assembled** to save disk space.
- **Status polling** — use JavaScript `setInterval` to check `/api/status/<id>/` every 5 seconds and show a live progress bar to the user.

---

*AI Movie Generator — v1.0 | Django + FFmpeg + Ollama + edge-tts + Hugging Face | 100% Free Stack*
