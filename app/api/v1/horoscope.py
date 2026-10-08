from app.services.kp_engine import generate_kp_system
"""Flask Horoscope, Janam Kundli, Dasha & Ashtakvarga Blueprint."""
from flask import Blueprint, jsonify, request
from app.services.vedic_engine import generate_full_kundli
from app.services.lal_kitab_engine import generate_lal_kitab_chart
from app.services.bnn_engine import generate_bnn_chart
from app.services.jaimini_engine import generate_jaimini_chart
from app.services.daily_horoscope_engine import generate_daily_horoscope
from app.services.kota_engine import generate_kota_chakra

horoscope_bp = Blueprint('horoscope', __name__)

def parse_horoscope_data():
    data = request.json or {}
    return {
        "name": data.get("name", "Rahul Sharma"),
        "date_of_birth": data.get("date_of_birth", ""),
        "time_of_birth": data.get("time_of_birth", ""),
        "place_of_birth": data.get("place_of_birth", "New Delhi, India"),
        "latitude": float(data.get("latitude", 28.6139)),
        "longitude": float(data.get("longitude", 77.2090)),
        "timezone": float(data.get("timezone", 5.5)),
        "days_in_year": float(data.get("days_in_year", 365.256364)),
        "bhava_system": data.get("bhava_system", "Porphyry (Sripathi)"),
        "ayanamsa": data.get("ayanamsa", "LAHIRI"),
        "custom_ayanamsa": float(data.get("custom_ayanamsa", 0.0)) if data.get("custom_ayanamsa") is not None else None
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
    , ayanamsa=data["ayanamsa"], custom_ayanamsa=data["custom_ayanamsa"])
    result = remove_hindi_text(result)
    return jsonify(result)

@horoscope_bp.route("/bnn", methods=["POST"])
def get_bnn():
    """Calculate exact BNN linkages and event analysis."""
    data = parse_horoscope_data()
    target_date_str = request.json.get("target_date_str") if request.is_json else None
    
    result = generate_bnn_chart(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"],
        target_date_str=target_date_str
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
        days_in_year, bhava_system, ayanamsa=data["ayanamsa"], custom_ayanamsa=data["custom_ayanamsa"]
    )
    result = remove_hindi_text(result)
    return jsonify(result)

@horoscope_bp.route("/sample", methods=["GET"])
def get_sample_kundli():
    """Retrieve sample Kundli for instant UI testing."""
    result = generate_full_kundli(
        name="Rahul Sharma",
        dob_str="",
        tob_str="",
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
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"],
        ayanamsa=data["ayanamsa"], custom_ayanamsa=data["custom_ayanamsa"]
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
    , ayanamsa=data["ayanamsa"], custom_ayanamsa=data["custom_ayanamsa"])
    
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
    , ayanamsa=data["ayanamsa"], custom_ayanamsa=data["custom_ayanamsa"])
    return jsonify(remove_hindi_text(result["ashtakvarga"]))

@horoscope_bp.route("/upagrahas", methods=["POST"])
def get_upagrahas():
    """Retrieve classical Upagrahas (Mandi, Gulika, Dhuma, etc.)."""
    data = parse_horoscope_data()
    result = generate_full_kundli(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"]
    , ayanamsa=data["ayanamsa"], custom_ayanamsa=data["custom_ayanamsa"])
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
    , ayanamsa=data["ayanamsa"], custom_ayanamsa=data["custom_ayanamsa"])
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
    , ayanamsa=data["ayanamsa"], custom_ayanamsa=data["custom_ayanamsa"])
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

@horoscope_bp.route("/kota-chakra", methods=["POST"])
def get_kota_chakra():
    """Calculate complete Kota Chakra including 28 Nakshatras and Transit mapping."""
    data = parse_horoscope_data()
    transit_date = request.json.get("transit_date")
    transit_time = request.json.get("transit_time")
    
    result = generate_kota_chakra(
        data["name"], data["date_of_birth"], data["time_of_birth"],
        data["place_of_birth"], data["latitude"], data["longitude"], data["timezone"],
        transit_date_str=transit_date, transit_time_str=transit_time
    )
    result = remove_hindi_text(result)
    return jsonify(result)


@horoscope_bp.route("/kp", methods=["POST"])
def get_kp_system():
    """
    Real-Time Calculation-Based KP (Krishnamurti Paddhati) System API.
    Calculates dynamic KP Chart, Vimshottari Dasha, Significators, Aspects,
    Nakshatra Nadi, and 4-Step KP from user birth details and selected Ayanamsa.
    """
    try:
        data = parse_horoscope_data()
        ayanamsa = request.json.get("ayanamsa", "Krishnamurti (KP New)")
        
        result = generate_kp_system(
            name=data.get("name", "User"),
            dob_str=data.get("date_of_birth", ""),
            tob_str=data.get("time_of_birth", ""),
            pob_str=data.get("place_of_birth", "Delhi, India"),
            latitude=float(data.get("latitude", 28.6139)),
            longitude=float(data.get("longitude", 77.2090)),
            timezone=float(data.get("timezone", 5.5)),
            ayanamsa_name=ayanamsa,
            transit_datetime_str=data.get("transit_datetime"),
            transit_timezone=float(data.get("transit_timezone", data.get("timezone", 5.5))) if "transit_timezone" in data else None
        )
        return jsonify(remove_hindi_text(result))
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unable to calculate KP chart: {str(e)}"
        }), 400


