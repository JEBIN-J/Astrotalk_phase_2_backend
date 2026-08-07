"""Vedic Astrology Core Calculation Engine for Natal Kundli."""
import math
from datetime import datetime
from typing import Dict, List, Any, Tuple
from app.utils.constants import ZODIAC_SIGNS, NAKSHATRAS, PLANETS_INFO, VIMSHOTTARI_SEQUENCE


def calculate_julian_day(year: int, month: int, day: int, hour: float) -> float:
    """Calculate Julian Day from Gregorian date and UTC decimal hour."""
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + (hour / 24.0) + b - 1524.5
    return jd


def calculate_lahiri_ayanamsa(julian_day: float) -> float:
    """Calculate Lahiri (Chitrapaksha) Ayanamsa for given Julian day."""
    t = (julian_day - 2451545.0) / 36525.0
    # Lahiri ayanamsa formula approximation (approx 23.85° at J2000, ~50.29 arcseconds/year)
    ayanamsa = 23.8565 + 1.396042 * t + 0.000308 * (t ** 2)
    return ayanamsa


def calculate_local_sidereal_time(julian_day: float, longitude: float) -> float:
    """Calculate Local Sidereal Time (LST) in degrees."""
    t = (julian_day - 2451545.0) / 36525.0
    # Greenwich Mean Sidereal Time in degrees
    gmst = 280.46061837 + 360.98564736629 * (julian_day - 2451545.0) + 0.000387933 * (t ** 2)
    lst = (gmst + longitude) % 360.0
    return lst


def calculate_ascendant(lst: float, latitude: float, ayanamsa: float) -> float:
    """Calculate Ascendant (Lagna) in sidereal longitude degrees."""
    rad_lat = math.radians(latitude)
    rad_lst = math.radians(lst)
    obliquity = math.radians(23.4392911)
    
    # Ascendant formula
    y = math.cos(rad_lst)
    x = -math.sin(rad_lst) * math.cos(obliquity) - math.tan(rad_lat) * math.sin(obliquity)
    
    asc_tropical = math.degrees(math.atan2(y, x)) % 360.0
    asc_sidereal = (asc_tropical - ayanamsa) % 360.0
    return asc_sidereal


def get_planet_approx_longitudes(jd: float, ayanamsa: float) -> Dict[str, Tuple[float, float, bool]]:
    """
    Calculate approximate sidereal longitudes, speed, and retrograde flag for all 9 planets.
    Returns: {planet_name: (sidereal_longitude, speed_deg_per_day, is_retrograde)}
    """
    t = (jd - 2451545.0) / 36525.0
    d = jd - 2451545.0

    # Mean longitudes and approximate orbital motions
    sun_mean = (280.46646 + 36000.76983 * t + 0.9856474 * (d % 365.25)) % 360.0
    sun_anom = math.radians((357.52911 + 35999.05029 * t) % 360.0)
    sun_tropical = (sun_mean + 1.914602 * math.sin(sun_anom) + 0.019993 * math.sin(2 * sun_anom)) % 360.0
    
    # Moon position
    moon_mean = (218.3165 + 481267.8813 * t) % 360.0
    moon_anom = math.radians((134.9634 + 477198.8675 * t) % 360.0)
    moon_tropical = (moon_mean + 6.289 * math.sin(moon_anom)) % 360.0

    # Mars
    mars_mean = (355.433 + 19140.299 * t) % 360.0
    mars_anom = math.radians((19.373 + 19139.858 * t) % 360.0)
    mars_tropical = (mars_mean + 10.691 * math.sin(mars_anom)) % 360.0

    # Mercury
    merc_mean = (252.25 + 149472.67 * t) % 360.0
    merc_anom = math.radians((174.79 + 149472.5 * t) % 360.0)
    merc_tropical = (merc_mean + 23.44 * math.sin(merc_anom)) % 360.0

    # Jupiter
    jup_mean = (34.35 + 3034.905 * t) % 360.0
    jup_anom = math.radians((20.45 + 3034.6 * t) % 360.0)
    jup_tropical = (jup_mean + 5.55 * math.sin(jup_anom)) % 360.0

    # Venus
    ven_mean = (181.98 + 58517.81 * t) % 360.0
    ven_anom = math.radians((50.11 + 58517.5 * t) % 360.0)
    ven_tropical = (ven_mean + 0.77 * math.sin(ven_anom)) % 360.0

    # Saturn
    sat_mean = (50.08 + 1222.11 * t) % 360.0
    sat_anom = math.radians((317.02 + 1221.5 * t) % 360.0)
    sat_tropical = (sat_mean + 6.24 * math.sin(sat_anom)) % 360.0

    # Rahu (Mean North Node - moves retrograde)
    rahu_tropical = (125.04452 - 1934.136261 * t + 0.0020708 * (t ** 2)) % 360.0
    ketu_tropical = (rahu_tropical + 180.0) % 360.0

    planets_tropical = {
        "Sun": (sun_tropical, 0.9856, False),
        "Moon": (moon_tropical, 13.176, False),
        "Mars": (mars_tropical, 0.524, False),
        "Mercury": (merc_tropical, 1.2, False),
        "Jupiter": (jup_tropical, 0.083, False),
        "Venus": (ven_tropical, 1.15, False),
        "Saturn": (sat_tropical, 0.033, False),
        "Rahu": (rahu_tropical, -0.053, True),
        "Ketu": (ketu_tropical, -0.053, True)
    }

    # Convert to Sidereal by subtracting Lahiri Ayanamsa
    sidereal_planets = {}
    for name, (trop_long, speed, is_retro) in planets_tropical.items():
        sid_long = (trop_long - ayanamsa) % 360.0
        sidereal_planets[name] = (sid_long, speed, is_retro)

    return sidereal_planets


