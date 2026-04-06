"""
Video Generation Service.

This module handles video assembly using FFmpeg.
Merges images, audio, and background music into final video files.
"""

import os
import subprocess
import tempfile
from pathlib import Path


def merge_scene(image_path: str, audio_path: str, output_path: str, duration: int = 30) -> None:
    """
    Merge a single image and audio file into a video clip.

    Creates a video by looping the image for the duration of the audio.
    Uses FFmpeg's stillimage preset for optimal quality.

    Args:
        image_path: Path to the image file (PNG/JPG)
        audio_path: Path to the audio file (MP3/WAV)
        output_path: Path to save the output video (MP4)
        duration: Duration in seconds (default: 30)

    Raises:
        Exception: If FFmpeg command fails
    """
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file
        '-loop', '1',  # Loop image
        '-i', image_path,  # Input image
        '-i', audio_path,  # Input audio
        '-c:v', 'libx264',  # Video codec
        '-tune', 'stillimage',  # Optimize for still image
        '-c:a', 'aac',  # Audio codec
        '-b:a', '192k',  # Audio bitrate
        '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
        '-t', str(duration),  # Duration
        '-shortest',  # Stop when audio ends
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        if result.returncode != 0:
            raise Exception(f'FFmpeg error: {result.stderr}')
    except subprocess.TimeoutExpired:
        raise Exception('FFmpeg timed out')
    except FileNotFoundError:
        raise Exception('FFmpeg not found. Please install FFmpeg.')


def concat_scenes(scene_clips: list, output_path: str) -> None:
    """
    Concatenate multiple scene clips into a single video.

    Uses FFmpeg concat demuxer to join all clips without re-encoding.

    Args:
        scene_clips: List of paths to scene clip files
        output_path: Path to save the concatenated video

    Raises:
        Exception: If FFmpeg command fails
    """
    # Create temporary file list for FFmpeg
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for clip in scene_clips:
            # Use forward slashes for FFmpeg compatibility
            clip_path = clip.replace('\\', '/')
            f.write(f"file '{clip_path}'\n")
        list_file = f.name

    try:
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',  # Stream copy (no re-encoding)
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        if result.returncode != 0:
            raise Exception(f'FFmpeg error: {result.stderr}')

    finally:
        # Clean up temporary file
        os.unlink(list_file)


def add_music(video_path: str, music_path: str, output_path: str, music_volume: float = 0.08) -> None:
    """
    Add background music to a video at reduced volume.

    Mixes the original audio with background music using FFmpeg's amix filter.

    Args:
        video_path: Path to the input video file
        music_path: Path to the background music file
        output_path: Path to save the output video
        music_volume: Volume level for music (0.0-1.0, default: 0.08)

    Raises:
        Exception: If FFmpeg command fails
    """
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-i', video_path,  # Input video
        '-i', music_path,  # Input music
        '-filter_complex',
        f'[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]',
        '-map', '0:v',  # Video from first input
        '-map', '[aout]',  # Mixed audio
        '-c:v', 'copy',  # Copy video stream
        '-c:a', 'aac',  # Re-encode audio
        '-b:a', '192k',  # Audio bitrate
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        if result.returncode != 0:
            raise Exception(f'FFmpeg error: {result.stderr}')
    except subprocess.TimeoutExpired:
        raise Exception('FFmpeg timed out')


def get_video_duration(video_path: str) -> float:
    """
    Get the duration of a video file in seconds.

    Args:
        video_path: Path to the video file

    Returns:
        Duration in seconds

    Raises:
        Exception: If FFmpeg command fails
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return float(result.stdout.strip())
        raise Exception(f'FFprobe error: {result.stderr}')
    except (subprocess.TimeoutExpired, ValueError) as e:
        raise Exception(f'Could not get video duration: {str(e)}')


def create_video_from_scenes(scenes: list, output_path: str, music_path: str = None) -> str:
    """
    Complete pipeline to create video from scene clips.

    Args:
        scenes: List of dictionaries with image_path, audio_path, duration
        output_path: Path for final video
        music_path: Optional background music path

    Returns:
        Path to the final video file

    Raises:
        Exception: If any step fails
    """
    temp_clips = []

    try:
        # Step 1: Create clip for each scene
        for i, scene in enumerate(scenes):
            clip_path = output_path.replace('.mp4', f'_scene_{i}.mp4')
            merge_scene(
                scene['image_path'],
                scene['audio_path'],
                clip_path,
                scene.get('duration', 30)
            )
            temp_clips.append(clip_path)

        # Step 2: Concatenate all clips
        temp_video = output_path.replace('.mp4', '_temp.mp4')
        concat_scenes(temp_clips, temp_video)

        # Step 3: Add background music if provided
        if music_path:
            add_music(temp_video, music_path, output_path)
            os.unlink(temp_video)  # Remove temp file
        else:
            os.rename(temp_video, output_path)

        return output_path

    finally:
        # Clean up temporary clip files
        for clip in temp_clips:
            if os.path.exists(clip):
                os.unlink(clip)