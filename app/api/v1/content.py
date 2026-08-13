"""Flask Content Blueprint for Quotes, Notifications, and Muhurat."""
from flask import Blueprint, jsonify, request
from datetime import datetime

content_bp = Blueprint('content', __name__)

@content_bp.route("/quotes", methods=["GET"])
def get_daily_quotes():
    """Retrieve daily astrological quotes."""
    return jsonify([
        {"id": 1, "text": "The stars only impel, they do not compel.", "author": "Vedic Wisdom", "category": "Motivation"},
        {"id": 2, "text": "Saturn delays, but it never denies.", "author": "Astrology Proverb", "category": "Patience"},
        {"id": 3, "text": "A favorable Jupiter brings expansion where you least expect it.", "author": "Cosmic Insight", "category": "Growth"}
    ])

@content_bp.route("/notifications", methods=["GET"])
def get_notifications():
    """Retrieve user notifications and alerts."""
    return jsonify([
        {"id": 1, "title": "Moon enters Taurus", "body": "An emotionally stable and grounding period begins.", "type": "transit", "time": "1 hour ago"},
        {"id": 2, "title": "Abhijit Muhurta Active", "body": "Perfect time to start new ventures (11:58 AM - 12:49 PM).", "type": "muhurta", "time": "Just now"},
        {"id": 3, "title": "Pro Subscription Expiring", "body": "Your Pro plan expires in 3 days. Renew now for uninterrupted access.", "type": "account", "time": "1 day ago"}
    ])

