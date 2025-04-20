import os
import gpt
import search
import video
import moviepy.config as mpy_config  # type: ignore
from dotenv import load_dotenv

mpy_config.FFMPEG_BINARY = "ffmpeg"
mpy_config.IMAGEMAGICK_BINARY = "magick"

try:
    from moviepy.audio.io.AudioFileClip import AudioFileClip  # type: ignore
except ImportError as exc:
    raise ImportError(
        "moviepy is required but missing type stubs. Ensure moviepy is "
        "installed and consider using a type checker that supports dynamic "
        "imports."
    ) from exc

# Removed unused and problematic import for change_setting

load_dotenv(r"C:\Users\johnb\Repos\Automate-YT-Shorts-Video-Resource-\.env")

os.environ["IMAGEMAGICK_BINARY"] = os.getenv("IMAGEMAGICK_BINARY", "")

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
        "set in the environment variables."
    )

# Fetch videos from Twitch
video_urls = video.fetch_twitch_videos(
    TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN, TWITCH_CHANNEL_ID
)

# Save Twitch videos locally
video_paths = video.save_video(video_urls)

if not video_paths:
    if not PEXELS_API_KEY:
        raise ValueError(
            "PEXELS_API_KEY must be set in the environment variables."
        )
    topic = "Default Topic for Stock Videos"
    script = gpt.generate_script(topic)
    tags = gpt.get_search_terms(topic, 10, script)
    links = search.search_for_stock_videos(tags, api_key_value=PEXELS_API_KEY)
    video_paths = video.save_video(links)
# Fetch video titles from Twitch
video_titles = video.fetch_twitch_video_titles(
    TWITCH_CLIENT_ID, TWITCH_ACCESS_TOKEN, TWITCH_CHANNEL_ID
)

# Generate script and tags
topic = "Twitch Streamer Zepor1 Marvel Rivals Highlights and Fails Compilation"
script = gpt.generate_script(topic)
tags = gpt.get_search_terms(topic, 10, script)
script = gpt.generate_script(topic)
tags = gpt.get_search_terms(topic, 10, script)

# Search for stock videos (optional, if needed)
if not PEXELS_API_KEY:
    raise ValueError(
        "PEXELS_API_KEY must be set in the environment variables."
    )
links = search.search_for_stock_videos(tags, api_key_value=PEXELS_API_KEY)

video_paths = video.save_video(links)

# Generate dynamic topics and tags
for title in video_titles:
    print(f"Processing video: {title}")
    script = gpt.generate_script(title)
    tags = gpt.get_search_terms(title, 10, script)

    # Generate speech and subtitles
    speech_file_path = video.text_to_speech(script)
    if not ASSEMBLY_AI_API_KEY:
        raise ValueError(
            "ASSEMBLY_AI_API_KEY must be set in the environment variables."
        )

    subtitle_path = video.generate_subtitles(
        speech_file_path, ASSEMBLY_AI_API_KEY
    )

    audio_duration = AudioFileClip(speech_file_path).duration
    combined_video_path = video.combine_videos(video_paths, audio_duration)
    video.generate_video(combined_video_path, speech_file_path, subtitle_path)
