from flask import Blueprint, jsonify, request
import logging
from Backend.dashboard.orchestration_logic import run_evaluation_if_code_changed

bp_orchestration = Blueprint('orchestration', __name__, url_prefix='/api/orchestration')

@bp_orchestration.route('/', methods=['POST'])
def run_orchestration():
    """
    Run orchestration logic (e.g., evaluation if code changed).
    """
    try:
        # Example: expects JSON with code_dir, hash_file, evaluation_script
        data = request.get_json(force=True)
        code_dir = data.get('code_dir')
        hash_file = data.get('hash_file')
        evaluation_script = data.get('evaluation_script')
        run_evaluation_if_code_changed(code_dir, hash_file, evaluation_script)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logging.error(f"Orchestration failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
