"""
vod_ingestion.py
Modular Twitch VOD and chat ingestion logic for the pipeline.
Compatible with Windows 11 and Docker.
"""
import logging
import os
from typing import List, Optional
from Backend.content.gpt import generate_script, get_search_terms
from Backend.content.search import search_for_stock_videos

# Configure logging
logger = logging.getLogger(__name__)

# Import video editing functions
from Backend.video_editing.editor import (
    fetch_twitch_videos,
    save_video,
)


def ingest_vods(
    twitch_client_id: str,
    twitch_access_token: str,
    twitch_channel_id: str,
    pexels_api_key: Optional[str] = None,
    temp_dir: str = "temp"
) -> List[str]:
    """
    Download Twitch VODs and save them to the temp directory.
    If no VODs are found, fallback to stock videos.
    Args:
        twitch_client_id (str): Twitch API client ID.
        twitch_access_token (str): Twitch API access token.
    # Removed import statement; moved to top-level.
        List[str]: List of local video file paths.
    """
    from Backend.video_editing.editor import (
        fetch_twitch_videos,
        save_video,
    )
    # Ensure temp directory exists, create if missing
    os.makedirs(temp_dir, exist_ok=True)
    logger.info("Fetching videos from Twitch for channel %s", twitch_channel_id)
    video_urls = fetch_twitch_videos(twitch_client_id, twitch_access_token, twitch_channel_id)
    video_paths = save_video(video_urls)
    if not video_paths:
        logger.warning("No Twitch VODs found. Falling back to stock videos.")
        if not pexels_api_key:
            raise ValueError("PEXELS_API_KEY must be set for fallback stock videos.")
        topic = "Default Topic for Stock Videos"
        script = generate_script(topic)
        tags = get_search_terms(topic, 10, script)
        links = search_for_stock_videos(tags, api_key_value=pexels_api_key)
        video_paths = save_video(links)
    logger.info("Ingested %d videos.", len(video_paths))
    return video_paths
