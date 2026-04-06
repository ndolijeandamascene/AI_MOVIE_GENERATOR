"""
Text-to-Speech Service.

This module handles text-to-speech conversion using edge-tts
(Microsoft Neural voices) for free, high-quality narration.
"""

import asyncio
import edge_tts
from django.conf import settings


async def generate_audio_async(text: str, output_path: str, genre: str = 'action') -> None:
    """
    Generate audio file from text using edge-tts.

    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file
        genre: Movie genre (determines voice selection)
    """
    # Select voice based on genre
    voice = settings.GENRE_VOICES.get(genre, 'en-US-GuyNeural')

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_audio(text: str, output_path: str, genre: str = 'action') -> None:
    """
    Synchronous wrapper for audio generation.

    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file
        genre: Movie genre (determines voice selection)

    Raises:
        Exception: If audio generation fails
    """
    try:
        asyncio.run(generate_audio_async(text, output_path, genre))
    except Exception as e:
        raise Exception(f'Audio generation failed: {str(e)}')


# Available voices for reference (can be used for voice customization)
AVAILABLE_VOICES = {
    'en-US-GuyNeural': 'Deep, dramatic male voice (Action, Thriller)',
    'en-US-RogerNeural': 'Confident male voice (Sci-Fi)',
    'en-GB-RyanNeural': 'Dark British male voice (Horror)',
    'en-US-AnaNeural': 'Cheerful female voice (Kids Animation)',
    'en-US-JennyNeural': 'Warm female voice (Romantic, Fairy Tale)',
    'en-US-ChristopherNeural': 'Clear male voice (Educational)',
    'en-US-MichelleNeural': 'Upbeat female voice (Romantic Comedy)',
    'en-US-AriaNeural': 'Expressive female voice (Drama)',
    'en-GB-ThomasNeural': 'British male voice (Historical)',
    'en-GB-SoniaNeural': 'British female voice (Mystery)',
    'en-US-EricNeural': 'Strong male voice (Adventure)',
    'en-US-BrandonNeural': 'Friendly male voice (Comedy)',
}