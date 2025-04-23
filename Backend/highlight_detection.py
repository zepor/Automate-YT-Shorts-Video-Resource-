# highlight_detection.py
"""
Module for detecting highlights in Twitch VODs using chat activity spikes and audio peaks.

Approach:
- Fetch chat logs and VODs automatically (using Twitch API or Streamlink/VodBot).
- Analyze chat logs for message rate and emote bursts (pandas/numpy).
- Analyze audio for peaks (FFmpeg, via subprocess, for robust detection).
- Output highlights.json with highlight timestamps.

Future enhancements, limitations, and references are documented in highlight_detection_README.md.
"""

import json
import subprocess
from typing import List, Dict
import logging
import pandas as pd

# --- Chat Analysis ---
def load_chat_log(chat_log_path: str) -> pd.DataFrame:
    """Load chat log JSON into a DataFrame."""
    with open(chat_log_path, 'r', encoding='utf-8') as f:
        chat_data = json.load(f)
    # Expecting chat_data as a list of dicts with 'timestamp' and 'message' keys
    df = pd.DataFrame(chat_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    return df

def detect_chat_spikes(df: pd.DataFrame, window_sec: int = 10, threshold: int = 10) -> List[int]:
    """Detect time windows with chat spikes."""
    df = df.set_index('timestamp')
    counts = df['message'].resample(f'{window_sec}S').count()
    spikes = counts[counts > threshold]
    return [int(ts.timestamp()) for ts in spikes.index]

# --- Audio Analysis ---
def detect_audio_peaks_ffmpeg(video_path: str, silence_thresh: float = -30.0,
    min_duration: float = 0.5) -> List[int]:
    """Detect audio peaks using FFmpeg's silencedetect (returns start times of loud segments)."""
    cmd = [
        'ffmpeg', '-i', video_path, '-af',
        f'silencedetect=noise={silence_thresh}dB:d={min_duration}',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE,
        stdout=subprocess.PIPE, text=True, check=True)
    lines = result.stderr.split('\n')
    peaks = []
    for line in lines:
        if 'silence_end:' in line:
            # FFmpeg logs silence_end: <time> | silence_duration: <dur>
            try:
                time_str = line.split('silence_end:')[1].split('|')[0].strip()
                peaks.append(int(float(time_str)))
            except (ValueError, IndexError):
                continue
    return peaks

# --- Highlight Detection ---
def find_highlights(chat_spikes: List[int], audio_peaks: List[int], window: int = 10) -> List[Dict]:
    """Find highlight timestamps where chat and audio spikes overlap within a window (seconds)."""
    highlights = []
    for chat_time in chat_spikes:
        for audio_time in audio_peaks:
            if abs(chat_time - audio_time) <= window:
                highlights.append({'timestamp': chat_time})
                break
    return highlights

# --- Main Pipeline ---
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
    """
    try:
        chat_df = load_chat_log(chat_log_path)
        chat_spikes = detect_chat_spikes(chat_df)
        audio_peaks = detect_audio_peaks_ffmpeg(video_path)
        highlights = find_highlights(chat_spikes, audio_peaks)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(highlights, f, indent=2)
        print(f"Highlights written to {output_path}")
        return highlights
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        logging.error("Highlight detection failed: %s", e)
        return []

# Example usage (to be replaced with integration in main pipeline):
# detect_highlights('path/to/video.mp4', 'path/to/chat.json')
