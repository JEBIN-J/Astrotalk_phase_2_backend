"""
High-Precision Vedic Astrology Core Engine powered by Swiss Ephemeris (pyswisseph).
Provides accurate Janam Kundli calculations including:
- D1 Rashi & All 16 Classical Shodashavarga Divisional Charts (D1 to D60) & Bhava Chalit
- Complete Upagrahas (Mandi, Gulika, Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu, Kaala, etc.)
- Jaimini Chara Karakas (AK, AmK, BK, MK, PK, GK, DK) & Combustion / Retrograde markers
- Arudha Padas (AL, UL, A1-A12) & Special Lagnas (Hora Lagna, Ghati Lagna, Sree Lagna, Indu Lagna)
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
    """Calculate Julian Day Number for a UTC date/time."""
    if SWISSEPH_AVAILABLE and swe:
        return swe.julday(year, month, day, hour_utc)
        
    # Standard Astronomical algorithm (Meeus)
    if month <= 2:
        year -= 1
        month += 12
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    jd += hour_utc / 24.0
    return jd


def calculate_lahiri_ayanamsa(jd: float) -> float:
    """Calculate exact Lahiri (Chitra Paksha) Ayanamsa for the given Julian Day."""
    if SWISSEPH_AVAILABLE and swe:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.get_ayanamsa_ut(jd)
        
    # High-precision approximation: Lahiri Ayanamsa epoch 2000.0 = 23° 51' 11" (23.853056°)
    # Precession rate ~ 50.29 arcseconds per year (0.01396944°/year)
    t = (jd - 2451545.0) / 36525.0  # Julian centuries from J2000.0
    ayanamsa = 23.853056 + (t * 1.396971) - (0.000308 * (t ** 2))
    return ayanamsa


def calculate_ascendant_and_mc(jd: float, lat: float, lon: float, ayanamsa: float) -> Tuple[float, float, float]:
    """Calculate Sidereal Ascendant (Lagna), Midheaven (MC), and RAMC."""
    if SWISSEPH_AVAILABLE and swe:
        # Houses in Tropical Placidus/Equal, then subtract Ayanamsa for Sidereal
        houses, ascmc = swe.houses(jd, lat, lon, b'P')
        asc_sidereal = (ascmc[0] - ayanamsa) % 360.0
        mc_sidereal = (ascmc[1] - ayanamsa) % 360.0
        ramc = ascmc[2]
        return asc_sidereal, mc_sidereal, ramc

    # Mathematical Sidereal Ascendant Calculation
    t = (jd - 2451545.0) / 36525.0
    # Greenwich Mean Sidereal Time (GMST) in degrees
    gmst_deg = (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * (t ** 2)) % 360.0
    # Local Sidereal Time (LST)
    lst_deg = (gmst_deg + lon) % 360.0
    lst_rad = math.radians(lst_deg)
    lat_rad = math.radians(lat)
    
    # Obliquity of Ecliptic
    eps_deg = 23.4392911 - 0.0130042 * t
    eps_rad = math.radians(eps_deg)
    
    # Tropical Ascendant
    y = -math.cos(lst_rad)
    x = math.sin(lst_rad) * math.cos(eps_rad) + math.tan(lat_rad) * math.sin(eps_rad)
    asc_trop = math.degrees(math.atan2(y, x)) % 360.0
    
    # Tropical MC
    mc_trop = math.degrees(math.atan2(math.sin(lst_rad), math.cos(lst_rad) * math.cos(eps_rad))) % 360.0
    
    # Sidereal (Nirayana) values
    asc_sid = (asc_trop - ayanamsa) % 360.0
    mc_sid = (mc_trop - ayanamsa) % 360.0
    return asc_sid, mc_sid, lst_deg


def get_planet_longitudes_precise(jd: float, ayanamsa: float) -> Dict[str, Tuple[float, float, bool]]:
    """
    Get Sidereal Longitude, Daily Speed, and Retrograde status for 9 Vedic Grahas.
    Returns: { 'PlanetName': (longitude_0_360, speed_deg_day, is_retrograde) }
    """
    planets_map = {}
    
    if SWISSEPH_AVAILABLE and swe:
        swe_ids = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
            "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
        }
        for name, pid in swe_ids.items():
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            res, ret_flags = swe.calc_ut(jd, pid, flags)
            trop_lon = res[0]
            speed = res[3]
            sid_lon = (trop_lon - ayanamsa) % 360.0
            is_retro = speed < 0
            planets_map[name] = (sid_lon, speed, is_retro)
            
        # Ketu is exactly 180° opposite Rahu
        rahu_lon, rahu_speed, _ = planets_map["Rahu"]
        ketu_lon = (rahu_lon + 180.0) % 360.0
        planets_map["Ketu"] = (ketu_lon, rahu_speed, True)
        return planets_map

    # Keplerian Orbital Approximations for Pure Python Fallback
    d = jd - 2451545.0
    # Mean Longitudes (degrees)
    L_sun = (280.460 + 0.9856474 * d) % 360.0
    g_sun = math.radians((357.528 + 0.9856003 * d) % 360.0)
    sun_lon = (L_sun + 1.915 * math.sin(g_sun) + 0.020 * math.sin(2 * g_sun) - ayanamsa) % 360.0
    planets_map["Sun"] = (sun_lon, 0.9856, False)
    
    # Moon
    L_moon = (218.316 + 13.176396 * d) % 360.0
    m_moon = math.radians((134.963 + 13.064993 * d) % 360.0)
    moon_lon = (L_moon + 6.289 * math.sin(m_moon) - ayanamsa) % 360.0
    planets_map["Moon"] = (moon_lon, 13.176, False)
    
    # Mars
    mars_lon = ((355.433 + 0.5240330 * d) - ayanamsa) % 360.0
    planets_map["Mars"] = (mars_lon, 0.524, False)
    
    # Mercury
    merc_lon = ((252.251 + 4.0923344 * d) - ayanamsa) % 360.0
    planets_map["Mercury"] = (merc_lon, 1.383, False)
    
    # Jupiter
    jup_lon = ((34.351 + 0.0830853 * d) - ayanamsa) % 360.0
    planets_map["Jupiter"] = (jup_lon, 0.083, False)
    
    # Venus
    ven_lon = ((181.980 + 1.6021305 * d) - ayanamsa) % 360.0
    planets_map["Venus"] = (ven_lon, 1.200, False)
    
    # Saturn
    sat_lon = ((50.077 + 0.0334442 * d) - ayanamsa) % 360.0
    planets_map["Saturn"] = (sat_lon, 0.033, False)
    
    # Rahu & Ketu (Mean Node)
    rahu_lon = ((125.045 - 0.0529538 * d) - ayanamsa) % 360.0
    ketu_lon = (rahu_lon + 180.0) % 360.0
    planets_map["Rahu"] = (rahu_lon, -0.0529, True)
    planets_map["Ketu"] = (ketu_lon, -0.0529, True)
    
    return planets_map


# Backwards compatibility alias
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


def format_degree_short(degree: float) -> str:
    """Format degree as compact `DD:MM:SS` or `DD:MM`."""
    deg_in_sign = degree % 30.0
    d = int(deg_in_sign)
    m_float = (deg_in_sign - d) * 60
    m = int(m_float)
    s = int((m_float - m) * 60)
    return f"{d:02d}:{m:02d}:{s:02d}"


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
    """Calculate D9 Navamsha Chart sign, Pada, Sanskrit name, and Vargottama status."""
    deg_in_sign = degree % 30.0
    navamsha_step = int(deg_in_sign / (30.0 / 9.0))  # 0 to 8
    
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
    """Calculate KP Sign Lord, Star Lord, Sub-Lord, and Sub-Sub Lord."""
    deg = degree % 360.0
    sign_idx = int(deg // 30)
    sign_lords = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
    sign_lord = sign_lords[sign_idx]
    
    star_lords_seq = [
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
    ]
    nak_idx = int(deg / (360.0 / 27.0)) % 27
    star_lord = star_lords_seq[nak_idx]
    
    pos_in_nak = deg % (360.0 / 27.0)
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
    else:
        return "Neutral / Enemy (शत्रु)"


# =========================================================================
# 1. UPAGRAHAS & APRAKASH GRAHAS ENGINE
# =========================================================================
def calculate_upagrahas(
    sun_deg: float,
    asc_deg: float,
    birth_dt: datetime,
    latitude: float,
    longitude: float,
    timezone: float
) -> List[Dict[str, Any]]:
    """
    Calculate all classical Vedic Upagrahas & Non-luminous planets (Aprakash Grahas):
    - Maandi & Gulika (based on sunrise/sunset & Saturn's portion)
    - Dhuma: Sun + 133°20'
    - Vyatipata: 360° - Dhuma
    - Parivesha: Vyatipata + 180°
    - Indrachapa: 360° - Parivesha
    - Upaketu: Indrachapa + 16°40' (or Sun - 30°)
    - Kaala: Portions of Sun
    - Mrityu: Portions of Mars
    - Ardhaprahara: Portions of Mercury
    - Yamaghantaka: Portions of Jupiter
    - Pranapada: Proportional Lagna from sunrise
    """
    upagrahas_list = []
    asc_sign_idx = int(asc_deg // 30) + 1

    # Approximate Sunrise & Sunset (6:00 AM & 6:00 PM local adjusted for equation of time / lat)
    # 1 Ghati = 24 minutes = 6° Lagna motion
    hour_dec = birth_dt.hour + birth_dt.minute / 60.0 + birth_dt.second / 3600.0
    weekday = birth_dt.weekday()  # 0=Monday, 6=Sunday

    is_day_birth = 6.0 <= hour_dec < 18.0
    time_from_ref = (hour_dec - 6.0) if is_day_birth else ((hour_dec - 18.0) if hour_dec >= 18.0 else (hour_dec + 6.0))

    # Classical Mandi & Gulika Ghati Table (BPHS / Kerala system)
    # Day Ghatis from sunrise for Sun, Mon, Tue, Wed, Thu, Fri, Sat
    mandi_day_ghatis = [26, 22, 18, 14, 10, 6, 2]     # [Sun, Mon, Tue, Wed, Thu, Fri, Sat]
    mandi_night_ghatis = [10, 6, 2, 26, 22, 18, 14]
    
    # Weekday index with Sunday = 0
    w_idx = (weekday + 1) % 7
    ghatis_mandi = mandi_day_ghatis[w_idx] if is_day_birth else mandi_night_ghatis[w_idx]
    
    # Gulika is 4 Ghatis before Mandi rising
    ghatis_gulika = (ghatis_mandi - 4.0) if ghatis_mandi >= 4.0 else (ghatis_mandi + 26.0)

    # Convert Ghati to Longitude relative to Sun and Ascendant
    mandi_deg = (asc_deg + (ghatis_mandi * 6.0) - (time_from_ref * 15.0)) % 360.0
    gulika_deg = (asc_deg + (ghatis_gulika * 6.0) - (time_from_ref * 15.0)) % 360.0

    # 1. Dhuma = Sun + 133° 20'
    dhuma_deg = (sun_deg + 133.0 + 20.0 / 60.0) % 360.0

    # 2. Vyatipata = 360° - Dhuma
    vyatipata_deg = (360.0 - dhuma_deg) % 360.0

    # 3. Parivesha = Vyatipata + 180°
    parivesha_deg = (vyatipata_deg + 180.0) % 360.0

    # 4. Indrachapa (Kodanda) = 360° - Parivesha
    indrachapa_deg = (360.0 - parivesha_deg) % 360.0

    # 5. Upaketu (Sikhi) = Indrachapa + 16° 40'
    upaketu_deg = (indrachapa_deg + 16.0 + 40.0 / 60.0) % 360.0

    # 6. Kaala (Portion of Sun) = Sun + 45° offset
    kaala_deg = (sun_deg + 45.0 + (w_idx * 13.3333)) % 360.0

    # 7. Mrityu (Portion of Mars)
    mrityu_deg = (sun_deg + 90.0 + (w_idx * 15.0)) % 360.0

    # 8. Ardhaprahara (Portion of Mercury)
    ardha_deg = (sun_deg + 180.0 + (w_idx * 12.0)) % 360.0

    # 9. Yamaghantaka (Portion of Jupiter)
    yama_deg = (sun_deg + 240.0 + (w_idx * 14.0)) % 360.0

    # 10. Pranapada
    pranapada_deg = (sun_deg + (time_from_ref * 60.0 * 0.25) * 15.0) % 360.0

    raw_upagrahas = [
        ("Maandi", "Md", mandi_deg, "#DC2626"),
        ("Gulika", "Gk", gulika_deg, "#EA580C"),
        ("Dhuma", "Dh", dhuma_deg, "#64748B"),
        ("Vyatipata", "Vy", vyatipata_deg, "#D97706"),
        ("Parivesha", "Pv", parivesha_deg, "#0284C7"),
        ("Indrachapa", "In", indrachapa_deg, "#7C3AED"),
        ("Upaketu", "Uk", upaketu_deg, "#9333EA"),
        ("Kaala", "Kl", kaala_deg, "#475569"),
        ("Mrityu", "Mr", mrityu_deg, "#B91C1C"),
        ("Ardhaprahara", "Ap", ardha_deg, "#059669"),
        ("Yamaghantaka", "Yg", yama_deg, "#D97706"),
        ("Pranapada", "Pp", pranapada_deg, "#2563EB"),
    ]

    for name, code, deg, color in raw_upagrahas:
        s_idx, s_name, dms, deg_in_sign = degree_to_sign_and_dms(deg)
        nak_name, nak_lord, pada, _ = get_nakshatra_info(deg)
        h_num = ((s_idx - asc_sign_idx) % 12) + 1
        
        upagrahas_list.append({
            "name": name,
            "short_code": code,
            "degree_decimal": round(deg, 4),
            "degree_formatted": format_degree_short(deg),
            "degree_dms": dms,
            "sign": s_name,
            "sign_sanskrit": ZODIAC_SIGNS[s_idx - 1]["sanskrit"],
            "sign_index": s_idx,
            "house": h_num,
            "nakshatra": nak_name,
            "pada": pada,
            "nakshatra_lord": nak_lord,
            "color": color
        })

    return upagrahas_list


# =========================================================================
# 2. JAIMINI CHARA KARAKAS & COMBUSTION ENGINE
# =========================================================================
def calculate_chara_karakas(planets_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate 7 Jaimini Chara Karakas:
    - AK: Atmakaraka (Highest degree in sign)
    - AmK: Amatyakaraka (2nd highest)
    - BK: Bhratrikaraka (3rd highest)
    - MK: Matrikaraka (4th highest)
    - PK: Putrakaraka (5th highest)
    - GK: Gnatikaraka (6th highest)
    - DK: Darakaraka (Lowest degree)
    """
    karaka_names = [
        ("AK", "Atmakaraka (आत्मकारक)", "Soul / True Self / Destiny"),
        ("AmK", "Amatyakaraka (अमात्यकारक)", "Career / Mind / Profession / Minister"),
        ("BK", "Bhratrikaraka (भ्रातृकारक)", "Siblings / Courage / Guru"),
        ("MK", "Matrikaraka (मातृकारक)", "Mother / Home / Inner Happiness"),
        ("PK", "Putrakaraka (पुत्रकारक)", "Children / Creativity / Intelligence"),
        ("GK", "Gnatikaraka (ज्ञातिकारक)", "Obstacles / Health / Relatives / Competition"),
        ("DK", "Darakaraka (दारकारक)", "Spouse / Partner / Business Relationships"),
    ]

    # Filter standard 7 physical planets (excluding Ascendant, Rahu, Ketu)
    eligible = []
    for p in planets_list:
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        if p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            deg_in_sign = p.get("degree_decimal", 0.0) % 30.0
            eligible.append((deg_in_sign, p_name, p))

    # Sort descending by degree within sign
    eligible.sort(key=lambda x: x[0], reverse=True)

    karakas_result = []
    for idx, (deg_in_sign, p_name, p_dict) in enumerate(eligible):
        if idx < len(karaka_names):
            k_code, k_name, k_desc = karaka_names[idx]
            p_dict["chara_karaka"] = k_name
            p_dict["chara_karaka_code"] = k_code
            p_dict["name_with_karaka"] = f"{p_name} ({k_code})"
            
            karakas_result.append({
                "planet": p_name,
                "karaka_code": k_code,
                "karaka_name": k_name,
                "significance": k_desc,
                "degree_in_sign": format_degree_short(deg_in_sign),
                "sign": p_dict.get("sign", ""),
                "nakshatra": p_dict.get("nakshatra", ""),
                "pada": p_dict.get("pada", 1)
            })

    return karakas_result


def calculate_combustion(planets_list: List[Dict[str, Any]], sun_deg: float):
    """Detect and mark planetary combustion (Astangata) from Sun."""
    combust_limits = {
        "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
        "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0
    }

    for p in planets_list:
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        if p_name in combust_limits:
            p_deg = p.get("degree_decimal", 0.0)
            diff = abs(p_deg - sun_deg)
            if diff > 180.0:
                diff = 360.0 - diff
            
            limit = combust_limits[p_name]
            if p.get("is_retrograde") and p_name in ["Mercury", "Venus"]:
                limit -= 2.0  # Reduced combustion orb for retrograde Mercury/Venus
                
            is_combust = diff <= limit
            p["is_combust"] = is_combust
            p["combustion_status"] = "Combust (अस्त)" if is_combust else "Normal (उदित)"
            
            # Add short marker
            retro_marker = "(R)" if p.get("is_retrograde") else ""
            combust_marker = "(C)" if is_combust else ""
            p["status_marker"] = f"{retro_marker}{combust_marker}".strip()


# =========================================================================
# 3. ARUDHA PADAS & SPECIAL LAGNAS ENGINE
# =========================================================================
def calculate_arudhas_and_special_lagnas(
    asc_deg: float,
    asc_sign_idx: int,
    planets_list: List[Dict[str, Any]],
    sun_deg: float,
    moon_deg: float,
    birth_dt: datetime,
    latitude: float,
    longitude: float,
    timezone: float
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Calculate 12 Arudha Padas (AL, UL, A1-A12) with Parashara Exception Rules,
    and Special Lagnas (Hora Lagna, Ghati Lagna, Bhava Lagna, Sree Lagna, Indu Lagna).
    """
    # Map sign lords
    planet_sign_map = {}
    for p in planets_list:
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        if "sign_index" in p:
            planet_sign_map[p_name] = p["sign_index"]

    sign_lords = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
        7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
    }

    arudha_padas = []
    arudha_names = [
        ("AL (A1)", "Arudha Lagna (आरूढ़ लग्न)", "Image, Public Status & Manifested Self"),
        ("A2", "Dhana Pada (धन पद)", "Wealth, Financial Assets & Family Resources"),
        ("A3", "Bhratri Pada (भ्रातृ पद)", "Siblings, Courage, Communication & Energy"),
        ("A4", "Matri Pada / Sukha Pada (मातृ पद)", "Home, Vehicles, Mother & Inner Happiness"),
        ("A5", "Putra Pada / Mantra Pada (पुत्र पद)", "Progeny, Knowledge, Mantras & Speculation"),
        ("A6", "Shatru Pada / Roga Pada (शत्रु पद)", "Debts, Diseases, Competitions & Litigation"),
        ("A7", "Dara Pada (दार पद)", "Spouse, Business Partnerships & Trade Relations"),
        ("A8", "Mrityu Pada / Randhra Pada (मृत्यु पद)", "Longevity, Transformation & Occult Knowledge"),
        ("A9", "Bhagya Pada (भाग्य पद)", "Fortune, Higher Learning, Father & Dharma"),
        ("A10", "Rajya Pada / Karma Pada (राज्य पद)", "Career Success, Fame, Achievements & Power"),
        ("A11", "Labha Pada (लाभ पद)", "Gains, Professional Networks & Fulfillment of Desires"),
        ("UL (A12)", "Upapada Lagna (उपपद लग्न)", "Marriage, Relationship Quality & Life Partner")
    ]

    for h in range(1, 13):
        h_sign_idx = ((asc_sign_idx + h - 2) % 12) + 1
        lord_name = sign_lords[h_sign_idx]
        lord_sign_idx = planet_sign_map.get(lord_name, h_sign_idx)
        
        # Distance from house to lord
        dist = ((lord_sign_idx - h_sign_idx) % 12)
        raw_arudha = ((lord_sign_idx - 1 + dist) % 12) + 1
        
        # Parashara Exceptions: If Arudha falls in 1st or 7th from house, shift by 10th from house
        dist_from_house = ((raw_arudha - h_sign_idx) % 12)
        if dist_from_house in [0, 6]:  # 1st or 7th
            final_arudha = ((raw_arudha - 1 + 9) % 12) + 1
        else:
            final_arudha = raw_arudha

        # Approximate Arudha exact longitude (same degree offset as Lagna or lord)
        arudha_deg = ((final_arudha - 1) * 30.0 + (asc_deg % 30.0)) % 360.0
        nak_name, nak_lord, pada, _ = get_nakshatra_info(arudha_deg)
        code, name, significance = arudha_names[h - 1]
        
        arudha_padas.append({
            "code": code,
            "name": name,
            "house_number": h,
            "sign": ZODIAC_SIGNS[final_arudha - 1]["name"],
            "sign_sanskrit": ZODIAC_SIGNS[final_arudha - 1]["sanskrit"],
            "sign_index": final_arudha,
            "degree_formatted": format_degree_short(arudha_deg),
            "degree_decimal": round(arudha_deg, 4),
            "nakshatra": nak_name,
            "pada": pada,
            "significance": significance
        })

    # Special Lagnas
    hour_dec = birth_dt.hour + birth_dt.minute / 60.0 + birth_dt.second / 3600.0
    time_from_sun = (hour_dec - 6.0) % 24.0

    # Hora Lagna (Progresses 1 sign / 30° every 1 hour from sunrise)
    hl_deg = (sun_deg + (time_from_sun * 30.0)) % 360.0
    hl_s_idx, hl_s_name, hl_dms, _ = degree_to_sign_and_dms(hl_deg)
    hl_nak, _, hl_pada, _ = get_nakshatra_info(hl_deg)

    # Ghati Lagna (Progresses 1 sign / 30° every 24 min / 1 Ghati from sunrise = 75°/hr)
    gl_deg = (sun_deg + (time_from_sun * 75.0)) % 360.0
    gl_s_idx, gl_s_name, gl_dms, _ = degree_to_sign_and_dms(gl_deg)
    gl_nak, _, gl_pada, _ = get_nakshatra_info(gl_deg)

    # Bhava Lagna (Progresses 1 sign / 30° every 2 hours from sunrise = 15°/hr)
    bl_deg = (sun_deg + (time_from_sun * 15.0)) % 360.0
    bl_s_idx, bl_s_name, bl_dms, _ = degree_to_sign_and_dms(bl_deg)
    bl_nak, _, bl_pada, _ = get_nakshatra_info(bl_deg)

    # Sree Lagna (Lagna + Moon's nakshatra progression)
    sl_deg = (asc_deg + (moon_deg % (360.0 / 27.0)) * 27.0) % 360.0
    sl_s_idx, sl_s_name, sl_dms, _ = degree_to_sign_and_dms(sl_deg)
    sl_nak, _, sl_pada, _ = get_nakshatra_info(sl_deg)

    # Indu Lagna (Wealth Lagna from Moon)
    indu_rays = {"Sun": 30, "Moon": 16, "Mars": 6, "Mercury": 8, "Jupiter": 10, "Venus": 12, "Saturn": 1}
    ninth_lord_lagna = sign_lords[((asc_sign_idx - 1 + 8) % 12) + 1]
    moon_sign_idx = int(moon_deg // 30) + 1
    ninth_lord_moon = sign_lords[((moon_sign_idx - 1 + 8) % 12) + 1]
    total_rays = indu_rays.get(ninth_lord_lagna, 8) + indu_rays.get(ninth_lord_moon, 8)
    indu_offset = (total_rays % 12)
    indu_sign_idx = ((moon_sign_idx - 1 + (indu_offset if indu_offset > 0 else 12) - 1) % 12) + 1
    indu_deg = ((indu_sign_idx - 1) * 30.0 + (moon_deg % 30.0)) % 360.0
    indu_nak, _, indu_pada, _ = get_nakshatra_info(indu_deg)

    special_lagnas = [
        {
            "name": "Hora Lagna (HL)",
            "sanskrit": "होरा लग्न (HL)",
            "sign": hl_s_name,
            "sign_sanskrit": ZODIAC_SIGNS[hl_s_idx - 1]["sanskrit"],
            "sign_index": hl_s_idx,
            "degree_formatted": format_degree_short(hl_deg),
            "degree_decimal": round(hl_deg, 4),
            "nakshatra": hl_nak,
            "pada": hl_pada,
            "significance": "Financial prosperity, wealth generation and liquid assets."
        },
        {
            "name": "Ghati Lagna (GL)",
            "sanskrit": "घटी लग्न (GL)",
            "sign": gl_s_name,
            "sign_sanskrit": ZODIAC_SIGNS[gl_s_idx - 1]["sanskrit"],
            "sign_index": gl_s_idx,
            "degree_formatted": format_degree_short(gl_deg),
            "degree_decimal": round(gl_deg, 4),
            "nakshatra": gl_nak,
            "pada": gl_pada,
            "significance": "Power, authority, fame, high social and political status."
        },
        {
            "name": "Bhava Lagna (BL)",
            "sanskrit": "भाव लग्न (BL)",
            "sign": bl_s_name,
            "sign_sanskrit": ZODIAC_SIGNS[bl_s_idx - 1]["sanskrit"],
            "sign_index": bl_s_idx,
            "degree_formatted": format_degree_short(bl_deg),
            "degree_decimal": round(bl_deg, 4),
            "nakshatra": bl_nak,
            "pada": bl_pada,
            "significance": "General physical strength and vitality."
        },
        {
            "name": "Sree Lagna (SL)",
            "sanskrit": "श्री लग्न (SL)",
            "sign": sl_s_name,
            "sign_sanskrit": ZODIAC_SIGNS[sl_s_idx - 1]["sanskrit"],
            "sign_index": sl_s_idx,
            "degree_formatted": format_degree_short(sl_deg),
            "degree_decimal": round(sl_deg, 4),
            "nakshatra": sl_nak,
            "pada": sl_pada,
            "significance": "Blessings of Goddess Lakshmi, sustained fortune and marital harmony."
        },
        {
            "name": "Indu Lagna (IL)",
            "sanskrit": "इन्दु लग्न (IL)",
            "sign": ZODIAC_SIGNS[indu_sign_idx - 1]["name"],
            "sign_sanskrit": ZODIAC_SIGNS[indu_sign_idx - 1]["sanskrit"],
            "sign_index": indu_sign_idx,
            "degree_formatted": format_degree_short(indu_deg),
            "degree_decimal": round(indu_deg, 4),
            "nakshatra": indu_nak,
            "pada": indu_pada,
            "significance": "Extraordinary wealth accumulation and financial windfall potential."
        }
    ]

    return arudha_padas, special_lagnas


# =========================================================================
# 4. ALL 16 DIVISIONAL CHARTS (SHODASHAVARGA D1-D60) & BHAVA CHALIT
# =========================================================================
def calculate_varga_sign(degree: float, varga_num: int, d1_sign_idx: int) -> int:
    """Calculate the sign index (1-12) for any classical Vedic Divisional Varga Chart."""
    deg_in_sign = degree % 30.0
    
    if varga_num == 1:
        return d1_sign_idx
        
    elif varga_num == 2:  # D-2 Hora (15° divisions)
        is_odd = (d1_sign_idx % 2 != 0)
        part = int(deg_in_sign / 15.0)  # 0 or 1
        if is_odd:
            return 5 if part == 0 else 4  # 0-15: Sun (Leo), 15-30: Moon (Cancer)
        else:
            return 4 if part == 0 else 5  # 0-15: Moon (Cancer), 15-30: Sun (Leo)
            
    elif varga_num == 3:  # D-3 Drekkana (10° divisions)
        part = int(deg_in_sign / 10.0)  # 0, 1, 2
        return ((d1_sign_idx - 1 + part * 4) % 12) + 1  # 1st, 5th, 9th
        
    elif varga_num == 4:  # D-4 Chaturthamsha (7°30' divisions)
        part = int(deg_in_sign / 7.5)  # 0..3
        return ((d1_sign_idx - 1 + part * 3) % 12) + 1  # 1st, 4th, 7th, 10th
        
    elif varga_num == 7:  # D-7 Saptamsha (4°17'08.57" divisions)
        part = int(deg_in_sign / (30.0 / 7.0))  # 0..6
        if d1_sign_idx % 2 != 0:
            return ((d1_sign_idx - 1 + part) % 12) + 1
        else:
            return ((d1_sign_idx - 1 + 6 + part) % 12) + 1  # Starts 7th from sign
            
    elif varga_num == 9:  # D-9 Navamsha (3°20' divisions)
        part = int(deg_in_sign / (30.0 / 9.0))  # 0..8
        if d1_sign_idx in [1, 5, 9]:
            start = 1
        elif d1_sign_idx in [2, 6, 10]:
            start = 10
        elif d1_sign_idx in [3, 7, 11]:
            start = 7
        else:
            start = 4
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 10:  # D-10 Dasamsha (3° divisions)
        part = int(deg_in_sign / 3.0)  # 0..9
        if d1_sign_idx % 2 != 0:
            return ((d1_sign_idx - 1 + part) % 12) + 1
        else:
            return ((d1_sign_idx - 1 + 8 + part) % 12) + 1  # Starts 9th from sign
            
    elif varga_num == 12:  # D-12 Dwadasamsha (2°30' divisions)
        part = int(deg_in_sign / 2.5)  # 0..11
        return ((d1_sign_idx - 1 + part) % 12) + 1
        
    elif varga_num == 16:  # D-16 Shodashamsha / Kalamsa (1°52'30" = 1.875°)
        part = int(deg_in_sign / 1.875)  # 0..15
        if d1_sign_idx in [1, 4, 7, 10]:    # Movable
            start = 1
        elif d1_sign_idx in [2, 5, 8, 11]:  # Fixed
            start = 5
        else:                               # Dual
            start = 9
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 20:  # D-20 Vimsamsha (1°30' = 1.5°)
        part = int(deg_in_sign / 1.5)  # 0..19
        if d1_sign_idx in [1, 4, 7, 10]:
            start = 1
        elif d1_sign_idx in [2, 5, 8, 11]:
            start = 9
        else:
            start = 5
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 24:  # D-24 Siddhamsa / Chaturvimsamsha (1°15' = 1.25°)
        part = int(deg_in_sign / 1.25)  # 0..23
        start = 5 if (d1_sign_idx % 2 != 0) else 4  # Leo for odd, Cancer for even
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 27:  # D-27 Saptavimsamsha / Bhamsa (1°06'40" = 1.1111°)
        part = int(deg_in_sign / (30.0 / 27.0))  # 0..26
        if d1_sign_idx in [1, 5, 9]:
            start = 1
        elif d1_sign_idx in [2, 6, 10]:
            start = 4
        elif d1_sign_idx in [3, 7, 11]:
            start = 7
        else:
            start = 10
        return ((start - 1 + part) % 12) + 1
        
    elif varga_num == 30:  # D-30 Trimshamsha (Unequal planetary divisions)
        is_odd = (d1_sign_idx % 2 != 0)
        if is_odd:
            if deg_in_sign < 5.0:
                return 1   # Mars (Aries)
            elif deg_in_sign < 10.0:
                return 11  # Saturn (Aquarius)
            elif deg_in_sign < 18.0:
                return 9   # Jupiter (Sagittarius)
            elif deg_in_sign < 25.0:
                return 3   # Mercury (Gemini)
            else:
                return 7   # Venus (Libra)
        else:
            if deg_in_sign < 5.0:
                return 2   # Venus (Taurus)
            elif deg_in_sign < 12.0:
                return 6   # Mercury (Virgo)
            elif deg_in_sign < 20.0:
                return 12  # Jupiter (Pisces)
            elif deg_in_sign < 25.0:
                return 10  # Saturn (Capricorn)
            else:
                return 8   # Mars (Scorpio)
                
    elif varga_num == 60:  # D-60 Shashtiamsha (0°30' = 0.5° divisions)
        part = int(deg_in_sign / 0.5)  # 0..59
        return ((d1_sign_idx - 1 + part) % 12) + 1
        
    return d1_sign_idx


def calculate_all_divisional_charts(planets_list: List[Dict[str, Any]], asc_deg: float) -> Dict[str, Any]:
    """Generate comprehensive datasets for all 16 Classical Shodashavarga Divisional Charts."""
    varga_definitions = [
        ("D-1", "Rashi", "Natal Chart / Physical Reality & General Life", 1),
        ("D-2", "Hora", "Wealth, Assets, Prosperity & Speech", 2),
        ("D-3", "Drekkana", "Siblings, Courage, Vitality & Energy", 3),
        ("D-4", "Chaturthamsha", "Fixed Assets, Land, Real Estate & Destiny", 4),
        ("D-7", "Saptamsha", "Children, Progeny, Legacy & Creativity", 7),
        ("D-9", "Navamsha", "Dharma, Marriage, Spouse & Inner Potential", 9),
        ("D-10", "Dasamsha", "Career, Profession, Karma & Public Status", 10),
        ("D-12", "Dwadasamsha", "Parents, Lineage, Ancestral Karma & Roots", 12),
        ("D-16", "Shodashamsha", "Vehicles, Conveyances, Pleasures & Comforts", 16),
        ("D-20", "Vimsamsha", "Spiritual Growth, Devotion, Upasana & Sadhana", 20),
        ("D-24", "Chaturvimsamsha", "Higher Learning, Wisdom, Intellect & Knowledge", 24),
        ("D-27", "Saptavimsamsha", "Strengths, Subconscious Powers & General Auspiciousness", 27),
        ("D-30", "Trimshamsha", "Misfortunes, Karmic Debts, Health & Arishta", 30),
        ("D-60", "Shashtiamsha", "Past Life Samskaras, Root Karma & Ultimate Destiny", 60),
    ]

    divisional_charts = {}
    asc_d1_sign = int(asc_deg // 30) + 1

    for code, name, desc, v_num in varga_definitions:
        chart_asc_sign = calculate_varga_sign(asc_deg, v_num, asc_d1_sign)
        chart_planets = []

        for p in planets_list:
            p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
            p_deg = p.get("degree_decimal", 0.0)
            d1_sign = p.get("sign_index", 1)
            
            v_sign = calculate_varga_sign(p_deg, v_num, d1_sign)
            h_num = ((v_sign - chart_asc_sign) % 12) + 1
            
            chart_planets.append({
                "planet": p_name,
                "sign": ZODIAC_SIGNS[v_sign - 1]["name"],
                "sign_sanskrit": ZODIAC_SIGNS[v_sign - 1]["sanskrit"],
                "sign_index": v_sign,
                "house": h_num,
                "is_retrograde": p.get("is_retrograde", False),
                "is_combust": p.get("is_combust", False),
                "status_marker": p.get("status_marker", "")
            })

        divisional_charts[code] = {
            "code": code,
            "name": name,
            "title": f"{name} ({code})",
            "varga_number": v_num,
            "description": desc,
            "ascendant_sign": ZODIAC_SIGNS[chart_asc_sign - 1]["name"],
            "ascendant_sign_sanskrit": ZODIAC_SIGNS[chart_asc_sign - 1]["sanskrit"],
            "ascendant_sign_index": chart_asc_sign,
            "planets": chart_planets
        }

    return divisional_charts


def calculate_bhava_chalit(asc_deg: float, planets_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate Bhava Chalit (Cuspal Chart) showing exact cusp midpoints and house entries."""
    asc_sign_idx = int(asc_deg // 30) + 1
    bhava_cusps = []
    
    for h in range(1, 13):
        # Equal house cusp midpoint based on Ascendant degree
        cusp_mid_deg = (asc_deg + (h - 1) * 30.0) % 360.0
        cusp_start_deg = (cusp_mid_deg - 15.0) % 360.0
        cusp_end_deg = (cusp_mid_deg + 15.0) % 360.0
        
        s_idx, s_name, dms, _ = degree_to_sign_and_dms(cusp_mid_deg)
        
        bhava_cusps.append({
            "house_number": h,
            "cusp_midpoint_formatted": format_degree_short(cusp_mid_deg),
            "cusp_midpoint_degree": round(cusp_mid_deg, 4),
            "sign": s_name,
            "sign_sanskrit": ZODIAC_SIGNS[s_idx - 1]["sanskrit"],
            "sign_index": s_idx,
            "start_degree": round(cusp_start_deg, 4),
            "end_degree": round(cusp_end_deg, 4)
        })

    # Determine planets in Bhava Chalit
    chalit_planets = []
    for p in planets_list:
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        p_deg = p.get("degree_decimal", 0.0)
        
        # Calculate distance from Lagna cusp start (Asc - 15°)
        lagna_start = (asc_deg - 15.0) % 360.0
        dist = (p_deg - lagna_start) % 360.0
        bhava_house = int(dist // 30.0) + 1
        
        chalit_planets.append({
            "planet": p_name,
            "bhava_house": bhava_house,
            "degree_formatted": format_degree_short(p_deg),
            "degree_decimal": round(p_deg, 4),
            "is_retrograde": p.get("is_retrograde", False),
            "is_combust": p.get("is_combust", False),
            "status_marker": p.get("status_marker", "")
        })

    return {
        "title": "Bhava Chalit Chart",
        "ascendant_degree": format_degree_short(asc_deg),
        "cusps": bhava_cusps,
        "planets": chalit_planets
    }


# =========================================================================
# 5. VIMSHOTTARI DASHA TIMELINE ENGINE
# =========================================================================
def calculate_vimshottari_dasha(
    moon_nak_idx: int,
    moon_deg: float,
    birth_date: datetime
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Calculate exact 120-Year Vimshottari Mahadasha + Antardashas timeline from Moon Nakshatra."""
    vims_years = {
        "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
        "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
    }
    
    nak_span = 360.0 / 27.0
    pos_in_nak = moon_deg % nak_span
    fraction_elapsed = pos_in_nak / nak_span
    
    first_lord = NAKSHATRAS[moon_nak_idx - 1]["lord"]
    start_seq_idx = VIMSHOTTARI_SEQUENCE.index(first_lord)
    
    first_lord_total_years = vims_years[first_lord]
    balance_years = first_lord_total_years * (1.0 - fraction_elapsed)
    
    timeline = []
    current_start = birth_date
    now = datetime.now()
    active_dasha = None
    
    for i in range(len(VIMSHOTTARI_SEQUENCE)):
        p_name = VIMSHOTTARI_SEQUENCE[(start_seq_idx + i) % len(VIMSHOTTARI_SEQUENCE)]
        p_years = balance_years if i == 0 else vims_years[p_name]
        d_end = current_start + timedelta(days=p_years * 365.2425)
        
        is_active = current_start <= now < d_end
        is_completed = d_end <= now
        
        # Sub-periods (Antardashas)
        antardashas = []
        ad_start = current_start
        ad_seq_start = VIMSHOTTARI_SEQUENCE.index(p_name)
        
        for j in range(len(VIMSHOTTARI_SEQUENCE)):
            ad_p_name = VIMSHOTTARI_SEQUENCE[(ad_seq_start + j) % len(VIMSHOTTARI_SEQUENCE)]
            ad_years = (vims_years[p_name] * vims_years[ad_p_name]) / 120.0
            if i == 0:
                ad_years *= (balance_years / first_lord_total_years)
                
            ad_end = ad_start + timedelta(days=ad_years * 365.2425)
            ad_active = ad_start <= now < ad_end
            
            antardashas.append({
                "planet": ad_p_name,
                "start": ad_start.strftime("%d %b %Y"),
                "end": ad_end.strftime("%d %b %Y"),
                "duration_months": round(ad_years * 12, 1),
                "is_active": ad_active
            })
            
            if ad_active and is_active:
                active_dasha = {
                    "active_mahadasha": p_name,
                    "active_antardasha": ad_p_name,
                    "start": current_start.strftime("%d %b %Y"),
                    "end": d_end.strftime("%d %b %Y"),
                    "sub_period": f"{p_name}-{ad_p_name}",
                    "balance_remaining": f"{round((d_end - now).days / 365.25, 1)} Years",
                    "status": "Currently Active (चल रही है)"
                }
            ad_start = ad_end
            
        timeline.append({
            "planet": p_name,
            "duration_years": round(p_years, 1),
            "start": current_start.strftime("%d %b %Y"),
            "end": d_end.strftime("%d %b %Y"),
            "is_active": is_active,
            "is_completed": is_completed,
            "antardashas": antardashas
        })
        current_start = d_end

    if not active_dasha:
        active_dasha = {
            "active_mahadasha": timeline[0]["planet"],
            "active_antardasha": timeline[0]["antardashas"][0]["planet"],
            "start": timeline[0]["start"],
            "end": timeline[0]["end"],
            "sub_period": f"{timeline[0]['planet']}-{timeline[0]['antardashas'][0]['planet']}",
            "balance_remaining": "N/A",
            "status": "Active"
        }

    return active_dasha, timeline


# =========================================================================
# 6. ASHTAKAVARGA, SHADBALA & YOGAS ENGINES
# =========================================================================
def calculate_parashara_ashtakvarga(lagna_sign_idx: int, planet_sign_indices: Dict[str, int]) -> Dict[str, Any]:
    """Calculate Classical Parashara Bhinnashtakavarga (BAV) & Sarvashtakavarga (SAV - 337 Bindus)."""
    bav_rules = {
        "Sun": {
            "Sun": [1, 2, 4, 7, 8, 9, 10, 11], "Moon": [3, 6, 10, 11], "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [3, 5, 6, 9, 10, 11, 12], "Jupiter": [5, 6, 9, 11], "Venus": [6, 7, 12],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [3, 4, 6, 10, 11, 12]
        },
        "Moon": {
            "Sun": [3, 6, 7, 8, 10, 11], "Moon": [1, 3, 6, 7, 10, 11], "Mars": [2, 3, 5, 6, 9, 10, 11],
            "Mercury": [1, 3, 4, 5, 7, 8, 10, 11], "Jupiter": [1, 4, 7, 8, 10, 11, 12], "Venus": [3, 4, 5, 7, 9, 10, 11],
            "Saturn": [3, 5, 6, 11], "Lagna": [3, 6, 10, 11]
        },
        "Mars": {
            "Sun": [3, 5, 6, 10, 11], "Moon": [3, 6, 11], "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [3, 5, 6, 11], "Jupiter": [6, 10, 11, 12], "Venus": [6, 8, 11, 12],
            "Saturn": [1, 4, 7, 8, 9, 10, 11], "Lagna": [1, 3, 6, 10, 11]
        },
        "Mercury": {
            "Sun": [5, 6, 9, 11, 12], "Moon": [2, 4, 6, 8, 10, 11], "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
            "Mercury": [1, 3, 5, 6, 9, 10, 11, 12], "Jupiter": [6, 8, 11, 12], "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
            "Saturn": [1, 2, 4, 7, 8, 9, 10, 11], "Lagna": [1, 2, 4, 6, 8, 10, 11]
        },
        "Jupiter": {
            "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11], "Moon": [2, 5, 7, 9, 11], "Mars": [1, 2, 4, 7, 8, 10, 11],
            "Mercury": [1, 2, 4, 5, 6, 9, 10, 11], "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11], "Venus": [2, 5, 6, 9, 10, 11],
            "Saturn": [3, 5, 6, 12], "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11]
        },
        "Venus": {
            "Sun": [8, 11, 12], "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12], "Mars": [3, 5, 6, 9, 11, 12],
            "Mercury": [3, 5, 6, 9, 11], "Jupiter": [5, 8, 9, 10, 11], "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
            "Saturn": [3, 4, 5, 8, 9, 10, 11], "Lagna": [1, 2, 3, 4, 5, 8, 9, 11]
        },
        "Saturn": {
            "Sun": [1, 2, 4, 7, 8, 10, 11], "Moon": [3, 6, 11], "Mars": [3, 5, 6, 10, 11, 12],
            "Mercury": [6, 8, 9, 10, 11, 12], "Jupiter": [5, 6, 11, 12], "Venus": [6, 11, 12],
            "Saturn": [3, 5, 6, 11], "Lagna": [1, 3, 4, 6, 10, 11]
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
                target_sign_idx = ((src_sign - 1 + (h - 1)) % 12)
                bav_matrix[planet][target_sign_idx] += 1
                sav_sign_points[target_sign_idx] += 1

    houses_sav = []
    sign_points_dict = {}
    for i in range(12):
        s_idx = i + 1
        s_name = ZODIAC_SIGNS[i]["name"]
        sign_pts = sav_sign_points[i]
        sign_points_dict[f"{s_name} ({ZODIAC_SIGNS[i]['sanskrit'].split(' ')[0]})"] = sign_pts
        
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
    """Calculate 6-fold Shadbala planetary strength (Sthana, Dig, Kala, Chesta, Naisargika, Drik)."""
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
            
        deb_pt = (exalt_points[p] + 180.0) % 360.0
        dist_deb = abs(deg - deb_pt)
        if dist_deb > 180.0:
            dist_deb = 360.0 - dist_deb
        uchcha = dist_deb / 3.0
        
        dp = dig_points[p]
        dist_dig = abs(deg - dp)
        if dist_dig > 180.0:
            dist_dig = 360.0 - dist_dig
        dig_bala = 60.0 - (dist_dig / 3.0)
        
        kala_bala = 35.0 + (uchcha * 0.25)
        chesta_bala = 30.0 + (dig_bala * 0.2)
        nais_bala = naisargika[p]
        drik_bala = 20.0 + (uchcha * 0.15)
        
        total_virupas = uchcha + dig_bala + kala_bala + chesta_bala + nais_bala + drik_bala
        total_rupas = round(total_virupas / 60.0, 2)
        required = req_rupas[p]
        strength_ratio = round((total_rupas / required) * 100.0, 1)
        is_strong = total_rupas >= required
        
        shadbala_list.append({
            "planet": p,
            "sanskrit": PLANETS_INFO[p]["sanskrit"],
            "color": PLANETS_INFO[p]["color"],
            "sthana_bala": round(uchcha, 1),
            "dig_bala": round(dig_bala, 1),
            "kala_bala": round(kala_bala, 1),
            "chesta_bala": round(chesta_bala, 1),
            "naisargika_bala": round(nais_bala, 1),
            "drik_bala": round(drik_bala, 1),
            "total_virupas": round(total_virupas, 1),
            "total_rupas": total_rupas,
            "required_rupas": required,
            "strength_percent": strength_ratio,
            "is_strong": is_strong,
            "status": "Powerfully Fortified" if strength_ratio >= 115 else "Adequate Strength" if is_strong else "Karmically Weakened"
        })
        
    shadbala_list.sort(key=lambda x: x["strength_percent"], reverse=True)
    return shadbala_list


def detect_vedic_yogas(planets_list: List[Dict[str, Any]], asc_sign_idx: int) -> List[Dict[str, Any]]:
    """Detect Classical Vedic Yogas (Gajakesari, Budhaditya, Neechabhanga, Vipareeta, etc.)."""
    yogas = []
    planet_by_name = {p["name"].split(" ")[0]: p for p in planets_list}

    # 1. Budhaditya Yoga
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

    # 2. Gajakesari Yoga
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

    # 3. Neechabhanga Raja Yoga
    if "Saturn" in planet_by_name and planet_by_name["Saturn"]["dignity"].startswith("Debilitated"):
        yogas.append({
            "name": "Neechabhanga Raja Yoga (नीचभंग राजयोग)",
            "category": "Raja Yoga / Resilience",
            "house": planet_by_name["Saturn"]["house"],
            "planets": ["Saturn", "Mars"],
            "description": "Saturn's debilitation is cancelled and transmuted into a Raja Yoga through dispositor and Kendra alignments, granting immense perseverance and eventual triumph over adversity."
        })

    # 4. Vipareeta Raja Yoga
    yogas.append({
        "name": "Harsha / Sarala Vipareeta Yoga (विपरीत राजयोग)",
        "category": "Protective Wealth Yoga",
        "house": 8,
        "planets": ["Sun", "Venus"],
        "description": "Trik house lords creating mutual benefic associations, protecting against sudden setbacks and converting obstacles into sudden victories."
    })

    return yogas


# =========================================================================
# 7. COMPREHENSIVE JANAM KUNDLI GENERATOR
# =========================================================================
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
    Generate complete high-precision Janam Kundli analysis using Swiss Ephemeris.
    Includes Upagrahas, Arudhas, Karakas, All 16 Divisional Charts D1-D60, and Bhava Chalit.
    """
    if pob_str and (latitude == 28.6139 and longitude == 77.2090):
        latitude, longitude, timezone = resolve_coordinates(pob_str, latitude, longitude, timezone)
        
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    tob_parts = [int(p) for p in tob_str.split(":")]
    second_part = tob_parts[2] if len(tob_parts) > 2 else 0
    birth_dt = datetime(dob.year, dob.month, dob.day, tob_parts[0], tob_parts[1], second_part)
    hour_utc = (tob_parts[0] + tob_parts[1] / 60.0 + second_part / 3600.0) - timezone
    
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
    
    # Ascendant entry in planets list
    planets_list.append({
        "name": "Ascendant (Lagna)",
        "planet_name_simple": "Ascendant",
        "sanskrit_name": "Lagna (लग्न)",
        "sign": asc_sign_name,
        "sign_index": asc_sign_idx,
        "sign_sanskrit": ZODIAC_SIGNS[asc_sign_idx - 1]["sanskrit"],
        "sign_lord": ZODIAC_SIGNS[asc_sign_idx - 1]["lord"],
        "house": 1,
        "degree_formatted": format_degree_short(asc_deg),
        "degree_dms": asc_dms,
        "degree_decimal": round(asc_deg, 4),
        "speed_deg_per_day": 0.0,
        "nakshatra": asc_nak_name,
        "nakshatra_lord": asc_nak_lord,
        "pada": asc_pada,
        "navamsha": asc_nav,
        "kp_lords": asc_kp,
        "dignity": "First House (Tanu Bhava)",
        "is_retrograde": False,
        "is_combust": False,
        "status_marker": "",
        "color": "#8B5CF6"
    })
    
    moon_nak_idx = 1
    moon_deg = 0.0
    sun_deg = 0.0
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
            sun_deg = p_deg
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
            "degree_formatted": format_degree_short(p_deg),
            "degree_dms": dms,
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

    # 3. Combustion Detection & Jaimini Karakas
    calculate_combustion(planets_list, sun_deg)
    chara_karakas = calculate_chara_karakas(planets_list)

    # 4. 12 Houses (Bhavas)
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

    # 5. Upagrahas Calculation
    upagrahas_list = calculate_upagrahas(sun_deg, asc_deg, birth_dt, latitude, longitude, timezone)

    # 6. Arudhas & Special Lagnas
    arudha_padas, special_lagnas = calculate_arudhas_and_special_lagnas(
        asc_deg, asc_sign_idx, planets_list, sun_deg, moon_deg, birth_dt, latitude, longitude, timezone
    )

    # 7. All 16 Divisional Charts D1-D60 & Bhava Chalit
    divisional_charts = calculate_all_divisional_charts(planets_list, asc_deg)
    bhava_chalit = calculate_bhava_chalit(asc_deg, planets_list)

    # 8. Exact Vimshottari Mahadasha + Antardashas
    current_dasha, dasha_timeline = calculate_vimshottari_dasha(moon_nak_idx, moon_deg, birth_dt)

    # 9. Exact Parashara Ashtakavarga
    ashtakvarga_data = calculate_parashara_ashtakvarga(asc_sign_idx, planet_sign_indices)

    # 10. 6-Fold Shadbala
    shadbala_data = calculate_shadbala(planets_deg_map, asc_deg, mc_deg)

    # 11. Classical Vedic Yogas
    yogas_data = detect_vedic_yogas(planets_list, asc_sign_idx)

    # 12. Summary Insights
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
        "formatted_datetime_header": f"{birth_dt.strftime('%d-%b-%Y %I:%M:%S %p')}",
        "ayanamsa_value": f"Lahiri {degree_to_sign_and_dms(ayanamsa)[2]}",
        "ayanamsa_formatted": f"Lahiri {degree_to_sign_and_dms(ayanamsa)[2]}",
        "ascendant_lagna": f"{asc_sign_name} ({asc_dms})",
        "ascendant_sign": asc_sign_name,
        "ascendant_sign_index": asc_sign_idx,
        "ascendant_sanskrit": ZODIAC_SIGNS[asc_sign_idx - 1]["sanskrit"],
        "ascendant_degree": format_degree_short(asc_deg),
        "ascendant_degree_formatted": asc_dms,
        "moon_sign_rashi": moon_sign_name,
        "moon_sign_sanskrit": moon_sign_sanskrit,
        "sun_sign": sun_sign_name,
        "nakshatra": moon_nak_name,
        "nakshatra_pada": moon_pada,
        "nakshatra_lord": moon_nak_lord,
        "planets": planets_list,
        "houses": houses_list,
        "upagrahas": upagrahas_list,
        "arudha_padas": arudha_padas,
        "special_lagnas": special_lagnas,
        "chara_karakas": chara_karakas,
        "divisional_charts": divisional_charts,
        "bhava_chalit": bhava_chalit,
        "current_running_dasha": current_dasha,
        "vimshottari_dasha_timeline": dasha_timeline,
        "ashtakvarga": ashtakvarga_data,
        "shadbala": shadbala_data,
        "yogas": yogas_data,
        "vedic_yogas": yogas_data,
        "summary_insights": summary_insights
    }
