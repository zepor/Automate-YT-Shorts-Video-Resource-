"""
Utility module for documenting pipeline steps and managing project progress.
"""

import os
import json
from datetime import datetime
import re


def document_step(
    step_name,
    files_modified,
    rationale,
    prompt,
    status,
    code_comments=None,
    user_prompt=None,
):
    """
    Appends a detailed, foldable entry for a pipeline step to READMEBUILD.md
    and updates progress.json. Optionally adds code comments to the top of
    each modified file.
    """
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(project_dir, "READMEBUILD.md")
    progress_path = os.path.join(project_dir, "progress.json")

    # Update progress.json
    if os.path.exists(progress_path):
        with open(progress_path, "r", encoding="utf-8") as progress_file:
            progress = json.load(progress_file)
    else:
        progress = {}

    progress[step_name] = {
        "status": status,
        "details": rationale,
        "timestamp": datetime.now().isoformat(),
        "files_modified": files_modified,
        "prompt": prompt,
        "user_prompt": user_prompt,
    }
    with open(progress_path, "w", encoding="utf-8") as progress_file:
        json.dump(progress, progress_file, indent=2)

    # Add foldable details to READMEBUILD.md
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as readme_file:
            readme = readme_file.read()
    else:
        readme = ""

    details_pattern = re.compile(
        rf"<!--STEP_{step_name}_START-->.*" rf"<!--STEP_{step_name}_END-->", re.DOTALL
    )
    readme = details_pattern.sub("", readme)
    details = (
        "\n<!--STEP_"
        + str(step_name)
        + "_START-->\n"
        + "<details>\n<summary><b>"
        + str(step_name)
        + " ("
        + str(status)
        + ")</b></summary>\n\n"
        + "- **Status:** "
        + str(status)
        + "\n"
        + "- **Files Modified:** "
        + ", ".join(files_modified)
        + "\n"
        + "- **Rationale:** "
        + str(rationale)
        + "\n"
        + "- **Prompt Used:** `"
        + str(prompt)
        + "`\n"
        + "- **User Prompt:** `"
        + str(user_prompt or "")
        + "`\n"
        + "- **Timestamp:** "
        + str(progress[step_name]["timestamp"])
        + "\n"
        + "</details>\n<!--STEP_"
        + str(step_name)
        + "_END-->\n"
    )
    readme = details + readme
    with open(readme_path, "w", encoding="utf-8") as readme_file:
        readme_file.write(readme)

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
                print(f"Could not add comment to {file_path}: {e}")
