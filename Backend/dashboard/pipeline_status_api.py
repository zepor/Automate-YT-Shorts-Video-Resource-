"""
Flask blueprint for the /pipeline_status endpoint.
Aggregates video pipeline status for the dashboard Kanban view.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, jsonify

bp_pipeline_status = Blueprint("bp_pipeline_status", __name__)

# Config-driven paths for Windows/Docker compatibility
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
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

def get_pipeline_status() -> Dict[str, List[Dict[str, Any]]]:
    """
    Aggregates the status of all videos in the pipeline, grouped by stage.
    Returns a dict with keys: Ingested, Detection, Editing, Publishing.
    """
    status: Dict[str, list] = {"Ingested": [], "Detection": [], "Editing": [], "Publishing": []}
    video_files = [f for f in TEMP_DIR.glob("*.mp4") if f.is_file()]
    logging.info("[pipeline_status] Found video files: %s", [str(f) for f in video_files])
    highlight_json = load_json_safe(HIGHLIGHT_DIR / "highlight.json") or {}
    ratings_json = load_json_safe(HIGHLIGHT_DIR / "highlight_ratings.json") or {}
    # Defensive: ensure both are dicts, not lists
    if not isinstance(highlight_json, dict):
        logging.warning("[pipeline_status] highlight.json"
            "is not a dict. Got: %s. Treating as empty.", type(highlight_json))
        highlight_json = {}
    if not isinstance(ratings_json, dict):
        logging.warning("[pipeline_status] highlight_ratings.json"
            "is not a dict. Got: %s. Treating as empty.", type(ratings_json))
        ratings_json = {}
    logging.info("[pipeline_status] Loaded highlight_json keys: %s", list(highlight_json.keys()))
    logging.info("[pipeline_status] Loaded ratings_json keys: %s", list(ratings_json.keys()))
    for video_path in video_files:
        video_name = video_path.name
        # If video is not in highlight.json, it's only ingested
        if video_name not in highlight_json:
            status["Ingested"].append({"video": video_name, "status": "Ready for Detection"})
            continue
        # Detection info
        highlights = highlight_json.get(video_name, [])
        rating = ratings_json.get(video_name, None)
        detection_info = {
            "video": video_name,
            "highlights": highlights,
            "rating": rating,
            "approved": rating is not None,
        }
        # Editing info (check for edited file, planogram, etc.)
        edited_path = TEMP_DIR / f"edited_{video_name}"
        editing_info = {
            "video": video_name,
            "edited": edited_path.exists(),
            "edited_path": str(edited_path) if edited_path.exists() else None,
        }
        # Publishing info (check for published flag/output)
        published_flag = TEMP_DIR / f"published_{video_name}.flag"
        publishing_info = {
            "video": video_name,
            "published": published_flag.exists(),
            "output_location": str(published_flag) if published_flag.exists() else None,
        }
        # Assign to Kanban column
        if not detection_info["approved"]:
            status["Detection"].append(detection_info)
        elif not editing_info["edited"]:
            status["Editing"].append({**detection_info, **editing_info})
        else:
            status["Publishing"].append({**detection_info, **editing_info, **publishing_info})
    # Add mock rows if any column is empty
    if not status["Ingested"]:
        status["Ingested"].append({"video": "No videos awaiting detection",
            "status": "All processed"})
    if not status["Detection"]:
        status["Detection"].append({"video": "No videos in detection",
            "status": "All processed"})
    if not status["Editing"]:
        status["Editing"].append({"video": "No videos in editing", "status": "All processed"})
    if not status["Publishing"]:
        status["Publishing"].append({"video": "No videos in publishing", "status": "All processed"})
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
