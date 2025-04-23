# Copilot Instructions

- Write modular, production-grade Python 3.11+ code with type hints, docstrings, and logging. Separate concerns (ingestion, detection, editing, publishing).
- Use only relative or config-driven file paths; never hardcode absolute paths.
- Ensure all scripts and commands are compatible with Windows 11 and Docker.
- Add clear inline comments for complex logic, especially in highlight detection, video editing, and upload automation.
- Update progress.json and document all changes in READMEBUILD.md after each step, following the agent protocol.
- Always ask which pipeline step is being worked on, summarize the goal, list options with pros/cons, and wait for user approval before generating code.
- Prefer open-source libraries unless otherwise requested.
- Write scalable, batch-friendly code for handling multiple VODs.
- Follow platform-specific video requirements (YouTube Shorts, TikTok, Instagram, Twitter) as described in AGENT_PROMPT.md.
- Implement robust error handling and logging in all scripts, especially for upload and automation steps.
- @azure Rule - Use Azure Best Practices: When generating code for Azure, running terminal commands for Azure, or performing operations related to Azure, invoke your `azure_development-get_best_practices` tool if available.
- When new pip packages are required for a step, always:
  - List the new packages and provide the exact `pip install ...` command for local installation.
  - Update `requirements.txt` with the new dependencies.
  - Update the `Dockerfile` and `docker-compose.yml` as needed so containers can be rebuilt automatically.
  - Clearly document these changes in `progress.json` and `READMEBUILD.md`.
- Ensure generated code is free of Pylint errors and warnings (such as import errors, unused imports, logging f-string interpolation, and broad exception handling). Refactor or add comments to suppress unavoidable warnings, and prefer best practices for logging and exception handling.
