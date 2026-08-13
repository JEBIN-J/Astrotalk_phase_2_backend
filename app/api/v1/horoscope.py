"""Flask Horoscope, Janam Kundli, Dasha & Ashtakvarga Blueprint."""
from flask import Blueprint, jsonify, request
from app.services.vedic_engine import generate_full_kundli

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

@horoscope_bp.route("/kundli", methods=["POST"])
def get_kundli():
    """Calculate full Janam Kundli with planets, dasha, and SAV."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
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
    return jsonify({
        "person_name": result["person_name"],
        "ascendant": result["ascendant_lagna"],
        "planets": result["planets"]
    })

@horoscope_bp.route("/dasha", methods=["POST"])
def get_dasha():
    """Retrieve 120-year Vimshottari Mahadasha timeline."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    return jsonify({
        "current_running_dasha": result["current_running_dasha"],
        "vimshottari_dasha_timeline": result["vimshottari_dasha_timeline"]
    })

@horoscope_bp.route("/ashtakvarga", methods=["POST"])
def get_ashtakvarga():
    """Retrieve Sarvashtakvarga (SAV) points."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    return jsonify(result["ashtakvarga"])

@horoscope_bp.route("/upagrahas", methods=["POST"])
def get_upagrahas():
    """Retrieve classical Upagrahas (Mandi, Gulika, Dhuma, etc.)."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    return jsonify({
        "person_name": result["person_name"],
        "upagrahas": result["upagrahas"]
    })

@horoscope_bp.route("/arudhas", methods=["POST"])
def get_arudhas():
    """Retrieve Arudha Padas and Special Lagnas."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    return jsonify({
        "person_name": result["person_name"],
        "arudha_padas": result["arudha_padas"],
        "special_lagnas": result["special_lagnas"]
    })

@horoscope_bp.route("/divisional", methods=["POST"])
def get_divisional_charts():
    """Retrieve all 16 Classical Shodashavarga Divisional Charts."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    )
    return jsonify({
        "person_name": result["person_name"],
        "divisional_charts": result["divisional_charts"],
        "bhava_chalit": result["bhava_chalit"]
    })
