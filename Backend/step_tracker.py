import os
import json
from datetime import datetime

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
    user_prompt=None
):
    # Update progress.json
    if os.path.exists(PROGRESS_PATH):
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            progress = json.load(f)
    else:
        progress = {}

    progress[step_name] = {
        "status": status,
        "details": rationale,
        "files_modified": files_modified,
        "prompt": prompt,
        "user_prompt": user_prompt,
        "timestamp": datetime.now().isoformat(),
        "code_refs": code_refs or []
    }
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

    # Update README summary and foldable details
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # Remove old summary and details for this step
    import re
    summary_pattern = re.compile(r"<!--SUMMARY_TABLE_START-->.*<!--SUMMARY_TABLE_END-->", re.DOTALL)
    details_pattern = re.compile(rf"<!--STEP_{step_name}_START-->.*<!--STEP_{step_name}_END-->", re.DOTALL)
    readme = summary_pattern.sub("", readme)
    readme = details_pattern.sub("", readme)

    # Build summary table
    summary = "<!--SUMMARY_TABLE_START-->\n"
    summary += "| Step | Status |\n|---|---|\n"
    for s in progress:
        summary += f"| {s} | {progress[s]['status']} |\n"
    summary += "<!--SUMMARY_TABLE_END-->\n"

    # Build foldable details
    details = (
        f"\n<!--STEP_{step_name}_START-->\n"
        f"<details>\n<summary><b>{step_name} ({status})</b></summary>\n\n"
        f"- **Status:** {status}\n"
        f"- **Files Modified:** {', '.join(files_modified)}\n"
        f"- **Rationale:** {rationale}\n"
        f"- **Prompt Used:** `{prompt}`\n"
        f"- **User Prompt:** `{user_prompt or ''}`\n"
        f"- **Timestamp:** {progress[step_name]['timestamp']}\n"
        f"- **Code References:**\n"
    )
    if code_refs:
        for ref in code_refs:
            details += f"  - `{ref}`\n"
    details += "\n</details>\n<!--STEP_{step_name}_END-->\n"

    # Insert summary and details at the top
    readme = summary + details + readme

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme)

# Example usage:
if __name__ == "__main__":
    update_step(
        step_name="Ingest VOD",
        status="completed",
        files_modified=["Backend/main.py", "Backend/video.py"],
        rationale="Implemented Twitch VOD download and save logic.",
        prompt="Build a Python function to download Twitch VODs and save them to the temp folder, using the Twitch API and yt-dlp.",
        code_refs=["main.py:fetch_twitch_videos", "video.py:save_video"],
        user_prompt="Build a Python function to download Twitch VODs and save them to the temp folder, using the Twitch API and yt-dlp."
    )