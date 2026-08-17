"""Flask Horoscope, Janam Kundli, Dasha & Ashtakvarga Blueprint."""
from flask import Blueprint, jsonify, request
from app.services.vedic_engine import generate_full_kundli
from app.services.lal_kitab_engine import generate_lal_kitab_chart
from app.services.bnn_engine import generate_bnn_chart
from app.services.jaimini_engine import generate_jaimini_chart
from app.services.daily_horoscope_engine import generate_daily_horoscope

horoscope_bp = Blueprint('horoscope', __name__)

def parse_horoscope_data():
    data = request.json or {}
    return {
        "name": data.get("name", "Rahul Sharma"),
        "date_of_birth": data.get("date_of_birth", "1995-08-15"),
        "time_of_birth": data.get("time_of_birth", "06:30"),
        "place_of_birth": data.get("place_of_birth", "New Delhi, India"),
        "latitude": float(data.get("latitude", 28.6139)),
        "longitude": float(data.get("longitude", 77.2090)),
        "timezone": float(data.get("timezone", 5.5))
    }

import re

def remove_hindi_text(obj):
    if isinstance(obj, str):
        cleaned = re.sub(r'[\u0900-\u097F]+', '', obj)
        cleaned = re.sub(r'\(\s*\)', '', cleaned)
        return cleaned.strip()
    elif isinstance(obj, list):
        return [remove_hindi_text(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: remove_hindi_text(v) for k, v in obj.items()}
    return obj

@horoscope_bp.route("/jaimini", methods=["POST"])
def get_jaimini():
    """Calculate exact Jaimini Chara Karakas, Arudhas, and Rashi Aspects."""
    data = parse_horoscope_data()
    result = generate_jaimini_chart(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    result = remove_hindi_text(result)
    return jsonify(result)

@horoscope_bp.route("/bnn", methods=["POST"])
def get_bnn():
    """Calculate exact BNN linkages and event analysis."""
    data = parse_horoscope_data()
    result = generate_bnn_chart(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    result = remove_hindi_text(result)
    return jsonify(result)

@horoscope_bp.route("/lal-kitab", methods=["POST"])
def get_lal_kitab():
    """Calculate exact Lal Kitab planetary placements and remedies."""
    data = parse_horoscope_data()
    result = generate_lal_kitab_chart(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    result = remove_hindi_text(result)
    return jsonify(result)

@horoscope_bp.route("/kundli", methods=["POST"])
def get_kundli():
    """Calculate full Janam Kundli with planets, dasha, and SAV."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    result = remove_hindi_text(result)
    return jsonify(result)

@horoscope_bp.route("/sample", methods=["GET"])
def get_sample_kundli():
    """Retrieve sample Kundli for instant UI testing."""
    result = generate_full_kundli(
        name="Rahul Sharma",
        dob_str="1995-08-15",
        tob_str="06:30",
        pob_str="New Delhi, India",
        latitude=28.6139,
        longitude=77.2090,
        timezone=5.5
    )
    return jsonify(result)

@horoscope_bp.route("/planets", methods=["POST"])
def get_planets():
    """Retrieve isolated planetary degrees and dignities."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    resp = {
        "person_name": result["person_name"],
        "ascendant": result["ascendant_lagna"],
        "planets": result["planets"]
    }
    return jsonify(remove_hindi_text(resp))

@horoscope_bp.route("/dasha", methods=["POST"])
def get_dasha():
    """Retrieve 120-year Vimshottari Mahadasha timeline."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    resp = {
        "current_running_dasha": result["current_running_dasha"],
        "vimshottari_dasha_timeline": result["vimshottari_dasha_timeline"]
    }
    return jsonify(remove_hindi_text(resp))

@horoscope_bp.route("/ashtakvarga", methods=["POST"])
def get_ashtakvarga():
    """Retrieve Sarvashtakvarga (SAV) points."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    return jsonify(remove_hindi_text(result["ashtakvarga"]))

@horoscope_bp.route("/upagrahas", methods=["POST"])
def get_upagrahas():
    """Retrieve classical Upagrahas (Mandi, Gulika, Dhuma, etc.)."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    resp = {
        "person_name": result["person_name"],
        "upagrahas": result["upagrahas"]
    }
    return jsonify(remove_hindi_text(resp))

@horoscope_bp.route("/arudhas", methods=["POST"])
def get_arudhas():
    """Retrieve Arudha Padas and Special Lagnas."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    resp = {
        "person_name": result["person_name"],
        "arudha_padas": result["arudha_padas"],
        "special_lagnas": result["special_lagnas"]
    }
    return jsonify(remove_hindi_text(resp))

@horoscope_bp.route("/divisional", methods=["POST"])
def get_divisional_charts():
    """Retrieve all 16 Classical Shodashavarga Divisional Charts."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    resp = {
        "person_name": result["person_name"],
        "divisional_charts": result["divisional_charts"],
        "bhava_chalit": result["bhava_chalit"]
    }
    return jsonify(remove_hindi_text(resp))


@horoscope_bp.route('/daily', methods=['GET'])
def daily_horoscope():
    rashi = request.args.get('rashi', 'Aries')
    try:
        data = generate_daily_horoscope(rashi)
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

