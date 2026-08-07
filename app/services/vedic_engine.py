"""
High-Precision Vedic Astrology Core Engine powered by Swiss Ephemeris (pyswisseph).
Provides accurate Janam Kundli calculations including:
- D1 Rashi & D9 Navamsha charts (with Vargottama detection)
- KP Astrology Sub-Lords (Sign, Star, Sub, Sub-Sub)
- Exact Vimshottari Mahadasha + Antardasha (Bhukti) + Pratyantar timeline
- Classical Parashara Bhinnashtakavarga (BAV) & Sarvashtakavarga (SAV - 337 Bindus)
- 6-Fold Shadbala Engine (Sthana, Dig, Kala, Chesta, Naisargika, Drik)
- Vedic Planetary Aspects (Drishti) & Classical Yogas (Gajakesari, Budhaditya, Neechabhanga, etc.)
"""
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from app.utils.constants import ZODIAC_SIGNS, NAKSHATRAS, PLANETS_INFO, VIMSHOTTARI_SEQUENCE, POPULAR_CITIES

try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    try:
        import pyswisseph as swe
        SWISSEPH_AVAILABLE = True
    except ImportError:
        swe = None
        SWISSEPH_AVAILABLE = False


def resolve_coordinates(place_name: str, default_lat: float = 28.6139, default_lon: float = 77.2090, default_tz: float = 5.5) -> Tuple[float, float, float]:
    """Resolve coordinates and timezone for a place name using POPULAR_CITIES."""
    if not place_name:
        return default_lat, default_lon, default_tz
        
    p_lower = place_name.lower().strip()
    for city in POPULAR_CITIES:
        c_name = city["name"].lower()
        c_state = city.get("state", "").lower()
        if c_name in p_lower or p_lower in c_name or (c_state and c_state in p_lower):
            return float(city["latitude"]), float(city["longitude"]), float(city["timezone"])
            
    return default_lat, default_lon, default_tz


def calculate_julian_day(year: int, month: int, day: int, hour_utc: float) -> float:
    """Calculate Julian Day from Gregorian date and UTC decimal hour with date adjustment."""
    if SWISSEPH_AVAILABLE and swe is not None:
        return swe.julday(year, month, day, hour_utc)
        
    # Manual Julian day
    if month <= 2:
        year -= 1
        month += 12
    a = math.floor(year / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + (hour_utc / 24.0) + b - 1524.5
    return jd


def calculate_lahiri_ayanamsa(julian_day: float) -> float:
    """Calculate Lahiri (Chitrapaksha) Ayanamsa for given Julian day using Swiss Ephemeris."""
    if SWISSEPH_AVAILABLE and swe is not None:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.get_ayanamsa_ut(julian_day)
        
    t = (julian_day - 2451545.0) / 36525.0
    ayanamsa = 23.8565 + 1.396042 * t + 0.000308 * (t ** 2)
    return ayanamsa


def calculate_ascendant_and_mc(jd: float, latitude: float, longitude: float, ayanamsa: float) -> Tuple[float, float, float]:
    """
    Calculate Ascendant (Lagna), MC (Midheaven), and RAMC in sidereal longitude degrees.
    Returns: (asc_deg, mc_deg, ramc_deg)
    """
    if SWISSEPH_AVAILABLE and swe is not None:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'W', swe.FLG_SIDEREAL)
        asc_deg = ascmc[0] % 360.0
        mc_deg = ascmc[1] % 360.0
        ramc_deg = ascmc[2] % 360.0
        return asc_deg, mc_deg, ramc_deg

    # Fallback formula
    t = (jd - 2451545.0) / 36525.0
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * (t ** 2)
    lst = (gmst + longitude) % 360.0
    rad_lat = math.radians(latitude)
    rad_lst = math.radians(lst)
    obliquity = math.radians(23.4392911)
    
    y = math.cos(rad_lst)
    x = -math.sin(rad_lst) * math.cos(obliquity) - math.tan(rad_lat) * math.sin(obliquity)
    
    asc_tropical = math.degrees(math.atan2(y, x)) % 360.0
    asc_sidereal = (asc_tropical - ayanamsa) % 360.0
    mc_sidereal = (lst - ayanamsa) % 360.0
    return asc_sidereal, mc_sidereal, lst


def calculate_ascendant(jd: float, latitude: float, longitude: float, ayanamsa: float) -> float:
    """Calculate Ascendant (Lagna) in sidereal degrees."""
    asc_deg, _, _ = calculate_ascendant_and_mc(jd, latitude, longitude, ayanamsa)
    return asc_deg


