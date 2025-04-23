# chat_analysis.py
"""
Chat analysis for highlight detection: detects chat spikes and emote bursts.
"""
import pandas as pd
from typing import List
import logging

def load_chat_log(chat_log_path: str) -> pd.DataFrame:
    """Load chat log JSON into a DataFrame."""
    import json
    with open(chat_log_path, 'r', encoding='utf-8') as f:
        chat_data = json.load(f)
    df = pd.DataFrame(chat_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    logging.info(f"Loaded chat log with {len(df)} messages from {chat_log_path}")
    return df

def detect_chat_spikes(df: pd.DataFrame, window_sec: int = 10, threshold: int = 10) -> List[int]:
    """Detect time windows with chat spikes."""
    df = df.set_index('timestamp')
    counts = df['message'].resample(f'{window_sec}S').count()
    spikes = counts[counts > threshold]
    logging.info(f"Detected {len(spikes)} chat spikes.")
    return [int(ts.timestamp()) for ts in spikes.index]
