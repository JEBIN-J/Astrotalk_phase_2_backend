"""
angel_numbers.py
REST API Blueprint for Angel Numbers Module.
Route prefix: /api/v1/numerology/angel-numbers
"""

from flask import Blueprint, request, jsonify
from app.services.angel_number_service import AngelNumberService
from app.api.v1.auth import get_current_user

angel_numbers_bp = Blueprint('angel_numbers', __name__)

def _resolve_user_id(data: dict = None):
    """Resolves authenticated user ID from JWT or payload."""
    current_user, _ = get_current_user()
    if current_user and current_user.get("id"):
        return str(current_user.get("id"))
    if data and data.get("user_id"):
        return str(data.get("user_id"))
    # Also check query param or header
    uid = request.args.get("user_id") or request.headers.get("X-User-ID")
    if uid:
        return str(uid)
    return None

@angel_numbers_bp.route("/lookup", methods=["POST"])
def lookup_sequence():
    """
    Accepts sequence or clock string and returns deterministic reduction,
    detected mathematical patterns, and reviewed interpretation.
    """
    try:
        data = request.get_json() or {}
        sequence = data.get("sequence", "")
        if not sequence:
            return jsonify({
                "status": "error",
                "message": "Sequence is required (e.g. '111', '1234', '11:11')"
            }), 400
        
        result = AngelNumberService.lookup_sequence(str(sequence))
        if not result.get("success"):
            return jsonify({
                "status": "error",
                "message": result.get("error", "Failed to process sequence")
            }), 400
            
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Internal error during sequence lookup: {str(e)}"
        }), 500

@angel_numbers_bp.route("/personal-number", methods=["POST"])
def calculate_personal_number():
    """
    Calculates personal angel number via DOB (Method A) or Name (Method B).
    """
    try:
        data = request.get_json() or {}
        method = data.get("method", "dob").lower()
        dob = data.get("dob")
        name = data.get("name")

        result = AngelNumberService.calculate_personal_number(method=method, dob=dob, name=name)
        if not result.get("success"):
            return jsonify({
                "status": "error",
                "message": result.get("error", "Personal number calculation failed")
            }), 400

        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Internal error calculating personal number: {str(e)}"
        }), 500

@angel_numbers_bp.route("/patterns", methods=["GET"])
def get_patterns():
    """Returns all published sequence pattern definitions."""
    try:
        patterns = AngelNumberService.get_published_patterns()
        return jsonify({
            "status": "success",
            "data": patterns
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@angel_numbers_bp.route("/popular", methods=["GET"])
def get_popular():
    """Returns curated popular sequences with reviewed entries."""
    try:
        sequences = AngelNumberService.get_popular_sequences()
        return jsonify({
            "status": "success",
            "data": sequences
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@angel_numbers_bp.route("/mirror-hours", methods=["GET"])
def get_mirror_hours():
    """Returns all published mirror hour entries and clock patterns."""
    try:
        hours = AngelNumberService.get_mirror_hours()
        return jsonify({
            "status": "success",
            "data": hours
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@angel_numbers_bp.route("/daily", methods=["GET"])
def get_daily():
    """Returns deterministic daily reflection for date."""
    try:
        date_str = request.args.get("date")
        tz = request.args.get("timezone", "UTC")
        res = AngelNumberService.get_daily_reflection(date_str=date_str, timezone=tz)
        if not res.get("success"):
            return jsonify({
                "status": "error",
                "message": res.get("error", "No reflection found")
            }), 404
        return jsonify({
            "status": "success",
            "data": res["daily"]
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ================================
# Journal Endpoints (Authorized)
# ================================

@angel_numbers_bp.route("/journal", methods=["GET"])
def get_journal():
    """Returns genuine sightings for authenticated user only."""
    try:
        user_id = _resolve_user_id()
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "Authentication required to access journal"
            }), 401
        
        search = request.args.get("search")
        res = AngelNumberService.get_sightings(user_id=user_id, search=search)
        return jsonify({
            "status": "success",
            "data": res
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@angel_numbers_bp.route("/journal", methods=["POST"])
def add_journal_entry():
    """Records a new sighting for the user."""
    try:
        data = request.get_json() or {}
        user_id = _resolve_user_id(data)
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "Authentication required to record sightings"
            }), 401
        
        seq = data.get("observed_sequence")
        if not seq:
            return jsonify({
                "status": "error",
                "message": "observed_sequence is required"
            }), 400

        res = AngelNumberService.add_sighting(
            user_id=user_id,
            observed_sequence=seq,
            observed_at=data.get("observed_at"),
            timezone=data.get("timezone", "UTC"),
            context_category=data.get("context_category"),
            personal_note=data.get("personal_note"),
            mood=data.get("mood")
        )
        if not res.get("success"):
            return jsonify({"status": "error", "message": res.get("error")}), 400
        
        return jsonify({
            "status": "success",
            "data": res
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@angel_numbers_bp.route("/journal/<int:sighting_id>", methods=["PATCH"])
def update_journal_entry(sighting_id):
    """Updates an existing sighting owned by the user."""
    try:
        data = request.get_json() or {}
        user_id = _resolve_user_id(data)
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "Authentication required"
            }), 401
        
        res = AngelNumberService.update_sighting(
            user_id=user_id,
            sighting_id=sighting_id,
            context_category=data.get("context_category"),
            personal_note=data.get("personal_note"),
            mood=data.get("mood")
        )
        if not res.get("success"):
            status_code = 403 if "Unauthorized" in res.get("error", "") else 404
            return jsonify({"status": "error", "message": res.get("error")}), status_code

        return jsonify({
            "status": "success",
            "data": res
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@angel_numbers_bp.route("/journal/<int:sighting_id>", methods=["DELETE"])
def delete_journal_entry(sighting_id):
    """Deletes a sighting owned by the user."""
    try:
        data = request.get_json() if request.is_json else {}
        user_id = _resolve_user_id(data)
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "Authentication required"
            }), 401
        
        res = AngelNumberService.delete_sighting(user_id=user_id, sighting_id=sighting_id)
        if not res.get("success"):
            status_code = 403 if "Unauthorized" in res.get("error", "") else 404
            return jsonify({"status": "error", "message": res.get("error")}), status_code

        return jsonify({
            "status": "success",
            "data": res
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
