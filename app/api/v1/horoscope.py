"""Flask Horoscope, Janam Kundli, Dasha & Ashtakvarga Blueprint."""
from flask import Blueprint, request, jsonify
from app.services.vedic_engine import generate_full_kundli

horoscope_bp = Blueprint("horoscope", __name__, url_prefix="/api/v1/horoscope")


@horoscope_bp.route("/kundli", methods=["POST"])
def get_kundli():
    """Calculate full Janam Kundli with planets, dasha, and SAV."""
    data = request.get_json() or {}
    name = data.get("name", "Rahul Sharma")
    dob = data.get("date_of_birth", "1995-08-15")
    tob = data.get("time_of_birth", "06:30")
    pob = data.get("place_of_birth", "New Delhi, India")
    latitude = float(data.get("latitude", 28.6139))
    longitude = float(data.get("longitude", 77.2090))
    timezone = float(data.get("timezone", 5.5))
    
    result = generate_full_kundli(name, dob, tob, pob, latitude, longitude, timezone)
    return jsonify(result), 200


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
    return jsonify(result), 200


@horoscope_bp.route("/planets", methods=["POST"])
def get_planets():
    """Retrieve isolated planetary degrees and dignities."""
    data = request.get_json() or {}
    result = generate_full_kundli(
        data.get("name", "User"),
        data.get("date_of_birth", "1995-08-15"),
        data.get("time_of_birth", "06:30"),
        data.get("place_of_birth", "New Delhi, India"),
        float(data.get("latitude", 28.6139)),
        float(data.get("longitude", 77.2090)),
        float(data.get("timezone", 5.5))
    )
    return jsonify({
        "person_name": result["person_name"],
        "ascendant": result["ascendant_lagna"],
        "planets": result["planets"]
    }), 200


@horoscope_bp.route("/dasha", methods=["POST"])
def get_dasha():
    """Retrieve 120-year Vimshottari Mahadasha timeline."""
    data = request.get_json() or {}
    result = generate_full_kundli(
        data.get("name", "User"),
        data.get("date_of_birth", "1995-08-15"),
        data.get("time_of_birth", "06:30"),
        data.get("place_of_birth", "New Delhi, India"),
        float(data.get("latitude", 28.6139)),
        float(data.get("longitude", 77.2090)),
        float(data.get("timezone", 5.5))
    )
    return jsonify({
        "current_running_dasha": result["current_running_dasha"],
        "vimshottari_dasha_timeline": result["vimshottari_dasha_timeline"]
    }), 200


@horoscope_bp.route("/ashtakvarga", methods=["POST"])
def get_ashtakvarga():
    """Retrieve Sarvashtakvarga (SAV) points."""
    data = request.get_json() or {}
    result = generate_full_kundli(
        data.get("name", "User"),
        data.get("date_of_birth", "1995-08-15"),
        data.get("time_of_birth", "06:30"),
        data.get("place_of_birth", "New Delhi, India"),
        float(data.get("latitude", 28.6139)),
        float(data.get("longitude", 77.2090)),
        float(data.get("timezone", 5.5))
    )
    return jsonify(result["ashtakvarga"]), 200


@horoscope_bp.route("/upagrahas", methods=["POST"])
def get_upagrahas():
    """Retrieve classical Upagrahas (Mandi, Gulika, Dhuma, etc.)."""
    data = request.get_json() or {}
    result = generate_full_kundli(
        data.get("name", "User"),
        data.get("date_of_birth", "1995-08-15"),
        data.get("time_of_birth", "06:30"),
        data.get("place_of_birth", "New Delhi, India"),
        float(data.get("latitude", 28.6139)),
        float(data.get("longitude", 77.2090)),
        float(data.get("timezone", 5.5))
    )
    return jsonify({
        "person_name": result["person_name"],
        "upagrahas": result["upagrahas"]
    }), 200


@horoscope_bp.route("/arudhas", methods=["POST"])
def get_arudhas():
    """Retrieve Arudha Padas and Special Lagnas."""
    data = request.get_json() or {}
    result = generate_full_kundli(
        data.get("name", "User"),
        data.get("date_of_birth", "1995-08-15"),
        data.get("time_of_birth", "06:30"),
        data.get("place_of_birth", "New Delhi, India"),
        float(data.get("latitude", 28.6139)),
        float(data.get("longitude", 77.2090)),
        float(data.get("timezone", 5.5))
    )
    return jsonify({
        "person_name": result["person_name"],
        "arudha_padas": result["arudha_padas"],
        "special_lagnas": result["special_lagnas"]
    }), 200


@horoscope_bp.route("/divisional", methods=["POST"])
def get_divisional_charts():
    """Retrieve all 16 Classical Shodashavarga Divisional Charts."""
    data = request.get_json() or {}
    result = generate_full_kundli(
        data.get("name", "User"),
        data.get("date_of_birth", "1995-08-15"),
        data.get("time_of_birth", "06:30"),
        data.get("place_of_birth", "New Delhi, India"),
        float(data.get("latitude", 28.6139)),
        float(data.get("longitude", 77.2090)),
        float(data.get("timezone", 5.5))
    )
    return jsonify({
        "person_name": result["person_name"],
        "divisional_charts": result["divisional_charts"],
        "bhava_chalit": result["bhava_chalit"]
    }), 200
