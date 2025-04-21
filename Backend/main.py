"""
Main script for automating the creation of YouTube Shorts videos.

This script integrates various modules to fetch Twitch videos, generate
scripts,
search for stock videos, and produce final video outputs with subtitles and
audio.
"""

import os
import gpt
import search
import video
from dotenv import load_dotenv
from moviepy.config import change_settings

# mpy_config.FFMPEG_BINARY = "ffmpeg"
# mpy_config.IMAGEMAGICK_BINARY = "magick"

load_dotenv(r"C:\Users\johnb\Repos\Automate-YT-Shorts-Video-Resource-\.env")
change_settings({"IMAGEMAGICK_BINARY": os.getenv("IMAGEMAGICK_BINARY")})

try:
    from moviepy.audio.io.AudioFileClip import AudioFileClip  # type: ignore
except ImportError as exc:
    raise ImportError(
        "moviepy is required but missing type stubs. Ensure moviepy is "
        + "installed and consider using a type checker that supports dynamic "
        + "imports."
    ) from exc

ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
IMAGEMAGICK_BINARY = os.getenv("IMAGEMAGICK_BINARY")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
TWITCH_CHANNEL_ID = os.getenv("TWITCH_CHANNEL_ID")

print("TWITCH_CLIENT_ID:", TWITCH_CLIENT_ID)
print("TWITCH_ACCESS_TOKEN:", TWITCH_ACCESS_TOKEN)
print("TWITCH_CHANNEL_ID:", TWITCH_CHANNEL_ID)

if not TWITCH_CLIENT_ID or not TWITCH_ACCESS_TOKEN or not TWITCH_CHANNEL_ID:
    raise ValueError(
        "TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN, and TWITCH_CHANNEL_ID must be "
        + "set in the environment variables."
    )

# Fetch videos from Twitch
video_urls = video.fetch_twitch_videos(
    TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN, TWITCH_CHANNEL_ID
)

# Save Twitch videos locally
video_paths = video.save_video(video_urls)

if not video_paths:
    if not PEXELS_API_KEY:
        raise ValueError("PEXELS_API_KEY must be set in the environment variables.")
    TOPIC = "Default Topic for Stock Videos"
    SCRIPT = gpt.generate_script(TOPIC)
    TAGS = gpt.get_search_terms(TOPIC, 10, SCRIPT)
    links = search.search_for_stock_videos(TAGS, api_key_value=PEXELS_API_KEY)
    video_paths = video.save_video(links)
# Fetch video titles from Twitch
video_titles = video.fetch_twitch_video_titles(
    TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN, TWITCH_CHANNEL_ID
)

# Generate script and tags
TOPIC = "Twitch Streamer Zepor1 Marvel Rivals Highlights and Fails Compilation"
SCRIPT = gpt.generate_script(TOPIC)
TAGS = gpt.get_search_terms(TOPIC, 10, SCRIPT)
SCRIPT = gpt.generate_script(TOPIC)
TAGS = gpt.get_search_terms(TOPIC, 10, SCRIPT)

# Search for stock videos (optional, if needed)
if not PEXELS_API_KEY:
    raise ValueError("PEXELS_API_KEY must be set in the environment variables.")
links = search.search_for_stock_videos(TAGS, api_key_value=PEXELS_API_KEY)

video_paths = video.save_video(links)

# Generate dynamic topics and tags
for title in video_titles:
    print(f"Processing video: {title}")
    SCRIPT = gpt.generate_script(title)
    tags = gpt.get_search_terms(title, 10, SCRIPT)

    # Generate speech and subtitles
    SPEECH_FILE_PATH = video.text_to_speech(SCRIPT)
    if not ASSEMBLY_AI_API_KEY:
        raise ValueError(
            "ASSEMBLY_AI_API_KEY must be set in the environment variables."
        )

    SUBTITLE_PATH = video.generate_subtitles(SPEECH_FILE_PATH, ASSEMBLY_AI_API_KEY)

    audio_duration = AudioFileClip(SPEECH_FILE_PATH).duration
    COMBINED_VIDEO_PATH = video.combine_videos(video_paths, audio_duration)
    video.generate_video(COMBINED_VIDEO_PATH, SPEECH_FILE_PATH, SUBTITLE_PATH)
