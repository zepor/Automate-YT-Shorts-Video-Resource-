"""
Module for tracking and updating the progress of pipeline steps,
including generating summaries and detailed documentation in project files.
"""

import os
import json
from datetime import datetime
import re
from Backend.utils import document_step

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(PROJECT_DIR, "READMEBUILD.md")
PROGRESS_PATH = os.path.join(PROJECT_DIR, "progress.json")


def update_step(
    step_name,
    status,
    files_modified,
    rationale,
    prompt,
    code_refs=None,
    user_prompt=None,
):
    """
    Function generating the summaries and detailed documentation for the
    pipeline steps.
    It updates the progress.json file and the README file with the current
    status of the pipeline.
    """
    # Update progress.json
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r", encoding="utf-8") as progress_file:
            progress = json.load(progress_file)
    else:
        progress = {}

    if step_name not in progress:
        progress[step_name] = []

    progress[step_name].append(
        {
            "status": status,
            "details": rationale,
            "files_modified": files_modified,
            "prompt": prompt,
            "user_prompt": user_prompt,
            "timestamp": datetime.now().isoformat(),
            "code_refs": code_refs or [],
        }
    )

    with open(PROGRESS_PATH, "w", encoding="utf-8") as progress_file:
        json.dump(progress, progress_file, indent=2)

    # Update README summary and foldable details
    if os.path.exists(README_PATH):
        with open(README_PATH, "r", encoding="utf-8") as readme_file:
            readme = readme_file.read()
    else:
        readme = ""

    summary_pattern = re.compile(
        r"<!--SUMMARY_TABLE_START-->.*<!--SUMMARY_TABLE_END-->", re.DOTALL
    )
    details_pattern = re.compile(
        rf"<!--STEP_{step_name}_START-->.*" rf"<!--STEP_{step_name}_END-->", re.DOTALL
    )
    readme = summary_pattern.sub("", readme)
    readme = details_pattern.sub("", readme)

    # Build summary table
    summary = "<!--SUMMARY_TABLE_START-->\n"
    summary += "| Step | Status |\n|---|---|\n"
    for step in progress:
        latest_status = progress[step][-1]["status"]
        summary += "| " + str(step) + " | " + str(latest_status) + " |\n"
    summary += "<!--SUMMARY_TABLE_END-->\n"

    # Insert summary and details at the top
    step_documentation = (
        document_step(
            step_name, status, files_modified, rationale, prompt, user_prompt, code_refs
        )
        or ""
    )
    readme = summary + step_documentation + readme

    with open(README_PATH, "w", encoding="utf-8") as readme_file:
        readme_file.write(readme)


# Example usage:
if __name__ == "__main__":
    update_step(
        step_name="Ingest VOD",
        status="completed",
        files_modified=["Backend/main.py", "Backend/video.py"],
        rationale="Implemented Twitch VOD download and save logic.",
        prompt=(
            "Build a Python function to download Twitch VODs and save them to "
            "the temp folder, using the Twitch API and yt-dlp."
        ),
        code_refs=["main.py:fetch_twitch_videos", "video.py:save_video"],
        user_prompt=(
            "Build a Python function to download Twitch VODs and save them to "
            "the temp folder, using the Twitch API and yt-dlp."
        ),
    )
