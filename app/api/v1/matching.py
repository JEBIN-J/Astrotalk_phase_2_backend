"""Flask Horoscope Matching (Milan) Blueprint."""
from flask import Blueprint, request, jsonify
from app.services.matching_engine import calculate_ashtakoota_milan

matching_bp = Blueprint("matching", __name__, url_prefix="/api/v1/matching")


@matching_bp.route("/ashtakoota", methods=["POST"])
def match_ashtakoota():
    """Calculate 36 Guna Ashtakoota Milan and Manglik Analysis."""
    data = request.get_json() or {}
    boy = data.get("boy", {})
    girl = data.get("girl", {})
    
    result = calculate_ashtakoota_milan(boy, girl)
    return jsonify(result), 200


@matching_bp.route("/sample", methods=["GET"])
def sample_match():
    """Retrieve sample 36-point compatibility report."""
    boy = {
        "name": "Aarav Sharma",
        "date_of_birth": "1994-01-12",
        "time_of_birth": "07:15",
        "place_of_birth": "New Delhi, India",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": 5.5
    }
    girl = {
        "name": "Ananya Patel",
        "date_of_birth": "1996-06-24",
        "time_of_birth": "14:45",
        "place_of_birth": "Ahmedabad, India",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "timezone": 5.5
    }
    result = calculate_ashtakoota_milan(boy, girl)
    return jsonify(result), 200
