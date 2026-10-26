"""Flask Varshaphal / Annual Horoscope Blueprint."""
from flask import Blueprint, jsonify, request
from app.services.varshaphal_engine import generate_varshaphal
import re

varshaphal_bp = Blueprint('varshaphal', __name__)

def parse_varshaphal_request():
    data = request.json or {}
    return {
        "name": data.get("name", "User"),
        "date_of_birth": data.get("date_of_birth", "1984-01-22"),
        "time_of_birth": data.get("time_of_birth", "02:39:13"),
        "place_of_birth": data.get("place_of_birth", "HAJIPUR (BIHAR)"),
        "latitude": float(data.get("latitude", 25.6833)),
        "longitude": float(data.get("longitude", 85.2167)),
        "timezone": float(data.get("timezone", 5.5)),
        "target_year": int(data.get("target_year", 2026)),
        "return_place": data.get("return_place"),
        "return_latitude": float(data.get("return_latitude")) if data.get("return_latitude") is not None else None,
        "return_longitude": float(data.get("return_longitude")) if data.get("return_longitude") is not None else None,
        "return_timezone": float(data.get("return_timezone")) if data.get("return_timezone") is not None else None,
        "ayanamsa": data.get("ayanamsa", "LAHIRI"),
        "custom_ayanamsa": float(data.get("custom_ayanamsa", 0.0)) if data.get("custom_ayanamsa") is not None else None,
        "house_system": data.get("house_system", "Sripathi")
    }

def clean_hindi_text(obj):
    if isinstance(obj, str):
        cleaned = re.sub(r'[\u0900-\u097F]+', '', obj)
        cleaned = re.sub(r'\(\s*\)', '', cleaned)
        return cleaned.strip()
    elif isinstance(obj, list):
        return [clean_hindi_text(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: clean_hindi_text(v) for k, v in obj.items()}
    return obj

@varshaphal_bp.route("/calculate", methods=["POST"])
def calculate_varshaphal_route():
    """Calculate full classical Varshaphal (Annual Horoscope) chart, strengths & predictions."""
    params = parse_varshaphal_request()
    try:
        result = generate_varshaphal(
            name=params["name"],
            date_of_birth=params["date_of_birth"],
            time_of_birth=params["time_of_birth"],
            place_of_birth=params["place_of_birth"],
            latitude=params["latitude"],
            longitude=params["longitude"],
            timezone=params["timezone"],
            target_year=params["target_year"],
            return_place=params["return_place"],
            return_latitude=params["return_latitude"],
            return_longitude=params["return_longitude"],
            return_timezone=params["return_timezone"],
            ayanamsa=params["ayanamsa"],
            custom_ayanamsa=params["custom_ayanamsa"],
            house_system=params["house_system"]
        )
        return jsonify(clean_hindi_text(result)), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@varshaphal_bp.route("/mudda-dasha", methods=["POST"])
def get_mudda_dasha_route():
    """Get standalone annual Mudda Dasha timeline with sub-periods."""
    params = parse_varshaphal_request()
    try:
        result = generate_varshaphal(
            name=params["name"],
            date_of_birth=params["date_of_birth"],
            time_of_birth=params["time_of_birth"],
            place_of_birth=params["place_of_birth"],
            latitude=params["latitude"],
            longitude=params["longitude"],
            timezone=params["timezone"],
            target_year=params["target_year"],
            ayanamsa=params["ayanamsa"]
        )
        return jsonify(clean_hindi_text(result.get("mudda_dasha", {}))), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@varshaphal_bp.route("/sahams", methods=["POST"])
def get_sahams_route():
    """Get all 40 classical Tajika Sahams for the annual chart."""
    params = parse_varshaphal_request()
    try:
        result = generate_varshaphal(
            name=params["name"],
            date_of_birth=params["date_of_birth"],
            time_of_birth=params["time_of_birth"],
            place_of_birth=params["place_of_birth"],
            latitude=params["latitude"],
            longitude=params["longitude"],
            timezone=params["timezone"],
            target_year=params["target_year"],
            ayanamsa=params["ayanamsa"]
        )
        return jsonify({"sahams": clean_hindi_text(result.get("sahams", []))}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@varshaphal_bp.route("/tripataki", methods=["POST"])
def get_tripataki_route():
    """Get Tripataki Chakra and Vedhas on Moon and planets."""
    params = parse_varshaphal_request()
    try:
        result = generate_varshaphal(
            name=params["name"],
            date_of_birth=params["date_of_birth"],
            time_of_birth=params["time_of_birth"],
            place_of_birth=params["place_of_birth"],
            latitude=params["latitude"],
            longitude=params["longitude"],
            timezone=params["timezone"],
            target_year=params["target_year"],
            ayanamsa=params["ayanamsa"]
        )
        return jsonify(clean_hindi_text(result.get("tripataki_chakra", {}))), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
