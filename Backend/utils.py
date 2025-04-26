"""
Utility module for documenting pipeline steps and managing project progress.
"""

import os
import json
from datetime import datetime
import re
import logging
from typing import Dict, List, Optional

# Config-driven, always-writable temp directory for progress and log state
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp')
PROGRESS_PATH = os.path.join(TEMP_DIR, 'progress.json')
LOG_STATE_PATH = os.path.join(TEMP_DIR, 'evaluation_log_state.json')
README_PATH = os.path.join(PROJECT_ROOT, 'READMEBUILD.md')


def document_step(
    step_name: str,
    files_modified: List[str],
    rationale: str,
    prompt: str,
    status: str,
    code_comments: Optional[Dict[str, str]] = None,
    user_prompt: Optional[str] = None,
) -> None:
    """
    Appends a detailed, foldable entry for a pipeline step to READMEBUILD.md
    and updates progress.json. Optionally adds code comments to the top of
    each modified file.
    Uses config-driven, always-writable paths for Windows and Docker compatibility.
    """
    # Ensure temp dir exists
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Update progress.json in temp dir
    try:
        if os.path.exists(PROGRESS_PATH):
            with open(PROGRESS_PATH, "r", encoding="utf-8") as progress_file:
                progress = json.load(progress_file)
        else:
            progress = {}
    except (OSError, json.JSONDecodeError) as e:
        logging.warning("Could not read progress.json: %s", e)
        progress = {}

    progress[step_name] = {
        "status": status,
        "details": rationale,
        "timestamp": datetime.now().isoformat(),
        "files_modified": files_modified,
        "prompt": prompt,
        "user_prompt": user_prompt,
    }
    try:
        with open(PROGRESS_PATH, "w", encoding="utf-8") as progress_file:
            json.dump(progress, progress_file, indent=2)
    except OSError as e:
        logging.error("Could not write progress.json: %s", e)

    # Add foldable details to READMEBUILD.md
    if os.path.exists(README_PATH):
        with open(README_PATH, "r", encoding="utf-8") as readme_file:
            readme = readme_file.read()
    else:
        readme = ""

    details_pattern = re.compile(
        rf"<!--STEP_{step_name}_START-->.*<!--STEP_{step_name}_END-->", re.DOTALL
    )
    readme = details_pattern.sub("", readme)
    details = (
        f"\n<!--STEP_{step_name}_START-->\n"
        f"<details>\n<summary><b>{step_name} ({status})</b></summary>\n\n"
        f"- **Status:** {status}\n"
        f"- **Files Modified:** {', '.join(files_modified)}\n"
        f"- **Rationale:** {rationale}\n"
        f"- **Prompt Used:** `{prompt}`\n"
        f"- **User Prompt:** `{user_prompt or ''}`\n"
        f"- **Timestamp:** {progress[step_name]['timestamp']}\n"
        f"</details>\n<!--STEP_{step_name}_END-->\n"
    )
    readme = details + readme
    try:
        with open(README_PATH, "w", encoding="utf-8") as readme_file:
            readme_file.write(readme)
    except OSError as e:
        logging.error("Could not write to READMEBUILD.md: %s", e)

    # Optionally add code comments to each file
    if code_comments:
        for file_path, comment in code_comments.items():
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                if not content.startswith(comment):
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(comment + "\n" + content)
            except (FileNotFoundError, PermissionError, IOError) as e:
                logging.warning("Could not add comment to %s: %s", file_path, e)
