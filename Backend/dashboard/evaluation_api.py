from flask import Blueprint, jsonify, request
import logging
from Backend.dashboard.evaluation_logic import evaluate_codebase

bp_evaluation = Blueprint('evaluation', __name__, url_prefix='/api/evaluation')

@bp_evaluation.route('/', methods=['POST'])
def run_evaluation():
    """
    Run the codebase evaluation and return the results as JSON.
    """
    try:
        missing_steps = evaluate_codebase()
        return jsonify({
            'status': 'success',
            'missing_steps': missing_steps
        }), 200
    except Exception as e:
        logging.error(f"Evaluation failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
