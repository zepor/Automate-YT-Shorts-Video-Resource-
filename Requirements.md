# Twitch-to-Shorts Automation Pipeline Requirements Document

## 1. System Overview

This document specifies a production-grade Twitch-to-Shorts video automation pipeline and guidelines for the AI agent that maintains and iterates on it. The pipeline automatically converts long-form Twitch VODs (Video on Demand recordings) into optimized short-form videos suitable for platforms like YouTube Shorts, TikTok, Instagram Reels, and Twitter. It achieves this through a sequence of steps: ingesting Twitch content, detecting highlight moments (via chat and audio analysis), clipping those highlights, adding subtitles, formatting for each platform, and finally uploading the results.

**Architecture Summary:**
The system is composed of modular Python components for each stage of processing, orchestrated by an intelligent agent. The agent ensures each step is executed in order, meets its success criteria, and handles any necessary user approvals or error retries. Progress is tracked in a JSON log (progress.json) for transparency and potential recovery. The pipeline runs in a containerized environment (Docker) for consistency, and relies on both Python libraries and external tools (e.g. FFmpeg, platform-specific upload CLIs).

**Key Goals:**

- Fully automate Twitch VOD processing end-to-end without manual video editing.
- Leverage chat activity spikes and audio cues to identify the most engaging - moments.
- Produce short clips with subtitles and appropriate aspect ratio/format for each target platform.
- Auto-upload the finalized shorts to multiple social platforms to maximize reach.
- Track each step’s status and outcomes for monitoring and debugging.
- Allow the AI agent to iteratively improve the pipeline (optimize methods, fix errors, adapt to changes) while documenting its changes.

---

## 2. Functional Requirements by Pipeline Stage

Each functional requirement below corresponds to a pipeline step the AI agent must perform or oversee. For each step, the requirement includes a description, expected inputs/outputs, success criteria, and retry conditions (how the agent should respond to failures or edge cases).

### 2.1 Step 1: Ingest Twitch VOD

**Description:** Download the Twitch VOD video and associated chat log for a given stream. This forms the raw material for all subsequent steps.

- **Inputs:** A reference to the Twitch VOD (e.g. VOD URL or ID, and possibly Twitch API credentials or OAuth if required for chat download). Configuration may include the desired video quality.

- **Process:** Use an automated tool or API to fetch the VOD content. Primary method is via a Twitch VOD management library (e.g. VodBot) or Twitch API. If that fails, fallback to reliable download utilities like streamlink or yt-dlp to retrieve the video file. In parallel, retrieve the chat messages (if available via Twitch API or third-party services) for the duration of the VOD.

- **Outputs:** The full video file saved locally (e.g. vod.mp4) and a synchronized chat log (e.g. chat.json or similar) containing timestamped chat messages.

- **Success Criteria:** The video file and chat log are successfully saved to the designated location. Specifically, vod.mp4 and chat.json (or equivalent) exist and are readable. No major corruption or missing content in the video.

- **Retry/Failure Handling:** If the initial download method fails or the file is incomplete:
  - Use a backup approach (for example, switch from VodBot to yt-dlp or vice-versa).
  - If network issues occur, retry the download up to a set number of times with exponential backoff.
  - If the chat log fails to download (API errors), log the error and attempt again after a short delay. If chat still cannot be obtained, proceed with video only (but mark in progress.json that chat data is unavailable).
  - The agent should mark this step as failed in progress.json if all retry attempts fail, and alert the user or administrator (e.g. via a webhook) for manual intervention.

---

### 2.2 Step 2: Highlight Detection

**Description:** Automatically identify the most engaging highlight moments within the Twitch VOD by analyzing both chat activity and the video/audio content. This step produces timestamps for segments likely to be good highlights.

- **Inputs:** The full VOD video file from Step 1 and the chat log (if available). Configuration parameters for detection (e.g. chat spike threshold, audio volume spike threshold, max number of highlights desired) are also considered.

- **Process**: Analyze the inputs using two parallel approaches:
  1. **Chat Activity Analysis**: Parse the chat log to find time periods with unusually high message rates or specific keywords/emotes indicating excitement. For example, detect "chat spikes" where message frequency exceeds a threshold, under the assumption that those correspond to exciting moments.
  2. **Audio/Visual Analysis**: Scan the VOD for notable audio spikes (crowd noise, loud reactions) or visual scene changes. This could involve using audio amplitude analysis and, optionally, computer vision (via OpenCV) to detect sudden scene changes or on-screen effects.
  - Combine these analyses to propose highlight timestamps (start and end times). A highlight might be chosen where both chat and audio indicate something interesting.
  - Rank or score highlights by intensity (e.g. number of chat messages, volume level) to prioritize them if there are many.
  - The agent compiles a highlights JSON (e.g. highlights.json) listing each candidate highlight with its start time, end time, and a brief description or reason (e.g. "big play occurs" or "chat explosion during event X").

- **Outputs:** A highlights data structure (list or JSON file) enumerating the timestamps of detected highlight clips, along with any metadata (e.g. scores or descriptions for each highlight).

- **Success Criteria:** At least one highlight is detected and the highlights JSON/file is created with plausible timestamp entries. In typical cases, multiple highlights (e.g. 3-10) should be identified for a multi-hour VOD. The highlight list should not be empty unless the source content truly has no noticeable excitement (edge case).

- **Retry/Failure Handling:** If zero highlights are detected or the results seem incorrect:
  - The agent should adjust detection parameters or methods and rerun the analysis. For example, lower the threshold for chat spikes or use a different indicator (like detect specific hype words).
  - If chat analysis alone yields nothing, try relying more on audio cues, or vice versa. Ensure both chat and audio data are properly synced with the video timeline.
  - The agent might use a fallback approach such as uniformly sampling the video for candidate clips (not ideal but ensures something is picked) if automated analysis fails entirely.
  - **Highlight Approval Loop**: Before finalizing this step, the agent will present the list of detected highlights to a user or a review module:
    - The user (or a QA process) can rate each highlight’s quality (e.g. 1–5 stars) and either approve or reject the highlights set.
    - If the user approves the highlights list (possibly after removing low-quality ones), the pipeline can proceed. If the user disapproves or wants changes, the agent must refine the detection (e.g. try different thresholds or include additional highlights) and present a new list. This loop continues until approval is given.
  - Only after receiving approval on the highlight selection does the agent mark this step as completed. If user approval is not obtained (e.g. user is unavailable), the agent may either pause here or proceed with best-guess highlights but that would be configurable.

