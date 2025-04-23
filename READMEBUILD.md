# 🎬 Twitch-to-Shorts Pipeline (Comprehensive Production Guide)

This document presents a comprehensive, open-source pipeline designed for the automated transformation of Twitch VODs into optimized short-form video content suitable for platforms including YouTube Shorts, TikTok, Instagram Reels, and Twitter. Utilizing Python and Docker on a Windows environment, the pipeline enhances modularity, detailed progress tracking, and strategically drives audience engagement and channel growth.

---

## ✅ Objectives

- Fully automate Twitch VOD ingestion.
- Implement advanced highlight detection using chat activity, auditory signals, and visual content variations.
- Systematically segment VODs into distinct, engaging highlight clips by precisely identifying the most compelling moments through detailed timestamp analysis, ensuring each segment accurately captures viewer interest and effectively maintains audience attention throughout the clips.
- Automatically generate subtitles using Whisper AI.
- Optimize video content formats for various social media platforms.
- Automate video uploads across multiple social media channels.
- Track pipeline execution, agent interactions, and outcomes.
- Maximize user traffic to the originating Twitch channel.

---

## 🛠️ Setup Requirements

- Windows 10/11 with Docker Desktop installed (WSL2 backend enabled)
- VS Code with GitHub Copilot extension (for agent-driven development)
- Python 3.11
- Docker (Linux containers mode)

Python environment path:

```bash
C:\Users\johnb\Repos\Automate-YT-Shorts-Video-Resource-\.venv\Scripts\python.exe
```

Install Python packages locally:

```bash
pip install vodbot moviepy streamlink yt-dlp openai-whisper opencv-python pandas numpy requests
```

---

## 📦 Technology Stack

| Tool | Purpose |
|-----|---------|
| VodBot | Twitch VOD management, clip slicing, YouTube upload |
| Streamlink/yt-dlp | Backup Twitch VOD download methods |
| Whisper (Auto-Subtitle) | Speech-to-text for auto-captioning |
| MoviePy | Video editing (split, overlay, resizing) |
| FFmpeg | Low-level video/audio trimming and processing |
| OpenCV (optional) | Face filter/humor detection |
| YouTube API (youtube-upload) | YouTube Shorts publishing |
| TikTok Uploader CLI | TikTok video publishing |
| pandas/numpy | Chat spike detection and data analysis |
| requests | Webhooks and error notification |

---

## 🐳 Dockerfile (Production Ready)

```dockerfile
FROM python:3.11-slim

# Install required packages with security and size optimizations
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    ffmpeg \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m twitchuser
USER twitchuser

# Set working directory
WORKDIR /app

# Copy project files
COPY --chown=twitchuser:twitchuser . .

# Install Python dependencies
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

# Healthcheck to ensure container stays healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 CMD python -c "import os; assert os.path.exists('evaluation.py')"

EXPOSE 8000

# Default command
CMD ["python", "evaluation.py"]
```

---

## 🚀 Deployment Instructions

- `.dockerignore` should exclude heavy folders like `/temp/`, `/fonts/`, `/har_and_cookies/`, `.vscode/`, and `__pycache__/`.
- Docker Compose automatically mounts `temp/` dynamically without bloating the image.

**Build the Image:**

```bash
docker-compose build --no-cache
```

**Run the Container:**

```bash
docker-compose up
```

**Stop the Container:**

```bash
docker-compose down
```

---

## 🗂️ Modular Project Folder Structure

```plaintext
/backend
  /vod_ingestion
    __init__.py
    vod_downloader.py
  /highlight_detection
    __init__.py
    chat_analysis.py
    audio_analysis.py
  /video_editing
    __init__.py
    clip_editor.py
    subtitle_overlay.py
  /publishing
    __init__.py
    youtube_uploader.py
    tiktok_uploader.py
  /dashboard
    __init__.py
    evaluation.py
    orchestration.py
  main.py
  utils.py
/fonts
  bold_font.ttf
/temp
  (video files stay local only, mounted at runtime)
/har_and_cookies
  (authentication and cookies stay local)
.github
.vscode
.gitignore
.dockerignore
Dockerfile
docker-compose.yml
LICENSE
README.md
requirements.txt
```

