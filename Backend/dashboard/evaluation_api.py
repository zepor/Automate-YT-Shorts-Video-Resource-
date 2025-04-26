"""
__summary__: Evaluation API for the codebase.
__author__: Your Name
"""
import logging

from flask import Blueprint, jsonify

from Backend.dashboard.evaluation_logic import evaluate_codebase

bp_evaluation = Blueprint("bp_evaluation", __name__)

@bp_evaluation.route("/evaluation/", methods=["POST"])
def run_evaluation():
    """
    API endpoint to run codebase evaluation and return prompt recommendation.
    Always returns a valid JSON response with prompt_recommendation and errors.
    """
    try:
        result = evaluate_codebase()
        # Always return a valid JSON with prompt_recommendation
        if not result.get("prompt_recommendation"):
            result["prompt_recommendation"] = (
                "No prompt recommendation available. Please check logs for errors."
            )
        return jsonify(result), 200
    except (ImportError, ValueError) as e:
        logging.error("Known exception during evaluation: %s", str(e), exc_info=True)
        return jsonify({
            "prompt_recommendation": f"Error: {str(e)}",
            "errors": [str(e)]
        }), 500
    except Exception as e:  # pylint: disable=broad-except
        # Catch-all for unexpected exceptions; suppressed pylint warning as this is an API boundary
        logging.error("Unhandled exception during evaluation: %s", str(e), exc_info=True)
        return jsonify({
            "prompt_recommendation": f"Error: {str(e)}",
            "errors": [str(e)]
        }), 500
