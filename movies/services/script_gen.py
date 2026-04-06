"""
Script Generation Service.

This module handles movie script generation using Groq (Llama 3.3 70B).
Groq is a free, cloud-hosted API that's dramatically faster than local models.
It uses the modern OpenAI-compatible SDK for reliability.
"""

import json
from openai import OpenAI
from django.conf import settings

# Initialize Groq client using the OpenAI SDK
try:
    client = OpenAI(
        api_key=settings.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )
except Exception:
    client = None

# Genre-specific prompt instructions (stay same)
GENRE_INSTRUCTIONS = {
    'action': 'Include car chases, fights, explosions, a hero and villain. Build tension progressively. End with epic climax.',
    'thriller': 'Include suspense, psychological tension, plot twists. Build dread slowly. End with shocking revelation.',
    'sci_fi': 'Include futuristic technology, space or advanced cities, a discovery or conflict, and scientific concepts.',
    'horror': 'Build slow dread. Include jump-scare moments, dark environments, mysterious threat. Do not make it too graphic.',
    'kids_animation': 'Use friendly animal characters. Include humor, bright colors, a simple problem to solve, and a moral lesson. Age 3-8.',
    'fairy_tale': 'Use magical creatures and settings. Include a hero journey, moral lesson, and happy ending. Age 3-10.',
    'educational': 'Include learning moments woven into the story. Make it engaging and informative. Age 5-15.',
    'romantic': 'Include meet-cute, misunderstanding, emotional separation, and happy reunion. Warm, emotional tone.',
    'romantic_comedy': 'Include funny meet-cute, humorous misunderstandings, romantic tension, and happy ending. Lighthearted tone.',
    'drama': 'Focus on human relationships, emotional conflict, personal growth. Realistic settings and dialogue.',
    'historical': 'Set in a specific historical era. Use period-accurate descriptions, clothing, and language. Educational but engaging.',
    'mystery': 'Include a crime or puzzle, clues, red herrings, suspects, and a satisfying reveal at the end.',
    'adventure': 'Include exploration, discovery, journeys, obstacles to overcome, and heroic achievements.',
    'comedy': 'Include funny situations, humorous characters, witty dialogue, and comedic timing throughout.',
}


def create_movie_script(genre: str, title: str, description: str, num_scenes: int = 60) -> list:
    """
    Generate a movie script using Groq (Llama 3.3 70B).
    """
    if not client:
        raise Exception("Groq API client not initialized. Check your GROQ_API_KEY.")

    genre_instruction = GENRE_INSTRUCTIONS.get(genre, GENRE_INSTRUCTIONS['drama'])
    
    # Precise prompting for Llama 3.3 on Groq
    system_prompt = "You are a specialized screenwriting assistant. You output strictly raw JSON arrays only."
    user_prompt = f"""Write a script for a {genre} movie titled "{title}".
Premise: {description}

Requirements:
1. Output exactly {num_scenes} scenes in a JSON list.
2. Each item is like: {{"scene": index, "description": "cinematic visual description", "narration": "voiceover audio text"}}
3. Make visual descriptions extremely detailed for a movie director.
4. {genre_instruction}

Respond with only the valid JSON array."""

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=8192,
            response_format={"type": "json_object"} if "70b" in settings.GROQ_MODEL else None
        )
        
        raw_output = response.choices[0].message.content.strip()
        
        # Clean potential markdown
        if raw_output.startswith("```"):
            raw_output = raw_output.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
        
        try:
            scenes = json.loads(raw_output)
        except json.JSONDecodeError:
            # Fallback for complex outputs
            start = raw_output.find('[')
            end = raw_output.rfind(']') + 1
            scenes = json.loads(raw_output[start:end])

        # Validate structure
        if isinstance(scenes, dict) and "scenes" in scenes:
            scenes = scenes["scenes"]
            
        validated = []
        for i, s in enumerate(scenes[:num_scenes]):
            validated.append({
                "scene": s.get("scene", i + 1),
                "description": s.get("description", ""),
                "narration": s.get("narration", "")
            })
        return validated

    except Exception as e:
        raise Exception(f"AI Script Generation failed: {str(e)}")


def create_episode_script(
    series_title: str,
    genre: str,
    series_description: str,
    episode_number: int,
    total_episodes: int,
    previous_summary: str = '',
    previous_cliffhanger: str = 'The adventure begins.',
    num_scenes: int = 60
) -> tuple:
    """
    Generate an episode script with story continuity.
    """
    if not client:
        raise Exception("Groq API client not initialized.")

    system_prompt = "You are a professional TV showrunner. Ensure continuity and end with a cliffhanger."
    user_prompt = f"""Write script for Episode {episode_number}/{total_episodes} of "{series_title}".
Series Premise: {series_description}
Previously: {previous_summary}
Cliffhanger: {previous_cliffhanger}

Rules:
1. Exactly {num_scenes} scenes in JSON format.
2. End with SUMMARY and CLIFFHANGER text blocks.

Format:
[ {{"scene": 1, ...}}, ... ]
SUMMARY: ...
CLIFFHANGER: ..."""

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.75
        )
        
        full_text = response.choices[0].message.content.strip()
        
        # Extract JSON
        s_idx = full_text.find('[')
        e_idx = full_text.rfind(']') + 1
        scenes_raw = full_text[s_idx:e_idx]
        scenes = json.loads(scenes_raw)
        
        # Extract Summary/Cliffhanger
        rest = full_text[e_idx:]
        summary = rest.split("SUMMARY:")[1].split("CLIFFHANGER:")[0].strip() if "SUMMARY:" in rest else ""
        cliff = rest.split("CLIFFHANGER:")[1].strip() if "CLIFFHANGER:" in rest else ""
        
        validated = []
        for i, s in enumerate(scenes[:num_scenes]):
            validated.append({
                "scene": s.get("scene", i + 1),
                "description": s.get("description", ""),
                "narration": s.get("narration", "")
            })
            
        return validated, summary, cliff

    except Exception as e:
        raise Exception(f"Episode generation failed: {str(e)}")


# Keep original function names for compatibility if needed elsewhere
generate_script = create_movie_script
generate_episode_script = create_episode_script