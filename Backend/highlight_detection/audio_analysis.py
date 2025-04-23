# audio_analysis.py
"""
Audio analysis for highlight detection: detects audio peaks using FFmpeg.
"""
import subprocess
from typing import List
import logging

def detect_audio_peaks_ffmpeg(video_path: str, silence_thresh: float = -30.0, min_duration: float = 0.5) -> List[int]:
    """Detect audio peaks using FFmpeg's silencedetect (returns start times of loud segments)."""
    cmd = [
        'ffmpeg', '-i', video_path, '-af',
        f'silencedetect=noise={silence_thresh}dB:d={min_duration}',
        '-f', 'null', '-'
    ]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    lines = result.stderr.split('\n')
    peaks = []
    for line in lines:
        if 'silence_end:' in line:
            try:
                time_str = line.split('silence_end:')[1].split('|')[0].strip()
                peaks.append(int(float(time_str)))
            except Exception as e:
                logging.error(f"Error parsing silence_end line: {line} | {e}")
                continue
    logging.info(f"Detected {len(peaks)} audio peaks in {video_path}")
    return peaks
