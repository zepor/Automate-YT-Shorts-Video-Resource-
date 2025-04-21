"""
Utility module for documenting pipeline steps and managing project progress.
"""

import os

# Removed unused import 'sys'
import json

# Paths
PROJECT_DIR = os.getcwd()
PROGRESS_FILE = os.path.join(PROJECT_DIR, "progress.json")
README_FILE = os.path.join(PROJECT_DIR, "READMEBUILD.md")

# Expected Key Steps
expected_steps = [
    "Ingest VOD",
    "Highlight Detection",
    "Highlight Approval",
    "Slice Highlights",
    "Subtitles Generation & Overlay",
    "Format Clips for Shorts",
    "Automate Platform Uploads",
    "Error Handling & Logging",
]


def evaluate_codebase() -> list:
    """Evaluate the current project structure against the ideal README workflow
    and actual codebase."""
    print("🔍 Starting Codebase Evaluation...")

    missing_steps_local = []
    completed_steps = {}

    # Check or create progress.json
    if not os.path.exists(PROGRESS_FILE):
        print("⚠️ progress.json not found. Creating new one...")
        with open(PROGRESS_FILE, "w", encoding="utf-8") as progress_file:
            json.dump({}, progress_file)

    with open(PROGRESS_FILE, "r", encoding="utf-8") as progress_file:
        progress = json.load(progress_file)

    # --- Step 1: Ingest VOD ---
    ingest_vod_complete = False
    # Check for Twitch VOD download logic in Backend/main.py
    # and Backend/video.py
    try:
        with open(
            os.path.join(PROJECT_DIR, "Backend", "main.py"), "r", encoding="utf-8"
        ) as main_file:
            main_py = main_file.read()
        with open(
            os.path.join(PROJECT_DIR, "Backend", "video.py"), "r", encoding="utf-8"
        ) as video_file:
            video_py = video_file.read()
        if (
            "fetch_twitch_videos" in main_py
            and "save_video" in main_py
            and "fetch_twitch_videos" in video_py
            and "save_video" in video_py
        ):
            ingest_vod_complete = True
    except (FileNotFoundError, IOError) as error:
        print("Error reading files for Ingest VOD check: " + str(error))

    if ingest_vod_complete:
        progress["Ingest VOD"] = {
            "status": "completed",
            "details": ("Twitch VOD download logic" "found in main.py and video.py."),
        }
    else:
        missing_steps_local.append("Ingest VOD")

    # --- Step 2: Highlight Detection ---
    highlight_detection_complete = False
    # Look for highlight detection logic (e.g., chat analysis, audio analysis)
    if (
        "highlight" in main_py
        or "highlight" in video_py
        or "chat_analysis" in main_py
        or "audio_analysis" in main_py
    ):
        highlight_detection_complete = True
    if highlight_detection_complete:
        progress["Highlight Detection"] = {
            "status": "completed",
            "details": "Highlight detection logic found.",
        }
    else:
        missing_steps_local.append("Highlight Detection")

    # --- Steps 3-8: Use progress.json as fallback ---
    for step in expected_steps[2:]:
        if step not in progress:
            missing_steps_local.append(step)
        else:
            completed_steps[step] = progress[step]

    # Save progress.json
    with open(PROGRESS_FILE, "w", encoding="utf-8") as progress_file:
        json.dump(progress, progress_file, indent=2)

    print("\n\u2705 Evaluation Results:")
    print(f"- Steps Completed: {len(progress)} / {len(expected_steps)}")
    missing_steps_message = "- Missing Steps: " + str(
        missing_steps_local if missing_steps_local else "None"
    )
    print(missing_steps_message)

    generate_improvement_plan(missing_steps_local)
    return missing_steps_local


def generate_improvement_plan(missing_steps_list):
    """Suggest a next action plan based on evaluation."""
    print("\n🛠️ Improvement Plan:")
    if missing_steps_list:
        for step in missing_steps_list:
            if step == "Ingest VOD":
                print(
                    "➤ You appear to be missing Twitch VOD ingestion logic. "
                    "If you want to implement this, copy and paste the "
                    "following prompt:"
                )
                print(
                    "\nPROMPT: Build a Python function to download Twitch "
                    + "VODs and save them to the temp folder,"
                    "using the Twitch "
                    + "API and yt-dlp. Ensure it works on Windows and is "
                    + "modular.\n"
                )
            elif step == "Highlight Detection":
                print(
                    "\nPROMPT: Build a Python module to detect highlights in "
                    + "a Twitch VOD using chat activity spikes (pandas/numpy) "
                    + "and audio peaks (FFmpeg or PyDub). Output a "
                    + "highlights.json file with timestamps.\n"
                )
            else:
                print(f"➤ Create missing module for: {step}")
    else:
        print(
            "\ud83c\udf89 All high-level steps are represented. Focus next on "
            + "detailed quality improvements."
        )


def main():
    """Main function to execute the evaluation process."""
    missing_steps_local = evaluate_codebase()
    if missing_steps_local:
        print("".join(f"- {step}\n" for step in missing_steps_local))
    else:
        print(
            "- Refine current implementations for performance, user"
            + " engagement, or automation depth.\n"
        )

    print("\n🧠 Next Agent Prompt Suggestion:\n")
    print("plaintext")
    print("Which missing or incomplete step would you like to start or improve?\n")
    print("Options:")
    print("".join(f"- {step}\n" for step in expected_steps))


if __name__ == "__main__":
    main()
