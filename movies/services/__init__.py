"""
Services package for AI Movie Generator.

This package contains all the AI integration services:
- script_gen: Ollama/LLaMA3 script generation
- tts: edge-tts text-to-speech
- image_gen: Hugging Face image generation
- video_gen: FFmpeg video assembly
- music: Pixabay background music
"""

from .script_gen import generate_script, generate_episode_script
from .tts import generate_audio
from .image_gen import generate_image
from .video_gen import merge_scene, concat_scenes, add_music
from .music import get_music
from .youtube import upload_video_to_youtube

__all__ = [
    'generate_script',
    'generate_episode_script',
    'generate_audio',
    'generate_image',
    'merge_scene',
    'concat_scenes',
    'add_music',
    'get_music',
    'upload_video_to_youtube',
]