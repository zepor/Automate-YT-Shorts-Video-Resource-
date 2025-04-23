"""
approval_app.py
Web-based dashboard for reviewing, rating, and approving detected highlights.
"""
import sys
import json
import logging
import subprocess
import threading
from typing import Dict, List, Any
from pathlib import Path
import os
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify, abort
import markdown

# Relative paths for highlights and ratings
BASE_DIR = Path(__file__).parent.parent
HIGHLIGHTS_PATH = BASE_DIR / 'highlight_detection' / 'highlights.json'
RATINGS_PATH = BASE_DIR / 'highlight_detection' / 'highlight_ratings.json'
VIDEO_DIR = BASE_DIR.parent / 'temp'

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For flash messages

# Configure logging with lazy formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'highlight_approval.log')),
        logging.StreamHandler()
    ]
)

def load_highlights() -> List[Dict]:
    """
    Load highlights from highlights.json.
    """
    try:
        if os.path.exists(HIGHLIGHTS_PATH):
            with open(HIGHLIGHTS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                logging.error("highlights.json is not a list. Returning empty list.")
                return []
        return []
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logging.error("Error loading highlights.json: %s", e)
        return []


def load_ratings() -> Dict:
    """
    Load highlight ratings from highlight_ratings.json.

    Returns:
        Dict: A dictionary of highlight ratings with timestamps as keys.
    """
    try:
        if os.path.exists(RATINGS_PATH):
            with open(RATINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                logging.error("highlight_ratings.json is not a dict. Returning empty dict.")
                return {}
        return {}
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logging.error("Error loading highlight_ratings.json: %s", e)
        return {}


def save_ratings(ratings: Dict):
    """
    Save highlight ratings to a JSON file.
    """
    with open(RATINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, indent=2)
    logging.info("Highlight ratings updated.")

@app.route('/', methods=['GET', 'POST'])
def approval_dashboard():
    """
    _summary_: Dashboard for reviewing and rating highlights.
    _return_: Rendered HTML template with highlights and ratings.
    """
    highlights = load_highlights()
    ratings = load_ratings()
    message = None
    if request.method == 'POST':
        for h in highlights:
            ts = str(h['timestamp'])
            rating = request.form.get(f'rating_{ts}')
            approved = request.form.get(f'approve_{ts}') == 'on'
            if rating:
                ratings[ts] = {'rating': int(rating), 'approved': approved}
        save_ratings(ratings)
        flash('Ratings and approvals saved!', 'success')
        return redirect(url_for('approval_dashboard'))
    # If no highlights, show a message and display previously reviewed highlights if any
    if not highlights:
        message = 'No new highlights to review.'
    # Prepare a list of previously reviewed highlights
    reviewed = []
    for ts, data in ratings.items():
        reviewed.append({'timestamp': ts, 'rating': data.get('rating'),
            'approved': data.get('approved')})
    return render_template('approval.html', highlights=highlights,
        ratings=ratings, reviewed=reviewed, message=message, video_dir=VIDEO_DIR)

@app.route('/run_evaluation', methods=['POST'])
def run_evaluation():
    """
    API endpoint to trigger evaluation.py. Runs in a background thread.
    Returns JSON status.
    """
    def background_eval():
        run_evaluation_script()
    thread = threading.Thread(target=background_eval, daemon=True)
    thread.start()
    logging.info("Manual evaluation triggered via dashboard.")
    return jsonify({'status': 'started', 'message': 'Evaluation started.'}), 202

def run_evaluation_script() -> None:
    """Run evaluation.py as a background subprocess. Logs output and errors."""
    eval_path = Path(__file__).parent.parent.parent / 'Dashboard' / 'evaluation.py'
    try:

        cmd = [sys.executable, str(eval_path)]
        logging.info("Running evaluation.py: %s", ' '.join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logging.info("evaluation.py output: %s", result.stdout)
        if result.stderr:
            logging.warning("evaluation.py stderr: %s", result.stderr)
    except subprocess.CalledProcessError as e:
        logging.error("evaluation.py failed: %s", e.stderr)
    except OSError as e:
        logging.error("Error running evaluation.py: %s", e)

def list_videos_for_step(step: str) -> List[str]:
    """
    List available videos for a given pipeline step.
    Filters videos based on the provided step.
    """
    temp_dir = Path(__file__).parent.parent.parent / 'temp'
    if not temp_dir.exists():
        return []
    # Filter videos based on the step (e.g., detection, editing, publishing)
    if step == 'detection':
        return [str(f.name) for f in temp_dir.glob('*.mp4')]
    elif step == 'editing':
        editing_dir = Path(__file__).parent.parent / 'video_editing' / 'edited'
        return [str(f.name) for f in editing_dir.glob('*.mp4')] if editing_dir.exists() else []
    elif step == 'publishing':
        publishing_dir = Path(__file__).parent.parent / 'uploader' / 'published'
        return [f.name for f in publishing_dir.glob('*.mp4')] if publishing_dir.exists() else []
    else:
        logging.warning("Unknown step: %s", step)
        return []

@app.route('/run_step/<step>', methods=['POST'])
def run_step(step):
    """
    API endpoint to trigger a pipeline step script. 
    Supported steps: evaluation, detection, editing, publishing.
    """
    script_map = {
        'evaluation': Path(__file__).parent.parent.parent / 'Dashboard' / 'evaluation.py',
        'detection': BASE_DIR / 'highlight_detection' / 'highlight_detector.py',
        'editing': BASE_DIR.parent / 'video_editing' / 'editor.py',
        'publishing': BASE_DIR.parent / 'uploader' / 'publish.py',
    }
    script_path = script_map.get(step)
    if not script_path or not script_path.exists():
        return jsonify({'status': 'error', 'message': f'No script for step: {step}'}), 400
    def background_run():
        try:
            cmd = [sys.executable, str(script_path)]
            logging.info("Running %s script: %s", step, ' '.join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logging.info("%s output: %s", step, result.stdout)
            if result.stderr:
                logging.warning("%s stderr: %s", step, result.stderr)
        except subprocess.CalledProcessError as e:
            logging.error("%s failed: %s", step, e.stderr)
        except (OSError, subprocess.SubprocessError) as e:
            logging.error("Error running %s: %s", step, e)
    thread = threading.Thread(target=background_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'message': f'{step.capitalize()} started.'}), 202

def get_pipeline_status() -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns a dict with videos grouped by pipeline stage, each with expandable details.
    Stages: detection, editing, publishing. Each video is only in one stage at a time.
    """
    temp_dir = Path(__file__).parent.parent.parent / 'temp'
    highlights_path = Path(__file__).parent.parent / 'highlight_detection' / 'highlights.json'
    ratings_path = Path(__file__).parent.parent / 'highlight_detection' / 'highlight_ratings.json'
    editing_dir = Path(__file__).parent.parent / 'video_editing' / 'edited'
    publishing_dir = Path(__file__).parent.parent / 'uploader' / 'published'

    # Load highlight approvals
    highlights = []
    if highlights_path.exists():
        try:
            with open(highlights_path, 'r', encoding='utf-8') as f:
                highlights = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logging.error("Error loading highlights.json: %s", e)
    ratings = {}
    if ratings_path.exists():
        try:
            with open(ratings_path, 'r', encoding='utf-8') as f:
                ratings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logging.error("Error loading highlight_ratings.json: %s", e)

    # Gather all videos in temp
    all_videos = list(temp_dir.glob('*.mp4')) if temp_dir.exists() else []
    # Gather edited and published videos
    edited_videos = list(editing_dir.glob('*.mp4')) if editing_dir.exists() else []
    published_videos = list(publishing_dir.glob('*.mp4')) if publishing_dir.exists() else []

    # Helper: get highlights for a video
    def get_highlights_for_video(video_name: str) -> List[Dict[str, Any]]:
        return [h for h in highlights if h.get('video') == video_name]

    # Helper: get highlight approval status
    def highlight_approved(ts: str) -> bool:
        return ratings.get(str(ts), {}).get('approved', False)

    # Build pipeline status
    status = {'detection': [], 'editing': [], 'publishing': []}
    for v in all_videos:
        video_name = v.name
        video_highlights = get_highlights_for_video(video_name)
        if not video_highlights:
            # No highlights yet, still in detection
            status['detection'].append({'video': video_name, 'highlights': []})
            continue
        # Check if all highlights are approved/rejected
        all_reviewed = all(str(h['timestamp']) in ratings for h in video_highlights)
        all_approved = all(highlight_approved(h['timestamp']) for h in video_highlights)
        if not all_reviewed:
            # Still in detection until all highlights reviewed
            status['detection'].append({
                'video': video_name,
                'highlights': [
                    {
                        'timestamp': h['timestamp'],
                        'approved': highlight_approved(h['timestamp']),
                        'rating': ratings.get(str(h['timestamp']), {}).get('rating')
                    } for h in video_highlights
                ]
            })
        elif all_approved:
            # If all highlights approved, move to editing
            # Find edited highlights for this video
            edited = [e for e in edited_videos if e.stem.startswith(video_name.replace('.mp4', ''))]
            status['editing'].append({
                'video': video_name,
                'highlights': [
                    {
                        'timestamp': h['timestamp'],
                        'approved': True,
                        'edited': any(e.stem.endswith(str(h['timestamp'])) for e in edited),
                        'planogram': None,  # Placeholder for planogram info
                        'edited_video': next((str(e.name) for e in edited 
                            if e.stem.endswith(str(h['timestamp']))), None)
                    } for h in video_highlights if highlight_approved(h['timestamp'])
                ]
            })
        else:
            # If any highlight rejected, do not proceed to editing
            status['detection'].append({
                'video': video_name,
                'highlights': [
                    {
                        'timestamp': h['timestamp'],
                        'approved': highlight_approved(h['timestamp']),
                        'rating': ratings.get(str(h['timestamp']), {}).get('rating')
                    } for h in video_highlights
                ]
            })
    # Now, check for videos in publishing (all highlights edited)
    for v in edited_videos:
        video_name = v.name.split('_')[0] + '.mp4'
        # Assumes edited files are named like original_highlight.mp4
        # If published, move to publishing
        published = any(p.name.startswith(v.stem) for p in published_videos)
        if published:
            status['publishing'].append({
                'video': video_name,
                'edited_video': v.name,
                'published': True
            })
        else:  # already shown in editing
            status['editing'].append({
                'video': video_name,
                'edited_video': v.name,
                'published': False
            })
    return status

@app.route('/pipeline_status')
def pipeline_status():
    """
    Returns videos grouped by pipeline stage, with expandable details for highlights and edits.
    """
    return jsonify(get_pipeline_status())

@app.route('/docs')
def list_docs():
    """
    List all .md files in the repo for documentation viewing.
    """
    repo_root = Path(__file__).parent.parent.parent
    md_files = list(repo_root.glob('*.md'))
    return jsonify([f.name for f in md_files])

@app.route('/docs/<filename>')
def get_doc(filename):
    """Serve the contents of a .md file as HTML (rendered markdown)."""
    repo_root = Path(__file__).parent.parent.parent
    file_path = repo_root / filename
    if not file_path.exists() or not file_path.suffix == '.md':
        abort(404)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        html = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
        return jsonify({'html': html, 'filename': filename})
    except (FileNotFoundError, OSError, IOError) as e:
        logging.error("Error reading markdown file %s: %s", filename, e)
        abort(500)

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle unhandled exceptions and log the error."""
    logging.error("Unhandled exception: %s", e)
    return render_template('approval.html', highlights=[], ratings={},
        reviewed=[], message="An error occurred. Please check the logs.", video_dir=VIDEO_DIR), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
