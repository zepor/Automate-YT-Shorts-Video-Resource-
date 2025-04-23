"""
publish.py
Module for automating upload of final edited videos to target platforms.
Includes batch-friendly, placeholder implementations to be extended with real APIs.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Default directory where edited videos are saved
DEFAULT_EDITED_DIR = Path(__file__).parent.parent / 'video_editing' / 'edited'


def publish_video(video_path: Path, metadata: Dict[str, Any]) -> bool:
    """
    Publish a single video to a target platform.

    Args:
        video_path (Path): Path to the video file to upload.
        metadata (Dict[str, Any]): Metadata including title, description, tags, etc.

    Returns:
        bool: True if upload succeeds, False otherwise.
    """
    try:
        # Simulated upload logic for YouTube and TikTok
        logger.info("Publishing video: %s with metadata: %s", video_path, metadata)

        if "platform" not in metadata:
            logger.error("Metadata must include 'platform' key.")
            return False

        platform = metadata["platform"].lower()
        if platform == "youtube":
            logger.info("Simulating YouTube upload for video: %s", video_path)
            # Simulate success
            return True
        elif platform == "tiktok":
            logger.info("Simulating TikTok upload for video: %s", video_path)
            # Simulate success
            return True
        else:
            logger.error("Unsupported platform: %s", platform)
            return False
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error("Failed to publish video %s due to %s: %s", video_path, type(e).__name__, e)
        return False


def publish_all_videos(edited_dir: Path = DEFAULT_EDITED_DIR,
                       metadata_map: Dict[str, Dict[str, Any]] = None) -> List[Path]:
    """
    Batch publish all videos in the edited directory.

    Args:
        edited_dir (Path): Directory containing edited videos.
        metadata_map (Dict[str, Dict[str, Any]], optional): Mapping from video filename to metadata.
            If None, uses default empty metadata.

    Returns:
        List[Path]: List of successfully uploaded video paths.
    """
    if metadata_map is None:
        metadata_map = {}

    success_list: List[Path] = []
    if not edited_dir.exists():
        logger.warning("Edited directory does not exist: %s", edited_dir)
        return success_list

    for video_file in sorted(edited_dir.glob('*.mp4')):
        meta = metadata_map.get(video_file.name, {})
        if publish_video(video_file, meta):
            success_list.append(video_file)
        else:
            logger.warning("Skipping failed upload: %s", video_file)
    return success_list


def main() -> None:
    """
    Entrypoint for the publisher module. Publishes all edited videos.
    """
    uploaded = publish_all_videos()
    logger.info("Uploaded %d videos." , len(uploaded))


if __name__ == '__main__':
    main()
