import os
import json
from datetime import datetime

def document_step(step_name, files_modified, rationale, prompt, status, code_comments=None):
    """
    Appends a detailed entry for a pipeline step to READMEBUILD.md and updates progress.json.
    Optionally adds code comments to the top of each modified file.
    """
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(project_dir, "READMEBUILD.md")
    progress_path = os.path.join(project_dir, "progress.json")

    # Update progress.json
    if os.path.exists(progress_path):
        with open(progress_path, "r", encoding="utf-8") as f:
            progress = json.load(f)
    else:
        progress = {}

    progress[step_name] = {
        "status": status,
        "details": rationale,
        "timestamp": datetime.now().isoformat()
    }
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

    # Append to READMEBUILD.md
    entry = f"""
### Step: {step_name}
- **Status:** {status}
- **Files Modified:** {', '.join(files_modified)}
- **Rationale:** {rationale}
- **Prompt Used:** `{prompt}`
- **Timestamp:** {datetime.now().isoformat()}
"""
    with open(readme_path, "a", encoding="utf-8") as f:
        f.write(entry)

    # Optionally add code comments to each file
    if code_comments:
        for file_path, comment in code_comments.items():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if not content.startswith(comment):
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(comment + "\n" + content)
            except Exception as e:
                print(f"Could not add comment to {file_path}: {e}")