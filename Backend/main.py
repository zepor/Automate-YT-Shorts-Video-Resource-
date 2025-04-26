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
from typing import List  # Ensure List is imported for type hints

from flask import Blueprint, Flask, abort, jsonify, send_from_directory, Response

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
    from Backend.dashboard.evaluation_api import bp_evaluation
    from Backend.dashboard.orchestration_api import bp_orchestration
    from Backend.dashboard.pipeline_status_api import bp_pipeline_status
    from Backend.highlight_detection.highlight_detector import \
        detect_highlights
    from Backend.ingestion.ingestion_api import bp_ingestion
    from Backend.video_editing.editor import combine_videos
    import openai  # Only import openai, do not import error submodule
except ModuleNotFoundError as e:
    logging.error("Import failed: %s. Please ensure all"
        "dependencies are installed and requirements.txt is up to date.", e)
    # Exit with code 3 to indicate a fatal import error (Compose will only restart twice)
    sys.exit(3)
except ImportError as e:
    logging.error("ImportError for openai: %s", e, exc_info=True)
    openai = None

# Set up unified backend logging to Backend/backend.log
LOG_DIR = os.path.join(os.path.dirname(__file__), 'backend.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

HASH_FILE = BACKEND_DIR / '.codebase_hash'
EVAL_SCRIPT = BACKEND_DIR / 'dashboard' / 'evaluation_logic.py'
DASHBOARD_SCRIPT = BACKEND_DIR / 'highlight_approval' / 'approval_app.py'

bp_temp = Blueprint('temp', __name__)

def get_temp_dir() -> str:
    """
    Returns the absolute path to the temp directory for video files.
    Uses only relative/config-driven paths for Windows and Docker compatibility.
    Always resolves to the project root's temp directory (e.g., /app/temp in Docker).
    """
    # Use pathlib for robust, cross-platform path resolution
    project_root = Path(__file__).resolve().parent.parent
    temp_dir = project_root / 'temp'
    return str(temp_dir)

def is_valid_video_filename(filename: str) -> bool:
    """
    Validate that the filename is a valid .mp4 file and does not contain suspicious characters.
    Only allow alphanumeric, space, dash, underscore, and dot.
    """
    import re
    return bool(re.match(r'^[\w\- .]+\.mp4$', filename))

@bp_temp.route('/temp/<path:filename>')
def serve_temp_file(filename: str):
    """
    Serves video files from the temp directory. Logs and returns 404 if file is missing or invalid.
    Always logs the full absolute path being checked.
    """
    temp_dir = get_temp_dir()
    # Validate filename for security and correctness
    if not is_valid_video_filename(filename):
        logging.warning("Rejected malformed or unsafe video filename: %s", filename)
        abort(404, description=f"Invalid video filename: {filename}")
    file_path = os.path.abspath(os.path.join(temp_dir, filename))
    # Log the full absolute path being checked
    logging.info("Checking for video file at: %s", file_path)
    if not os.path.isfile(file_path):
        logging.warning("Requested video file not found: %s", file_path)
        abort(404, description=f"Video file not found: {filename}")
    logging.info("Serving video file: %s", file_path)
    return send_from_directory(temp_dir, filename)


def get_py_files(directory: Path) -> List[Path]:
    """
    Recursively get all .py files in the directory, excluding __pycache__ and venv.
    """
    py_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'venv')]
        # Ensure brackets are properly closed
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
    """
    __summary__: Create and configure the Flask application.
    """
    app = Flask(__name__)
    # Register blueprints with correct prefixes
    app.register_blueprint(bp_evaluation, url_prefix="/api")
    app.register_blueprint(bp_orchestration)
    app.register_blueprint(bp_ingestion)
    app.register_blueprint(bp_pipeline_status, url_prefix="/api")
    app.register_blueprint(bp_temp)
    
    @app.route('/api/markdown_files')
    def list_markdown_files() -> 'flask.Response':
        """
        List all markdown (.md) files in the project root, excluding ENV.md.
        Returns:
            flask.Response: JSON list of markdown filenames.
        """
        try:
            # Use pathlib for robust, cross-platform path resolution
            project_root = Path(__file__).resolve().parent.parent
            md_files = [f.name for f in project_root.glob('*.md') if f.name.lower() != 'env.md']
            logging.info("Markdown files found in %s: %s", project_root, md_files)
            return jsonify(md_files)
        except (OSError, UnicodeDecodeError) as e:
            logging.error("Error listing markdown files in %s: %s", project_root, e)
            return jsonify([]), 500

    @app.route('/api/markdown_file/<filename>')
    def get_markdown_file(filename: str) -> Response:
        """
        Serve the content of a markdown file from the project root.
        Only allows .md files that exist in the project root.
        """
        project_root = Path(__file__).resolve().parent.parent
        # Security: Only allow .md files, no path traversal
        if not filename.endswith('.md') or '/' in filename or '\\' in filename:
            logging.warning("Rejected markdown file request: %s", filename)
            return Response("Invalid filename", status=400)
        file_path = project_root / filename
        if not file_path.exists():
            logging.warning("Markdown file not found: %s", file_path)
            return Response("File not found", status=404)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logging.info("Served markdown file: %s", file_path)
            return Response(content, mimetype='text/markdown')
        except (OSError, UnicodeDecodeError) as e:
            logging.error("Error reading markdown file %s: %s", file_path, e)
            return Response("Error reading file", status=500)

    return app


def main():
    """
    Entrypoint for the application. 
    Checks for Backend code changes, runs evaluation logic 
    if needed, then starts the Flask dashboard app.
    """
    load_env_vars()
    logging.info("App started. Checking for Backend code changes...")
    logging.info("Python executable: %s", sys.executable)
    logging.info("sys.path: %s", sys.path)
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