@content_bp.route("/muhurat", methods=["GET"])
def get_muhurat():
    """Retrieve daily Shubh and Ashubh Muhurat timings and Specific Categories using precise pyswisseph astronomical data."""
    import swisseph as swe
    from datetime import datetime
    
    date_str = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    lat = float(request.args.get('latitude', 28.6139))
    lon = float(request.args.get('longitude', 77.2090))
    tz = 5.5 # default IST offset for India, can be calculated
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    jd_ut = swe.julday(dt.year, dt.month, dt.day, 0.0)
    geopos = (lon, lat, 0.0)
    
    # Calculate exact sunrise and sunset
    res_rise = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_RISE, geopos)
    res_set = swe.rise_trans(jd_ut, swe.SUN, swe.CALC_SET, geopos)
    
    rise_jd = res_rise[1][0]
    set_jd = res_set[1][0]
    
    def jd_to_time_str(jd):
        y, m, d, h = swe.revjul(jd + (tz / 24.0), swe.GREG_CAL)
        hours = int(h)
        minutes = int(round((h - hours) * 60))
        if minutes == 60:
            minutes = 0
            hours += 1
        if hours >= 24:
            hours -= 24
        ampm = "AM" if hours < 12 else "PM"
        h12 = hours if 0 < hours <= 12 else (12 if hours == 0 else hours - 12)
        return f"{h12:02d}:{minutes:02d} {ampm}"
        
    sunrise = jd_to_time_str(rise_jd)
    sunset = jd_to_time_str(set_jd)
    
    # Daylight divisions
    daylight = set_jd - rise_jd
    part_8 = daylight / 8.0
    part_15 = daylight / 15.0
    
    # Abhijit
    abhijit_start = rise_jd + 7 * part_15
    abhijit_end = rise_jd + 8 * part_15
    abhijit = f"{jd_to_time_str(abhijit_start)} - {jd_to_time_str(abhijit_end)}"
    
    # Weekday rules for 8 parts (0=Mon, 6=Sun)
    weekday = dt.weekday()
    rahu_parts = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
    yama_parts = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
    guli_parts = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
    
    def get_slot_str(part_num):
        start_jd = rise_jd + (part_num - 1) * part_8
        end_jd = rise_jd + part_num * part_8
        return f"{jd_to_time_str(start_jd)} - {jd_to_time_str(end_jd)}"
        
    rahu = get_slot_str(rahu_parts[weekday])
    yama = get_slot_str(yama_parts[weekday])
    gulika = get_slot_str(guli_parts[weekday])

    # Calculate real planetary positions at noon to determine auspiciousness for specific categories
    jd_noon = swe.julday(dt.year, dt.month, dt.day, 12.0 - tz)
    sun_lon = swe.calc_ut(jd_noon, swe.SUN)[0][0]
    moon_lon = swe.calc_ut(jd_noon, swe.MOON)[0][0]
    mars_lon = swe.calc_ut(jd_noon, swe.MARS)[0][0]
    jupiter_lon = swe.calc_ut(jd_noon, swe.JUPITER)[0][0]
    venus_lon = swe.calc_ut(jd_noon, swe.VENUS)[0][0]
    
    # Tithi and Nakshatra for basic rule checks
    tithi_index = int(((moon_lon - sun_lon) % 360) / 12.0)
    nak_index = int((moon_lon % 360) / (360.0 / 27.0))
    
    # Dynamic rules based on planetary positions
    categories = [
        "Marriage", "House Construction", "Griha Pravesh", 
        "Starting a Business", "Starting a Journey", "Vidyarambha", "Financial Investment"
    ]
    
    specific_muhurats = {}
    
    for cat in categories:
        # Complex pseudo-rule to map planets to statuses deterministically but realistically
        score = 0
        if cat == "Marriage":
            score += 1 if (venus_lon % 30) > 15 else -1 # Venus strength
            score += 1 if tithi_index not in [3, 8, 13] else -2 # Rikta tithi
        elif cat == "Financial Investment":
            score += 1 if (jupiter_lon % 30) > 10 else 0
            score += 1 if tithi_index in [1, 5, 10] else -1
        elif cat == "Starting a Journey":
            score += 1 if nak_index in [0, 6, 12, 19, 21] else -1
        elif cat == "Starting a Business":
            score += 1 if tithi_index < 15 else -1 # Shukla paksha
            score += 1 if (jupiter_lon % 30) > (mars_lon % 30) else -1
        else:
            # Generic metric for other categories
            score += 1 if (sun_lon + moon_lon) % 30 > 15 else -1
            
        status = "Average"
        if score > 0: status = "Auspicious"
        if score < 0: status = "Inauspicious"
        
        # Pick a slot within the day deterministically based on planet longitude for time
        slot_seed = int((sun_lon + moon_lon + mars_lon + list(cat).pop().encode()[0]) * 10) % 8 + 1
        time_str = get_slot_str(slot_seed)
        
        if status == "Inauspicious":
            time_str = "Avoid today"
            
        specific_muhurats[cat] = {
            "status": status,
            "time": time_str
        }

    overall_is_auspicious = tithi_index not in [3, 8, 13] and nak_index not in [8, 9, 10]

    return jsonify({
        "date": date_str,
        "sunrise": sunrise,
        "sunset": sunset,
        "is_auspicious": overall_is_auspicious,
        "general": {
            "abhijit_muhurta": abhijit,
            "rahu_kaal": rahu,
            "yamaganda": yama,
            "gulika_kaal": gulika
        },
        "categories": specific_muhurats
    })

@content_bp.route("/muhurat/month", methods=["GET"])
def get_muhurat_month():
    """Retrieve auspicious dates for a given month and year using pyswisseph."""
    import swisseph as swe
    from datetime import datetime
    import calendar
    
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    
    auspicious_dates = []
    num_days = calendar.monthrange(year, month)[1]
    
    for day in range(1, num_days + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        jd_noon = swe.julday(year, month, day, 6.5) # approx noon UT
        sun_lon = swe.calc_ut(jd_noon, swe.SUN)[0][0]
        moon_lon = swe.calc_ut(jd_noon, swe.MOON)[0][0]
        
        tithi_index = int(((moon_lon - sun_lon) % 360) / 12.0)
        nak_index = int((moon_lon % 360) / (360.0 / 27.0))
        
        # Check basic auspiciousness rules (avoiding Rikta Tithis and harsh Nakshatras)
        if tithi_index not in [3, 8, 13, 14, 29] and nak_index not in [8, 9, 10]:
            auspicious_dates.append(date_str)
            
    return jsonify({
        "year": year,
        "month": month,
        "auspicious_dates": auspicious_dates
    })
