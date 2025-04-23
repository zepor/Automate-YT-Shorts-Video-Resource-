import os
import json
from typing import List

PROJECT_DIR = os.getcwd()
PROGRESS_FILE = os.path.join(PROJECT_DIR, "progress.json")
README_FILE = os.path.join(PROJECT_DIR, "READMEBUILD.md")

expected_steps = [
    "Ingest VOD",
    "Highlight Detection",
    "Highlight Approval",
    "Slice Highlights",
    "Subtitles Generation & Overlay",
    "Format Clips for Shorts",
    "Automate Platform Uploads",
    "Error Handling & Logging",
    "UI/Dashboard Integration",
]

def evaluate_codebase() -> List[str]:
    """
    Evaluate the current project structure against the ideal workflow and codebase.
    Returns a list of missing steps.
    """
    missing_steps_local = []
    completed_steps = {}
    if not os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "w", encoding="utf-8") as progress_file:
            json.dump({}, progress_file)
    with open(PROGRESS_FILE, "r", encoding="utf-8") as progress_file:
        progress = json.load(progress_file)
    ingest_vod_complete = False
    try:
        with open(os.path.join(PROJECT_DIR, "Backend", "main.py"), "r", encoding="utf-8") as main_file:
            main_py = main_file.read()
        with open(os.path.join(PROJECT_DIR, "Backend", "video.py"), "r", encoding="utf-8") as video_file:
            video_py = video_file.read()
        if (
            "fetch_twitch_videos" in main_py
            and "save_video" in main_py
            and "fetch_twitch_videos" in video_py
            and "save_video" in video_py
        ):
            ingest_vod_complete = True
    except (FileNotFoundError, IOError):
        pass
    if ingest_vod_complete:
        progress["Ingest VOD"] = {
            "status": "completed",
            "details": "Twitch VOD download logic found in main.py and video.py.",
        }
    else:
        missing_steps_local.append("Ingest VOD")
    highlight_detection_complete = False
    if (
        "highlight" in main_py
        or "highlight" in video_py
        or "chat_analysis" in main_py
        or "audio_analysis" in main_py
    ):
        highlight_detection_complete = True
    if highlight_detection_complete:
        progress["Highlight Detection"] = {
            "status": "completed",
            "details": "Highlight detection logic found.",
        }
    else:
        missing_steps_local.append("Highlight Detection")
    for step in expected_steps[2:]:
        if step not in progress:
            missing_steps_local.append(step)
        else:
            completed_steps[step] = progress[step]
    with open(PROGRESS_FILE, "w", encoding="utf-8") as progress_file:
        json.dump(progress, progress_file, indent=2)
    return missing_steps_local
