# highlight_detector.py
"""
Main highlight detection logic: combines chat and 
audio spikes, manages highlight ratings, logging, and output.
"""
import os
import json
import logging
from typing import List, Dict
from .chat_analysis import load_chat_log, detect_chat_spikes
from .audio_analysis import detect_audio_peaks_ffmpeg

HIGHLIGHT_RATINGS_PATH = os.path.join(os.path.dirname(__file__), 'highlight_ratings.json')

def get_log_dir() -> str:
    """
    Get the directory for highlight detection logs. 
    Uses the HIGHLIGHT_LOG_DIR environment variable if set,
    otherwise defaults to '../../temp'.
    Returns:
        str: Path to the log directory (relative).
    """
    return os.environ.get("HIGHLIGHT_LOG_DIR",
        os.path.join(os.path.dirname(__file__), '../../temp'))

# Set up logging to a writable directory
log_dir = get_log_dir()
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "highlight_detection.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def find_highlights(chat_spikes: List[int], audio_peaks: List[int], window: int = 10) -> List[Dict]:
    """
    Find highlight timestamps where chat and audio spikes overlap within a window (seconds).
    """
    highlights = []
    for chat_time in chat_spikes:
        for audio_time in audio_peaks:
            if abs(chat_time - audio_time) <= window:
                highlights.append({'timestamp': chat_time})
                break
    logging.info("Matched %d highlights (chat+audio overlap)", len(highlights))
    return highlights

def save_highlights_json(highlights: List[Dict], output_path: str):
    """
    Save highlights to a JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(highlights, f, indent=2)
    logging.info("Highlights written to %s", output_path)

def load_ratings() -> Dict:
    """
    Load highlight ratings from a JSON file.
    """
    if os.path.exists(HIGHLIGHT_RATINGS_PATH):
        with open(HIGHLIGHT_RATINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_ratings(ratings: Dict):
    """
    Save highlight ratings to a JSON file.

    Args:
        ratings (Dict): A dictionary of highlight ratings where 
        keys are timestamps and values are ratings.
    """
    with open(HIGHLIGHT_RATINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(ratings, f, indent=2)
    logging.info("Highlight ratings updated in %s", HIGHLIGHT_RATINGS_PATH)

def rate_highlights(highlights: List[Dict]):
    """
    Rate highlights based on user input.

    Args:
        highlights (List[Dict]): List of highlights to be rated.
    """
    ratings = load_ratings()
    for h in highlights:
        ts = str(h['timestamp'])
        if ts not in ratings:
            # Placeholder: In production, replace with UI or CLI prompt for user rating
            print(f"Rate highlight at timestamp {ts} (1-5): ", end='')
            try:
                rating = int(input())
                if 1 <= rating <= 5:
                    ratings[ts] = rating
                else:
                    print("Invalid rating, must be 1-5. Skipping.")
            except (ValueError, KeyboardInterrupt):
                print("Invalid input. Skipping.")
    save_ratings(ratings)

def detect_highlights(video_path: str, chat_log_path: str, output_path: str = 'highlights.json'):
    """
    Detects highlights in a video based on chat activity and audio peaks.

    This function processes a video file and its corresponding chat log to identify
    moments of high activity or interest, referred to as highlights. It combines
    chat spikes and audio peaks to determine these moments and saves the results
    in a JSON file.

    Args:
        video_path (str): The file path to the video file.
        chat_log_path (str): The file path to the chat log file.
        output_path (str, optional): The file path to save the detected highlights in JSON format.
                                     Defaults to 'highlights.json'.

    Returns:
        list: A list of detected highlights, where each highlight is represented as a dictionary.
              Returns an empty list if no highlights are detected or if an error occurs.

    Raises:
        FileNotFoundError: If the video or chat log file is not found.
        ValueError: If the input data is invalid or improperly formatted.
        json.JSONDecodeError: If the chat log file contains invalid JSON.
    """
    try:
        chat_df = load_chat_log(chat_log_path)
        chat_spikes = detect_chat_spikes(chat_df)
        audio_peaks = detect_audio_peaks_ffmpeg(video_path)
        highlights = find_highlights(chat_spikes, audio_peaks)
        save_highlights_json(highlights, output_path)
        if not highlights:
            logging.warning("No highlights detected. Consider"
                            "adjusting thresholds or reviewing input data.")
        else:
            rate_highlights(highlights)
        return highlights
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        logging.error("Highlight detection failed: %s", e)
        return []
