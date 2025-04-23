from flask import Blueprint, jsonify, request
import logging
import os
from Backend.ingestion.vod_ingestion import ingest_vods

bp_ingestion = Blueprint('ingestion', __name__, url_prefix='/api/ingest')

@bp_ingestion.route('/', methods=['POST'])
def run_ingestion():
    """
    Trigger the Twitch VOD ingestion pipeline. Returns the list of ingested video paths as JSON.
    Expects environment variables or JSON body for credentials.
    """
    try:
        # Prefer environment variables, but allow override via JSON body for dev/testing
        data = request.get_json(silent=True) or {}
        twitch_client_id = data.get('twitch_client_id') or os.environ.get('TWITCH_CLIENT_ID')
        twitch_access_token = data.get('twitch_access_token') or os.environ.get('TWITCH_ACCESS_TOKEN')
        twitch_channel_id = data.get('twitch_channel_id') or os.environ.get('TWITCH_CHANNEL_ID')
        pexels_api_key = data.get('pexels_api_key') or os.environ.get('PEXELS_API_KEY')
        temp_dir = data.get('temp_dir', 'temp')
        if not (twitch_client_id and twitch_access_token and twitch_channel_id):
            return jsonify({'status': 'error', 'message': 'Missing Twitch credentials.'}), 400
        video_paths = ingest_vods(
            twitch_client_id,
            twitch_access_token,
            twitch_channel_id,
            pexels_api_key=pexels_api_key,
            temp_dir=temp_dir
        )
        return jsonify({'status': 'success', 'video_paths': video_paths}), 200
    except ValueError as e:
        logging.error(f"Value error during ingestion: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid input provided.'}), 400
    except KeyError as e:
        logging.error(f"Missing key during ingestion: {e}")
        return jsonify({'status': 'error', 'message': f'Missing required key: {e}'}), 400
    except Exception as e:
        logging.error(f"Unexpected error during ingestion: {e}")
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred.'}), 500
