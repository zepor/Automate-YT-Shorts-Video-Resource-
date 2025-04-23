import hashlib
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

def run_evaluation_if_code_changed(
    code_dir: Path,
    hash_file: Path,
    evaluation_script: Path
) -> None:
    """
    Checks if the codebase has changed by comparing hashes. If changed, runs evaluation.py.
    Args:
        code_dir (Path): Directory to hash (e.g., project root).
        hash_file (Path): File to store the last hash.
        evaluation_script (Path): Path to evaluation.py script.
    """
    def hash_directory(directory: Path) -> str:
        sha256 = hashlib.sha256()
        for file in sorted(directory.rglob('*.py')):
            with open(file, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
        return sha256.hexdigest()
    logging.info(f"Checking for codebase changes in {code_dir}")
    current_hash = hash_directory(code_dir)
    last_hash: Optional[str] = None
    if hash_file.exists():
        try:
            with open(hash_file, 'r') as f:
                last_hash = json.load(f).get('hash')
        except Exception as e:
            logging.warning(f"Could not read hash file: {e}")
    if current_hash != last_hash:
        logging.info(f"Codebase changed. Running evaluation: {evaluation_script}")
        try:
            result = subprocess.run([sys.executable, str(evaluation_script)], check=True)
            logging.info(f"Evaluation completed with exit code {result.returncode}")
            with open(hash_file, 'w') as f:
                json.dump({'hash': current_hash}, f)
        except subprocess.CalledProcessError as e:
            logging.error(f"evaluation.py failed with exit code {e.returncode}")
            raise
        except OSError as e:
            logging.error(f"Error running evaluation.py: {e}")
            raise
    else:
        logging.info("No codebase changes detected. Skipping evaluation.")
