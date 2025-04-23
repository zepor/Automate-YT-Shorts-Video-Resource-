"""
Main script for automating the creation of YouTube Shorts videos.

This script integrates various modules to fetch Twitch videos, generate
scripts,
search for stock videos, and produce final video outputs with subtitles and
audio.
"""

import hashlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List
from flask import Flask

# Ensure the project root is in sys.path for absolute imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure the Backend directory is in sys.path for imports
BACKEND_DIR = Path(__file__).parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from dotenv import load_dotenv
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from Backend.content.gpt import generate_script, get_search_terms
    from Backend.content.search import search_for_stock_videos
    from Backend.highlight_detection.highlight_detector import \
        detect_highlights
    from Backend.video_editing.editor import (combine_videos,
                                              fetch_twitch_video_titles,
                                              fetch_twitch_videos,
                                              generate_subtitles,
                                              generate_video, save_video,
                                              text_to_speech)
    from Backend.dashboard.evaluation_api import bp_evaluation
    from Backend.dashboard.orchestration_api import bp_orchestration
    from Backend.ingestion.ingestion_api import bp_ingestion
    from Backend.dashboard.pipeline_status_api import bp_pipeline_status
except ModuleNotFoundError as e:
    logging.error("Import failed: %s. Please ensure all"
        "dependencies are installed and requirements.txt is up to date.", e)
    # Exit with code 3 to indicate a fatal import error (Compose will only restart twice)
    sys.exit(3)

HASH_FILE = BACKEND_DIR / '.codebase_hash'
EVAL_SCRIPT = BACKEND_DIR / 'dashboard' / 'evaluation_logic.py'
DASHBOARD_SCRIPT = BACKEND_DIR / 'highlight_approval' / 'approval_app.py'


def get_py_files(directory: Path) -> List[Path]:
    """
    Recursively get all .py files in the directory, excluding __pycache__ and venv.
    """
    py_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'venv')]
        for file in files:
            if file.endswith('.py'):
                py_files.append(Path(root) / file)
    return py_files


def compute_hash(files: List[Path]) -> str:
    """
    Compute a SHA256 hash of the contents of the given files.
    """
    hasher = hashlib.sha256()
    for file in sorted(files):
        try:
            with open(file, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)
        except OSError as e:
            logging.error("Failed to read %s: %s", file, e)
    return hasher.hexdigest()


def read_last_hash() -> str:
    """
    Read the last known hash value from the HASH_FILE.

    Returns:
        str: The last hash value, or an empty string if no hash file exists.
    """
    if HASH_FILE.exists():
        try:
            with open(HASH_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except OSError as e:
            logging.warning("Could not read hash file: %s", e)
    return ''


def write_hash(hash_value: str) -> None:
    """
    Write the provided hash value to the HASH_FILE.

    Args:
        hash_value (str): The hash string to write.
    """
    try:
        with open(HASH_FILE, 'w', encoding='utf-8') as f:
            f.write(hash_value)
    except OSError as e:
        logging.error("Could not write hash file: %s", e)


def run_script(script_path: Path) -> int:
    """
    Run a Python script using the current interpreter. Returns exit code.
    """
    cmd = [sys.executable, str(script_path)]
    logging.info("Running script: %s", ' '.join(cmd))
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        logging.error("Script %s failed with exit code %s", script_path, e.returncode)
        return e.returncode
    except OSError as e:
        logging.error("Unexpected error running %s: %s", script_path, e)
        return 1


def load_env_vars(dotenv_path: str = ".env") -> None:
    """
    Load environment variables from a .env file using python-dotenv.
    Args:
        dotenv_path (str): Path to the .env file (relative).
    """
    env_path = Path(__file__).parent.parent / dotenv_path
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path))
        logging.info("Loaded environment variables from %s", env_path)
    else:
        logging.warning(".env file not found at %s", env_path)


def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp_evaluation)
    app.register_blueprint(bp_orchestration)
    app.register_blueprint(bp_ingestion)
    app.register_blueprint(bp_pipeline_status, url_prefix="/api")
    return app


def main():
    """
    Entrypoint for the application. 
    Checks for Backend code changes, runs evaluation logic 
    if needed, then starts the Flask dashboard app.
    """
    load_env_vars()
    logging.info("App started. Checking for Backend code changes...")
    py_files = get_py_files(BACKEND_DIR)
    current_hash = compute_hash(py_files)
    last_hash = read_last_hash()
    if current_hash != last_hash:
        logging.info("Codebase changed. Running evaluation logic...")
        exit_code = run_script(EVAL_SCRIPT)
        if exit_code == 0:
            write_hash(current_hash)
        else:
            logging.error("evaluation logic failed. Not updating hash.")
    else:
        logging.info("No code changes detected. Skipping evaluation logic.")
    # Set ImageMagick binary for MoviePy if needed
    imagemagick_binary = os.environ.get("IMAGEMAGICK_BINARY")
    if imagemagick_binary:
        os.environ["IMAGEMAGICK_BINARY"] = imagemagick_binary
        logging.info("IMAGEMAGICK_BINARY set to: %s", imagemagick_binary)
    else:
        logging.warning("IMAGEMAGICK_BINARY not set in environment.")
    # Start the dashboard Flask app
    logging.info("Starting highlight approval dashboard...")
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)


if __name__ == '__main__':
    main()