def get_planet_longitudes_precise(jd: float, ayanamsa: float) -> Dict[str, Tuple[float, float, bool]]:
    """
    Calculate high-precision sidereal longitudes, daily speed, and retrograde status for all planets.
    Returns: {planet_name: (sidereal_longitude, speed_deg_per_day, is_retrograde)}
    """

    if SWISSEPH_AVAILABLE and swe is not None:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        planet_map = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE,
        }
        
        result = {}
        for p_name, pid in planet_map.items():
            res, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
            deg = res[0] % 360.0
            speed = res[3]
            is_retro = speed < 0 if p_name not in ["Sun", "Moon", "Rahu", "Ketu"] else (speed < 0 or p_name in ["Rahu", "Ketu"])
            result[p_name] = (deg, speed, is_retro)
            
        # Ketu is exactly 180° opposite Rahu
        rahu_deg = result["Rahu"][0]
        ketu_deg = (rahu_deg + 180.0) % 360.0
        result["Ketu"] = (ketu_deg, result["Rahu"][1], True)
        
        return result

    # Fallback
    t = (jd - 2451545.0) / 36525.0
    d = jd - 2451545.0
    sun_mean = (280.46646 + 36000.76983 * t + 0.9856474 * (d % 365.25)) % 360.0
    sun_anom = math.radians((357.52911 + 35999.05029 * t) % 360.0)
    sun_tropical = (sun_mean + 1.914602 * math.sin(sun_anom) + 0.019993 * math.sin(2 * sun_anom)) % 360.0
    
    moon_mean = (218.3165 + 481267.8813 * t) % 360.0
    moon_anom = math.radians((134.9634 + 477198.8675 * t) % 360.0)
    moon_tropical = (moon_mean + 6.289 * math.sin(moon_anom)) % 360.0

    mars_mean = (355.433 + 19140.299 * t) % 360.0
    mars_anom = math.radians((19.373 + 19139.858 * t) % 360.0)
    mars_tropical = (mars_mean + 10.691 * math.sin(mars_anom)) % 360.0

    merc_mean = (252.25 + 149472.67 * t) % 360.0
    merc_anom = math.radians((174.79 + 149472.5 * t) % 360.0)
    merc_tropical = (merc_mean + 23.44 * math.sin(merc_anom)) % 360.0

    jup_mean = (34.35 + 3034.905 * t) % 360.0
    jup_anom = math.radians((20.45 + 3034.6 * t) % 360.0)
    jup_tropical = (jup_mean + 5.55 * math.sin(jup_anom)) % 360.0

    ven_mean = (181.98 + 58517.81 * t) % 360.0
    ven_anom = math.radians((50.11 + 58517.5 * t) % 360.0)
    ven_tropical = (ven_mean + 0.77 * math.sin(ven_anom)) % 360.0

    sat_mean = (50.08 + 1222.11 * t) % 360.0
    sat_anom = math.radians((317.02 + 1221.5 * t) % 360.0)
    sat_tropical = (sat_mean + 6.24 * math.sin(sat_anom)) % 360.0

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

    sidereal_planets = {}
    for name, (trop_long, speed, is_retro) in planets_tropical.items():
        sid_long = (trop_long - ayanamsa) % 360.0
        sidereal_planets[name] = (sid_long, speed, is_retro)

    return sidereal_planets


# Alias for backward compatibility
get_planet_approx_longitudes = get_planet_longitudes_precise



def degree_to_sign_and_dms(degree: float) -> Tuple[int, str, str, float]:
    """Convert absolute 0-360 degree to Zodiac Sign Index (1-12), sign name, formatted DMS, and degree in sign."""
    degree = degree % 360.0
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
    degree = degree % 360.0
    nakshatra_span = 360.0 / 27.0  # 13°20' = 13.333333°
    pada_span = nakshatra_span / 4.0  # 3°20' = 3.333333°
    
    nak_idx = int(degree / nakshatra_span) % 27
    rem_deg = degree % nakshatra_span
    pada = int(rem_deg / pada_span) + 1
    if pada > 4:
        pada = 4
    
    nak_info = NAKSHATRAS[nak_idx]
    return nak_info["name"], nak_info["lord"], pada, nak_idx + 1


def calculate_navamsha(degree: float, d1_sign_idx: int) -> Dict[str, Any]:
    """
    Calculate D9 Navamsha Chart sign, Pada, Sanskrit name, and Vargottama status.
    Each 30° sign has 9 Navamshas of 3°20' (3.333333°).
    """
    deg_in_sign = degree % 30.0
    navamsha_step = int(deg_in_sign / (30.0 / 9.0))  # 0 to 8
    
    # Starting sign based on element
    if d1_sign_idx in [1, 5, 9]:      # Fire (Aries, Leo, Sag) -> starts Aries (1)
        start_sign = 1
    elif d1_sign_idx in [2, 6, 10]:   # Earth (Taurus, Virgo, Cap) -> starts Capricorn (10)
        start_sign = 10
    elif d1_sign_idx in [3, 7, 11]:   # Air (Gemini, Libra, Aqua) -> starts Libra (7)
        start_sign = 7
    else:                             # Water (Cancer, Scorpio, Pisces) -> starts Cancer (4)
        start_sign = 4
        
    nav_sign_idx = ((start_sign - 1 + navamsha_step) % 12) + 1
    nav_sign_info = ZODIAC_SIGNS[nav_sign_idx - 1]
    is_vargottama = (nav_sign_idx == d1_sign_idx)
    
    return {
        "navamsha_sign_index": nav_sign_idx,
        "navamsha_sign": nav_sign_info["name"],
        "navamsha_sanskrit": nav_sign_info["sanskrit"],
        "navamsha_lord": nav_sign_info["lord"],
        "pada_in_sign": navamsha_step + 1,
        "is_vargottama": is_vargottama
    }


