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
        "timezone": float(data.get("timezone", 5.5)),
        "days_in_year": float(data.get("days_in_year", 365.256364)),
        "bhava_system": data.get("bhava_system", "Porphyry (Sripathi)")
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
    days_in_year = data.get("days_in_year", 365.256364)
    bhava_system = data.get("bhava_system", "Porphyry (Sripathi)")
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"],
        days_in_year, bhava_system
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
    """Retrieve Dynamic Dasha timeline."""
    req_data = request.json or {}
    dasha_type = req_data.get("dasha_type", "Vimshottari Dasha")
    days_in_year = float(req_data.get("days_in_year", 365.256364))
    
    # DEBUG: Log what the app is sending
    import logging
    logging.warning(f"[DASHA API] Received: name={req_data.get('name')}, dob={req_data.get('date_of_birth')}, tob={req_data.get('time_of_birth')}, lat={req_data.get('latitude')}, lon={req_data.get('longitude')}, tz={req_data.get('timezone')}, dasha_type={dasha_type}")
    
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"],
        days_in_year
    )
    
    if dasha_type == "Vimshottari Dasha":
        timeline = result["vimshottari_dasha_timeline"]
        # Enrich: add Pratyantardasha (Prati) inside each Antardasha
        _add_pratyantardasha(timeline, dasha_type, days_in_year)
        resp = {
            "current_running_dasha": result["current_running_dasha"],
            "dasha_timeline": timeline
        }
    else:
        from app.services.vedic_engine import calculate_advanced_dasha
        from datetime import datetime
        
        moon_deg = 0.0
        moon_nak_idx = 1
        for p in result["planets"]:
            if p["planet_name_simple"] == "Moon":
                moon_deg = p["degree_decimal"]
                moon_nak_idx = int(moon_deg / 13.333333) + 1
                break
                
        dob_str = result["date_of_birth"]
        tob_str = result["time_of_birth"]
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        tob_parts = [int(p) for p in tob_str.split(":")]
        second_part = tob_parts[2] if len(tob_parts) > 2 else 0
        birth_dt = datetime(dob.year, dob.month, dob.day, tob_parts[0], tob_parts[1], second_part)
        
        timeline = calculate_advanced_dasha(
            dasha_type, moon_nak_idx, moon_deg, birth_dt, result["planets"], days_in_year
        )
        
        # Enrich: add Pratyantardasha for advanced dashas too
        _add_pratyantardasha(timeline, dasha_type, days_in_year)
        
        active_dasha = None
        for item in timeline:
            if item.get("is_active"):
                active_dasha = {
                    "active_mahadasha": item.get("planet"),
                    "active_antardasha": item.get("antardashas")[0]["planet"] if item.get("antardashas") else None,
                    "start": item.get("start"),
                    "end": item.get("end")
                }
                for ad in item.get("antardashas", []):
                    if ad.get("is_active"):
                        active_dasha["active_antardasha"] = ad.get("planet")
                        break
                break
                
        if not active_dasha and timeline:
            active_dasha = {
                "active_mahadasha": timeline[0]["planet"],
                "active_antardasha": timeline[0]["antardashas"][0]["planet"] if timeline[0]["antardashas"] else None,
                "start": timeline[0]["start"],
                "end": timeline[0]["end"]
            }
            
        resp = {
            "current_running_dasha": active_dasha,
            "dasha_timeline": timeline
        }
        
    return jsonify(remove_hindi_text(resp))


def _add_pratyantardasha(timeline: list, dasha_type: str, days_in_year: float = 365.256364):
    """Adds Pratyantardasha periods inside each Antardasha for full 3-level calculation."""
    from datetime import datetime, timedelta
    
    if "Chara Dasha" in dasha_type:
        return # Skip for Chara Dasha as it requires complex Jaimini forward/reverse sub-sub calculation
        
    if "Ashtottari" in dasha_type:
        years_map = {"Sun": 6, "Moon": 15, "Mars": 8, "Mercury": 17, "Saturn": 10, "Jupiter": 19, "Rahu": 12, "Venus": 21}
        sequence = ["Sun", "Moon", "Mars", "Mercury", "Saturn", "Jupiter", "Rahu", "Venus"]
        total_cycle = 108.0
    elif "Yogini" in dasha_type:
        years_map = {"Mangala": 1, "Pingala": 2, "Dhanya": 3, "Bhramari": 4, "Bhadrika": 5, "Ulka": 6, "Siddha": 7, "Sankata": 8}
        sequence = ["Mangala", "Pingala", "Dhanya", "Bhramari", "Bhadrika", "Ulka", "Siddha", "Sankata"]
        total_cycle = 36.0
    else: # Vimshottari (including Tribhagi and all D1/D9 variants)
        years_map = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
        sequence = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
        total_cycle = 120.0
        
    now = datetime.now()
    
    for maha in timeline:
        maha_planet = maha.get("planet", "")
        # For Tribhagi, the actual mahadasha years are divided by 3, but the proportions stay identical.
        # We can just extract the total days of the Antardasha directly from dates!
        
        for antara in maha.get("antardashas", []):
            ad_planet = antara.get("planet", "")
            
            # Parse antara start/end dates
            try:
                ad_start = datetime.strptime(antara["start"], "%d %b %Y")
                ad_end   = datetime.strptime(antara["end"],   "%d %b %Y")
            except Exception:
                antara["pratyantardashas"] = []
                continue
                
            ad_total_days = (ad_end - ad_start).total_seconds() / 86400.0
            
            try:
                prati_seq_start = sequence.index(ad_planet)
            except ValueError:
                # If planet not found in sequence, skip
                antara["pratyantardashas"] = []
                continue
                
            prati_start = ad_start
            pratis = []
            
            seq_len = len(sequence)
            for k in range(seq_len):
                prati_planet = sequence[(prati_seq_start + k) % seq_len]
                # Proportion of this planet in the cycle
                proportion = years_map.get(prati_planet, 0) / total_cycle
                prati_days = ad_total_days * proportion
                
                prati_end = prati_start + timedelta(days=prati_days)
                
                # To avoid rounding drift on the very last item, just pin it to ad_end
                if k == seq_len - 1:
                    prati_end = ad_end
                    
                is_active = prati_start <= now < prati_end
                pratis.append({
                    "planet": prati_planet,
                    "start": prati_start.strftime("%d %b %Y"),
                    "end": prati_end.strftime("%d %b %Y"),
                    "duration_days": round((prati_end - prati_start).days, 0),
                    "is_active": is_active
                })
                prati_start = prati_end
            
            antara["pratyantardashas"] = pratis


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