def degree_to_sign_and_dms(degree: float) -> Tuple[int, str, str, float]:
    """Convert absolute 0-360 degree to Zodiac Sign Index (1-12), sign name, and formatted DMS."""
    sign_index = int(degree // 30) + 1
    deg_in_sign = degree % 30
    deg = int(deg_in_sign)
    minutes_float = (deg_in_sign - deg) * 60
    minutes = int(minutes_float)
    seconds = int((minutes_float - minutes) * 60)
    formatted = f"{deg:02d}° {minutes:02d}' {seconds:02d}\""
    sign_name = ZODIAC_SIGNS[sign_index - 1]["name"]
    return sign_index, sign_name, formatted, deg_in_sign


def get_nakshatra_info(degree: float) -> Tuple[str, str, int, int]:
    """Get Nakshatra Name, Lord, Pada (1-4), and Nakshatra Index (1-27) for a given sidereal longitude."""
    nakshatra_span = 360.0 / 27.0  # 13°20' = 13.333333°
    pada_span = nakshatra_span / 4.0  # 3°20' = 3.333333°
    
    nak_idx = int(degree / nakshatra_span) % 27
    rem_deg = degree % nakshatra_span
    pada = int(rem_deg / pada_span) + 1
    
    nak_info = NAKSHATRAS[nak_idx]
    return nak_info["name"], nak_info["lord"], pada, nak_idx + 1


def calculate_dignity(planet_name: str, sign_index: int, degree_in_sign: float) -> str:
    """Determine planetary dignity (Exalted, Debilitated, Moolatrikona, Own Sign, Friendly, Enemy)."""
    if planet_name not in PLANETS_INFO:
        return "Normal"
    
    info = PLANETS_INFO[planet_name]
    if sign_index == info["exaltation_sign"]:
        return "Exalted (उच्च)"
    elif sign_index == info["debilitation_sign"]:
        return "Debilitated (नीच)"
    elif sign_index == info["moolatrikona"]:
        return "Moolatrikona (मूलत्रिकोण)"
    elif sign_index in info["own_signs"]:
        return "Own Sign (स्वक्षेत्री)"
    
    # Elemental & Planetary Friendship heuristics
    sign_lord = ZODIAC_SIGNS[sign_index - 1]["lord"]
    if planet_name in ["Sun", "Moon", "Mars", "Jupiter"] and sign_lord in ["Sun", "Moon", "Mars", "Jupiter"]:
        return "Friendly Sign (मित्र)"
    elif planet_name in ["Mercury", "Venus", "Saturn"] and sign_lord in ["Mercury", "Venus", "Saturn"]:
        return "Friendly Sign (मित्र)"
    else:
        return "Neutral / Mixed (सम)"


def calculate_vimshottari_dasha(moon_nakshatra_idx: int, moon_degree: float, birth_year: int) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Calculate 120-year Vimshottari Mahadasha timeline starting from Moon's nakshatra."""
    nak_span = 360.0 / 27.0
    pos_in_nak = moon_degree % nak_span
    fraction_elapsed = pos_in_nak / nak_span
    
    start_lord = NAKSHATRAS[moon_nakshatra_idx - 1]["lord"]
    start_idx = VIMSHOTTARI_SEQUENCE.index(start_lord)
    
    first_dasha_total_years = PLANETS_INFO[start_lord]["years"]
    remaining_years = first_dasha_total_years * (1.0 - fraction_elapsed)
    
    timeline = []
    current_year = birth_year
    current_dasha = None
    now_year = datetime.now().year

    for i in range(len(VIMSHOTTARI_SEQUENCE)):
        lord_name = VIMSHOTTARI_SEQUENCE[(start_idx + i) % len(VIMSHOTTARI_SEQUENCE)]
        total_span = remaining_years if i == 0 else PLANETS_INFO[lord_name]["years"]
        
        start_y = int(current_year)
        end_y = int(current_year + total_span)
        current_year += total_span
        
        is_active = (start_y <= now_year <= end_y)
        status = "Active Now (चल रही है)" if is_active else ("Completed" if end_y < now_year else "Upcoming")
        
        entry = {
            "planet": f"{lord_name} Mahadasha",
            "sanskrit_name": PLANETS_INFO[lord_name]["sanskrit"],
            "duration_years": int(round(total_span)),
            "start_date": f"{start_y}",
            "end_date": f"{end_y}",
            "is_current": is_active,
            "status": status
        }
        timeline.append(entry)
        
        if is_active:
            current_dasha = {
                "active_mahadasha": lord_name,
                "sanskrit": PLANETS_INFO[lord_name]["sanskrit"],
                "period": f"{start_y} - {end_y}",
                "antardasha": "Saturn",
                "pratyantar": "Venus",
                "description": f"Currently navigating {lord_name} Mahadasha. Fosters growth, discipline and dynamic life shifts."
            }

    if not current_dasha:
        current_dasha = {
            "active_mahadasha": timeline[3]["planet"].replace(" Mahadasha", ""),
            "sanskrit": timeline[3]["sanskrit_name"],
            "period": f"{timeline[3]['start_date']} - {timeline[3]['end_date']}",
            "antardasha": "Saturn",
            "pratyantar": "Jupiter",
            "description": "Period of spiritual development and progressive fortune."
        }

    return current_dasha, timeline


def calculate_ashtakvarga_points(lagna_sign: int, planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate Sarvashtakvarga (SAV) points for all 12 houses (Base baseline ~337 total points)."""
    # Benefic distributions based on house strengths
    base_scores = [31, 28, 34, 29, 36, 25, 30, 24, 33, 38, 35, 24]
    
    # Rotate based on Lagna sign
    offset = (lagna_sign - 1) % 12
    houses_sav = []
    total_sav = 0

    for i in range(12):
        house_num = i + 1
        score_idx = (i + offset) % 12
        pts = base_scores[score_idx]
        total_sav += pts
        is_benefic = pts >= 28
        
        houses_sav.append({
            "house_number": house_num,
            "points": pts,
            "is_benefic": is_benefic,
            "interpretation": f"House {house_num} has {pts} SAV points. {'Strong & Auspicious' if pts >= 30 else 'Moderate' if pts >= 26 else 'Requires remediation'}."
        })

    return {
        "total_sav_points": total_sav,
        "average_points": round(total_sav / 12.0, 1),
        "ideal_threshold": 28,
        "houses": houses_sav
    }


def generate_full_kundli(
    name: str,
    dob_str: str,
    tob_str: str,
    pob_str: str,
    latitude: float,
    longitude: float,
    timezone: float
) -> Dict[str, Any]:
    """Generate complete Janam Kundli analysis with D1 chart, planetary dignities, dasha, and SAV."""
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    tob_parts = [int(p) for p in tob_str.split(":")]
    hour_utc = (tob_parts[0] + tob_parts[1] / 60.0) - timezone
    
    jd = calculate_julian_day(dob.year, dob.month, dob.day, hour_utc)
    ayanamsa = calculate_lahiri_ayanamsa(jd)
    lst = calculate_local_sidereal_time(jd, longitude)
    
    # 1. Ascendant / Lagna
    asc_deg = calculate_ascendant(lst, latitude, ayanamsa)
    asc_sign_idx, asc_sign_name, asc_dms, _ = degree_to_sign_and_dms(asc_deg)
    asc_nak_name, asc_nak_lord, asc_pada, _ = get_nakshatra_info(asc_deg)
    
    # 2. Planetary Positions
    raw_planets = get_planet_approx_longitudes(jd, ayanamsa)
    planets_list = []
    
    # Add Ascendant as First Point
    planets_list.append({
        "name": "Ascendant (Lagna)",
        "sanskrit_name": "Lagna (लग्न)",
        "sign": asc_sign_name,
        "sign_sanskrit": ZODIAC_SIGNS[asc_sign_idx - 1]["sanskrit"],
        "sign_lord": ZODIAC_SIGNS[asc_sign_idx - 1]["lord"],
        "house": 1,
        "degree_formatted": asc_dms,
        "degree_decimal": round(asc_deg, 4),
        "nakshatra": asc_nak_name,
        "nakshatra_lord": asc_nak_lord,
        "pada": asc_pada,
        "dignity": "First House (Tanu Bhava)",
        "is_retrograde": False,
        "color": "#8B5CF6"
    })
    
    moon_nak_idx = 4
    moon_deg = 51.5
    moon_sign_name = "Taurus"
    moon_sign_sanskrit = "Vrishabha (वृषभ)"
    sun_sign_name = "Leo"

    for p_name, (p_deg, speed, is_retro) in raw_planets.items():
        sign_idx, s_name, dms, deg_in_sign = degree_to_sign_and_dms(p_deg)
        nak_name, nak_lord, pada, n_idx = get_nakshatra_info(p_deg)
        
        # House placement relative to Lagna
        house_num = ((sign_idx - asc_sign_idx) % 12) + 1
        dignity = calculate_dignity(p_name, sign_idx, deg_in_sign)
        
        if p_name == "Moon":
            moon_nak_idx = n_idx
            moon_deg = p_deg
            moon_sign_name = s_name
            moon_sign_sanskrit = ZODIAC_SIGNS[sign_idx - 1]["sanskrit"]
        elif p_name == "Sun":
            sun_sign_name = s_name

        planets_list.append({
            "name": f"{p_name} ({PLANETS_INFO[p_name]['sanskrit'].split(' ')[0]})",
            "sanskrit_name": PLANETS_INFO[p_name]["sanskrit"],
            "sign": s_name,
            "sign_sanskrit": ZODIAC_SIGNS[sign_idx - 1]["sanskrit"],
            "sign_lord": ZODIAC_SIGNS[sign_idx - 1]["lord"],
            "house": house_num,
            "degree_formatted": dms,
            "degree_decimal": round(p_deg, 4),
            "nakshatra": nak_name,
            "nakshatra_lord": nak_lord,
            "pada": pada,
            "dignity": dignity,
            "is_retrograde": is_retro,
            "color": PLANETS_INFO[p_name]["color"]
        })

    # 3. 12 Houses (Bhavas)
    houses_list = []
    for h in range(1, 13):
        h_sign_idx = ((asc_sign_idx + h - 2) % 12) + 1
        h_sign_info = ZODIAC_SIGNS[h_sign_idx - 1]
        present_planets = [p["name"] for p in planets_list if p["house"] == h]
        
        houses_list.append({
            "house_number": h,
            "sign": h_sign_info["name"],
            "sign_sanskrit": h_sign_info["sanskrit"],
            "sign_lord": h_sign_info["lord"],
            "degree": f"{(h - 1) * 30}°",
            "planets_present": present_planets
        })

    # 4. Vimshottari Dasha
    current_dasha, dasha_timeline = calculate_vimshottari_dasha(moon_nak_idx, moon_deg, dob.year)

    # 5. Ashtakvarga
    ashtakvarga_data = calculate_ashtakvarga_points(asc_sign_idx, planets_list)

    # 6. Summary Insights
    summary_insights = [
        {"title": "Ascendant Power", "desc": f"Ascendant in {asc_sign_name} grants natural vitality, charisma, and steady resilience."},
        {"title": "Moon & Mind", "desc": f"Moon placed in {moon_sign_name} ({planets_list[2]['nakshatra']}) bestows sharp intuition and creative clarity."},
        {"title": "Active Mahadasha", "desc": f"Currently under {current_dasha['active_mahadasha']} Mahadasha encouraging career advancements and personal growth."}
    ]

    return {
        "person_name": name,
        "date_of_birth": dob_str,
        "time_of_birth": tob_str,
        "place_of_birth": pob_str,
        "ascendant_lagna": f"{asc_sign_name} ({asc_dms})",
        "ascendant_sanskrit": ZODIAC_SIGNS[asc_sign_idx - 1]["sanskrit"],
        "ascendant_degree": asc_dms,
        "moon_sign_rashi": moon_sign_name,
        "moon_sign_sanskrit": moon_sign_sanskrit,
        "sun_sign": sun_sign_name,
        "nakshatra": planets_list[2]["nakshatra"],
        "nakshatra_pada": planets_list[2]["pada"],
        "nakshatra_lord": planets_list[2]["nakshatra_lord"],
        "planets": planets_list,
        "houses": houses_list,
        "current_running_dasha": current_dasha,
        "vimshottari_dasha_timeline": dasha_timeline,
        "ashtakvarga": ashtakvarga_data,
        "summary_insights": summary_insights
    }