@horoscope_bp.route("/ayanamsa_degrees", methods=["GET"])
def get_ayanamsa_degrees():
    """
    Returns the live ayanamsa degree values for ALL supported ayanamsas,
    computed by Swiss Ephemeris for the given birth date/time/location.
    """
    from app.services.vedic_engine import calculate_julian_day, calculate_lahiri_ayanamsa
    from datetime import datetime

    date_str = request.args.get("date")
    time_str = request.args.get("time")
    if not date_str or not time_str:
        return jsonify({"error": "date and time are required"}), 400

    lat = float(request.args.get("lat", 28.6139))
    lon = float(request.args.get("lon", 77.2090))
    tz = float(request.args.get("tz", 5.5))

    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError:
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return jsonify({"error": "Invalid date or time format"}), 400

    hour_utc = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 - tz
    jd = calculate_julian_day(dt.year, dt.month, dt.day, hour_utc)

    all_ayanamsas = [
        "LAHIRI", "BV_RAMAN", "KP_OLD", "SRI_YUKTESWAR", "DE_LUCE",
        "USHA_SHASHI", "DJWHAL_KHOOL", "JN_BHASIN", "FAGAN_BRADLEY",
        "TROPICAL", "KP_NEW", "KP_STRAIGHT_LINE", "KHULLAR", "CHANDRA_HARI",
    ]

    result = {}
    for key in all_ayanamsas:
        try:
            deg = calculate_lahiri_ayanamsa(jd, ayanamsa_key=key)
            result[key] = round(float(deg), 6)
        except Exception as e:
            result[key] = None

    return jsonify({
        "jd": round(jd, 6),
        "date": date_str,
        "time": time_str,
        "lat": lat,
        "lon": lon,
        "tz": tz,
        "ayanamsa_degrees": result
    })