- `__init__.py` marks all functional folders as Python packages.
- Each functional domain (ingestion, detection, editing, publishing) is cleanly modular.
- `utils.py` is for general helper functions.

---

## 🎯 Strategy for Maximum Viewer Traffic to Twitch

- Mandatory CTA overlays ("Catch me live on Twitch!") every 20–30 seconds
- Pinned comments linking to Twitch
- YouTube Shorts optimization (first 3s hook, vertical 9:16)
- TikTok/Instagram Reels optimization (more emojis, faster cuts)
- Twitter optimization (square format option for previews)
- Platform-specific hashtag usage
- Cross-promoting live Twitch status in video text

---

## 🚧 Future Extensions

- GPU acceleration for Whisper
- Humor classifier for highlight ranking
- Instagram Reels and Facebook Stories automation
- Auto-generated custom thumbnails
- Twitch Clip Leaderboard integration
- Dynamic hashtag selection based on clip content

---

## 🧠 Agent Interaction & Progress Tracking

**Agent Must:**

- Always ask: "Which step (1–7) are we currently working on?"
- Summarize the goal for the chosen step.
- List all available methods with pros/cons and recommend the best based on automation, scalability, and quality prior to generating code for each step
- Document ALL changes made for each step,the files modified, and the rational behind the changes in the READMEBUILD.md file and comments in the code generated, if the code is alreayd generated add comments to explain what step the code is a part of and what its for. Through this process, the agent will be able to track progress and make informed decisions about the project's direction
- Wait for user approval before generating code.
- Be aware if the code generated is not working and actively bug fix with the user. The more proactive the agent is in fixing bugs, the more likely the user will be to trust the agent and continue with approvals.
- After each step, update README Entry Template

  ### Step: [Step Name]

  - **Status:** completed/pending/failed
  - **Files Modified:** file1.py, file2.py
  - **Rationale:** <Why this change was made, what it accomplishes>
  - **Prompt Used:** (The exact prompt you used to generate the code)
  - **Timestamp:** ISO timestamp (progress, decisions, prompt) and `progress.json`.

Example `progress.json`:

```json
{
  "Ingest VOD": {
    "status": "completed",
    "details": "Downloaded VOD and chat. No issues."
  },
  "Highlight Detection": {
    "status": "pending",
    "details": "Highlights generated. Awaiting user rating and approval."
  }
}
```

---

## 🧩 Step-by-Step Workflow (with Checklists & Success Criteria)

### Step 1: ⬇️ Ingest VOD

- [ ] Download Twitch VOD and Chat Log.
- ✅ Success if `vod.mp4` and `chat.json` exist.

### Step 2: 🚨 Highlight Detection (Automated)

## Step 2: Highlight Detection

## This function analyzes chat and audio to detect highlights in Twitch VODs

- [ ] Detect highlights from chat and audio spikes.
- ✅ Success if highlights JSON created.
- 🚑 Retry if 0 highlights.
- [ ] **Highlight Approval:**
  - Agent must present detected highlights.
  - User rates highlight quality (1–5 stars).
  - User must approve before proceeding to slicing.
  - If user disapproves, agent must retry or refine detection methods.
- After approval, present multiple video edit style options:
  - Fast-paced energetic cut (TikTok vibe)
  - Cinematic build-up and payoff (YouTube Shorts)
  - Meme/overlay explosion (meme culture targeting Instagram/Twitter)
- Recommend the best style based on detected highlight tone and audience engagement goals.
- Provide pros/cons of each editing style.

### Step 3: ✂️ Slice Highlights into Clips

- [ ] Slice based on timestamps.
- ✅ Success if clips saved.

### Step 4: 📝 Subtitles Generation & Overlay

- [ ] Generate and overlay subtitles.
- ✅ Success if subtitle-enhanced clips created.

### Step 5: 📐 Format Clips for Shorts

| Platform         | Format Instructions                        |
| ---------------- | ------------------------------------------ |
| YouTube Shorts   | 9:16, 1080x1920, fast-paced first 3 seconds |
| TikTok / Instagram | 9:16, 1080x1920, text-heavy, emoji overlays |
| Facebook Reels   | 4:5 or 9:16, slightly longer intros         |
| Twitter Video    | 1:1 or 9:16, punchy, humor hooks first      |

