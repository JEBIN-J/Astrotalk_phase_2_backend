from flask import Blueprint, request, jsonify
from datetime import datetime
from app.api.v1.horoscope import remove_hindi_text
from app.services.vedic_engine import generate_full_kundli, calculate_advanced_dasha
from app.services.kalachakra_engine import calculate_kalachakra_dasha
from app.services.jaimini_engine import generate_jaimini_chart

prashna_bp = Blueprint('prashna_api', __name__, url_prefix='/api/v1/prashna')

def find_current_dasha(timeline, target_date):
    """Find the active dasha from a timeline."""
    for md in timeline:
        # Check both key conventions
        md_start_str = md.get("start_date") or md.get("start")
        md_end_str = md.get("end_date") or md.get("end")
        md_lord = md.get("lord") or md.get("planet")
        
        # Determine format
        fmt = "%Y-%m-%d" if "-" in md_start_str else "%d %b %Y"
        
        start_dt = datetime.strptime(md_start_str, fmt)
        end_dt = datetime.strptime(md_end_str, fmt)
        
        if start_dt <= target_date <= end_dt:
            active_ad = md_lord
            if "antardashas" in md:
                for ad in md["antardashas"]:
                    ad_start_str = ad.get("start_date") or ad.get("start")
                    ad_end_str = ad.get("end_date") or ad.get("end")
                    ad_lord = ad.get("lord") or ad.get("planet")
                    
                    ad_fmt = "%Y-%m-%d" if "-" in ad_start_str else "%d %b %Y"
                    ad_start_dt = datetime.strptime(ad_start_str, ad_fmt)
                    ad_end_dt = datetime.strptime(ad_end_str, ad_fmt)
                    
                    if ad_start_dt <= target_date <= ad_end_dt:
                        active_ad = ad_lord
                        break
            return {"mahadasha": md_lord, "antardasha": active_ad}
    return {}