@horoscope_bp.route("/cue_cards", methods=["GET"])
def get_cue_cards():
    """
    Returns data for KP System Cue Cards such as Parts of Body and Rasi Properties
    """
    rasi_properties = {
        "ARIES": "Fiery, Movable, Masculine, East, Short Stature, Barren",
        "TAURUS": "Earthy, Fixed, Feminine, South, Short Stature, Semi-Fruitful",
        "GEMINI": "Windy, Common, Masculine, West, Medium Stature, Barren",
        "CANCER": "Watery, Movable, Feminine Mute, North, Medium Stature, Fruitful",
        "LEO": "Fiery, Fixed, Masculine, East, Tall Stature, Barren",
        "VIRGO": "Earthy, Common, Feminine, South, Tall Stature, Barren",
        "LIBRA": "Windy, Movable, Masculine, West, Tall Stature, Semi-Fruitful",
        "SCORPIO": "Watery, Fixed, Feminine Mute, North, Tall Stature, Fruitful",
        "SAGITTARIUS": "Fiery, Common, Masculine, East, Medium Stature, Semi-Fruitful",
        "CAPRICORN": "Earthy, Movable, Feminine, South, Medium Stature, Semi-Fruitful",
        "AQUARIUS": "Windy, Fixed, Masculine, West, Short Stature, Barren",
        "PISCES": "Watery, Common, Feminine Mute, North, Short Stature, Fruitful"
    }

    parts_of_body = {
        "ARIES": "Head, Bones of Face, Skull, Brain",
        "TAURUS": "Neck, Throat, Eye, Nose, Ears, Tongue, Teeth",
        "GEMINI": "Respiratory System & Lungs, Shoulders, Arms, Hands, Collar Bones",
        "CANCER": "Breast, Chest, Heart, Stomach, Digestive Organs",
        "LEO": "Heart, Vertebrae, Spinal column, Back, upper Abdomen, Liver & Pancreas, Aorta, Coronary Arteries",
        "VIRGO": "Nervous System, Bowels, Abdominal & Umbilical Region",
        "LIBRA": "Lumbar Region, Skin, Kidneys, Bones of the Lumbar Region (Spine), Uterus",
        "SCORPIO": "Anus, Urinary tract (Bladder), Sexual Organs, Pelvic Bones",
        "SAGITTARIUS": "Hips, Thighs, Femur, Buttocks",
        "CAPRICORN": "Knees & Patella, Bones, Joints, Spleen",
        "AQUARIUS": "Legs & Ankles, Blood Circulation",
        "PISCES": "Feet & Toes, Lymphatic System, Blood"
    }

    houses_events = [
        {"sl": "1", "event": "Good Health", "signifying": "1, 11", "prime": "1", "remarks": "1st cusp sub-lord signifies 1 and 11, and its star lord is well placed. Health improves quickly. If connected to 5th or 11th, vitality is strong."},
        {"sl": "2", "event": "Proneness to Disease", "signifying": "1, 6, 8, 12", "prime": "1", "remarks": "Sub-lord of Ascendant signifies 6 (disease), 8 (danger/chronic), and 12 (hospitalization). Star lord of the sub-lord confirms severity."},
        {"sl": "3", "event": "Accident / Injury", "signifying": "1, 8, 12", "prime": "1", "remarks": "Sub-lord of 8th cusp signifies 8. If it further signifies 6th > fever/pain after accident; 12th > hospitalization; 2nd or 7th (maraka) > severe danger to longevity."},
        {"sl": "4", "event": "Recovery from Illness", "signifying": "1, 5, 11", "prime": "6", "remarks": "Sub-lord of 6th cusp signifies 5 and 11. 5th is 12th to 6th (negates disease), 11th indicates cure and fulfillment of desire."},
        {"sl": "5", "event": "Medical Treatment", "signifying": "6, 8, 12", "prime": "6", "remarks": "Sub-lord of 6th cusp signifies 6, 8, 12. Medical intervention is necessary. If connected to 11th, the treatment will be successful."},
        {"sl": "6", "event": "Hospitalization", "signifying": "6, 8, 12", "prime": "12", "remarks": "Sub-lord of 12th cusp is strongly connected to 6, 8, 12. Shows bed rest or hospitalization. If 11 is also signified, discharge happens soon."},
        {"sl": "7", "event": "Financial Status", "signifying": "2, 6, 11", "prime": "2", "remarks": "Sub-lord of 2nd cusp signifies 2, 6, 11. 2 indicates bank balance, 6 indicates regular inflow/service, 11 indicates net gains and desires fulfilled."},
        {"sl": "8", "event": "Gain of Money", "signifying": "2, 6, 11", "prime": "2", "remarks": "Sub-lord of 2nd or 11th cusp signifies 2, 6, 11. Native receives money without much obstacle. If retrograde, gain is delayed."},
        {"sl": "9", "event": "Obtaining a Loan", "signifying": "2, 6, 11", "prime": "6", "remarks": "Sub-lord of 6th cusp signifies 2, 6, 11. 6th is debt, 2nd is bank balance, 11th is gain. The ruling planets will indicate the timing of loan approval."},
        {"sl": "10", "event": "Repayment of Loan", "signifying": "5, 8, 12", "prime": "12", "remarks": "Sub-lord of 12th (expenditure) or 8th signifies 5, 8, 12. 5th is 12th to 6th (closing the debt), 12th is giving money away."},
        {"sl": "11", "event": "Opening Bank Account", "signifying": "2, 6, 11", "prime": "2", "remarks": "2 for money, 6 for banking/service matters and 11 for fulfillment."},
        {"sl": "12", "event": "Insurance Claim", "signifying": "2, 8, 11", "prime": "2", "remarks": "Sub-lord of 8th cusp signifies 2, 8, 11. 8th denotes unearned wealth/insurance, 2nd denotes financial receipt, 11th denotes profit."},
        {"sl": "13", "event": "Medical Insurance Claim", "signifying": "6, 8, 11", "prime": "6", "remarks": "6 for medical matter, 8 for insurance, 11 for settlement/gain."},
        {"sl": "14", "event": "Obtaining Jewellery", "signifying": "2, 11", "prime": "2", "remarks": "2 signifies valuables and 11 acquisition/gain."},
        {"sl": "15", "event": "Investment / Expenditure", "signifying": "2, 5, 8, 12", "prime": "2", "remarks": "Investment type determines additional houses; 12 indicates expenditure/outflow."},
        {"sl": "16", "event": "Unexpected Gain", "signifying": "2, 8, 11", "prime": "8", "remarks": "Sub-lord of 8th cusp signifies 2, 11. Unearned wealth like lottery or sudden inheritance. If node (Rahu/Ketu) is involved, it will be huge."},
        {"sl": "17", "event": "Unexpected Loss", "signifying": "5, 8, 12", "prime": "8", "remarks": "8/12 connections can indicate sudden financial loss or depletion."},
        {"sl": "18", "event": "Recovery of Lost Property", "signifying": "2, 6, 11", "prime": "8", "remarks": "8 represents the lost/missing matter; 2, 6 and 11 support recovery."},
        {"sl": "19", "event": "Signing a Contract", "signifying": "3, 6, 9, 11", "prime": "3", "remarks": "Sub-lord of 3rd cusp signifies 3, 6, 9, 11. 3 is agreement, 9 is long term contract. 11 indicates it will be beneficial."},
        {"sl": "20", "event": "Negotiation", "signifying": "3, 9, 11", "prime": "3", "remarks": "3 represents communication; 9/11 indicate agreement and completion."},
        {"sl": "21", "event": "Filing a Court Case", "signifying": "3, 6, 11", "prime": "3", "remarks": "Sub-lord of 3rd cusp (litigation filing) signifies 6 (disputes) and 11 (winning). If it signifies 12, money is wasted on legal fees."},
        {"sl": "22", "event": "Success in Litigation", "signifying": "1, 6, 11", "prime": "6", "remarks": "Sub-lord of 6th cusp (opponent) signifies 5, 8, 12 (loss for opponent) which means 1, 6, 11 for native (victory)."},
        {"sl": "23", "event": "Meeting Bank Officer", "signifying": "3, 6, 9, 11", "prime": "3", "remarks": "3 communication/meeting; 6 banking/debt; 11 fulfillment."},
        {"sl": "24", "event": "Passport", "signifying": "3, 9, 11, 12", "prime": "3", "remarks": "3 documentation/travel, 9 long-distance matters, 12 foreign connection."},
        {"sl": "25", "event": "Visa / Green Card", "signifying": "3, 9, 11, 12", "prime": "3", "remarks": "Documentation plus foreign travel/residence houses."},
        {"sl": "26", "event": "Starting a Journey", "signifying": "3, 9, 11", "prime": "3", "remarks": "3 indicates movement; 9 long journey; 11 successful completion."},
        {"sl": "27", "event": "Foreign Travel", "signifying": "3, 9, 12", "prime": "9", "remarks": "Sub-lord of 9th or 12th cusp signifies 3, 9, 12. 3 leaves current place, 9 long journey, 12 unknown environment/foreign land."},
        {"sl": "28", "event": "Foreign Residence", "signifying": "3, 9, 12", "prime": "12", "remarks": "12 is primary for foreign residence/separation from birthplace."},
        {"sl": "29", "event": "Return to Home", "signifying": "3, 9, 11", "prime": "3", "remarks": "3 movement, 9 long-distance journey and 11 fulfillment/return."},
        {"sl": "30", "event": "Change of Place", "signifying": "3, 9, 12", "prime": "3", "remarks": "Movement/change is judged through 3 with 9/12 depending on distance."},
        {"sl": "31", "event": "Transfer in Job", "signifying": "3, 10, 11", "prime": "3", "remarks": "Sub-lord of 10th or 3rd cusp signifies 3, 10, 11. 3 indicates change of place/movement, 10 is job, 11 is promotion or gain from transfer."},
        {"sl": "32", "event": "Basic Education", "signifying": "4, 11", "prime": "4", "remarks": "4 is primary for foundational education; 11 indicates completion."},
        {"sl": "33", "event": "Higher Education", "signifying": "4, 9, 11", "prime": "9", "remarks": "9 is primary for higher learning; 4 and 11 support education."},
        {"sl": "34", "event": "Examination Success", "signifying": "4, 5, 9, 11", "prime": "5", "remarks": "5 intelligence/performance, 4 education, 9 higher learning and 11 success."},
        {"sl": "35", "event": "Admission to Education", "signifying": "4, 9, 11", "prime": "4", "remarks": "Education cusp connected with 9/11 supports admission."},
        {"sl": "36", "event": "Engineering Education", "signifying": "4, 10", "prime": "4", "remarks": "4 education with 10 indicating technical/professional orientation."},
        {"sl": "37", "event": "Medical Education", "signifying": "4, 6", "prime": "4", "remarks": "4 education and 6 health/service-related field."},
        {"sl": "38", "event": "Legal Education", "signifying": "4, 6, 9", "prime": "4", "remarks": "4 education; 6/9 support legal/higher-learning context."},
        {"sl": "39", "event": "Fine Arts Education", "signifying": "4, 5", "prime": "4", "remarks": "4 education and 5 creativity/arts."},
        {"sl": "40", "event": "Teaching as Profession", "signifying": "2, 6, 10", "prime": "10", "remarks": "10 profession; 6 service; 2 earnings."},
        {"sl": "41", "event": "Childbirth", "signifying": "2, 5, 11", "prime": "5", "remarks": "Sub-lord of 5th cusp signifies 2, 5, 11. 5 is primary for progeny. Jupiter (karaka) must also be favorable and not retrograde."},
        {"sl": "42", "event": "Pregnancy", "signifying": "2, 5, 11", "prime": "5", "remarks": "5 child/procreation; 2 family expansion; 11 fulfillment."},
        {"sl": "43", "event": "First Child", "signifying": "2, 5, 11", "prime": "5", "remarks": "5 is the primary child house."},
        {"sl": "44", "event": "Second Child", "signifying": "2, 7, 11", "prime": "7", "remarks": "7 is used for the second-child matter in traditional KP house grouping."},
        {"sl": "45", "event": "Third Child", "signifying": "2, 9, 11", "prime": "9", "remarks": "9 is used as the primary cusp for the third-child matter."},
        {"sl": "46", "event": "Love Affair", "signifying": "5, 7, 11", "prime": "5", "remarks": "5 romance, 7 partnership and 11 fulfillment."},
        {"sl": "47", "event": "Love Marriage", "signifying": "5, 7, 11", "prime": "7", "remarks": "7 marriage; 5 love/romance; 11 fulfillment."},
        {"sl": "48", "event": "Marriage", "signifying": "2, 7, 11", "prime": "7", "remarks": "Sub-lord of 7th cusp signifies 2, 7, 11. 2 is addition to family, 7 is legal tie, 11 is permanent friendship/gain. If dual sign, multiple marriages possible."},
        {"sl": "49", "event": "Marriage Engagement", "signifying": "3, 9, 11", "prime": "7", "remarks": "3/9 indicate agreement/formalization and 11 fulfillment."},
        {"sl": "50", "event": "Second Marriage", "signifying": "2, 7, 9, 11", "prime": "9", "remarks": "9 is used as the primary cusp in the traditional second-marriage rule."},
        {"sl": "51", "event": "Marriage Delay", "signifying": "2, 7, 11 with 1, 6, 10", "prime": "7", "remarks": "Sub-lord of 7th cusp signifies 1, 6, 10 along with 2, 7, 11. Saturn's aspect or connection causes delay and frustration in finalizing."},
        {"sl": "52", "event": "Marriage Separation", "signifying": "6, 10, 12", "prime": "7", "remarks": "Sub-lord of 7th cusp signifies 6, 10, 12. 6 is divorce (12th to 7th), 10 is breaking of tie, 12 is separation."},
        {"sl": "53", "event": "Partnership", "signifying": "5, 7, 11", "prime": "7", "remarks": "7 partnership, with 5/11 supporting continuation and fulfillment."},
        {"sl": "54", "event": "Business Partnership", "signifying": "7, 10, 11", "prime": "7", "remarks": "7 partner, 10 business/profession and 11 gains."},
        {"sl": "55", "event": "Break in Partnership", "signifying": "6, 10, 12", "prime": "7", "remarks": "Adverse relationship houses can indicate interruption or separation."},
        {"sl": "56", "event": "Success in Competition", "signifying": "1, 6, 11", "prime": "6", "remarks": "1 self, 6 competition/opponents, 11 victory/fulfillment."},
        {"sl": "57", "event": "Winning in Love", "signifying": "5, 7, 11", "prime": "11", "remarks": "11 represents fulfillment, supported by 5 and 7."},
        {"sl": "58", "event": "Fulfillment of Desire", "signifying": "1, 11", "prime": "11", "remarks": "11 is the principal house of fulfillment; 1 represents the native."},
        {"sl": "59", "event": "Sexual Relationship", "signifying": "5, 7, 8, 11", "prime": "7", "remarks": "5 romance, 7 relationship, 8 intimacy/transformation and 11 fulfillment."},
        {"sl": "60", "event": "Theft / Loss by Others", "signifying": "2, 7, 12", "prime": "7", "remarks": "7 can represent the other party; 2 property and 12 loss."},
        {"sl": "61", "event": "Danger from Opponents", "signifying": "7, 8, 12", "prime": "7", "remarks": "7 opponents, with 8/12 indicating vulnerability or loss."},
        {"sl": "62", "event": "Bank Loan", "signifying": "2, 6, 7, 11", "prime": "7", "remarks": "7 can represent the financial institution/other party; 6 debt, 2 money, 11 receipt."},
        {"sl": "63", "event": "Business / Service", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "10 profession, 6 service, 2 income and 11 gain."},
        {"sl": "64", "event": "Getting a New Job", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "Sub-lord of 10th or 6th cusp signifies 2, 6, 10, 11. Dasha/Bhukti periods of significators will grant the job. 10th is status, 6th is service."},
        {"sl": "65", "event": "Job Confirmation", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "10 career status; 2/6/11 support employment and income."},
        {"sl": "66", "event": "Promotion", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "10 status/profession with 2, 6 and 11 supporting advancement."},
        {"sl": "67", "event": "Name and Fame", "signifying": "1, 10, 11", "prime": "10", "remarks": "10 public status, 1 self and 11 recognition/gain."},
        {"sl": "68", "event": "Salary Increase", "signifying": "2, 6, 10, 11", "prime": "2", "remarks": "2 income, 6 service, 10 career and 11 increase/gain."},
        {"sl": "69", "event": "Commission Business", "signifying": "3, 10, 11", "prime": "10", "remarks": "3 transactions/communication; 10 profession; 11 gain."},
        {"sl": "70", "event": "Export Business", "signifying": "2, 6, 10, 11, 12", "prime": "10", "remarks": "10 business, 2/6/11 income/gain and 12 foreign/export connection."},
        {"sl": "71", "event": "Medical Profession", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "10 profession, 6 health/service, 2 earnings and 11 gains."},
        {"sl": "72", "event": "Legal Profession", "signifying": "2, 6, 9, 10, 11", "prime": "10", "remarks": "10 profession with 6 legal disputes/service and 9 legal/higher knowledge."},
        {"sl": "73", "event": "Political Profession", "signifying": "2, 6, 9, 10, 11", "prime": "10", "remarks": "10 status, 6 service, 9 ideology/higher principles and 11 gains."},
        {"sl": "74", "event": "Computer / IT Profession", "signifying": "2, 3, 6, 10, 11", "prime": "10", "remarks": "3 communication/technology, 10 profession, 2/6/11 earnings/service/gain."},
        {"sl": "75", "event": "Publication as Profession", "signifying": "2, 3, 6, 10, 11", "prime": "10", "remarks": "3 writing/communication plus 10 profession and 2/6/11 income/service/gain."},
        {"sl": "76", "event": "Sports as Profession", "signifying": "2, 5, 10, 11", "prime": "10", "remarks": "5 sports/creative ability, 10 profession, 2 income and 11 gains."},
        {"sl": "77", "event": "Film / Arts as Profession", "signifying": "2, 5, 10, 11", "prime": "10", "remarks": "5 creativity/performance plus professional and financial houses."},
        {"sl": "78", "event": "Business Problems", "signifying": "5, 8, 10", "prime": "10", "remarks": "10 business; 5/8 can indicate obstacles, uncertainty or disruption."},
        {"sl": "79", "event": "Break in Service", "signifying": "5, 9, 10", "prime": "10", "remarks": "10 profession; 5/9 indicate interruption/change in the professional path."},
        {"sl": "80", "event": "Suspension from Service", "signifying": "5, 6, 8, 10", "prime": "10", "remarks": "10 employment with 5/6/8 indicating adverse service circumstances."},
        {"sl": "81", "event": "Removal from Service", "signifying": "5, 9, 10", "prime": "10", "remarks": "10 career with adverse houses indicating discontinuation."},
        {"sl": "82", "event": "Voluntary Retirement", "signifying": "1, 5, 9", "prime": "10", "remarks": "1 self-decision, 5 change in activity and 9 withdrawal/change of direction."},
        {"sl": "83", "event": "Compulsory Retirement", "signifying": "5, 8, 9, 10", "prime": "10", "remarks": "10 career with adverse/change houses indicating forced discontinuation."},
        {"sl": "84", "event": "Research", "signifying": "6, 8, 11, 12", "prime": "12", "remarks": "8/12 support deep/hidden investigation; 6 and 11 support useful results."},
        {"sl": "85", "event": "Spiritual Practice", "signifying": "6, 9, 11, 12", "prime": "9", "remarks": "9 spirituality/philosophy; 12 withdrawal; 6 disciplined practice; 11 fulfillment."},
        {"sl": "86", "event": "Long-Distance Travel", "signifying": "3, 9, 12", "prime": "9", "remarks": "9 is long journey; 3 movement and 12 foreign/separation."},
        {"sl": "87", "event": "Foreign Settlement", "signifying": "3, 9, 12", "prime": "12", "remarks": "12 is primary for foreign residence; 3/9 support movement and long distance."},
        {"sl": "88", "event": "Secret Activity", "signifying": "8, 12", "prime": "12", "remarks": "8 secrecy/hidden matters and 12 isolation/concealment."},
        {"sl": "89", "event": "Secret Documents", "signifying": "4, 11, 12", "prime": "12", "remarks": "12 hidden/confidential matter; 4 documents/property context; 11 receipt."},
        {"sl": "90", "event": "Imprisonment / Confinement", "signifying": "3, 8, 12", "prime": "12", "remarks": "12 confinement, 8 restriction/crisis and 3 movement/legal circumstances."},
        {"sl": "91", "event": "Absconding", "signifying": "3, 8, 12", "prime": "12", "remarks": "3 movement, 8 crisis/hidden circumstances and 12 disappearance/isolation."},
        {"sl": "92", "event": "Inheritance – Cash / Jewellery", "signifying": "2, 8, 11", "prime": "8", "remarks": "8 inheritance/other people's assets; 2 valuables; 11 receipt/gain."},
        {"sl": "93", "event": "Inheritance – Property / Vehicle", "signifying": "4, 8, 11", "prime": "8", "remarks": "8 inheritance; 4 property/vehicle; 11 acquisition."},
        {"sl": "94", "event": "Gifts / Benefits from Others", "signifying": "6, 8, 11", "prime": "8", "remarks": "8 indicates resources from others; 11 receipt/gain."},
        {"sl": "95", "event": "Property Purchase", "signifying": "4, 11, 12", "prime": "4", "remarks": "Sub-lord of 4th cusp signifies 4, 11, 12. 4th is property, 11th is acquisition, 12th is expenditure/investment of money."},
        {"sl": "96", "event": "Property Sale", "signifying": "3, 5, 10", "prime": "4", "remarks": "Sub-lord of 4th cusp signifies 3, 5, 10. 3 is parting with property, 5 is 12th from 6th (purchaser), 10 is 4th to 7th (purchaser's property)."},
        {"sl": "97", "event": "Possession of Property", "signifying": "4, 9, 11", "prime": "4", "remarks": "4 property, 9 transfer/long-distance/legal completion and 11 acquisition."},
        {"sl": "98", "event": "New House / Housewarming", "signifying": "4, 11", "prime": "4", "remarks": "4 home/residence and 11 fulfillment/acquisition."},
        {"sl": "99", "event": "Vehicle Purchase", "signifying": "4, 11, 12", "prime": "4", "remarks": "4 vehicle/property, 11 acquisition and 12 expenditure/investment."},
        {"sl": "100", "event": "Adoption of Child", "signifying": "2, 5, 11", "prime": "5", "remarks": "5 is the primary child house; 2 indicates addition to family and 11 fulfillment/acquisition."},
        {"sl": "101", "event": "Adopting a Son", "signifying": "2, 5, 11", "prime": "5", "remarks": "Child-related houses are primary; 2 and 11 support family addition and fulfillment."},
        {"sl": "102", "event": "Adopting a Daughter", "signifying": "2, 5, 11", "prime": "5", "remarks": "5 signifies child/progeny; 2 and 11 indicate addition and fulfillment."},
        {"sl": "103", "event": "Giving Child for Adoption", "signifying": "5, 8, 12", "prime": "12", "remarks": "5 signifies child; 8/12 indicate separation, transfer or relinquishment."},
        {"sl": "104", "event": "Birth of Son", "signifying": "2, 5, 11", "prime": "5", "remarks": "5 is primary for progeny; 2 indicates family addition and 11 fulfillment."},
        {"sl": "105", "event": "Birth of Daughter", "signifying": "2, 5, 11", "prime": "5", "remarks": "5 is primary for progeny; 2 and 11 support family expansion and fulfillment."},
        {"sl": "106", "event": "Child Conception", "signifying": "2, 5, 11", "prime": "5", "remarks": "5 is the primary progeny house; 2 and 11 support family expansion and fulfillment."},
        {"sl": "107", "event": "Childbirth after Treatment", "signifying": "5, 6, 11", "prime": "5", "remarks": "5 signifies child, 6 treatment/medical intervention and 11 successful outcome."},
        {"sl": "108", "event": "Difficulty in Childbirth", "signifying": "5, 6, 8, 12", "prime": "5", "remarks": "5 represents child; 6/8/12 indicate medical difficulty, complications or hospitalization."},
        {"sl": "109", "event": "Miscarriage / Pregnancy Loss", "signifying": "5, 8, 12", "prime": "8", "remarks": "5 signifies pregnancy/child; 8 and 12 indicate loss, interruption or complications."},
        {"sl": "110", "event": "Child's Health Problem", "signifying": "5, 6, 8, 12", "prime": "6", "remarks": "5 represents child; 6 disease, 8 complications and 12 hospitalization/expense."},
        {"sl": "111", "event": "Recovery of Child from Illness", "signifying": "5, 6, 11", "prime": "11", "remarks": "5 child, 6 illness/treatment and 11 recovery/success."},
        {"sl": "112", "event": "Child's Education", "signifying": "5, 4, 9, 11", "prime": "4", "remarks": "5 represents child; 4/9 education and 11 successful completion."},
        {"sl": "113", "event": "Child's Higher Education", "signifying": "5, 9, 11", "prime": "9", "remarks": "5 child; 9 higher education and 11 fulfillment."},
        {"sl": "114", "event": "Child's Marriage", "signifying": "5, 2, 7, 11", "prime": "7", "remarks": "5 represents child; 2 family addition, 7 marriage and 11 fulfillment."},
        {"sl": "115", "event": "Child's Employment", "signifying": "5, 2, 6, 10, 11", "prime": "10", "remarks": "5 child; 10 profession, 6 service, 2 income and 11 gains."},
        {"sl": "116", "event": "Child's Success", "signifying": "5, 10, 11", "prime": "11", "remarks": "5 represents child; 10 achievement/status and 11 success/fulfillment."},
        {"sl": "117", "event": "Child's Foreign Travel", "signifying": "5, 3, 9, 12", "prime": "9", "remarks": "5 child; 3 movement, 9 long-distance travel and 12 foreign connection."},
        {"sl": "118", "event": "Child's Foreign Settlement", "signifying": "5, 3, 9, 12", "prime": "12", "remarks": "5 child; 3/9 movement and long-distance travel; 12 foreign residence."},
        {"sl": "119", "event": "Child Custody", "signifying": "5, 7, 11", "prime": "5", "remarks": "5 represents child; 7 represents opposing/other party and 11 favorable fulfillment."},
        {"sl": "120", "event": "Child Custody Dispute", "signifying": "5, 6, 7, 11", "prime": "6", "remarks": "5 child, 6 dispute/litigation, 7 opposing party and 11 favorable result."},
        {"sl": "121", "event": "Child Support / Maintenance", "signifying": "2, 5, 11", "prime": "2", "remarks": "2 represents financial support; 5 child and 11 receipt/fulfillment."},
        {"sl": "122", "event": "Child Inheritance", "signifying": "2, 5, 8, 11", "prime": "8", "remarks": "5 child, 8 inheritance and 2/11 receipt of assets."},
        {"sl": "123", "event": "Second Pregnancy", "signifying": "2, 5, 11", "prime": "5", "remarks": "5 remains the principal progeny house; 2/11 support family expansion."},
        {"sl": "124", "event": "Fourth Child", "signifying": "2, 11, 11*", "prime": "11", "remarks": "Child numbering beyond the commonly used first-three-child grouping requires derived-house analysis rather than a universal single-house rule."},
        {"sl": "125", "event": "Engagement", "signifying": "2, 7, 11", "prime": "7", "remarks": "7 is the principal partnership/marriage house; 2 family formation and 11 fulfillment."},
        {"sl": "126", "event": "Engagement Ceremony", "signifying": "3, 7, 11", "prime": "7", "remarks": "3 communication/ceremony/documentation; 7 relationship and 11 fulfillment."},
        {"sl": "127", "event": "Engagement Confirmation", "signifying": "2, 7, 11", "prime": "7", "remarks": "7 partnership/marriage; 2 family formation and 11 realization."},
        {"sl": "128", "event": "Engagement Break", "signifying": "5, 6, 12", "prime": "7", "remarks": "7 relationship; 6/12 interruption or separation; 5 romance/relationship context."},
        {"sl": "129", "event": "Marriage Proposal", "signifying": "5, 7, 11", "prime": "7", "remarks": "5 romance, 7 partnership/marriage and 11 fulfillment."},
        {"sl": "130", "event": "Acceptance of Marriage Proposal", "signifying": "2, 7, 11", "prime": "7", "remarks": "7 marriage/partnership, 2 family formation and 11 fulfillment."},
        {"sl": "131", "event": "Government Job", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "10 profession/status, 6 service, 2 income and 11 gain. Government-specific judgment should additionally consider the relevant authority/status significators."},
        {"sl": "132", "event": "Government Employment", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "10 profession, 6 service, 2 earnings and 11 realization."},
        {"sl": "133", "event": "Government Promotion", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "10 career/status; 2 income, 6 service and 11 advancement/gain."},
        {"sl": "134", "event": "Government Transfer", "signifying": "3, 6, 10, 11", "prime": "3", "remarks": "3 movement/change, 6 service, 10 profession and 11 realization."},
        {"sl": "135", "event": "Government Appointment", "signifying": "2, 6, 10, 11", "prime": "10", "remarks": "10 appointment/career status; 2 income, 6 service and 11 fulfillment."},
        {"sl": "136", "event": "Government Contract", "signifying": "3, 6, 9, 10, 11", "prime": "10", "remarks": "3 documentation, 6 service/contractual matter, 9 formal/legal context, 10 professional authority and 11 completion."},
        {"sl": "137", "event": "Government Approval", "signifying": "3, 9, 11", "prime": "11", "remarks": "3 documentation/communication, 9 authority/legal process and 11 approval/fulfillment."},
        {"sl": "138", "event": "Government Permission / License", "signifying": "3, 9, 11", "prime": "9", "remarks": "3 documentation, 9 legal/official permission and 11 successful completion."},
        {"sl": "139", "event": "Government Benefit", "signifying": "2, 6, 11", "prime": "11", "remarks": "2 financial benefit, 6 service/government scheme context and 11 receipt."},
        {"sl": "140", "event": "Government Subsidy", "signifying": "2, 6, 11", "prime": "2", "remarks": "2 money/financial receipt, 6 service/scheme and 11 gain."},
        {"sl": "141", "event": "Government Pension", "signifying": "2, 6, 10, 11", "prime": "2", "remarks": "2 income, 6 service, 10 career/service record and 11 receipt."},
        {"sl": "142", "event": "Government Legal Notice", "signifying": "3, 6, 8, 9", "prime": "6", "remarks": "3 notice/documentation, 6 dispute, 8 complication and 9 legal/official process."},
        {"sl": "143", "event": "Government Case / Dispute", "signifying": "3, 6, 9, 11", "prime": "6", "remarks": "3 documentation, 6 dispute/litigation, 9 legal authority and 11 desired result."},
        {"sl": "144", "event": "Election", "signifying": "1, 5, 6, 10, 11", "prime": "10", "remarks": "1 self/candidate, 5 competition/creative public appeal, 6 opposition/competition, 10 status and 11 victory/result."},
        {"sl": "145", "event": "Winning Election", "signifying": "1, 6, 10, 11", "prime": "11", "remarks": "1 candidate, 6 competition/opponents, 10 public position and 11 victory/fulfillment."},
        {"sl": "146", "event": "Losing Election", "signifying": "5, 6, 8, 12", "prime": "6", "remarks": "6 competition/opposition; 8/12 indicate defeat, obstruction or loss."},
        {"sl": "147", "event": "Election Victory", "signifying": "1, 6, 10, 11", "prime": "11", "remarks": "Strong 1-6-10-11 connection supports victory and attainment of office."},
        {"sl": "148", "event": "Election Campaign", "signifying": "3, 5, 6, 10, 11", "prime": "10", "remarks": "3 communication/campaigning, 5 public appeal, 6 competition, 10 public position and 11 result."},
        {"sl": "149", "event": "Political Office", "signifying": "2, 6, 9, 10, 11", "prime": "10", "remarks": "10 authority/status, 6 public service, 9 ideology/principles, 2 income and 11 gains."},
        {"sl": "150", "event": "Becoming Minister / Public Authority", "signifying": "2, 6, 9, 10, 11", "prime": "10", "remarks": "10 is primary for status/position; 6 service, 9 principles/authority and 11 attainment."},
        {"sl": "151", "event": "Political Leadership", "signifying": "1, 5, 9, 10, 11", "prime": "10", "remarks": "1 self, 5 public influence/creative leadership, 9 ideology, 10 status and 11 recognition."},
        {"sl": "152", "event": "Political Party Appointment", "signifying": "3, 9, 10, 11", "prime": "10", "remarks": "3 communication, 9 organizational/ideological context, 10 position and 11 appointment."},
        {"sl": "153", "event": "Insurance Policy", "signifying": "2, 6, 8, 11", "prime": "8", "remarks": "8 represents insurance/risk protection; 2 financial assets, 6 service/contract and 11 benefit."},
        {"sl": "154", "event": "Obtaining Insurance", "signifying": "2, 6, 8, 11", "prime": "8", "remarks": "8 is the principal insurance house; 2/6 relate to financial/service arrangements and 11 completion."},
        {"sl": "155", "event": "Insurance Premium Payment", "signifying": "2, 6, 12", "prime": "6", "remarks": "2 money, 6 contractual/service obligation and 12 expenditure/outflow."},
        {"sl": "156", "event": "Life Insurance Claim", "signifying": "2, 8, 11", "prime": "8", "remarks": "8 insurance/claim settlement; 2 money/assets and 11 receipt."},
        {"sl": "157", "event": "Health Insurance Claim", "signifying": "6, 8, 11", "prime": "6", "remarks": "6 health/treatment, 8 insurance claim and 11 settlement."},
        {"sl": "158", "event": "Vehicle Insurance Claim", "signifying": "4, 8, 11", "prime": "8", "remarks": "4 vehicle/property, 8 insurance/claim and 11 settlement."},
        {"sl": "159", "event": "Property Insurance Claim", "signifying": "4, 8, 11", "prime": "8", "remarks": "4 property, 8 insurance and 11 receipt/settlement."},
        {"sl": "160", "event": "Insurance Claim Approval", "signifying": "8, 11", "prime": "11", "remarks": "8 claim/insurance and 11 approval/receipt."},
        {"sl": "161", "event": "Insurance Claim Rejection", "signifying": "6, 8, 12", "prime": "8", "remarks": "8 insurance claim; adverse 6/12 connections can indicate rejection, dispute or loss."},
        {"sl": "162", "event": "Insurance Settlement", "signifying": "2, 8, 11", "prime": "11", "remarks": "8 insurance, 2 money and 11 settlement/receipt."},
        {"sl": "163", "event": "Insurance Dispute", "signifying": "6, 8, 9, 12", "prime": "6", "remarks": "6 dispute, 8 insurance claim, 9 legal process and 12 loss/expense."},
        {"sl": "164", "event": "Insurance Maturity Benefit", "signifying": "2, 8, 11", "prime": "11", "remarks": "8 insurance policy, 2 financial receipt and 11 maturity/fulfillment."},
        {"sl": "165", "event": "Life Insurance Maturity", "signifying": "2, 8, 11", "prime": "11", "remarks": "8 insurance, 2 accumulated financial benefit and 11 receipt."},
        {"sl": "166", "event": "Child Insurance / Child Policy", "signifying": "2, 5, 8, 11", "prime": "5", "remarks": "5 child, 8 insurance, 2 money and 11 benefit."},
        {"sl": "167", "event": "Property Insurance", "signifying": "4, 8, 11", "prime": "8", "remarks": "4 property, 8 insurance/risk and 11 completion/benefit."},
        {"sl": "168", "event": "Vehicle Insurance", "signifying": "4, 8, 11", "prime": "8", "remarks": "4 vehicle, 8 insurance and 11 benefit/settlement."},
        {"sl": "169", "event": "Retirement Insurance / Annuity", "signifying": "2, 8, 10, 11", "prime": "2", "remarks": "2 financial income, 8 insurance, 10 career/retirement context and 11 receipt."},
        {"sl": "170", "event": "Receiving Insurance Money", "signifying": "2, 8, 11", "prime": "2", "remarks": "2 is primary for money received; 8 insurance and 11 gain/fulfillment."},
    ]
    return jsonify({
        "status": "success",
        "data": {
            "rasi_properties": rasi_properties,
            "parts_of_body": parts_of_body,
            "houses_events": houses_events
        }
    })
