"""
This module handles the evaluation logic for the codebase, including parsing README steps,
scanning logs for errors, and generating actionable next-step prompts.
It is designed to be used in a Flask application context.
"""
import os
import json
import re
import logging
import sys
import traceback
from typing import Dict, List, Optional

logging.info("Python executable: %s", sys.executable)
logging.info("sys.path: %s", sys.path)

# Only load .env locally (not in Docker)
if os.path.exists('.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logging.info("Loaded environment variables from .env")
    except ImportError:
        logging.warning("python-dotenv not installed; skipping .env load.")

try:
    import openai
    # OpenAI v1.x: error classes are at the top level, e.g. openai.OpenAIError
except ImportError as e:
    logging.error("ImportError for openai: %s", e)
    logging.error(traceback.format_exc())
    openai = None  # Will raise error if used without install

# Use config-driven, always-writable temp dir for log state
TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../temp'))
LOG_STATE_FILE = os.path.join(TEMP_DIR, 'evaluation_log_state.json')

def get_project_root() -> str:
    """
    Returns the absolute path to the project root directory.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

PROJECT_ROOT = get_project_root()
BACKEND_ROOT = os.path.join(PROJECT_ROOT, "Backend")
PROGRESS_FILE = os.path.join(PROJECT_ROOT, "progress.json")
README_FILE = os.path.join(PROJECT_ROOT, "READMEBUILD.md")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "Requirements.md")
READMEBUILD_FILE = os.path.join(PROJECT_ROOT, "READMEBUILD.md")
LOG_PATHS = [
    os.path.join(BACKEND_ROOT, 'backend.log'),
    os.path.join(PROJECT_ROOT, 'Dashboard/dashboard.log'),
]
RECOMMENDATION_TEMPLATE = (
    "## Prompt Recommendation\n\n"
    "{summary}\n\n"
    "**Next Step:** {next_step}\n\n"
    "**Rationale:** {rationale}\n\n"
    "{errors_section}"
)
expected_steps = [
    "Ingest VOD",
    "Highlight Detection",
    "Highlight Approval",
    "Slice Highlights",
    "Subtitles Generation & Overlay",
    "Format Clips for Shorts",
    "Automate Platform Uploads",
    "Error Handling & Logging",
    "UI/Dashboard Integration",
]

def parse_requirements_steps(requirements_path: str) -> List[str]:
    """
    Parse Requirements.md to extract the canonical list of pipeline steps.
    Returns a list of step names in order.
    """
    steps = []
    if not os.path.exists(requirements_path):
        return steps
    with open(requirements_path, encoding="utf-8") as f:
        content = f.read()
    # Look for lines like '### 2.x Step N: Step Name' in the requirements
    for line in content.splitlines():
        m = re.match(r"### 2\\.\\d+ Step \\d+: (.+)", line.strip())
        if m:
            steps.append(m.group(1).strip())
    return steps

def parse_readmebuild_status(readmebuild_path: str) -> Dict[str, str]:
    """
    Parse READMEBUILD.md to determine which steps have been implemented and their status.
    Returns a dict mapping step names to status (e.g., 'completed', 'pending', 'failed').
    """
    status = {}
    if not os.path.exists(readmebuild_path):
        return status
    with open(readmebuild_path, encoding="utf-8") as f:
        content = f.read()
    # Look for foldable details blocks for each step
    pattern = re.compile(
        r"<!--STEP_(.+?)_START-->.*?<summary><b>(.+?) \\((.+?)\\)</b></summary>", re.DOTALL
    )
    for m in pattern.finditer(content):
        step_name = m.group(2)
        step_status = m.group(3).lower()
        status[step_name] = step_status
    return status

def parse_readme_steps(readme_path: str) -> List[str]:
    """Extract step names from the README markdown file."""
    steps = []
    if not os.path.exists(readme_path):
        return steps
    with open(readme_path, encoding="utf-8") as f:
        content = f.read()
    # Look for lines like '### Step 1: ...' or '### Step: ...'
    for line in content.splitlines():
        m = re.match(r"#+ Step(?: \d+)?:? (.+)", line.strip())
        if m:
            steps.append(m.group(1).strip())
    return steps

def scan_logs_for_errors(log_paths: List[str], max_lines: int = 200) -> List[str]:
    """
    Scan only new lines of log files for error/warning messages since last evaluation.
    Log state is stored in /app/temp/evaluation_log_state.json for Docker compatibility.
    """
    errors = []
    # Load last read positions
    try:
        with open(LOG_STATE_FILE, 'r', encoding='utf-8') as f:
            log_state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log_state = {}
    new_log_state = {}
    for log_path in log_paths:
        if not os.path.exists(log_path):
            continue
        last_pos = log_state.get(log_path, 0)
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            f.seek(last_pos)
            new_lines = f.readlines()
            new_log_state[log_path] = f.tell()
        for line in new_lines[-max_lines:]:
            if any(w in line.lower() for w in ["error", "exception",
                "traceback", "permission denied", "not found", "failed"]):
                errors.append(line.strip())
    # Save new positions
    try:
        with open(LOG_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_log_state, f)
    except (OSError, IOError, json.JSONDecodeError) as e:
        # Log the error for debugging, but do not interrupt flow
        logging.warning("Failed to save log state: %s", e)
    return errors

def generate_next_step_prompt(
    readme_steps: List[str],
    progress: dict,
    errors: List[str],
) -> str:
    """Generate a context-aware, actionable next-step prompt."""
    # Find the first missing or incomplete step
    for step in readme_steps:
        if step not in progress or progress[step].get("status") != "completed":
            next_step = step
            break
    else:
        next_step = "All steps completed! Review for polish or new features."
    summary = (
        f"Pipeline is currently at:"
        f"{progress.get(next_step, {}).get('status', 'pending')}"
        f"for step '{next_step}'."
        if next_step != "All steps completed! Review for polish or new features."
        else "Pipeline appears complete."
    )
    rationale = (
        "This step is required by the project workflow in your README. "
        "Please refer to the relevant section in READMEBUILD.md for details."
        if next_step != "All steps completed! Review for polish or new features."
        else (
            "You may want to review logs, polish the UI, or add new features."
        )
    )
    errors_section = ""
    if errors:
        errors_section = (
            "**Recent Errors/Warnings:**\n" + "\n".join(f"- {e}" for e in errors[:5]) +
            ("\n..." if len(errors) > 5 else "")
        )
    return RECOMMENDATION_TEMPLATE.format(
        summary=summary,
        next_step=next_step,
        rationale=rationale,
        errors_section=errors_section,
    )

def generate_ai_prompt_recommendation(
    readme_steps: List[str],
    progress: dict,
    errors: List[str],
    readme_content: str,
    openai_api_key: str,
    model: str = None
) -> Optional[str]:
    """
    Use OpenAI (>=1.0.0) to generate a context-aware, actionable next-step prompt.
    Returns the AI-generated prompt, or None if the API call fails.
    """
    if openai is None:
        logging.error("openai package not installed. Cannot generate AI prompt.")
        return None
    # Load agent mission from AGENT_PROMPT.md (hardcoded summary for performance)
    agent_mission = (
        "Build a fully-automated, self-learning content engine that continuously ingests Twitch streams and outputs viral, "
        "platform-optimized short-form videos that pull viewers back to Twitch, grow brand reach, and attract other streamers to use this solution. "
        "Every step must be modular, batch-friendly, and production-grade. "
        "Follow the agent protocol: always confirm the current step, summarize the goal, list options with pros/cons, recommend the best, and wait for user approval before coding. "
        "Document all changes in progress.json and READMEBUILD.md."
    )
    # Use model from environment or default to GPT-4.1 (gpt-4.1-2025-04-14)
    model_name = model or os.environ.get("OPENAI_MODEL", "gpt-4.1-2025-04-14")
    logging.info("Using OpenAI model: %s", model_name)
    system_prompt = (
        f"You are an expert software project assistant for a Twitch-to-Shorts automation pipeline. "
        f"{agent_mission} "
        "Your recommendations must align with growth hacking principles: maximize viewer retention, CTR, rewatch rate, and Twitch brand recall. "
        "Reference the README, Requirements.md, and AGENT_PROMPT.md. "
        "Be concise, specific, and always provide a clear, actionable next step."
    )
    user_prompt = (
        f"README (truncated):\n{readme_content[:2000]}\n\n"
        f"Pipeline Steps: {readme_steps}\n"
        f"Progress: {progress}\n"
        f"Recent Errors: {errors[:5]}\n"
        f"Platform Requirements: YouTube Shorts (9:16, <60s), TikTok (emojis, fast cuts), Instagram Reels (polished transitions), Twitter (1:1 and 9:16 exports).\n"
    )
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=300,
        )
        logging.info("OpenAI API response: %s", response)
        if response and response.choices:
            # OpenAI v1.x: message is an object, not a dict
            return response.choices[0].message.content
        return None
    except openai.APIConnectionError as exc:
        logging.error("OpenAI API connection error: %s", exc)
        return None
    except openai.AuthenticationError as exc:
        logging.error("OpenAI API authentication error: %s", exc)
        return None
    except openai.OpenAIError as e:
        logging.error("OpenAI API error: %s", e)
        return None

def evaluate_codebase() -> Dict[str, str]:
    """
    Evaluate the codebase against Requirements.md (source of truth for pipeline goals)
    and READMEBUILD.md (summary/status of implemented steps). Always use the AI agent
    (OpenAI) to generate the prompt recommendation, based on the current state and logs.
    Returns a dict with 'prompt_recommendation' and 'errors'.
    """
    # Parse canonical steps from Requirements.md
    canonical_steps = parse_requirements_steps(REQUIREMENTS_FILE)
    # Parse summary status from READMEBUILD.md
    implemented_status = parse_readmebuild_status(READMEBUILD_FILE)
    # Scan logs for errors
    errors = scan_logs_for_errors(LOG_PATHS)
    # Prepare context for AI agent
    requirements_content = ""
    if not os.path.exists(REQUIREMENTS_FILE):
        logging.error("Requirements.md is missing at %s. Please add"
                      " it to the project root.", REQUIREMENTS_FILE)
        errors.append(f"Requirements.md missing at {REQUIREMENTS_FILE}")
    else:
        try:
            with open(REQUIREMENTS_FILE, "r", encoding="utf-8") as f:
                requirements_content = f.read()
        except (OSError, IOError) as e:
            logging.error("Could not read Requirements.md due to file-related error: %s", e)
            errors.append(f"Could not read Requirements.md: {e}")
        except json.JSONDecodeError as e:
            logging.error("Could not read Requirements.md due to JSON decoding error: %s", e)
            errors.append(f"Could not read Requirements.md (JSON error): {e}")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai is None:
        logging.error("openai package is not installed. Please add"
                      " 'openai' to requirements.txt and install it.")
        errors.append("openai package not installed. Cannot generate AI prompt.")
        return {"prompt_recommendation": "AI agent unavailable: openai"
                "package not installed.", "errors": errors}
    if not openai_api_key:
        logging.error("OPENAI_API_KEY not set. Cannot generate AI prompt.")
        errors.append("OPENAI_API_KEY not set. Cannot generate AI prompt.")
        return {"prompt_recommendation": "AI agent unavailable: missing API key.", "errors": errors}
    ai_prompt = generate_ai_prompt_recommendation(
        canonical_steps,
        implemented_status,
        errors,
        requirements_content,
        openai_api_key
    )
    # Fallback: if OpenAI fails, use next-step prompt logic
    if not ai_prompt:
        ai_prompt = generate_next_step_prompt(
            canonical_steps,
            implemented_status,
            errors
        )
    if not ai_prompt:
        logging.error("AI agent failed to generate a prompt recommendation.")
        errors.append("AI agent failed to generate a prompt recommendation.")
        return {"prompt_recommendation": "AI agent failed to generate a prompt.", "errors": errors}
    return {"prompt_recommendation": ai_prompt, "errors": errors}
