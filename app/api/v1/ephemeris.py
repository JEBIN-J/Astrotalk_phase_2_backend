"""Flask Ephemeris Blueprint."""
from flask import Blueprint, request, jsonify
from app.services.ephemeris_engine import calculate_ephemeris

ephemeris_bp = Blueprint("ephemeris", __name__, url_prefix="/api/v1/ephemeris")


@ephemeris_bp.route("/calculate", methods=["POST"])
def get_ephemeris():
    """Calculate astronomical ephemeris longitudes."""
    data = request.get_json() or {}
    result = calculate_ephemeris(
        date_str=data.get("date", "2026-08-06"),
        time_str=data.get("time", "12:00"),
        latitude=float(data.get("latitude", 28.6139)),
        longitude=float(data.get("longitude", 77.2090)),
        ayanamsa_type=data.get("ayanamsa_system", "lahiri")
    )
    return jsonify(result), 200
