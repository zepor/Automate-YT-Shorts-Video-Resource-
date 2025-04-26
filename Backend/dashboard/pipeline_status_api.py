"""
Flask blueprint for the /pipeline_status endpoint.
Aggregates video pipeline status for the dashboard Kanban view.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, jsonify

bp_pipeline_status = Blueprint("bp_pipeline_status", __name__)

# Config-driven paths for Windows/Docker compatibility
def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    """
    return Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = get_project_root()
TEMP_DIR = PROJECT_ROOT / "temp"
HIGHLIGHT_DIR = PROJECT_ROOT / "Backend" / "highlight_detection"
VIDEO_EDITING_DIR = PROJECT_ROOT / "Backend" / "video_editing"
UPLOADER_DIR = PROJECT_ROOT / "Backend" / "uploader"

# Helper to load JSON safely
def load_json_safe(path: Path) -> Any:
    """
    Load JSON data from a file safely.
    description: Handles FileNotFoundError, JSONDecodeError, and OSError.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logging.warning("Could not load %s: %s", path, e)
        return None

def is_valid_video_filename(filename: str) -> bool:
    """
    Validate that the filename is a valid .mp4 file and does not contain suspicious characters.
    Only allow alphanumeric, space, dash, underscore, and dot.
    """
    # Only allow .mp4 files with safe characters
    return bool(re.match(r'^[\w\- .]+\.mp4$', filename))

def get_pipeline_status() -> Dict[str, List[Dict[str, Any]]]:
    """
    Aggregates the status of all videos in the pipeline, grouped by stage.
    Returns a dict with keys: Ingested, Detection, Editing, Publishing.
    Only includes valid .mp4 files that exist in temp.
    """
    status: Dict[str, list] = {"Ingested": [], "Detection": [], "Editing": [], "Publishing": []}
    # Build a set of all valid .mp4 filenames in temp
    valid_video_files = {f.name for f in TEMP_DIR.glob("*.mp4")
        if f.is_file() and is_valid_video_filename(f.name)}
    logging.info("[pipeline_status] Found video files: %s", list(valid_video_files))
    highlight_json = load_json_safe(HIGHLIGHT_DIR / "highlight.json") or {}
    ratings_json = load_json_safe(HIGHLIGHT_DIR / "highlight_ratings.json") or {}
    if not isinstance(highlight_json, dict):
        logging.warning("[pipeline_status] highlight.json is not a dict."
            " Got: %s. Treating as empty.", type(highlight_json))
        highlight_json = {}
    if not isinstance(ratings_json, dict):
        logging.warning("[pipeline_status] highlight_ratings.json is not a dict. "
            "Got: %s. Treating as empty.", type(ratings_json))
        ratings_json = {}
    logging.info("[pipeline_status] Loaded highlight_json keys: %s", list(highlight_json.keys()))
    logging.info("[pipeline_status] Loaded ratings_json keys: %s", list(ratings_json.keys()))
    # Only process videos that actually exist in temp
    for video_name in valid_video_files:
        # If video is not in highlight.json, it's only ingested
        if video_name not in highlight_json:
            status["Ingested"].append({"video": video_name, "status": "Ready for Detection"})
            continue
        highlights = highlight_json.get(video_name, [])
        rating = ratings_json.get(video_name, None)
        detection_info = {
            "video": video_name,
            "highlights": highlights,
            "rating": rating,
            "approved": rating is not None,
        }
        edited_path = TEMP_DIR / f"edited_{video_name}"
        editing_info = {
            "video": video_name,
            "edited": edited_path.exists(),
            "edited_path": str(edited_path) if edited_path.exists() else None,
        }
        published_flag = TEMP_DIR / f"published_{video_name}.flag"
        publishing_info = {
            "video": video_name,
            "published": published_flag.exists(),
            "output_location": str(published_flag) if published_flag.exists() else None,
        }
        if not detection_info["approved"]:
            status["Detection"].append(detection_info)
        elif not editing_info["edited"]:
            status["Editing"].append({**detection_info, **editing_info})
        else:
            status["Publishing"].append({**detection_info, **editing_info, **publishing_info})
    # Do not add placeholder entries for empty columns
    logging.info("[pipeline_status] Final pipeline status: %s", status)
    return status

@bp_pipeline_status.route("/pipeline_status", methods=["GET"])
def pipeline_status():
    """
    API endpoint to get the status of all videos in the pipeline.
    Returns a Kanban-style JSON for the dashboard.
    """
    try:
        status = get_pipeline_status()
        return jsonify(status), 200
    except (KeyError, ValueError, OSError) as e:  # Catch specific exceptions
        logging.error("Error in /pipeline_status: %s", e)
        return jsonify({"error": str(e)}), 500
