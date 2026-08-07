"""Flask Ayanamsa Blueprint."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.services.ephemeris_engine import get_ayanamsa_offsets

ayanamsa_bp = Blueprint("ayanamsa", __name__, url_prefix="/api/v1/ayanamsa")


@ayanamsa_bp.route("/calculate", methods=["GET"])
def get_ayanamsa():
    """Retrieve Lahiri, KP, Raman, and Yukteshwar Ayanamsas."""
    year_param = request.args.get("year")
    year = int(year_param) if year_param else datetime.now().year
    result = get_ayanamsa_offsets(year)
    return jsonify(result), 200
