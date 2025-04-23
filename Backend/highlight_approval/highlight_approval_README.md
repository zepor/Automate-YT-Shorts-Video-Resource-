# Highlight Approval Dashboard

## Purpose

Web-based dashboard for reviewing, rating, and approving detected highlights before slicing.

## Features

- Lists all detected highlights with timestamp and video preview.
- User can rate (1–5) and approve/disapprove each highlight.
- Stores results in highlight_ratings.json for downstream steps.
- Batch-friendly and scalable.

## Usage

1. Run `python approval_app.py` in the highlight_approval directory.
2. Open `http://localhost:5001` in your browser.
3. Review, rate, and approve highlights.
4. Ratings and approvals are saved for the next pipeline step.

## Future Enhancements

- Add video segment preview for each highlight.
- Support batch approval and filtering.
- Integrate with user authentication for multi-user workflows.