Each format may slightly alter cut timing, caption size, or added visual effects.

### Step 6: 🚀 Automate Platform Uploads

- [ ] Upload to YouTube and TikTok.
- ✅ Success if video appears published.

### Step 7: 🛠️ Error Handling & Logging

- [ ] Log events, retry on errors.
- [ ] Alert via Discord webhook if critical failure.

---

## 🧠 Focused Copilot/Agent Prompts

You are helping me build a full Twitch-to-Shorts automation tool in Python. I have a multi-step plan.

For each step, before writing any code:

- Ask me **"Which step are we currently working on?"** (I will answer with a number 1-7 from the README.)
- Once I answer, **briefly summarize what the goal is for that step** to confirm understanding.
- If there are multiple options for how to approach the step, **list all options with pros/cons and your recommendation** based on my project goals (automation, speed, quality).
- Wait for me to pick or approve an option before proceeding.
- After approval, **generate fully detailed, production-quality Python code** for that step.
- Add **inline comments explaining complex sections** of the code clearly.
- **After generating each step's code**, ask me: "Would you like to proceed to the next step or refine this one?"

Repeat this pattern for all steps until the project is fully completed.

Important:

- Always use open-source libraries unless I explicitly request something else.
- Always prioritize Windows compatibility (assume I'm running this on a Windows 11 system).
- Ensure that every script is **modular**, **reusable**, and supports **scalability** (batch processing of multiple VODs if needed).

Start by asking me **"Which step are we currently working on?"**

---

## 🧑‍💻 Technical Commands & Code Snippets

### VOD Download

```bash
vodbot download <VOD_URL>
# Fallback method (Streamlink/yt-dlp):
streamlink "twitch.tv/username/vod_id" best -o vod.ts
yt-dlp "<vod_url>"
# Download chat logs (if not using VodBot):
twitch-chat-downloader <VOD_URL> -o chat.json
```

### Highlight Detection

- Analyze chat JSON for spikes/emote bursts (pandas, numpy)
- Detect audio peaks using FFmpeg/PyDub:

```bash
ffmpeg -i vod.mp4 -af "silencedetect=noise=-30dB:d=0.5" -f null -
```

- Optional: Face filter detection (OpenCV)
- Output highlights timestamps to JSON:

```json
{
  "highlights": [
    {"start": "00:45:10", "end": "00:45:40", "type": "humor"},
    {"start": "01:10:05", "end": "01:10:20", "type": "epic"}
  ]
}
```

### Slicing Clips

```bash
vodbot slice <VOD_ID> --start 00:45:10 --end 00:45:40 --title "Funny Moment"
# Or use FFmpeg batch slicing:
ffmpeg -ss 00:45:10 -to 00:45:40 -i vod.mp4 -c copy funny_clip.mp4
```

### Subtitles Generation & Overlay

```bash
auto_subtitle funny_clip.mp4 -o subtitled_clips/
```

- Add special effects/emojis if humor detected (MoviePy/FFmpeg overlays):

```python
# MoviePy example (pseudo-code)
clip = VideoFileClip('funny_clip.mp4')
txt_clip = TextClip("😂", fontsize=50, color='white').set_pos('center').set_duration(5)
final_clip = CompositeVideoClip([clip, txt_clip])
final_clip.write_videofile('enhanced_funny_clip.mp4')
```

### Platform Uploads

```bash
vodbot upload <clip_id> --to youtube
# OR
youtube-upload --title="Funny Moment" --privacy="public" final_short.mp4
# TikTok upload via CLI:
tiktok-uploader -v final_short.mp4 -d "Epic moment 😂 #gaming" -c cookies.txt
```

### Error Handling & Logging

```python
import logging

logging.basicConfig(filename='automation_log.log', level=logging.INFO)

try:
    # critical operations (e.g., upload)
except Exception as e:
    logging.error(f"Error: {e}")
    # retry logic or notification here
```

---

## Dashboard Integration & Project Flow

The dashboard provides a project flow/status process view of the pipeline, with videos grouped by stage:

- **Detection:** Videos awaiting highlight review. Expand to see highlights, approval status, and ratings. Videos remain here until all highlights are reviewed.
- **Editing:** Videos with all highlights approved. Expand to see each highlight, subtitle/overlay edit status, planogram assignment, and edited video location. Batch-friendly for multiple highlights per video.
- **Publishing:** Videos/sub-videos ready for or already published. Expand to see publishing status and output locations.

### Manual Step Triggers

- The dashboard includes buttons to manually trigger each pipeline step (evaluation, detection, editing, publishing). These call backend routes that run the corresponding scripts in a batch-friendly, robust way.

### Batch Handling & Status Tracking

- Each video is only in one stage at a time, ensuring clear process flow.
- Status and sub-statuses (e.g., highlight approval, edit completion) are shown in expandable/collapsible cards for clarity and scalability.

### Usage Instructions

1. **Start the application** (Docker or local): The dashboard is available at `http://localhost:5001`.
2. **Review videos in Detection:** Expand a video to review and approve/reject highlights.
3. **Move to Editing:** Once all highlights are approved, the video appears in Editing. Edit subtitles/overlays and assign planograms as needed.
4. **Publish:** When all edits are complete, videos move to Publishing. Monitor publishing status and outputs.
5. **Manual triggers:** Use the dashboard buttons to manually run any pipeline step as needed.

### Platform Compatibility & Best Practices

- All scripts use only relative/config-driven paths for Windows 11 and Docker compatibility.
- Modular, production-grade Python 3.11+ code with type hints, docstrings, and robust logging/error handling.
- Batch-friendly logic for handling multiple VODs and highlights.
- See AGENT_PROMPT.md for platform-specific video requirements (YouTube Shorts, TikTok, Instagram, Twitter).

### Pipeline Step Links

- **Ingestion:** See `main.py`, `video.py` for VOD download logic.
- **Detection:** See `highlight_detection/highlight_detector.py` for highlight detection.
- **Editing:** See `video_editing/editor.py` for editing logic.
- **Publishing:** See `uploader/publish.py` for upload automation.
- **Dashboard:** See `Backend/highlight_approval/approval_app.py` and `templates/approval.html` for dashboard logic and UI.

---

### Step: Highlight Detection

- **Status:** pending
- **Files Modified:** Backend/highlight_detection/**init**.py, Backend/highlight_detection/chat_analysis.py, Backend/highlight_detection/audio_analysis.py, Backend/highlight_detection/highlight_detector.py, Backend/highlight_detection/highlight_ratings.json, Backend/highlight_detection_README.md, Backend/main.py, progress.json
- **Rationale:** Refactored highlight detection logic into a modular package as per project structure. Added robust logging, highlight rating, and approval logic. Updated documentation with detailed approach comparisons and future enhancements. Integrated detection into main.py for automated pipeline execution. Updated progress.json for traceability.
- **Prompt Used:** Refactor and modularize the highlight detection logic into /Backend/highlight_detection/ (with chat_analysis.py, audio_analysis.py, highlight_detector.py, init.py). Implement robust logging and highlight rating logic. Update highlight_detection_README.md with all comparison details, rationale, and future enhancements. Integrate the new detection logic into main.py. Ensure all changes, rationale, and prompts are documented in READMEBUILD.md and progress.json for traceability.
- **Timestamp:** 2025-04-20T23:20:00Z

🚀 **Final Mission:** Create viral, dynamic, platform-optimized short videos that magnetically drive new traffic to your Twitch channel while building a brand presence across all major platforms.

## Hybrid Dashboard UI (Sidebar + Kanban + Docs)

A professional, user-friendly dashboard is now implemented with the following features:

- **Sidebar Navigation:**
  - Switch between Pipeline (project flow/status) and Docs (markdown file viewer).
- **Kanban Columns:**
  - Detection, Editing, and Publishing columns show videos in their current pipeline stage.
  - Each video is a card, expandable to show highlights, edit status, planogram, and publishing info.
  - Only one stage per video at a time; batch-friendly for multiple VODs.
- **Documentation Viewer:**
  - All .md files in the repo are listed and viewable in the dashboard, rendered as HTML.
- **Responsive UI:**
  - Uses Bootstrap 5 for a modern, professional look and mobile compatibility.
- **Extensible:**
  - Modular backend and frontend, easy to add new pipeline steps or documentation.

### User Flow

1. **Pipeline View:**
   - Track each video as it moves through Detection, Editing, and Publishing.
   - Expand a video card to see highlight approval, editing progress, and publishing status.
2. **Docs View:**
   - Browse and read project documentation directly in the dashboard.
3. **Manual Triggers:**
   - (Planned) Add action buttons to cards for manual step triggers (e.g., re-run detection, start editing).

### Rationale

- **Professional, SaaS-style UI** for clarity and ease of use.
- **Batch-friendly** for handling multiple videos and highlights.
- **Integrated documentation** for developer onboarding and reference.
- **Windows 11 and Docker compatible** with only relative/config-driven paths.

### Files Modified

- Backend/highlight_approval/approval_app.py
- Backend/highlight_approval/templates/approval.html
- progress.json
- READMEBUILD.md

### Prompt Used

Implement a hybrid dashboard UI with sidebar navigation (Pipeline, Docs), Kanban columns for Detection, Editing, Publishing, and integrated markdown documentation viewer. Use Bootstrap 5 for a professional, responsive interface. All code must be modular, batch-friendly, and production-grade. Backend should serve .md files as rendered HTML. Document all changes in progress.json and READMEBUILD.md.

### Timestamp

2024-06-10T00:00:00Z

---

## Dashboard Web Application Migration (April 2025)

## Migration Summary

- Migrated dashboard frontend to Vite + React + TypeScript in `Dashboard/frontend`.
- Added a Node.js Express server (`Dashboard/server.js`) to serve the static frontend and proxy API requests to the backend Python API.
- Updated Dockerfile.dashboard to build the frontend and run the Node server.
- Compose now triggers a rebuild on `Dashboard/package.json` changes.

## Local Development

1. Install Node.js 20+ and npm if not already installed.
2. In `Dashboard/frontend`:

   ```sh
   npm install
   npm run dev
   ```

   This starts the Vite dev server for local frontend development.
3. To run the Express server locally:

   ```sh
   cd Dashboard
   npm install express http-proxy-middleware
   node server.js
   ```

4. For Docker development, use:

   ```sh
   docker compose up --build
   ```

## Required npm Packages

- express
- http-proxy-middleware
- (plus all Vite/React/TypeScript dependencies in `Dashboard/frontend/package.json`)

## API Proxy

- The Express server proxies `/api` requests to the backend Python API (default: `http://twitch-shorts:8000`).
- Adjust `BACKEND_API_URL` env var if needed.

## Future Actions

- Continue to migrate or proxy additional endpoints as needed.
- See `progress.json` for pipeline step tracking.

## Dashboard Python File Migration (April 2025)

## Summary

- All Python files previously in Dashboard/ have been moved to Backend/dashboard/.
- Modular Flask blueprints now expose evaluation and orchestration logic as API endpoints:
  - POST /api/evaluation
  - POST /api/orchestration
- The Dashboard folder now contains only frontend code and the Node server.

## API Usage

- The Node/TypeScript dashboard can call these endpoints to trigger evaluation and orchestration logic.

## Justification

- This migration ensures a clean separation of concerns and a production-grade, maintainable architecture.

## Next Steps

- Continue to add new blueprints/routes for additional backend logic as needed.
- See progress.json for tracking.

## 2025-04-22: Dockerfile.backend Fix for moviepy.editor Import Error

- Pinned moviepy to version 2.0.0 and force-reinstalled all dependencies in Dockerfile.backend.
- Added a build-time import test for 'import moviepy.editor as mp' to ensure the editor submodule is present and importable in the container.
- This resolves the Docker build import error and ensures robust, production-grade builds for ingestion, detection, and editing pipeline steps.

**Prompt Used:**

Pin moviepy to 2.0.0 and force-reinstall all dependencies in Dockerfile.backend to resolve the Docker build import error for moviepy.editor as mp. Document this change in progress.json and READMEBUILD.md.
