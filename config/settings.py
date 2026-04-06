"""
Django settings for config project.

AI Movie Generator - Django web application for AI-powered movie generation.
"""

from pathlib import Path
import os
from decouple import config, Csv
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third party apps
    'rest_framework',
    'crispy_forms',
    'crispy_tailwind',
    'django_celery_results',

    # Local apps
    'users',
    'movies',
    
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASE_URL = config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}')

if DATABASE_URL.startswith('postgresql'):
    import dj_database_url
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (Generated videos, audio, images)
MEDIA_URL = '/media/'
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'movies:dashboard'
LOGOUT_REDIRECT_URL = 'movies:home'

# Allauth Settings
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
SOCIALACCOUNT_STORE_TOKENS = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/youtube.upload'
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
            'prompt': 'consent',
        }
    }
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# AI Service Configuration — Groq (replaces Ollama)
GROQ_API_KEY = config('GROQ_API_KEY', default='')
GROQ_MODEL = config('GROQ_MODEL', default='llama-3.3-70b-versatile')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'

# Kept for reference / fallback
OLLAMA_API_URL = config('OLLAMA_API_URL', default='http://localhost:11434/api/generate')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='llama3')

HUGGINGFACE_TOKEN = config('HUGGINGFACE_TOKEN', default='')
HUGGINGFACE_API_URL = config('HUGGINGFACE_API_URL', default='https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0')

PIXABAY_API_KEY = config('PIXABAY_API_KEY', default='')

# Stripe (Phase 2)
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')

# Genre-specific voice mapping for TTS
GENRE_VOICES = {
    'action': 'en-US-GuyNeural',
    'thriller': 'en-US-GuyNeural',
    'sci_fi': 'en-US-RogerNeural',
    'horror': 'en-GB-RyanNeural',
    'kids_animation': 'en-US-AnaNeural',
    'fairy_tale': 'en-US-JennyNeural',
    'educational': 'en-US-ChristopherNeural',
    'romantic': 'en-US-JennyNeural',
    'romantic_comedy': 'en-US-MichelleNeural',
    'drama': 'en-US-AriaNeural',
    'historical': 'en-GB-ThomasNeural',
    'mystery': 'en-GB-SoniaNeural',
    'adventure': 'en-US-EricNeural',
    'comedy': 'en-US-BrandonNeural',
}

# Pixabay music search queries by genre
GENRE_MUSIC_QUERIES = {
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