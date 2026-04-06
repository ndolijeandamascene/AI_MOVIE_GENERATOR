"""
Image Generation Service.

This module handles AI image generation using Hugging Face
Stable Diffusion API for free scene images.
"""

import time
import requests
from django.conf import settings


def generate_image(description: str, output_path: str, genre: str = 'action', max_retries: int = 5) -> None:
    """
    Generate an image from a text description using Hugging Face API.

    Args:
        description: Text description of the image to generate
        output_path: Path to save the generated image
        genre: The movie genre to stylize the image prompt
        max_retries: Maximum number of retries on model loading

    Raises:
        Exception: If image generation fails after all retries
    """
    if not settings.HUGGINGFACE_TOKEN:
        raise Exception('HUGGINGFACE_TOKEN not configured in settings')

    enhanced_prompt = enhance_prompt(description, genre)

    headers = {
        'Authorization': f'Bearer {settings.HUGGINGFACE_TOKEN}',
    }

    payload = {
        'inputs': enhanced_prompt,

        'options': {
            'wait_for_model': True,
        }
    }

    retry_count = 0

    while retry_count < max_retries:
        try:
            response = requests.post(
                settings.HUGGINGFACE_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                # Save the image
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return

            elif response.status_code == 503:
                # Model is loading, wait and retry
                retry_count += 1
                wait_time = 20 * retry_count  # Progressive backoff
                time.sleep(wait_time)
                continue

            elif response.status_code == 429:
                # Rate limited, wait and retry
                retry_count += 1
                time.sleep(30)
                continue

            else:
                raise Exception(f'Image generation failed: HTTP {response.status_code} - {response.text}')

        except requests.RequestException as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise Exception(f'Image generation failed after {max_retries} retries: {str(e)}')
            time.sleep(10)

    raise Exception(f'Image generation failed after {max_retries} retries')


def enhance_prompt(description: str, genre: str = 'action') -> str:
    """
    Enhance a scene description for better image generation.

    Adds style keywords based on genre for better Stable Diffusion results.

    Args:
        description: Original scene description
        genre: Movie genre

    Returns:
        Enhanced prompt with style keywords
    """
    # Genre-specific style enhancements
    genre_styles = {
        'action': 'cinematic, dramatic lighting, action movie still, 4k, high detail',
        'thriller': 'cinematic, dark atmosphere, suspenseful, dramatic shadows, 4k',
        'sci_fi': 'futuristic, sci-fi, cinematic, detailed, 4k, digital art',
        'horror': 'dark, atmospheric, horror movie, dramatic shadows, 4k',
        'kids_animation': 'colorful, bright, cartoon style, animated, whimsical, 4k',
        'fairy_tale': 'magical, fantasy art, ethereal, enchanted, beautiful, 4k',
        'educational': 'clean, bright, educational, clear composition, 4k',
        'romantic': 'soft lighting, romantic, warm colors, cinematic, beautiful, 4k',
        'romantic_comedy': 'bright, cheerful, romantic comedy, warm, cinematic, 4k',
        'drama': 'cinematic, dramatic lighting, emotional, film still, 4k',
        'historical': 'period accurate, historical, cinematic, detailed costumes, 4k',
        'mystery': 'noir style, mysterious, dramatic lighting, cinematic, 4k',
        'adventure': 'epic, cinematic, adventure, dramatic landscape, 4k, detailed',
        'comedy': 'bright, cheerful, comedic, colorful, cinematic, 4k',
    }

    style = genre_styles.get(genre, genre_styles['action'])

    # Combine description with style
    enhanced = f'{description}, {style}'

    # Limit prompt length (Stable Diffusion works best with ~75 tokens)
    if len(enhanced) > 500:
        enhanced = enhanced[:500]

    return enhanced