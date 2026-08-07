"""Flask Panchanga and Muhurta Blueprint."""
from flask import Blueprint, request, jsonify
from app.services.panchang_engine import calculate_daily_panchang

panchang_bp = Blueprint("panchang", __name__, url_prefix="/api/v1/panchang")


@panchang_bp.route("/today", methods=["GET"])
def get_today_panchang():
    """Retrieve today's live Panchanga and Shubh Muhurta."""
    lat = float(request.args.get("latitude", 28.6139))
    lon = float(request.args.get("longitude", 77.2090))
    tz = float(request.args.get("timezone", 5.5))
    place = request.args.get("place", "New Delhi")
    
    result = calculate_daily_panchang(
        target_date=None,
        latitude=lat,
        longitude=lon,
        timezone=tz,
        place_name=place
    )
    return jsonify(result), 200


@panchang_bp.route("/daily", methods=["POST"])
def get_daily_panchang():
    """Calculate Panchang for custom date and coordinates."""
    data = request.get_json() or {}
    result = calculate_daily_panchang(
        target_date=data.get("date"),
        latitude=float(data.get("latitude", 28.6139)),
        longitude=float(data.get("longitude", 77.2090)),
        timezone=float(data.get("timezone", 5.5)),
        place_name=data.get("place_name", "New Delhi")
    )
    return jsonify(result), 200


@panchang_bp.route("/muhurta", methods=["GET"])
def get_muhurta():
    """Fetch Abhijit Muhurta, Rahu Kaal, Yamaganda, Gulika Kaal."""
    lat = float(request.args.get("latitude", 28.6139))
    lon = float(request.args.get("longitude", 77.2090))
    tz = float(request.args.get("timezone", 5.5))
    
    panchang = calculate_daily_panchang(None, lat, lon, tz, "New Delhi")
    return jsonify({
        "date": panchang["formatted_date"],
        "abhijit_muhurta": panchang["abhijit_muhurta"],
        "rahu_kaal": panchang["rahu_kaal"],
        "yamaganda": panchang["yamaganda"],
        "gulika_kaal": panchang["gulika_kaal"],
        "sunrise": panchang["sunrise"],
        "sunset": panchang["sunset"]
    }), 200