- **Editing Style Planning:** (Intermediary decision) Once highlights are approved, the agent should propose video editing styles for how these highlights will be presented in short form. For example:
  - Option A: A fast-paced, energetic cut (suited for TikTok’s quick attention spans).
  - Option B: A cinematic build-up and payoff style (more dramatic, for YouTube Shorts).
  - Option C: A meme-heavy approach with overlay text and graphics (targeting humor and virality, good for Instagram/Twitter audiences).
  - The agent will recommend the best style based on the content tone and the creator’s goals (e.g. if the highlight is a funny moment, recommend the meme style). It should list pros and cons of each style option.
  - User Selection: The user or system can choose one of the style options (or accept the recommendation). This choice will influence the editing in the next steps (such as what overlays or pacing to apply).
  - This interaction ensures the pipeline tailors the output style appropriately. The choice and rationale should be logged (but this may not halt the pipeline if an automated decision is configured).

---

### 2.3 Step 3: Slice Highlights into Clips

**Description:** Using the timestamps of approved highlights, extract those segments from the full VOD to create individual short clip files for each highlight.

- **Inputs:** The original VOD video (vod.mp4) and the list of highlight timestamps (start/end times for each clip, as decided in Step 2). Also the chosen editing style might influence how the clip is cut (e.g. a few seconds of context before the moment, or a particular maximum length).

- **Process:** For each highlight entry:
  - Use a video editing library or tool (e.g. MoviePy or ffmpeg directly) to cut the segment from the source video. Include a small buffer (pre-roll or post-roll) around the highlight if needed for context, based on style guidelines (for example, maybe add 0.5s before the highlight start).
  - Save each segment as its own video file (e.g. clip1.mp4, clip2.mp4, ...). These will later be further processed.
  - If a chosen style requires multiple cuts or reordering (for instance, a dramatic replay or slow-motion insert), this step may also include that composition. However, typically complex editing is handled in the next step; Step 3 is primarily about raw cutting.
  
- **Outputs:** A set of raw highlight clip files in a temporary or working directory (one file per highlight, e.g. highlight_01.mp4, highlight_02.mp4, etc.).

- **Success Criteria:** Each intended highlight segment is successfully saved as an independent video file. The number of clip files matches the number of highlights approved. Each clip should play the correct content (verify that the duration and content roughly match expectations).