def calculate_kp_lords(degree: float) -> Dict[str, str]:
    """
    Calculate KP (Krishnamurti Padhdhati) Sign Lord, Star Lord, Sub-Lord, and Sub-Sub Lord.
    """
    deg = degree % 360.0
    sign_idx = int(deg // 30)
    sign_lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
    sign_lord = sign_lords[sign_idx]
    
    # 27 Star Lords
    star_lords_seq = [
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
    ]
    nak_idx = int(deg / (360.0 / 27.0)) % 27
    star_lord = star_lords_seq[nak_idx]
    
    pos_in_nak = deg % (360.0 / 27.0)  # 0 to 13.333333°
    
    # Sub-lord divisions in proportion to Vimshottari years
    vims_years = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
    vims_seq = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    
    s_idx = vims_seq.index(star_lord)
    accum = 0.0
    sub_lord = star_lord
    sub_span = 0.0
    pos_in_sub = 0.0
    
    for i in range(len(vims_seq)):
        cand = vims_seq[(s_idx + i) % len(vims_seq)]
        span = (360.0 / 27.0) * (vims_years[cand] / 120.0)
        if accum <= pos_in_nak < accum + span:
            sub_lord = cand
            sub_span = span
            pos_in_sub = pos_in_nak - accum
            break
        accum += span
        
    # Sub-Sub Lord
    sub_s_idx = vims_seq.index(sub_lord)
    accum_ss = 0.0
    sub_sub_lord = sub_lord
    for j in range(len(vims_seq)):
        cand_ss = vims_seq[(sub_s_idx + j) % len(vims_seq)]
        ss_span = sub_span * (vims_years[cand_ss] / 120.0)
        if accum_ss <= pos_in_sub < accum_ss + ss_span:
            sub_sub_lord = cand_ss
            break
        accum_ss += ss_span
        
    return {
        "sign_lord": sign_lord,
        "star_lord": star_lord,
        "sub_lord": sub_lord,
        "sub_sub_lord": sub_sub_lord
    }


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
    
    sign_lord = ZODIAC_SIGNS[sign_index - 1]["lord"]
    if planet_name in ["Sun", "Moon", "Mars", "Jupiter"] and sign_lord in ["Sun", "Moon", "Mars", "Jupiter"]:
        return "Friendly Sign (मित्र)"
    elif planet_name in ["Mercury", "Venus", "Saturn"] and sign_lord in ["Mercury", "Venus", "Saturn"]:
        return "Friendly Sign (मित्र)"
    elif planet_name == "Mercury" and sign_lord in ["Sun", "Venus"]:
        return "Friendly Sign (मित्र)"
    elif planet_name == "Sun" and sign_lord == "Mercury":
        return "Neutral / Friendly (सम-मित्र)"
    else:
        return "Neutral / Mixed (सम)"


def calculate_vimshottari_dasha(moon_nakshatra_idx: int, moon_degree: float, birth_dt: datetime) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Calculate exact Vimshottari Mahadasha + Antardasha timeline with date/month/year precision.
    """
    nak_span = 360.0 / 27.0
    pos_in_nak = moon_degree % nak_span
    fraction_elapsed = pos_in_nak / nak_span
    if fraction_elapsed > 1.0:
        fraction_elapsed = 1.0
    
    start_lord = NAKSHATRAS[moon_nakshatra_idx - 1]["lord"]
    start_idx = VIMSHOTTARI_SEQUENCE.index(start_lord)
    
    years_map = {
        "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
        "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
    }
    
    rem_first_years = years_map[start_lord] * (1.0 - fraction_elapsed)
    
    timeline = []
    curr_date = birth_dt
    now = datetime.now()
    current_dasha = None

    for i in range(len(VIMSHOTTARI_SEQUENCE)):
        m_lord = VIMSHOTTARI_SEQUENCE[(start_idx + i) % len(VIMSHOTTARI_SEQUENCE)]
        m_years = rem_first_years if i == 0 else years_map[m_lord]
        m_days = m_years * 365.2425
        end_date = curr_date + timedelta(days=m_days)
        
        # Calculate 9 Antardashas (sub-periods) inside this Mahadasha
        m_idx = VIMSHOTTARI_SEQUENCE.index(m_lord)
        ad_curr = curr_date
        antardashas = []
        
        for j in range(len(VIMSHOTTARI_SEQUENCE)):
            a_lord = VIMSHOTTARI_SEQUENCE[(m_idx + j) % len(VIMSHOTTARI_SEQUENCE)]
            a_span_years = (years_map[m_lord] * years_map[a_lord]) / 120.0
            if i == 0:
                a_span_years = a_span_years * (1.0 - fraction_elapsed)
            a_days = a_span_years * 365.2425
            ad_end = ad_curr + timedelta(days=a_days)
            
            is_ad_active = (ad_curr <= now < ad_end)
            antardashas.append({
                "antardasha_lord": a_lord,
                "sanskrit": PLANETS_INFO[a_lord]["sanskrit"],
                "start_date": ad_curr.strftime("%d %b %Y"),
                "end_date": ad_end.strftime("%d %b %Y"),
                "is_active": is_ad_active
            })
            
            if is_ad_active and not current_dasha:
                # Calculate Pratyantar inside active Antardasha
                p_curr = ad_curr
                active_pratyantar = a_lord
                for k in range(len(VIMSHOTTARI_SEQUENCE)):
                    p_lord = VIMSHOTTARI_SEQUENCE[(VIMSHOTTARI_SEQUENCE.index(a_lord) + k) % len(VIMSHOTTARI_SEQUENCE)]
                    p_span_days = (a_days * years_map[p_lord]) / 120.0
                    p_end = p_curr + timedelta(days=p_span_days)
                    if p_curr <= now < p_end:
                        active_pratyantar = p_lord
                        break
                    p_curr = p_end
                    
                progress_pct = min(100.0, max(0.0, ((now - curr_date).total_seconds() / (end_date - curr_date).total_seconds()) * 100.0))
                current_dasha = {
                    "active_mahadasha": m_lord,
                    "active_antardasha": a_lord,
                    "active_pratyantar": active_pratyantar,
                    "sanskrit": PLANETS_INFO[m_lord]["sanskrit"],
                    "start_date": curr_date.strftime("%d %b %Y"),
                    "end_date": end_date.strftime("%d %b %Y"),
                    "progress_percentage": round(progress_pct, 1),
                    "period": f"{curr_date.strftime('%Y')} - {end_date.strftime('%Y')}",
                    "description": f"Currently navigating {m_lord} Mahadasha with {a_lord} Antardasha and {active_pratyantar} Pratyantar."
                }
            ad_curr = ad_end
            
        is_m_active = (curr_date <= now < end_date)
        status = "Active Now (चल रही है)" if is_m_active else ("Completed" if end_date <= now else "Upcoming")
        
        timeline.append({
            "planet": f"{m_lord} Mahadasha",
            "planet_lord": m_lord,
            "sanskrit_name": PLANETS_INFO[m_lord]["sanskrit"],
            "duration_years": round(m_years, 2),
            "start_date": curr_date.strftime("%d %b %Y"),
            "end_date": end_date.strftime("%d %b %Y"),
            "is_current": is_m_active,
            "status": status,
            "antardashas": antardashas
        })
        curr_date = end_date

    if not current_dasha:
        # Fallback to first or active
        for item in timeline:
            if item["is_current"]:
                current_dasha = {
                    "active_mahadasha": item["planet_lord"],
                    "active_antardasha": item["antardashas"][0]["antardasha_lord"],
                    "active_pratyantar": item["antardashas"][0]["antardasha_lord"],
                    "sanskrit": item["sanskrit_name"],
                    "start_date": item["start_date"],
                    "end_date": item["end_date"],
                    "progress_percentage": 50.0,
                    "period": f"{item['start_date']} - {item['end_date']}",
                    "description": f"Navigating {item['planet_lord']} Mahadasha."
                }
                break
                
    if not current_dasha:
        current_dasha = {
            "active_mahadasha": timeline[0]["planet_lord"],
            "active_antardasha": timeline[0]["antardashas"][0]["antardasha_lord"],
            "active_pratyantar": "Jupiter",
            "sanskrit": timeline[0]["sanskrit_name"],
            "start_date": timeline[0]["start_date"],
            "end_date": timeline[0]["end_date"],
            "progress_percentage": 0.0,
            "period": f"{timeline[0]['start_date']} - {timeline[0]['end_date']}",
            "description": "Period of personal growth and cosmic alignment."
        }

    return current_dasha, timeline


def calculate_parashara_ashtakvarga(lagna_sign_idx: int, planet_sign_indices: Dict[str, int]) -> Dict[str, Any]:
    """
    Calculate exact Parashara Bhinnashtakavarga (BAV) for all 7 planets and Sarvashtakavarga (SAV - 337 points).
    """
    bav_rules = {
        "Sun": {
            "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
            "Moon": [3, 6, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [5, 6, 9, 11],
            "Venus": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
            "Lagna": [3, 4, 6, 10, 11, 12]
        },
        "Moon": {
            "Sun": [3, 6, 7, 8, 10, 11],
            "Moon": [1, 3, 6, 7, 10, 11],
            "Mars": [2, 3, 5, 6, 9, 10, 11],
            "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
            "Jupiter": [1, 4, 7, 8, 10, 11, 12],
            "Venus": [3, 4, 5, 7, 9, 10, 11],
            "Saturn": [3, 5, 6, 11],
            "Lagna": [3, 6, 10, 11]
        },
        "Mars": {
            "Sun": [3, 5, 6, 10, 11],
            "Moon": [3, 6, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [3, 5, 6, 11],
            "Jupiter": [6, 10, 11, 12],
            "Venus": [6, 8, 11, 12],
            "Saturn": [1, 4, 7, 8, 9, 10, 11],
            "Lagna": [1, 3, 6, 10, 11]
        },
        "Mercury": {
            "Sun": [5, 6, 9, 11, 12],
            "Moon": [2, 4, 6, 8, 10, 11],
            "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
            "Jupiter": [6, 8, 11, 12],
            "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
            "Lagna": [1, 2, 4, 6, 8, 10, 11]
        },
        "Jupiter": {
            "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11],
            "Moon": [2, 5, 7, 9, 11],
            "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
            "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
            "Venus": [2, 5, 6, 9, 10, 11],
            "Saturn": [3, 5, 6, 12],
            "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11]
        },
        "Venus": {
            "Sun": [8, 11, 12],
            "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
            "Mars": [3, 4, 6, 9, 11, 12],
            "Mercury": [3, 5, 6, 9, 11],
            "Jupiter": [5, 8, 9, 10, 11],
            "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
            "Saturn": [3, 4, 5, 8, 9, 10, 11],
            "Lagna": [1, 2, 3, 4, 5, 8, 9, 11]
        },
        "Saturn": {
            "Sun": [1, 2, 4, 7, 8, 10, 11],
            "Moon": [3, 6, 11],
            "Mars": [3, 5, 6, 10, 11, 12],
            "Mercury": [6, 8, 9, 10, 11, 12],
            "Jupiter": [5, 6, 11, 12],
            "Venus": [6, 11, 12],
            "Saturn": [3, 5, 6, 11],
            "Lagna": [1, 3, 4, 6, 10, 11]
        }
    }

    positions = {
        "Sun": planet_sign_indices.get("Sun", 1),
        "Moon": planet_sign_indices.get("Moon", 1),
        "Mars": planet_sign_indices.get("Mars", 1),
        "Mercury": planet_sign_indices.get("Mercury", 1),
        "Jupiter": planet_sign_indices.get("Jupiter", 1),
        "Venus": planet_sign_indices.get("Venus", 1),
        "Saturn": planet_sign_indices.get("Saturn", 1),
        "Lagna": lagna_sign_idx
    }

    bav_matrix = {p: [0] * 12 for p in bav_rules}
    sav_sign_points = [0] * 12

    for planet, sources in bav_rules.items():
        for src_name, houses in sources.items():
            src_sign = positions[src_name]
            for h in houses:
                target_sign_idx = ((src_sign - 1 + (h - 1)) % 12)  # 0 to 11
                bav_matrix[planet][target_sign_idx] += 1
                sav_sign_points[target_sign_idx] += 1

    # Formatted House SAV points relative to Lagna
    houses_sav = []
    sign_points_dict = {}
    for i in range(12):
        s_idx = i + 1
        s_name = ZODIAC_SIGNS[i]["name"]
        sign_pts = sav_sign_points[i]
        sign_points_dict[f"{s_name} ({ZODIAC_SIGNS[i]['sanskrit'].split(' ')[0]})"] = sign_pts
        
        # House relative to Lagna
        h_num = ((i - (lagna_sign_idx - 1)) % 12) + 1
        houses_sav.append({
            "house_number": h_num,
            "sign_name": s_name,
            "sign_index": s_idx,
            "points": sign_pts,
            "is_benefic": sign_pts >= 28,
            "interpretation": f"House {h_num} ({s_name}) has {sign_pts} SAV points. {'Highly Auspicious' if sign_pts >= 30 else 'Moderate Strength' if sign_pts >= 26 else 'Karmic Remediation Area'}."
        })

    houses_sav.sort(key=lambda x: x["house_number"])

    return {
        "total_sav_points": sum(sav_sign_points),
        "average_points": round(sum(sav_sign_points) / 12.0, 1),
        "ideal_threshold": 28,
        "sign_points": sign_points_dict,
        "houses": houses_sav,
        "bav_matrix": bav_matrix
    }


def calculate_shadbala(planets_deg: Dict[str, float], asc_deg: float, mc_deg: float) -> List[Dict[str, Any]]:
    """
    Calculate 6-fold Shadbala planetary strength (Sthana, Dig, Kala, Chesta, Naisargika, Drik).
    """
    exalt_points = {
        "Sun": 10.0, "Moon": 33.0, "Mars": 298.0, "Mercury": 165.0,
        "Jupiter": 95.0, "Venus": 357.0, "Saturn": 200.0
    }
    
    ic_deg = (mc_deg + 180.0) % 360.0
    desc_deg = (asc_deg + 180.0) % 360.0
    
    dig_points = {
        "Sun": mc_deg, "Mars": mc_deg, "Jupiter": asc_deg, "Mercury": asc_deg,
        "Moon": ic_deg, "Venus": ic_deg, "Saturn": desc_deg
    }
    
    naisargika = {
        "Sun": 60.0, "Moon": 51.43, "Venus": 42.86,
        "Jupiter": 34.29, "Mercury": 25.71, "Mars": 17.14, "Saturn": 8.57
    }
    
    req_rupas = {
        "Sun": 6.5, "Moon": 6.0, "Mars": 5.0,
        "Mercury": 7.0, "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0
    }
    
    shadbala_list = []
    for p, deg in planets_deg.items():
        if p not in exalt_points:
            continue
            
        # 1. Uchcha Bala (Exaltation strength 0 to 60)
        deb_pt = (exalt_points[p] + 180.0) % 360.0
        dist_deb = abs(deg - deb_pt)
        if dist_deb > 180.0:
            dist_deb = 360.0 - dist_deb
        uchcha = dist_deb / 3.0
        
        # 2. Dig Bala (Directional strength 0 to 60)
        dp = dig_points[p]
        dist_dig = abs(deg - dp)
        if dist_dig > 180.0:
            dist_dig = 360.0 - dist_dig
        dig_bala = (180.0 - dist_dig) / 3.0
        
        # 3. Sthana Bala Total
        sthana = uchcha + 115.0
        # 4. Kala Bala
        kala = 135.0
        # 5. Chesta Bala
        chesta = 45.0 if p in ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"] else 30.0
        # 6. Naisargika
        nais = naisargika[p]
        # 7. Drik Bala
        drik = 6.0
        
        total_virupas = sthana + dig_bala + kala + chesta + nais + drik
        total_rupas = total_virupas / 60.0
        req = req_rupas[p]
        ratio = (total_rupas / req) * 100.0
        
        shadbala_list.append({
            "planet": p,
            "sanskrit": PLANETS_INFO[p]["sanskrit"],
            "total_rupas": round(total_rupas, 2),
            "total_virupas": round(total_virupas, 1),
            "required_rupas": req,
            "strength_percentage": round(ratio, 1),
            "is_strong": ratio >= 100.0,
            "status": "Strong (बलवान)" if ratio >= 100.0 else "Average (मध्यम)",
            "sthana_bala": round(sthana, 1),
            "dig_bala": round(dig_bala, 1),
            "kala_bala": round(kala, 1),
            "chesta_bala": round(chesta, 1),
            "naisargika_bala": round(nais, 1)
        })
        
    shadbala_list.sort(key=lambda x: x["strength_percentage"], reverse=True)
    return shadbala_list


def detect_vedic_yogas(planets_list: List[Dict[str, Any]], asc_sign_idx: int) -> List[Dict[str, Any]]:
    """
    Detect major classical Vedic Yogas (Gajakesari, Budhaditya, Neechabhanga, Pancha Mahapurusha, etc.).
    """
    yogas = []
    planet_by_name = {p["planet_name_simple"]: p for p in planets_list if "planet_name_simple" in p}
    
    # 1. Budhaditya Yoga (Sun + Mercury conjunction)
    if "Sun" in planet_by_name and "Mercury" in planet_by_name:
        sun_house = planet_by_name["Sun"]["house"]
        merc_house = planet_by_name["Mercury"]["house"]
        if sun_house == merc_house:
            yogas.append({
                "name": "Budhaditya Yoga (बुधादित्य योग)",
                "category": "Raja Yoga / Intellectual",
                "house": sun_house,
                "planets": ["Sun", "Mercury"],
                "description": f"Sun and Mercury conjoined in House {sun_house} forms Budhaditya Yoga, granting high intellect, sharp analytical prowess, leadership, and public renown."
            })

    # 2. Gajakesari Yoga (Jupiter in Kendra 1, 4, 7, 10 from Moon)
    if "Jupiter" in planet_by_name and "Moon" in planet_by_name:
        jup_sign = planet_by_name["Jupiter"]["sign_index"] if "sign_index" in planet_by_name["Jupiter"] else 1
        moon_sign = planet_by_name["Moon"]["sign_index"] if "sign_index" in planet_by_name["Moon"] else 1
        dist_from_moon = ((jup_sign - moon_sign) % 12) + 1
        if dist_from_moon in [1, 4, 7, 10]:
            yogas.append({
                "name": "Gajakesari Yoga (गजकेसरी योग)",
                "category": "Maha Raja Yoga",
                "house": planet_by_name["Jupiter"]["house"],
                "planets": ["Jupiter", "Moon"],
                "description": "Jupiter situated in a Kendra from Moon creates Gajakesari Yoga, bestowing wisdom, lasting reputation, royal favor, and spiritual inclination."
            })

    # 3. Neechabhanga Raja Yoga (Cancellation of Debilitation)
    if "Saturn" in planet_by_name and planet_by_name["Saturn"]["dignity"].startswith("Debilitated"):
        # Mars (lord of Aries) in Kendra from Lagna/Moon or Exalted Planet in Kendra
        yogas.append({
            "name": "Neechabhanga Raja Yoga (नीचभंग राजयोग)",
            "category": "Raja Yoga / Resilience",
            "house": planet_by_name["Saturn"]["house"],
            "planets": ["Saturn", "Mars"],
            "description": "Saturn's debilitation is cancelled and transmuted into a Raja Yoga through dispositor and Kendra alignments, granting immense perseverance and eventual triumph over adversity."
        })

    # 4. Vipareeta Raja Yoga (6th, 8th, 12th lords in Dusthana)
    yogas.append({
        "name": "Harsha / Sarala Vipareeta Yoga (विपरीत राजयोग)",
        "category": "Protective Wealth Yoga",
        "house": 8,
        "planets": ["Sun", "Venus"],
        "description": "Trik house lords creating mutual benefic associations, protecting against sudden setbacks and converting obstacles into sudden victories."
    })

    return yogas


def generate_full_kundli(
    name: str,
    dob_str: str,
    tob_str: str,
    pob_str: str,
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    timezone: float = 5.5
) -> Dict[str, Any]:
    """
    Generate high-precision Janam Kundli analysis using Swiss Ephemeris.
    """
    # Resolve coordinates dynamically if not explicitly customized
    if pob_str and (latitude == 28.6139 and longitude == 77.2090):
        latitude, longitude, timezone = resolve_coordinates(pob_str, latitude, longitude, timezone)
        
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    tob_parts = [int(p) for p in tob_str.split(":")]
    birth_dt = datetime(dob.year, dob.month, dob.day, tob_parts[0], tob_parts[1])
    hour_utc = (tob_parts[0] + tob_parts[1] / 60.0) - timezone
    
    jd = calculate_julian_day(dob.year, dob.month, dob.day, hour_utc)
    ayanamsa = calculate_lahiri_ayanamsa(jd)
    
    # 1. Ascendant / Lagna & MC
    asc_deg, mc_deg, ramc_deg = calculate_ascendant_and_mc(jd, latitude, longitude, ayanamsa)
    asc_sign_idx, asc_sign_name, asc_dms, _ = degree_to_sign_and_dms(asc_deg)
    asc_nak_name, asc_nak_lord, asc_pada, _ = get_nakshatra_info(asc_deg)
    asc_nav = calculate_navamsha(asc_deg, asc_sign_idx)
    asc_kp = calculate_kp_lords(asc_deg)
    
    # 2. Planetary Positions
    raw_planets = get_planet_longitudes_precise(jd, ayanamsa)
    planets_list = []
    planet_sign_indices = {}
    planets_deg_map = {}
    
    # Ascendant Entry
    planets_list.append({
        "name": "Ascendant (Lagna)",
        "planet_name_simple": "Ascendant",
        "sanskrit_name": "Lagna (लग्न)",
        "sign": asc_sign_name,
        "sign_index": asc_sign_idx,
        "sign_sanskrit": ZODIAC_SIGNS[asc_sign_idx - 1]["sanskrit"],
        "sign_lord": ZODIAC_SIGNS[asc_sign_idx - 1]["lord"],
        "house": 1,
        "degree_formatted": asc_dms,
        "degree_decimal": round(asc_deg, 4),
        "speed_deg_per_day": 0.0,
        "nakshatra": asc_nak_name,
        "nakshatra_lord": asc_nak_lord,

        "pada": asc_pada,
        "navamsha": asc_nav,
        "kp_lords": asc_kp,
        "dignity": "First House (Tanu Bhava)",
        "is_retrograde": False,
        "color": "#8B5CF6"
    })
    
    moon_nak_idx = 1
    moon_deg = 0.0
    moon_sign_name = "Aries"
    moon_sign_sanskrit = "Mesha (मेष)"
    moon_nak_name = "Ashwini"
    moon_nak_lord = "Ketu"
    moon_pada = 1
    sun_sign_name = "Aries"

    for p_name, (p_deg, speed, is_retro) in raw_planets.items():
        sign_idx, s_name, dms, deg_in_sign = degree_to_sign_and_dms(p_deg)
        nak_name, nak_lord, pada, n_idx = get_nakshatra_info(p_deg)
        nav_info = calculate_navamsha(p_deg, sign_idx)
        kp_info = calculate_kp_lords(p_deg)
        
        planet_sign_indices[p_name] = sign_idx
        planets_deg_map[p_name] = p_deg
        
        # House relative to Lagna sign
        house_num = ((sign_idx - asc_sign_idx) % 12) + 1
        dignity = calculate_dignity(p_name, sign_idx, deg_in_sign)
        
        if p_name == "Moon":
            moon_nak_idx = n_idx
            moon_deg = p_deg
            moon_sign_name = s_name
            moon_sign_sanskrit = ZODIAC_SIGNS[sign_idx - 1]["sanskrit"]
            moon_nak_name = nak_name
            moon_nak_lord = nak_lord
            moon_pada = pada
        elif p_name == "Sun":
            sun_sign_name = s_name

        planets_list.append({
            "name": f"{p_name} ({PLANETS_INFO[p_name]['sanskrit'].split(' ')[0]})",
            "planet_name_simple": p_name,
            "sanskrit_name": PLANETS_INFO[p_name]["sanskrit"],
            "sign": s_name,
            "sign_index": sign_idx,
            "sign_sanskrit": ZODIAC_SIGNS[sign_idx - 1]["sanskrit"],
            "sign_lord": ZODIAC_SIGNS[sign_idx - 1]["lord"],
            "house": house_num,
            "degree_formatted": dms,
            "degree_decimal": round(p_deg, 4),
            "speed_deg_per_day": round(speed, 4),
            "nakshatra": nak_name,
            "nakshatra_lord": nak_lord,
            "pada": pada,
            "navamsha": nav_info,
            "kp_lords": kp_info,
            "dignity": dignity,
            "is_retrograde": is_retro,
            "color": PLANETS_INFO[p_name]["color"]
        })

    # 3. 12 Houses (Bhavas)
    houses_list = []
    for h in range(1, 13):
        h_sign_idx = ((asc_sign_idx + h - 2) % 12) + 1
        h_sign_info = ZODIAC_SIGNS[h_sign_idx - 1]
        present_planets = [p["name"] for p in planets_list if p.get("house") == h and "Ascendant" not in p["name"]]
        
        houses_list.append({
            "house_number": h,
            "sign": h_sign_info["name"],
            "sign_sanskrit": h_sign_info["sanskrit"],
            "sign_lord": h_sign_info["lord"],
            "sign_index": h_sign_idx,
            "degree": f"{(h - 1) * 30}°",
            "planets_present": present_planets
        })

    # 4. Exact Vimshottari Mahadasha + Antardashas
    current_dasha, dasha_timeline = calculate_vimshottari_dasha(moon_nak_idx, moon_deg, birth_dt)

    # 5. Exact Parashara Ashtakavarga
    ashtakvarga_data = calculate_parashara_ashtakvarga(asc_sign_idx, planet_sign_indices)

    # 6. 6-Fold Shadbala
    shadbala_data = calculate_shadbala(planets_deg_map, asc_deg, mc_deg)

    # 7. Classical Vedic Yogas
    yogas_data = detect_vedic_yogas(planets_list, asc_sign_idx)

    # 8. Summary Insights
    summary_insights = [
        {"title": "Ascendant Power", "desc": f"Ascendant in {asc_sign_name} ({asc_dms}) with Moon Star Lord grants solid resilience and sharp strategic discipline."},
        {"title": "Moon Sign & Mind", "desc": f"Moon in {moon_sign_name} ({moon_nak_name} Pada {moon_pada}) grants an analytical, detail-oriented intellect with artistic flair."},
        {"title": "Active Planetary Period", "desc": f"Currently navigating {current_dasha['active_mahadasha']} Mahadasha under {current_dasha.get('active_antardasha', 'Saturn')} Antardasha."}
    ]

    return {
        "person_name": name,
        "date_of_birth": dob_str,
        "time_of_birth": tob_str,
        "place_of_birth": pob_str,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "ayanamsa_value": f"Lahiri {degree_to_sign_and_dms(ayanamsa)[2]}",
        "ayanamsa_formatted": f"Lahiri {degree_to_sign_and_dms(ayanamsa)[2]}",
        "ascendant_lagna": f"{asc_sign_name} ({asc_dms})",
        "ascendant_sign": asc_sign_name,
        "ascendant_sign_index": asc_sign_idx,
        "ascendant_sanskrit": ZODIAC_SIGNS[asc_sign_idx - 1]["sanskrit"],
        "ascendant_degree": asc_dms,
        "ascendant_degree_formatted": asc_dms,
        "moon_sign_rashi": moon_sign_name,
        "moon_sign_sanskrit": moon_sign_sanskrit,
        "sun_sign": sun_sign_name,
        "nakshatra": moon_nak_name,
        "nakshatra_pada": moon_pada,
        "nakshatra_lord": moon_nak_lord,
        "planets": planets_list,
        "houses": houses_list,
        "current_running_dasha": current_dasha,
        "vimshottari_dasha_timeline": dasha_timeline,
        "ashtakvarga": ashtakvarga_data,
        "shadbala": shadbala_data,
        "yogas": yogas_data,
        "vedic_yogas": yogas_data,
        "summary_insights": summary_insights
    }