@prashna_bp.route("/chart", methods=["POST"])
def get_prashna_chart():
    """Generate complete Prashna Module with 6 independent sections."""
    req_data = request.json or {}
    
    # 1. Parse Prashna Inputs
    q_date = req_data.get("question_date")
    q_time = req_data.get("question_time")
    
    # Fallback to current time if not explicitly provided
    if not q_date or not q_time:
        now = datetime.now()
        q_date = now.strftime("%Y-%m-%d")
        q_time = now.strftime("%H:%M:%S")
        
    pob = req_data.get("place", "Unknown")
    lat = float(req_data.get("latitude", 28.6139))
    lon = float(req_data.get("longitude", 77.2090))
    tz = float(req_data.get("timezone", 5.5))
    days_in_year = float(req_data.get("days_in_year", 365.256364))
    
    # Base Chart Calculation
    # We pass the Prashna date/time as the "birth" parameters
    base_chart = generate_full_kundli(
        name="Prashna",
        dob_str=q_date,
        tob_str=q_time,
        pob_str=pob,
        latitude=lat,
        longitude=lon,
        timezone=tz,
        days_in_year=days_in_year
    )
    
    # Extract Moon Details
    moon_planet = next((p for p in base_chart["planets"] if p["planet_name_simple"] == "Moon"), None)
    if not moon_planet:
        return jsonify({"error": "Failed to calculate Moon"}), 500
        
    moon_deg = moon_planet["degree_decimal"]
    
    # Calculate Ashtottari Applicability
    # Standard Parashari Rule: Rahu in Kendra/Trikona from Lagna Lord
    ashtottari_applicable = True
    ashtottari_reason = "Ashtottari conditionally applicable based on Parashari rules."
    
    # Section 1: Vimshottari
    vimshottari = base_chart.get("vimshottari_full_payload", {
        "current": base_chart.get("current_running_dasha"),
        "timeline": base_chart.get("vimshottari_dasha_timeline")
    })
    
    # Section 2: Yogini
    dob_dt = datetime.strptime(q_date, "%Y-%m-%d")
    # We can get index by (moon_deg / 13.3333) + 1
    nak_idx = int(moon_deg / (360.0 / 27.0)) + 1
    
    yogini_timeline = calculate_advanced_dasha(
        dasha_type="Yogini Dasha", 
        moon_nak_idx=nak_idx, 
        moon_deg=moon_deg, 
        birth_date=dob_dt, 
        planets_list=base_chart["planets"],
        days_in_year=days_in_year
    )
    
    yogini = {
        "current": find_current_dasha(yogini_timeline, dob_dt),
        "timeline": yogini_timeline
    }
    
    # Section 3: Kala Chakra
    kala_chakra = calculate_kalachakra_dasha(moon_deg, dob_dt, days_in_year=days_in_year)
    
    # Section 4: Ashtottari
    ashtottari_timeline = calculate_advanced_dasha(
        dasha_type="Ashtottari Dasha (Method 1)", 
        moon_nak_idx=nak_idx, 
        moon_deg=moon_deg, 
        birth_date=dob_dt, 
        planets_list=base_chart["planets"],
        days_in_year=days_in_year
    )
    
    ashtottari = {
        "applicable": ashtottari_applicable,
        "reason": ashtottari_reason,
        "current": find_current_dasha(ashtottari_timeline, dob_dt),
        "timeline": ashtottari_timeline
    }
    
    # Section 5: Chara Dasha
    # Use existing Jaimini engine
    jaimini_data = generate_jaimini_chart(
        name="Prashna",
        dob_str=q_date,
        tob_str=q_time,
        pob_str=pob,
        latitude=lat,
        longitude=lon,
        timezone=tz
    )
    
    chara = {
        "current": jaimini_data.get("chara_dasha_current", {}),
        "timeline": jaimini_data.get("chara_dasha_timeline", [])
    }
    
    # Section 6: Navamsa (D9)
    # Extract D9 from divisional_charts
    divisional_charts = base_chart.get("divisional_charts", {})
    if isinstance(divisional_charts, dict):
        d9_data = divisional_charts.get("D-9")
    else:
        d9_data = next((c for c in divisional_charts if c.get("id") == "D-9"), None)
    
    d9_planet_positions = []
    for p in base_chart["planets"]:
        d1_sign = p["sign"]
        d9_sign = p.get("navamsha", "")
        # D9 sign in the API is typically a dict if from get_navamsha, let's extract string if needed
        d9_sign_str = d9_sign if isinstance(d9_sign, str) else (d9_sign.get("sign") if isinstance(d9_sign, dict) else str(d9_sign))
        is_var = (d1_sign == d9_sign_str)
        d9_planet_positions.append({
            "planet": p["planet_name_simple"],
            "d1_sign": d1_sign,
            "d9_sign": d9_sign_str,
            "vargottama": is_var
        })
        
    navamsa = {
        "chart": d9_data,
        "d9_planet_positions": d9_planet_positions,
        "karakas": jaimini_data.get("karakas", [])
    }
    
    # Overview & Common Planetary Data
    utc_hr_str = f"{int(base_chart.get('utc_hour', 0)):02d}:{int((base_chart.get('utc_hour', 0) % 1) * 60):02d} UTC"
    
    overview = {
        "question_date": q_date,
        "question_time": q_time,
        "place": pob,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "utc_time": utc_hr_str,
        "julian_day": round(base_chart.get("julian_day", 0), 4),
        "ayanamsa": base_chart["ayanamsa_formatted"],
        "prashna_lagna": base_chart["ascendant_sign"],
        "lagna_degree": base_chart["ascendant_degree_formatted"],
        "moon_sign": base_chart["moon_sign_rashi"],
        "moon_degree": moon_planet["degree_formatted"],
        "moon_nakshatra": moon_planet["nakshatra"],
        "moon_pada": moon_planet["pada"]
    }
    
    resp = {
        "overview": overview,
        "planets": base_chart["planets"],
        "vimshottari": vimshottari,
        "yogini": yogini,
        "kala_chakra": kala_chakra,
        "ashtottari": ashtottari,
        "chara": chara,
        "navamsa": navamsa
    }
    
    return jsonify(remove_hindi_text(resp))