- **Retry/Failure Handling:**  If any clip fails to generate:
  - The agent should attempt the slicing again for that segment, possibly using a different method. For example, if using MoviePy fails (due to a codec issue or memory error), try using an ffmpeg command as an alternative.
  - Ensure the file paths and durations are correct; a common failure could be out-of-range timestamps. If a timestamp is slightly out of video bounds, clamp it to the video length and retry.
  - If a clip is too short or empty, the agent should flag that highlight as problematic and could remove it from the list (with a warning in the details) or adjust the timeframe.
  - This step is usually fully automated. Only in rare error cases would user input be needed (for instance, if all slicing fails due to an unsupported video format, a user might need to intervene or provide a different tool).
  - Continue with remaining clips even if one fails (i.e., one bad highlight shouldn't stop the entire pipeline; mark that one as failed and proceed to others).

---

### 2.4 Step 4: Subtitles Generation & Overlay

**Description:** Generate and overlay subtitles using AI speech-to-text.

- **Inputs:** The set of highlight clip files from Step 3. Also the chosen editing style may influence subtitle style (font, size, position) or content (e.g. whether to include emoji or emphasis).

- **Process:** For each clip:
  - Use a speech-to-text AI model (such as OpenAI Whisper) to transcribe the audio. Use an appropriate language model to get an accurate transcript of the spoken words in the clip.
  - Convert the transcript into timestamped subtitles (SRT or similar, or directly into frames for overlay). This may involve aligning text with the audio if Whisper provides word timestamps.
  - Overlay the subtitles onto the video frames. This can be done with a video editing library (e.g. generating text clips in MoviePy to overlay) or via ffmpeg drawtext filters, etc. Use a clear, legible font (the project might include a font file, e.g. a bold font in /fonts/) and styling consistent with the platform (e.g. large text, maybe with background shadow).
  - Ensure subtitles are synchronized and do not obstruct important on-screen content (place appropriately, usually at bottom center).
  - If style guidelines call for certain keywords or phrases to be highlighted (or emoji to be added for emphasis), apply those transformations in the text.
  - Save the new video clip with subtitles (can overwrite the original clip file or create a new file like clip1_subtitled.mp4).

- **Outputs:** Updated highlight clip files that now include burned-in subtitles (or accompanying subtitle files if the approach is to upload separate captions, but typically for Shorts the text is burned in for visual effect).

- **Success Criteria:** Each clip has accurate subtitles appearing in sync with the spoken words. The subtitles are correctly spelled (or intentionally stylistic) and enhance the video without covering crucial visuals. Files are saved without corruption.

- **Retry/Failure Handling:** Potential issues and responses:
  - Transcription failure: If Whisper (or the transcription service) fails or produces low-confidence output (e.g. lots of [inaudible] segments), the agent can retry using a different Whisper model (perhaps a larger one for better accuracy, or a smaller one for speed if performance was an issue). Alternatively, if there's background noise, apply basic noise reduction on audio before transcribing.
  - Overlay failure: If adding text to video fails (for instance, due to missing font or codec issues in writing video), ensure the required font file is accessible and the correct codec is used. Try an alternate method (MoviePy vs. direct ffmpeg) to overlay text.
  - Timing issues: If subtitles appear out of sync or too fast, adjust the timing by re-aligning or splitting into more lines. The agent might simulate playback (if possible) or at least verify the duration of generated text against clip length.
  - These operations should be automatic; rarely would this require pausing for user input, except perhaps if the user wants to manually tweak wording or correct the transcript. If a user is in the loop, the agent could present the transcripts for approval before overlaying, but this is optional. In a fully automated run, proceed with best-effort subtitles and note any low-confidence areas in the log.

---

### 2.5 Step 5: Format Clips for Social Platforms

**Description:** Reformat or adjust the subtitled clips to ensure they meet the specifications and best practices for each target social media platform. Different platforms have varying aspect ratios, durations, and content style preferences.

- **Inputs:** The subtitled highlight clips from Step 4. Also a list of target platforms (e.g. YouTube, TikTok, etc.) and their format requirements. The editing style choice from Step 2 might also influence how each format is handled (for instance, a meme style might require certain overlays specifically on TikTok).
- **Process:**  For each platform the content will be posted to:
  - **Resize/Reframe:** If needed, adjust the video resolution and aspect ratio. All short-form vertical platforms typically use 9:16 (1080x1920) aspect. Ensure the clip is in vertical format. If source gameplay was 16:9, this may involve creative cropping or adding blurred background to fill vertical frame. Center the action or use zoom/pan to highlight the subject for vertical view.
  - **Duration Check:** Ensure the clip length fits within platform limits (e.g. ~60 seconds for Shorts/TikTok; Twitter might allow slightly longer but ideally keep it short). If a clip is too long, consider trimming or splitting it.
  - **Style Adjustments:** According to platform:
    - **YouTube Shorts:** Keep it fast-paced, especially the first 3 seconds need a hook. Possibly add a quick intro text if needed (the agent could add a frame "Awesome Highlight from Twitch!" as a hook).
    - **TikTok/Instagram:** Use very attention-grabbing visuals. Possibly add more emoji or dynamic caption styles. TikTok viewers often expect subtitles with emojis or creative fonts.
    - **Facebook Reels:** Might allow 4:5 format as well; if targeting, perhaps ensure compatibility (the system can stick to 9:16 to reuse the same video).
    - **Twitter:** Twitter videos can be 1:1 or 16:9; but posting a 9:16 is acceptable (it will show with black bars or cropped in feed). For Twitter, sometimes a 1:1 crop of the same content could be better for preview. The agent may generate an alternate version if specifically needed, but otherwise using the vertical video is fine.
  - The pipeline can use the same base vertical video for all, but might apply small tweaks per platform (for example, different caption text or end screens).
  - Ensure the final video files are named or tagged per platform (e.g. highlight1_youtube.mp4, highlight1_tiktok.mp4, etc.) if multiple outputs are produced.

- **Outputs** Platform-ready video files for each highlight (or each selected highlight) intended for upload. These are in the proper resolution/format for each platform. In many cases, one vertical video can serve all platforms, but separate files may be prepared if needed for differences.

- **Success Criteria:** The clips meet the technical requirements:
  - Correct resolution (e.g. 1080x1920 for vertical).
  - Acceptable file size and encoding (h264 codec, appropriate bitrate).
  - Visual elements (subtitles, overlays) are not cut off or misaligned after reformatting.
  - The content style aligns with platform norms (this is subjective, but the agent should have applied the chosen style consistently).

- **Retry/Failure Handling:** If formatting fails or output is not satisfactory:
  - If the aspect ratio conversion cuts off important content, the agent can try alternative methods (e.g., letterboxing vs cropping, or using a different focal point for crop).
  - If an encoding error occurs (some ffmpeg filter fails), adjust parameters or use a simpler approach (for instance, do one pass to scale resolution, another to overlay if doing simultaneously caused an issue).
  - In case a particular platform requires a drastic change (like a much shorter version for a teaser), the agent might alert the user that manual editing is recommended or automatically create a second shorter cut.
  - Since this step is usually straightforward, failures are uncommon beyond formatting issues. Ensure to log any modifications done for each platform.

**Platform Format Reference:** (For quick review, the common format guidelines are summarized below in a table.)

| Platform         | Key Format Requirements & Style Notes |
|------------------|--------------------------------------|
| YouTube Shorts   |  Vertical 9:16, 1080x1920. Hook viewer in first 3 seconds (fast intro). Standard subtitle style.|
| TikTok/Reels     |  Vertical 9:16, 1080x1920. Highly engaging subtitles (add emojis, flashy text as appropriate). Extremely attention-grabbing pacing.    |
| Facebook Reels   | Prefer 9:16 (1080x1920), also supports 4:5. Can allow slightly longer intro. Similar style to TikTok.     |
| Twitter Video    | Supports 1:1, 16:9, and vertical. Vertical 9:16 is okay but may be cropped in feed. Consider a 1:1 center crop for important content if needed. Keep it punchy with a humor or shock element early.    |

Note: Each platform’s audience might prefer slight content tweaks, but these are handled mostly in the earlier style planning. The formatting step ensures technical compliance above all.

---

### 2.6 Step 6: Automated Uploads to Platforms

**Description:** Publish the formatted short video(s) to the configured social media platforms (e.g. upload to YouTube Shorts and TikTok, optionally others) using automated scripts or APIs.

- **Inputs:** Final video file(s) for each platform from Step 5. Also required are credentials/API tokens or cookies for each platform’s upload API, and metadata like title, description, tags/hashtags to accompany the post. The pipeline configuration should include these details (e.g. a template title or any hashtags to append).

- **Process:** For Each target Platform:
  - Use platform-specific upload tools/APIs
    - YouTube: Use YouTube Data API or a command-line uploader (like youtube-upload CLI) to upload the short. Include title, description (which might have a call to action like "Catch me live on Twitch!"), and appropriate tags (e.g. #shorts).
    - TikTok: Use an automated uploader (TikTok might have a third-party CLI or require automation via Selenium or an API if available). Provide the video file and caption/hashtags.
    - (If extending to Instagram Reels or others, similar approach with their API or a third-party integration.)
  - Monitor the response or result of each upload command:
    - Confirm whether the upload succeeded (usually by checking the exit code of CLI or the API response indicating success and providing a video ID/url).
    - If needed, store the returned video URL or ID for reference.
  - Possibly post-upload, perform any follow-up actions:
    - For YouTube, maybe set the video as public (if not by default) and add a comment or end screen linking to Twitch.
    - For TikTok, ensure the video is public and perhaps log the URL.
  - This step can run in parallel for multiple platforms or sequentially, depending on implementation.

- **Outputs:** The short video content is now live on each platform. Internally, the system might produce a log entry or data structure with the published video URLs/IDs for confirmation. The progress.json and any dashboard should reflect that the video was published successfully on each platform.

- **Success Criteria:** Each target platform confirms the video has been uploaded and is accessible. For example, YouTube returns a video ID and the agent can verify the video’s existence (or at least no error was thrown). TikTok’s tool reports success. The success state for this step is reached when all required uploads have completed successfully.
  
- **Retry/Failure Handling:** Because uploads involve external services, errors can happen due to network or authentication:
  - If an upload fails due to a transient error (network timeout), the agent should retry a few times automatically.
  - If failure is due to invalid credentials or expired tokens, mark this step as failed and prompt for human intervention (to update login or tokens). Security-related failures (like 2FA required) typically cannot be solved automatically.
  - If one platform fails but others succeed, record the failure for that platform in progress.json (with details) but continue attempting the rest. The agent can then either retry the failed one later or notify the user.
  - In case of upload success but video not appearing (maybe processing delay on platform), the agent can wait and check after a short delay as confirmation.
  - The agent should ensure not to enter an infinite retry loop; after a set number of failures for a platform, log the error and move on.

---

### 2.7 Step 7: Error Handling and Logging

**Description:** This is an ongoing requirement throughout all steps to ensure robust operation. The agent should log important events, handle exceptions at each stage, and maintain a trail of actions for debugging. It also should notify maintainers of critical issues.
  
- **Logging:** Every major action and decision is logged with timestamp. Use a consistent logging framework or simple file logs. Include successes, failures, and key decisions (like "No highlights found, lowering threshold and retrying"). Logs should be both human-readable and easy for the agent to parse if needed (e.g. structured logging in JSON or a database could be considered for scaling).
- **Progress Tracking:** Update progress.json (detailed in section 4) after each step with the current status. This file acts as a lightweight database of what has been done and what is pending.
- **Exception Handling:** Wrap external calls (file I/O, network requests, API calls, CLI invocations) in try-except blocks. On exception:
  - Catch the error, log the stack trace or error message.
  - Mark that sub-step as failed in progress.json (with details of the error).
  - If the error is non-critical and a retry is possible, attempt the retry logic as defined per step. If the error is critical (e.g., out of disk space, or an undefined variable bug in code), halt the pipeline and flag for developer attention.

- **Notifications:** For critical failures that stop the pipeline, use a Discord webhook or similar notification to alert the maintainer instantly. Include the pipeline name, step that failed, and error details in the alert. This ensures prompt attention to issues even if the agent is running unattended on a server.

- **Success Logging:** On completing each step (and at the very end of the pipeline run), log a summary of results (e.g., "3 highlights extracted, 3 clips created, uploaded to YT and TikTok successfully"). This could be printed to console, stored in a log file, and appended to progress.json details.

- **Continuous Operation:** The pipeline should be able to recover or continue even if one video fails. For example, if running in batch mode for multiple VODs, one failure should be logged and skipped, while the agent moves to the next VOD. Robust error handling and logging make this possible

- **Cleanup:** An often overlooked aspect of robustness: ensure temporary files (raw VODs, intermediate clips) are cleaned up after successful upload to save space, unless they are needed for audit. On errors, keep enough data for debugging (the agent might keep failed outputs for analysis).

- **Security**  (if applicable): (No major user data is handled aside from chat logs and API keys for uploads. API keys and cookies should be stored securely and not logged. However, since this is an internal pipeline, security is mostly about protecting these credentials and not exposing them in logs.)

Logging and error handling are considered a functional requirement because they are integral to the pipeline’s reliable operation in production

---

## 3. Agent Interaction Protocols

The AI agent orchestrating this pipeline follows a structured loop for each step, ensuring clarity of purpose, user alignment on decisions, and robust handling of outcomes. The agent’s behavior protocol is outlined below:

**General Step Execution Loop:**

1. **Step Confirmation:** At the start of each pipeline step, the agent confirms the context. For example, it may internally note or even prompt (in a development scenario): "Proceeding to Step 2: Highlight Detection." This ensures it is aligned with the correct stage and allows any external interface (like a user or dashboard) to know what’s happening. Confirm context at start of each step

2. **Summarize Goal:** The agent explicitly recalls the goal of the current step in simple terms (for itself or the user). e.g., "Goal: Identify the best highlights from the VOD using chat and audio data." This self-check helps ensure the agent applies the correct logic and can be useful if the agent dynamically adjusts strategies.

3. **Determine Method:**  If multiple methods or strategies are available for the step, the agent evaluates options:
   - It gathers potential approaches (for instance, for highlight detection, methods might include chat-based only, audio-based only, or combined analysis).
   - It weighs pros and cons of each approach in terms of the project goals (automation, speed, quality, reliability). For example, "Approach A might be faster but less accurate, Approach B uses more data hence slower but better highlights."
   - The agent then recommends a preferred approach. This recommendation should align with achieving high quality output efficiently (based on prior knowledge or learned preferences).

4. **Wait for Approval:** For decision points that affect output quality or require subjective choice, the agent seeks approval from a human operator or a preset policy:
   - It may present the options and recommendation to the user: "Option 1: use chat spikes (fast, may miss some moments), Option 2: use chat+audio (slower, but more thorough). I recommend Option 2. Should I proceed?"
   - If the user is involved, the agent waits for the user’s selection or go-ahead. If no user is available (fully autonomous mode), the agent proceeds with the recommended default but logs that choice.
   - Some steps inherently require approval, e.g., highlight selection (user needs to approve highlights list), or final video review if desired. The agent’s protocol is to pause and request confirmation at these junctures before moving on.

5. **Execute the Step:** The agent carries out the step’s implementation by invoking the appropriate module or function in the pipeline (or generating code dynamically if it’s in a development cycle):
   - It supplies the necessary inputs (which it obtained or generated from previous steps).
   - It runs the process (download, analysis, editing, etc.), monitoring for success or errors.
   - If the agent itself is writing new code or modifying code (in a maintenance scenario), it will generate the code for that step following best practices (with comments and proper structure), then run it.

6. **Monitor and Error Correct:** During execution, the agent watches for any errors or anomalies:
   - If an error occurs, the agent catches it (from exceptions or error codes). It will attempt an automatic correction if possible: use a fallback method, adjust parameters, or even fix code if this is a development context. For example, if an undefined variable error happens, the agent might realize a module wasn’t imported and add the import, then retry.
   - The agent also uses the retry logic specified in the requirements for that step (see section 2) to guide its correction attempts.
   - If the error persists or is not automatically fixable, the agent flags the issue, and may ask the user: "I encountered an error downloading the VOD. Should I try an alternate method?" or present the error log for debugging.
   - This proactive bug-fixing approach helps maintain flow without constant human intervention, only escalating when needed.

7. **Document Progress:** After the step execution (whether success or failure), the agent updates the progress and logs
   - It updates progress.json with the step’s status ("completed" or "failed") and a brief detail message (e.g., “Downloaded VOD and chat successfully” or an error summary). This provides a machine-readable state tracking that can be used by the agent or UI to know what’s done.
   - It logs any important details or artifacts. If the agent is also maintaining documentation (like an internal changelog or the README), it appends an entry describing what was done in this step, which files were affected, and why (rationale). For example, "Step 3 completed: 4 clips created from the VOD. Files: clip_editor.py modified to fix an off-by-one timestamp bug." (The exact format of these logs is described in the progress tracking section and might also appear in a Markdown log or a database.)
   - If the agent had to write or modify code for this step (in an iteration scenario), it also notes the prompt or reasoning that led to the changes, and timestamps them. This creates an audit trail of how the pipeline evolves over time.

8. **Next Step Decision**: The agent then decides whether to move to the next step or take another action:
   - Normally, if the step succeeded, it proceeds to the next pipeline step in order.
   - If the step failed and was not recoverable, the agent may either retry (if attempts left), or pause the pipeline and seek human assistance depending on severity. It will not proceed to the next step if prerequisites are not met (e.g., if highlight detection failed, it cannot slice clips, so it should stop and mark the pipeline incomplete).
   - The agent may also ask the user “Would you like to refine this step or proceed to the next?” especially if in a development/tuning phase. For instance, after generating subtitles, a user might not be satisfied with their style and ask to refine Step 4 again before moving on.
   - This loop continues until all steps are completed or the pipeline is stopped.

**Interactive vs Autonomous Modes:** The above protocol is designed to accommodate both interactive use (where a human is guiding the agent, perhaps during initial development or when approving content) and autonomous runs (where the agent makes decisions based on configured preferences). The AI agent should be context-aware

- In interactive mode, it actively asks for user input at decision points and waits.
- In autonomous mode, it automatically chooses the recommended options, but could still log what it would have asked, for transparency.
- In either case, the agent always documents what it did and any approvals given (or defaults taken) so that the process is traceable.

**Human-in-the-Loop Points:** By design, certain points involve human confirmation for quality control – notably highlight approval and editing style choice. The agent’s logic treats these as mandatory pause points unless overridden by a configuration (for fully automatic operation, perhaps with a default approval or ML-based approval proxy). This ensures that content quality remains high and the user has creative control where it matters, while the agent handles the heavy lifting and technical details.

---

## 4. File and Module Responsibilities

The project’s codebase is organized into modules corresponding to each functional domain of the pipeline. Below is an overview of key files/modules and their responsibilities:

- **main.py**:The primary orchestrator of the pipeline. It coordinates the execution of each step in order, calling the appropriate functions from other modules. It handles high-level exception catching around the whole pipeline and triggers progress logging updates. In a production setup, main.py might be invoked for each new VOD to process (or for a batch of VODs).
- **utils.py**: A utility module providing helper functions used across the pipeline. This may include common routines like timestamp formatting, file path helpers, logging setup, configuration loading, etc. All generic functions that don’t belong in a specific step module reside here.

**Ingestion Modules:**

- vod_ingestion/vod_downloader.py: - Contains the logic for Step 1 (Twitch VOD download). Likely provides a function like download_vod(vod_id) which handles connecting to Twitch (via API or streamlink) and saving the video file. It also may retrieve chat by calling Twitch’s API or a service, then saves the chat log. Implements retry logic for downloads. It might use external tools (through subprocess calls or API calls) inside.
- (If there is a video.py or similar mentioned: earlier documentation references a video.py for VOD logic; that could be integrated into vod_downloader.py or a legacy name. The current structure encapsulates this in the vod_ingestion package.)

**Highlight Detection Modules (Step 2)**:

- **highlight_detection/chat_analysis.py**: Provides functions to analyze chat logs. For example, a function find_chat_spikes(chat_log) that returns time segments with high chat activity. It may parse the JSON of messages, count messages per minute, detect key phrases, etc.
- **highlight_detection/audio_analysis.py**: Provides functions to analyze the audio track of the video. For example, find_audio_spikes(video_file) which might leverage a library (or ffmpeg) to extract audio waveform and identify loud moments or other audio features.
- **highlight_detection/highlight_detector.py**: The main module that orchestrates highlight detection. It likely calls chat_analysis and audio_analysis functions, fuses their results, applies scoring, and outputs the final list of highlights. It also might handle the logic of requiring at least one highlight, adjusting thresholds, etc. This is where the agent would interface to get the highlights list for approval. The module may produce an output file or object (like highlights.json). It could also include logic for applying user feedback (e.g., if certain highlights are rejected, remove or replace them).

***Video Editing Modules (Step 3-4)**:

- **video_editing/clip_editor.py**: Responsible for cutting the video into clips given timestamp inputs (aligns with Step 3). Likely has a function like slice_video(input_video, timestamps_list) that uses MoviePy or FFmpeg to create subclips. It might also incorporate simple transition or padding if needed. This module focuses on raw splitting and possibly concatenation if needed for multiple parts.
- **video_editing/subtitle_overlay.py**: Handles subtitle generation and overlay (Step 4). It may interface with the Whisper API or library (OpenAI Whisper) to get transcriptions via a function transcribe_audio(video_clip). Then it has routines to either generate an SRT file or directly overlay text on video frames. Perhaps uses MoviePy TextClip or OpenCV for drawing text. It likely offers a function add_subtitles_to_video(video_clip, transcript) returning a new video with subtitles. Configuration for font, size, and placement would be here.

(In some projects, there might also be an integrated editor.py that covers both clipping and subtitles. According to the docs, an editor.py was referenced for editing logic, which might combine functionalities of the above two or coordinate them. The current breakdown assumes separation, which is good for modularity.)

**Publishing/Uploading Modules (Step 6):**

- **publishing/youtube_uploader.py**: Contains functionality to upload a given video file to YouTube. This might wrap around a CLI tool or use Google’s YouTube API. Functions might include upload_to_youtube(file_path, title, description, tags) which handles authentication and uploading. Could use a saved credential or OAuth flow (likely out-of-scope for the agent to handle manually each time, so credentials are prepared).
- **publishing/tiktok_uploader.py**:  Contains functionality for uploading to TikTok. This could be more complex as TikTok’s official API for uploading is limited. Possibly this module uses a headless browser automation or a third-party Python library/CLI to perform the upload. It will have a function like upload_to_tiktok(file_path, caption) and handle login (maybe via cookies stored in har_and_cookies folder as the project structure suggests).
- **publishing/publish.py**:  If present, this might be a higher-level module that calls specific uploader functions for each platform needed. The documentation mention of uploader/publish.py suggests a unified interface. For example, publish_all(video_files, metadata) which internally calls out to youtube_uploader and tiktok_uploader etc., coordinating the parallel or sequential uploads and returning a summary of results.

**Dashboard & Approval Modules:**

- **dashboard/orchestration.py**: Likely part of a web dashboard for monitoring. It might tie into main.py or run an asynchronous loop that triggers pipeline steps and updates a UI. It could also read progress.json to display status.
- **dashboard/approval_app.py**:  (and corresponding templates/approval.html) – Provides a web interface for the user to view detected highlights and approve or reject them (as noted in Step 2). This is essentially a front-end for the highlight approval loop: it would display the highlight timestamps (maybe with preview thumbnails or short clips) and accept user ratings/feedback. The agent (or backend) would then adjust highlights accordingly. This module might run as a Flask or FastAPI app serving a small web UI.
- **dashboard/evaluation.py**: Possibly a component to evaluate performance (e.g., track how videos are doing after upload, or some analytics), or to run a health check on the pipeline. It might also be used to verify everything is in place (the Docker healthcheck in the Dockerfile looks for evaluation.py as an indicator the container is alive).

**Other Files:**

- **fonts/**: directory – Contains font files used for subtitle overlay (like bold_font.ttf). The subtitle overlay module uses these.
- **har_and_cookies/**: directory – Intended to store authentication data (HAR files or cookies for platform logins). This keeps sensitive info out of code and in a safe location, not to be committed. The agent should not log these; it's for the uploading modules to use when logging into TikTok or others.
- **requirements.txt**: Lists all Python dependencies needed to run the pipeline (aligning with the ones mentioned in the Technical Dependencies section).
- **Dockerfile & docker-compose.yml**: Define the container environment (using Python 3.11 slim, installing system packages like ffmpeg, etc.) and how the services (pipeline, possibly the dashboard) run in Docker. The agent doesn’t modify these at runtime but should be aware of the environment it runs in.

Each module is designed to be relatively independent, communicating through well-defined inputs/outputs (files or function returns). The AI agent can focus on one module at a time during development or debugging, thanks to this modular structure. For example, if highlight detection needs improvement, changes will mostly be contained in the highlight_detection package, without affecting how videos are uploaded.

---

## 5. Progress Tracking (`progress.json`)

  Throughout pipeline execution, the agent maintains a JSON file (progress.json) to log the status of each step. This file serves as a lightweight database of progress that both the agent and the user (or any dashboard) can consult to see what has been done, what is in progress, and what might have failed. It is updated in real-time as the pipeline advances.

  **Formet**: The progress.json file is structured as a dictionary of pipeline steps (or sub-tasks) with their status info. For example:

```json
{
  "Ingest VOD": {
    "status": "completed",
    "details": "Downloaded VOD and chat. No issues."
  },
  "Highlight Detection": {
    "status": "pending",
    "details": "Highlights generated. Awaiting user rating and approval."
  },
  "Slice Clips": {
    "status": "pending",
    "details": ""
  },

}
```

Each top-level key is a step or stage name (it could be the exact step names or slightly abbreviated identifiers). The value is an object with at least the following fields:

- **status**: The current state of that step. Expected values typically include:
  - "pending" – The step is not yet done (or is currently in progress). It might be awaiting input or just not started.
  - "completed" – The step finished successfully.
  - "failed" – The step encountered an unrecoverable error.
  - (Optionally, one might also use "in_progress" to explicitly mark a step that has started but not yet finished, though in many cases we can infer in-progress if it's not pending or completed yet. If needed, the agent can set "in_progress" at step start and then "completed" or "failed" when done.)

- **details**: A human-readable string providing more context about the status. For a completed step, this might summarize the outcome (e.g. how many items processed, any notable info). For a pending step, it might note if it's waiting for something (as in the example: waiting for user approval). For a failed step, this should contain an error message or reason for failure.

**Update Protocol**: The agent updates this JSON at the end of each step (and possibly at key mid-points):

- When a step begins, it could set the status to "in_progress" (or simply leave as pending until completion).
- On success, set to "completed" and fill details with a short success note.
- On failure, set to "failed" and put the error summary in details.
- If a step involves a user decision (like highlight approval), the agent might update details to reflect that it's waiting on user input, as shown in the example for Highlight Detection.
- The JSON is written to disk so that if the process restarts, it can be read to know what was done. (In future, this could aid resuming: e.g., skip already completed steps if re-run.)

**Key Fields and Structure:**

- The keys ideally correspond exactly to the step names in this document (for clarity) or at least have a consistent naming scheme (no random wording each time). This ensures the agent can parse or manipulate them easily if needed (like finding which steps are left).
- Each value at minimum has status and details. We could also include:
  - timestamp: (optional) When that status was last updated. Could be helpful for knowing how long a step took or how fresh the info is. If included, use a consistent format (e.g. ISO 8601 string).
  - files or artifacts: (optional) If we want to log output file names or number of outputs. For example, after slicing clips, we might include "files_created": 3 or list their names. The current design hasn’t required this, but an extended progress log could have it.
  - user_feedback: (optional) For steps where user rating or selection occurs, we might log what the user chose (e.g. which style was picked, or highlight ratings). Currently such details might just be mentioned in details.

**Usage:** The agent and any UI or monitoring tool can read progress.json to:

- Display a dashboard of pipeline status (e.g., "Highlight Detection – pending (awaiting approval)").
- Decide logic, such as not re-running a step that is completed if the pipeline is re-invoked.
- Provide context if resuming after a crash (the agent might load this and see where it left off).
- The agent can also append entries to a persistent log (like the README changelog or a separate log file) with more detail, but progress.json remains a concise state snapshot.

**Consistency:** The agent must ensure the JSON remains valid and consistent. Each update should rewrite the JSON file (or use a file lock mechanism to avoid race conditions if multi-threaded). If a crash occurs while writing, the agent should handle partially written files gracefully (perhaps by writing to a temp file and moving it).

In summary, progress.json contains the key fields status and details per step, and it is the authoritative record of where each step stands. Keeping it up-to-date is critical for transparency and debugging, so the agent should treat updating this file as part of the completion routine for every step.

## 6. Technical Dependencies

This section enumerates the external tools, libraries, and environments required for the pipeline, as well as any system requirements. The AI agent should be aware of these dependencies to manage them (for example, ensuring they are installed, or using them correctly in code).

**Platform & Environment**:

- **OS**: Windows 10/11 (development environment) with WSL2 enabled for Docker, or any system capable of running Docker containers. The pipeline is designed to be OS-agnostic by using Docker; the host OS matters less in production (Linux containers run via Docker).
- **Python:** 3.11+ (the project targets Python 3.11+ for compatibility with certain libraries and to use the latest language features for performance and typing).

**Python Libraries (core pipeline):**

- **vodbot**: A custom or third-party library for Twitch VOD management (downloading videos, slicing clips, and possibly uploading to YouTube). This handles much of the heavy lifting for ingesting content and may integrate with Twitch APIs.
- **streamlink**: (CLI/Library) Used as a fallback method to download Twitch streams. Streamlink can fetch the livestream/VOD segments easily when direct API fails. Often run as an external process.
- **yt-dlp**: A powerful video download library, also used as a fallback or alternate method to download Twitch VODs (and can download from many platforms). Ensures we can get the video even if Twitch or VodBot has issues.
- **openai-whisper**: The Whisper AI speech-to-text model by OpenAI, possibly via the whisper Python package. Used for transcribing audio to text in Step 4. The model can run on CPU (slower) or GPU (faster if available).
- **moviepy**: A Python library for video editing that provides a high-level interface to cut videos, concatenate them, add effects, and overlay text/images. Used in slicing clips and adding subtitles. (MoviePy itself uses ffmpeg underneath.)
- **opencv-python**: OpenCV library for computer vision. Marked as optional in the tech stack, but could be used for advanced highlight detection (scene change detection or even for adding image overlays). If humor detection or face detection features are planned, OpenCV would be used.
- **ffmpeg**: (System dependency) The ubiquitous video processing tool. It’s called under the hood by MoviePy and possibly directly by the pipeline for certain tasks (e.g., precise cutting or format conversion). In Docker, ffmpeg is installed via apt. The agent might call ffmpeg via command-line for performance-critical tasks.
- **pandas & numpy**: Python data libraries used likely in chat analysis for efficient data manipulation (e.g., converting chat timestamps to a timeline and detecting spikes statistically). Numpy might also be used in audio analysis (processing waveform arrays).
- **requests**: Python HTTP library, used for any web requests the pipeline makes. This could include calling Twitch APIs to get chat or VOD info, or sending out webhook notifications (like the Discord alert on failure).
- **Flask/FastAPI** (for dashboard): If a dashboard web UI is included, a web framework like Flask or FastAPI is a dependency to run the web server that serves the dashboard and handles approvals. The presence of templates/approval.html suggests Flask (since FastAPI typically would use Jinja similarly).
- **youtube-api-python-client or youtube-upload**: For uploading to YouTube. Two possible approaches: using Google’s official Python client library for YouTube Data API (which requires OAuth setup) or using a CLI tool like youtube-upload which might simplify the process. The project mentions YouTube API (youtube-upload) in the stack, indicating a CLI is used for YouTube.
- **TikTok Uploader CLI**: TikTok doesn’t have an open public API for uploading, but there are community solutions. The pipeline likely relies on a CLI tool (which might use a browser automation under the hood). The agent must ensure this tool is installed and that TikTok credentials (or cookie file) are available for it to work.
- **Docker & Docker Compose**: The pipeline is intended to run inside Docker for consistency. The provided Dockerfile uses Python slim image and installs system deps (ffmpeg, git, curl). Docker Compose might be used to run multiple services (the pipeline agent, and the dashboard web UI, for example). The agent should be aware of the container context (file paths, etc.). In production, one would build the Docker image and run it; the agent’s code modifications would typically happen on the host or during a dev container build.

**Development/Agent Tools:**

- **VS Code + GitHub Copilot (for development)**: While not needed for running the pipeline, the original development environment included VS Code and Copilot to assist code generation. The AI agent in context might be playing the role that Copilot did, writing code. This is more of an environment note than a dependency.
- **Git (version control)**: The project is in a git repo (given .gitignore, etc.). Not directly used by pipeline at runtime, but the agent should use version control best practices when iterating (committing changes, etc., though that’s outside the scope of automated pipeline execution).
- **Discord webhook URL (for notifications)**: Not a library, but a configuration dependency. The pipeline likely needs a URL or token for a Discord channel to send error alerts. This should be stored securely.

### System Resources

- Adequate disk space for video processing (Twitch VODs can be many gigabytes, and intermediate files plus final outputs will take space).
- Sufficient CPU (or GPU if available) for processing and running Whisper transcription. If large VODs are processed regularly, consider using a machine with a GPU and enabling GPU in Docker for Whisper to speed up Step 4.
- Memory: Video editing and transcription can be memory-intensive for long videos. The Docker container might need a few GB of RAM allocated.

All these dependencies should be installed and configured prior to running the pipeline. The Dockerfile ensures most of the system and Python packages are in place inside the container. The AI agent should verify that dependencies are met (perhaps a quick check at startup, e.g. try importing all required modules and report if something is missing).

When updating the pipeline, if the agent decides to introduce a new library for an improvement, it must also update the requirements.txt and possibly the Dockerfile to include it, thus maintaining this dependencies list.

---

## 7. Recommendations for Production Robustness and Improvement

To ensure the pipeline is production-ready and robust, and to facilitate easy maintenance by the AI agent, the following recommendations and best practices are put forward:

- **Modular Design & Separation of Concerns**: The pipeline is already structured into modular components (ingestion, detection, editing, publishing). Continue to enforce clear boundaries between these modules. This makes testing and replacing parts easier. For example, one could swap out the highlight detection algorithm for a new one without affecting other parts, as long as it produces the same highlight JSON format. The agent should preserve this modular structure when making changes and avoid creating interdependencies that blur the roles of each module.

- **Clear Interface Contracts**: Define the inputs and outputs for each module (possibly as Python function signatures with type hints and docstrings) clearly. E.g., highlight_detector takes a video file path and chat data, and returns a list of highlights. By formalizing these interfaces, the agent (and future developers) can more easily refactor or replace implementations. Also consider using data classes or typed dictionaries for complex data (like highlight entries) for clarity.

- **Robust Logging & Monitoring**: Expand the logging from simply writing to console or file, to possibly a more structured logging:
  - Use Python’s logging module with appropriate log levels (INFO for routine progress, WARNING for recoverable issues, ERROR for critical failures). This allows filtering logs and integrating with monitoring systems.
  - Include unique identifiers for runs or videos in the logs if processing multiple VODs concurrently, to differentiate log streams.
  - Consider integrating with an external monitoring service or at least log to a persistent location. If this runs on a server, ensure logs rotate to not fill disk.
  - The Discord webhook for critical alerts is good; ensure it’s triggered on any exception that causes pipeline abort. Possibly extend to notify on completion of a batch or daily summary if desired.

- **Error Handling & Retries**: While each step has specific retry logic, generally:
  - Use try/except around all major external interactions. Never assume an external call will always succeed.
  - If an error is known to be non-recoverable (e.g., file not found because user gave wrong VOD ID), fail fast and report clearly. If recoverable, implement the retry with sensible limits.
  - For external services (Twitch, YouTube, TikTok), consider the possibility of API changes or deprecations. To mitigate, keep the integration layer (like uploaders) abstracted so they can be updated or swapped (e.g., if TikTok CLI stops working, you can implement another method without touching core logic).

- **Configuration Management**: Externalize configuration values such as API keys, file paths, default parameters, etc., into a config file or environment variables. For example, have a config.json or use environment vars for Twitch API credentials, output directories, etc. This way, changing an API key or adjusting a threshold doesn’t require code changes. The agent should update documentation for any config changes and ensure it loads config at runtime.

- **Platform Abstraction & Extensibility**: Design the publishing step to easily add new platforms or modify existing ones:
  - Perhaps maintain a config mapping of platform names to their required formats and upload functions. Then adding "Instagram" would be a matter of providing a new entry and corresponding uploader module.
  - Avoid hardcoding platform-specific logic scattered in the code; instead funnel it through clearly defined strategies (as partially done with the formatting table).
  - This abstraction allows the pipeline to adapt to new trends (e.g., if a new platform emerges or an existing one changes requirements) with minimal code overhaul.

- **Performance Optimizations**
  - **Parallel Processing:** Where possible, utilize parallelism. For instance, transcribing audio (Step 4) for multiple clips can be parallelized since they are independent (if CPU cores available, or using threads/processes because the GIL can be released during I/O or heavy C operations in numpy). Similarly, uploading to multiple platforms can happen in parallel threads. The agent could improve performance by introducing multi-threading or async execution carefully with thread-safe considerations.
  - **Batch Mode Efficiency:** If processing several VODs in a row (batch), consider reusing resources. For example, if Whisper model is loaded, reuse the model in memory for multiple transcriptions instead of re-loading for each video. The code could be structured to handle a list of VODs and loop through them in one run, rather than restarting the whole program each time (though either approach can work).
  - **Hardware Utilization:** If a GPU is present, use it for Whisper (and potentially for any future vision models). The Docker and code can be set up to detect GPU. Offload heavy operations to compiled libraries (ffmpeg, numpy) which is already largely done.

- **Resource Cleanup**: Ensure that after processing a VOD, large files are removed or archived. A production system could accumulate many gigabytes of video quickly. The agent should include a cleanup step after successful uploads, deleting the local vod.mp4 and intermediate clips, unless they are needed for something else. Perhaps keep only the final uploaded clips for a short period for verification, then delete. If failure happens, keep data for debugging but add a mechanism to purge old files after X days to prevent indefinite storage growth.

- **Testing & Quality Assurance Hooks** Introduce hooks and tests to validate the pipeline’s correctness:
  - Develop unit tests for key functions (like chat spike detector, or the audio analysis). This ensures that changes by the agent don’t break basic expected behaviors. The agent can run these tests after modifying code to verify nothing critical broke.
  - Use sample data for tests: e.g., include a short example VOD and chat log in the repo that can be used to run through a quick pipeline (maybe 1 minute long) to see that highlights are detected and a clip is produced. This could be part of a CI pipeline to catch issues.
  - Provide a way to simulate user input in tests (for the approval step, maybe assume auto-approve in test mode).
  - The agent, when making changes, should ideally run these tests (maybe even automatically if integrated) to ensure robustness.

- **Documentation & Maintainability**: Keep the documentation (like this requirements doc, and the README) updated as the pipeline evolves:
  - Every time the agent makes a significant change, it should update the relevant section of documentation and the change log. This helps future maintainers (or future versions of the agent) understand why changes were made.
  - Inline code comments should explain non-obvious logic. Complex ffmpeg command constructions or algorithm choices in highlight detection deserve comments. This will aid debugging if something goes wrong in production.
  - Maintain an updated architecture diagram or description (even if just textual as above) as new components are added.

- **Continuous Improvement**: Periodically re-evaluate the performance of each pipeline stage:
  - For example, if the highlight detection is producing subpar clips, consider incorporating new data (like Twitch “clips” data or viewer count spikes) or even training a machine learning model for highlight prediction. The system’s modular nature should allow swapping in a more advanced highlight detector.
  - If subtitle generation is too slow with Whisper large model, consider adding a configuration to use a faster model or a cloud API when under time constraints.
  - For uploading, monitor if any platform changes their requirements or if upload success rate drops, and adjust the code promptly (the agent can be tasked with this monitoring role as well).

- **Scalability & Distribution**: If the user scales up (many VODs or longer videos):
  - Possibly distribute work across machines or cloud instances. Containerization helps with deployment on cloud services or Kubernetes for scaling.
  - Use a message queue or job system for multiple VOD processing to ensure the main thread is not overloaded. The agent could be extended to pick up new VOD jobs from a queue, process them, and then loop continuously.
  - Consider the load of Whisper and video encoding on CPU/GPU; if doing many concurrently, maybe allocate separate worker processes for those heavy tasks.

By following these recommendations, the pipeline will become more robust against failures and easier to maintain or extend. The AI agent, in particular, will benefit from a stable, well-structured codebase when iterating. It will be able to pinpoint exactly where to make a change (thanks to modularity and clear documentation) and ensure that modifications don’t ripple unintended effects through the system (thanks to tests and clear interfaces).

In summary, maintain a philosophy of clean, modular code, thorough logging, and proactive error handling. Pair that with continuous monitoring and updating of documentation. This will ensure the Twitch-to-Shorts automation pipeline runs smoothly in production and can adapt to future needs with minimal friction, with the AI agent effectively acting as its caretaker and developer over time.

---
