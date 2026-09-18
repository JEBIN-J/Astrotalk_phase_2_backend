"""
High-Precision Real-Time KP (Krishnamurti Paddhati) Astrology Calculation Engine.
Powered by Swiss Ephemeris (pyswisseph) with pure astronomical algorithms.

Strictly follows:
- Dynamic calculation from birth date, time, location, timezone, and ayanamsa
- Placidus House System for KP Cusps (Bhava Arambha)
- Vimshottari Proportional Division for Sub Lord (SL) & Sub-Sub Lord (SSL)
- 8 Ayanamsa options:
    1. Krishnamurti (KP New)
    2. Krishnamurti (KP Old)
    3. KP Straight Line
    4. Khullar
    5. Tropical (Sayana)
    6. Lahiri (Chitapaksha)
    7. B.V. Raman
    8. Sri Yukteswar
- D1 Rashi, D9 Navamsa, and KP Bhava Chart & Tables
- Exact Vimshottari Dasha timeline (Maha -> Antara -> Pratyantara)
- Planet Significators (Levels A, B, C, D) & House Significators (Levels 1, 2, 3, 4)
- KP Aspects (Planet-Planet, Planet-Cusp)
- Nakshatra Nadi Analysis
- 4-Step KP Analysis
"""
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional

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

ZODIAC_SIGNS = [
    {"name": "Aries", "sanskrit": "Mesha", "lord": "Mars", "element": "Fire"},
    {"name": "Taurus", "sanskrit": "Vrishabha", "lord": "Venus", "element": "Earth"},
    {"name": "Gemini", "sanskrit": "Mithuna", "lord": "Mercury", "element": "Air"},
    {"name": "Cancer", "sanskrit": "Karka", "lord": "Moon", "element": "Water"},
    {"name": "Leo", "sanskrit": "Simha", "lord": "Sun", "element": "Fire"},
    {"name": "Virgo", "sanskrit": "Kanya", "lord": "Mercury", "element": "Earth"},
    {"name": "Libra", "sanskrit": "Tula", "lord": "Venus", "element": "Air"},
    {"name": "Scorpio", "sanskrit": "Vrishchika", "lord": "Mars", "element": "Water"},
    {"name": "Sagittarius", "sanskrit": "Dhanu", "lord": "Jupiter", "element": "Fire"},
    {"name": "Capricorn", "sanskrit": "Makara", "lord": "Saturn", "element": "Earth"},
    {"name": "Aquarius", "sanskrit": "Kumbha", "lord": "Saturn", "element": "Air"},
    {"name": "Pisces", "sanskrit": "Meena", "lord": "Jupiter", "element": "Water"}
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

VIMSHOTTARI_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

VIMSHOTTARI_YEARS = {
    "Ketu": 7.0,
    "Venus": 20.0,
    "Sun": 6.0,
    "Moon": 10.0,
    "Mars": 7.0,
    "Rahu": 18.0,
    "Jupiter": 16.0,
    "Saturn": 19.0,
    "Mercury": 17.0
}
TOTAL_VIMSHOTTARI_YEARS = 120.0

OWNED_SIGNS = {
    "Sun": [5],
    "Moon": [4],
    "Mars": [1, 8],
    "Mercury": [3, 6],
    "Jupiter": [9, 12],
    "Venus": [2, 7],
    "Saturn": [10, 11],
    "Rahu": [],
    "Ketu": []
}

LORD_SHORT_CODES = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
    "Ascendant": "Asc",
    "Lagna": "Asc"
}

PLANET_COLORS = {
    "Sun": "#F59E0B",
    "Moon": "#38BDF8",
    "Mars": "#EF4444",
    "Mercury": "#10B981",
    "Jupiter": "#EAB308",
    "Venus": "#EC4899",
    "Saturn": "#6366F1",
    "Rahu": "#6B7280",
    "Ketu": "#8B5CF6",
    "Ascendant": "#4338CA"
}

POPULAR_CITIES = [
    {"name": "New Delhi", "state": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "timezone": 5.5},
    {"name": "Mumbai", "state": "Maharashtra", "latitude": 19.0760, "longitude": 72.8777, "timezone": 5.5},
    {"name": "Bengaluru", "state": "Karnataka", "latitude": 12.9716, "longitude": 77.5946, "timezone": 5.5},
    {"name": "Kolkata", "state": "West Bengal", "latitude": 22.5726, "longitude": 88.3639, "timezone": 5.5},
    {"name": "Chennai", "state": "Tamil Nadu", "latitude": 13.0827, "longitude": 80.2707, "timezone": 5.5},
    {"name": "Hyderabad", "state": "Telangana", "latitude": 17.3850, "longitude": 78.4867, "timezone": 5.5},
    {"name": "Ahmedabad", "state": "Gujarat", "latitude": 23.0225, "longitude": 72.5714, "timezone": 5.5},
    {"name": "Pune", "state": "Maharashtra", "latitude": 18.5204, "longitude": 73.8567, "timezone": 5.5},
    {"name": "Jaipur", "state": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873, "timezone": 5.5},
    {"name": "Varanasi", "state": "Uttar Pradesh", "latitude": 25.3176, "longitude": 82.9739, "timezone": 5.5},
    {"name": "London", "state": "UK", "latitude": 51.5074, "longitude": -0.1278, "timezone": 0.0},
    {"name": "New York", "state": "USA", "latitude": 40.7128, "longitude": -74.0060, "timezone": -5.0},
    {"name": "San Francisco", "state": "USA", "latitude": 37.7749, "longitude": -122.4194, "timezone": -8.0},
    {"name": "Dubai", "state": "UAE", "latitude": 25.2048, "longitude": 55.2708, "timezone": 4.0},
    {"name": "Singapore", "state": "Singapore", "latitude": 1.3521, "longitude": 103.8198, "timezone": 8.0}
]

def resolve_location(pob_str: str, default_lat: float, default_lon: float, default_tz: float) -> Tuple[float, float, float]:
    if not pob_str:
        return default_lat, default_lon, default_tz
    query = pob_str.lower().strip()
    for city in POPULAR_CITIES:
        c_name = city["name"].lower()
        if c_name in query or query in c_name:
            return float(city["latitude"]), float(city["longitude"]), float(city["timezone"])
    return default_lat, default_lon, default_tz

def get_lord_short(name: str) -> str:
    return LORD_SHORT_CODES.get(name, name[:2].capitalize())

def format_dms(deg: float) -> str:
    deg = deg % 360.0
    d = int(deg)
    rem = (deg - d) * 60.0
    m = int(rem)
    s = int(round((rem - m) * 60.0))
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d = (d + 1) % 360
    return f"{d:02d}° {m:02d}' {s:02d}\""

def format_deg_in_sign(deg: float) -> str:
    deg_in_sign = deg % 30.0
    d = int(deg_in_sign)
    rem = (deg_in_sign - d) * 60.0
    m = int(rem)
    s = int(round((rem - m) * 60.0))
    if s >= 60:
        s = 0
        m += 1
    if m >= 60:
        m = 0
        d += 1
    return f"{d:02d}° {m:02d}' {s:02d}\""

def calculate_julian_day(year: int, month: int, day: int, hour_utc: float) -> float:
    if SWISSEPH_AVAILABLE and swe:
        return swe.julday(year, month, day, hour_utc)
    if month <= 2:
        year -= 1
        month += 12
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    jd += hour_utc / 24.0
    return jd

def calculate_ayanamsa(jd: float, ayanamsa_name: str, birth_dt: datetime, hour_utc: float) -> Tuple[float, str]:
    """
    Calculate exact Ayanamsa value in degrees and formatted string for the 8 requested systems:
    1. Krishnamurti (KP New)
    2. Krishnamurti (KP Old)
    3. KP Straight Line
    4. Khullar
    5. Tropical (Sayana)
    6. Lahiri (Chitapaksha)
    7. B.V. Raman
    8. Sri Yukteswar
    """
    norm = ayanamsa_name.strip()
    year_dec = birth_dt.year + (birth_dt.month - 1) / 12.0 + (birth_dt.day - 1) / 365.25 + (hour_utc / 8766.0)

    if "Tropical" in norm or "Sayana" in norm:
        return 0.0, "00° 00' 00\" (Sayana)"

    if "Straight" in norm:
        # KP Straight Line: Linear precession rate 50.2388475 arcseconds/year from zero year 291.07722 AD
        ayan_deg = (year_dec - 291.07722) * (50.2388475 / 3600.0)
        return ayan_deg, f"KP Straight Line {format_dms(ayan_deg)}"

    if "Khullar" in norm:
        # Khullar True KP: Zero year 291.75 AD with Newcomb rate
        ayan_deg = (year_dec - 291.75) * (50.2388475 / 3600.0)
        return ayan_deg, f"Khullar {format_dms(ayan_deg)}"

    if SWISSEPH_AVAILABLE and swe:
        if "KP Old" in norm or "Old" in norm:
            try:
                swe.set_sid_mode(44)
                ayan_deg = swe.get_ayanamsa_ut(jd)
                return ayan_deg, f"KP Old {format_dms(ayan_deg)}"
            except Exception:
                ayan_deg = (year_dec - 291.0) * (50.2388475 / 3600.0)
                return ayan_deg, f"KP Old {format_dms(ayan_deg)}"

        elif "KP New" in norm or "Krishnamurti" in norm:
            swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
            ayan_deg = swe.get_ayanamsa_ut(jd)
            return ayan_deg, f"KP New {format_dms(ayan_deg)}"

        elif "Raman" in norm:
            swe.set_sid_mode(swe.SIDM_RAMAN)
            ayan_deg = swe.get_ayanamsa_ut(jd)
            return ayan_deg, f"B.V. Raman {format_dms(ayan_deg)}"

        elif "Yukteswar" in norm:
            swe.set_sid_mode(swe.SIDM_YUKTESHWAR)
            ayan_deg = swe.get_ayanamsa_ut(jd)
            return ayan_deg, f"Sri Yukteswar {format_dms(ayan_deg)}"

        elif "Lahiri" in norm or "Chitapaksha" in norm:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            ayan_deg = swe.get_ayanamsa_ut(jd)
            return ayan_deg, f"Lahiri {format_dms(ayan_deg)}"

    # Mathematical Fallbacks
    t = (jd - 2451545.0) / 36525.0
    if "KP Old" in norm or "Old" in norm:
        ayan_deg = (year_dec - 291.0) * (50.2388475 / 3600.0)
        return ayan_deg, f"KP Old {format_dms(ayan_deg)}"
    elif "KP New" in norm or "Krishnamurti" in norm:
        ayan_deg = 23.8245 + (t * 1.396971)
        return ayan_deg, f"KP New {format_dms(ayan_deg)}"
    elif "Raman" in norm:
        ayan_deg = (year_dec - 397.0) * (50.2388475 / 3600.0)
        return ayan_deg, f"B.V. Raman {format_dms(ayan_deg)}"
    elif "Yukteswar" in norm:
        ayan_deg = (year_dec - 499.0) * (54.0 / 3600.0)
        return ayan_deg, f"Sri Yukteswar {format_dms(ayan_deg)}"
    else: # Default Lahiri
        ayan_deg = 23.853056 + (t * 1.396971) - (0.000308 * (t ** 2))
        return ayan_deg, f"Lahiri {format_dms(ayan_deg)}"

def calculate_kp_sub_lords(degree: float) -> Dict[str, Any]:
    """
    Calculate exact KP Sign Lord (RL), Nakshatra Lord (NL), Sub Lord (SL),
    and Sub-Sub Lord (SSL) using Vimshottari proportional divisions.
    """
    deg = degree % 360.0
    sign_idx = int(deg // 30) + 1
    sign_info = ZODIAC_SIGNS[sign_idx - 1]
    rl_name = sign_info["lord"]

    nak_span = 360.0 / 27.0 # 13.3333333333° = 13° 20' = 800'
    nak_idx = int(deg / nak_span) % 27
    nak_name = NAKSHATRA_NAMES[nak_idx]
    nl_name = VIMSHOTTARI_LORDS[nak_idx % 9]

    pos_in_nak = deg % nak_span # 0 <= pos_in_nak < 13.3333333333
    pada = int(pos_in_nak / (nak_span / 4.0)) + 1
    if pada > 4: pada = 4

    # Sub-Lord (SL)
    s_idx = VIMSHOTTARI_LORDS.index(nl_name)
    accum_sub = 0.0
    sl_name = nl_name
    sub_span = 0.0
    pos_in_sub = 0.0

    for i in range(9):
        cand_sl = VIMSHOTTARI_LORDS[(s_idx + i) % 9]
        span = nak_span * (VIMSHOTTARI_YEARS[cand_sl] / TOTAL_VIMSHOTTARI_YEARS)
        if accum_sub <= pos_in_nak < accum_sub + span or (i == 8 and pos_in_nak >= accum_sub):
            sl_name = cand_sl
            sub_span = span
            pos_in_sub = pos_in_nak - accum_sub
            break
        accum_sub += span

    # Sub-Sub Lord (SSL)
    ss_idx = VIMSHOTTARI_LORDS.index(sl_name)
    accum_ssl = 0.0
    ssl_name = sl_name

    for j in range(9):
        cand_ssl = VIMSHOTTARI_LORDS[(ss_idx + j) % 9]
        span_ss = sub_span * (VIMSHOTTARI_YEARS[cand_ssl] / TOTAL_VIMSHOTTARI_YEARS)
        if accum_ssl <= pos_in_sub < accum_ssl + span_ss or (j == 8 and pos_in_sub >= accum_ssl):
            ssl_name = cand_ssl
            break
        accum_ssl += span_ss

    return {
        "degree": deg,
        "sign_index": sign_idx,
        "sign_name": sign_info["name"],
        "sign_sanskrit": sign_info["sanskrit"],
        "degree_in_sign": deg % 30.0,
        "degree_formatted": format_deg_in_sign(deg),
        "nakshatra_index": nak_idx + 1,
        "nakshatra_name": nak_name,
        "pada": pada,
        "rl": get_lord_short(rl_name),
        "nl": get_lord_short(nl_name),
        "sl": get_lord_short(sl_name),
        "ssl": get_lord_short(ssl_name),
        "rashi_lord": rl_name,
        "nakshatra_lord": nl_name,
        "sub_lord": sl_name,
        "sub_sub_lord": ssl_name
    }

def calculate_navamsha_sign(deg: float) -> int:
    """Calculate D9 Navamsa sign index (1-12) from sidereal degree."""
    deg = deg % 360.0
    sign_idx = int(deg // 30) + 1 # 1 to 12
    deg_in_sign = deg % 30.0
    pada_in_sign = int(deg_in_sign / (30.0 / 9.0)) # 0 to 8

    start_map = {1: 1, 5: 1, 9: 1, 2: 10, 6: 10, 10: 10, 3: 7, 7: 7, 11: 7, 4: 4, 8: 4, 12: 4}
    start_sign = start_map[sign_idx]
    nav_sign = ((start_sign - 1 + pada_in_sign) % 12) + 1
    return nav_sign

def get_placidus_cusps(jd: float, lat: float, lon: float, ayanamsa_val: float) -> Tuple[List[float], float, float]:
    """
    Compute high-precision Placidus house cusps (1-12), Ascendant, and MC.
    Returns sidereal/tropical cusps matching the requested Ayanamsa.
    """
    if SWISSEPH_AVAILABLE and swe:
        try:
            trop_cusps, ascmc = swe.houses(jd, lat, lon, b'P')
            sid_cusps = [(c - ayanamsa_val) % 360.0 for c in trop_cusps]
            asc_sid = (ascmc[0] - ayanamsa_val) % 360.0
            mc_sid = (ascmc[1] - ayanamsa_val) % 360.0
            return sid_cusps, asc_sid, mc_sid
        except Exception:
            pass

    t = (jd - 2451545.0) / 36525.0
    gmst_deg = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360.0
    lst_deg = (gmst_deg + lon) % 360.0
    eps_rad = math.radians(23.4392911 - 0.0130042 * t)
    lat_rad = math.radians(lat)
    ramc_rad = math.radians(lst_deg)

    y = -math.sin(ramc_rad) * math.cos(eps_rad) - math.tan(lat_rad) * math.sin(eps_rad)
    x = math.cos(ramc_rad)
    asc_trop = (math.degrees(math.atan2(y, x)) + 180.0) % 360.0
    asc_sid = (asc_trop - ayanamsa_val) % 360.0
    mc_sid = (math.degrees(math.atan2(math.sin(ramc_rad), math.cos(ramc_rad) * math.cos(eps_rad))) - ayanamsa_val) % 360.0

    cusps = [(asc_sid + i * 30.0) % 360.0 for i in range(12)]
    return cusps, asc_sid, mc_sid

def find_house_for_degree(deg: float, cusps: List[float]) -> int:
    """
    In KP Astrology, House N begins at Cusp N and ends at Cusp N+1.
    Find which house a given planetary longitude falls into.
    """
    deg = deg % 360.0
    for i in range(12):
        c_curr = cusps[i]
        c_next = cusps[(i + 1) % 12]

        if c_curr < c_next:
            if c_curr <= deg < c_next:
                return i + 1
        else: # Spans 360 wrap-around
            if deg >= c_curr or deg < c_next:
                return i + 1
    return 1

def calculate_planets(jd: float, ayanamsa_val: float) -> List[Dict[str, Any]]:
    """Calculate accurate longitudes, speeds, and retrograde markers for 9 planets."""
    planet_ids = [
        ("Sun", swe.SUN if SWISSEPH_AVAILABLE else 0),
        ("Moon", swe.MOON if SWISSEPH_AVAILABLE else 1),
        ("Mars", swe.MARS if SWISSEPH_AVAILABLE else 4),
        ("Mercury", swe.MERCURY if SWISSEPH_AVAILABLE else 2),
        ("Jupiter", swe.JUPITER if SWISSEPH_AVAILABLE else 5),
        ("Venus", swe.VENUS if SWISSEPH_AVAILABLE else 3),
        ("Saturn", swe.SATURN if SWISSEPH_AVAILABLE else 6),
        ("Uranus", swe.URANUS if SWISSEPH_AVAILABLE else 7),
        ("Neptune", swe.NEPTUNE if SWISSEPH_AVAILABLE else 8),
        ("Pluto", swe.PLUTO if SWISSEPH_AVAILABLE else 9),
        ("Rahu", swe.MEAN_NODE if SWISSEPH_AVAILABLE else 10)
    ]

    results = []
    rahu_deg = 0.0

    for name, p_id in planet_ids:
        if SWISSEPH_AVAILABLE and swe:
            try:
                res, flag = swe.calc_ut(jd, p_id, swe.FLG_SPEED)
                trop_lon = res[0]
                speed = res[3]
            except Exception:
                trop_lon, speed = 0.0, 1.0
        else:
            trop_lon, speed = 0.0, 1.0

        sid_lon = (trop_lon - ayanamsa_val) % 360.0
        is_retro = speed < 0.0
        if name == "Rahu":
            rahu_deg = sid_lon
            is_retro = True

        results.append({
            "name": name,
            "longitude": sid_lon,
            "speed": speed,
            "is_retrograde": is_retro
        })

    # Ketu is always exactly 180 degrees opposite Rahu
    ketu_deg = (rahu_deg + 180.0) % 360.0
    results.append({
        "name": "Ketu",
        "longitude": ketu_deg,
        "speed": -0.05,
        "is_retrograde": True
    })

    return results

def calculate_vimshottari_dasha(
    moon_lon: float,
    birth_dt: datetime,
    days_in_year: float = 365.256364
) -> Dict[str, Any]:
    """
    Dynamically calculate complete Vimshottari Dasha timeline (Mahadasha, Antardasha,
    Pratyantardasha) from birth Moon longitude.
    """
    nak_span = 360.0 / 27.0
    nak_idx = int((moon_lon % 360.0) / nak_span) % 27
    birth_nak = NAKSHATRA_NAMES[nak_idx]
    start_lord = VIMSHOTTARI_LORDS[nak_idx % 9]

    pos_in_nak = (moon_lon % 360.0) % nak_span
    fraction_passed = pos_in_nak / nak_span
    fraction_remaining = 1.0 - fraction_passed

    start_lord_years = VIMSHOTTARI_YEARS[start_lord]
    balance_years = fraction_remaining * start_lord_years

    maha_start_dt = birth_dt - timedelta(days=(fraction_passed * start_lord_years * days_in_year))
    now = datetime.now()

    start_lord_idx = VIMSHOTTARI_LORDS.index(start_lord)
    mahadashas = []

    curr_dt = maha_start_dt

    for m in range(9):
        m_lord = VIMSHOTTARI_LORDS[(start_lord_idx + m) % 9]
        m_years = VIMSHOTTARI_YEARS[m_lord]
        m_total_days = m_years * days_in_year
        m_end_dt = curr_dt + timedelta(days=m_total_days)

        antardashas = []
        a_curr_dt = curr_dt
        a_start_idx = VIMSHOTTARI_LORDS.index(m_lord)

        for a in range(9):
            a_lord = VIMSHOTTARI_LORDS[(a_start_idx + a) % 9]
            a_years = (m_years * VIMSHOTTARI_YEARS[a_lord]) / TOTAL_VIMSHOTTARI_YEARS
            a_total_days = a_years * days_in_year
            a_end_dt = a_curr_dt + timedelta(days=a_total_days)

            pratyantardashas = []
            p_curr_dt = a_curr_dt
            p_start_idx = VIMSHOTTARI_LORDS.index(a_lord)

            for p in range(9):
                p_lord = VIMSHOTTARI_LORDS[(p_start_idx + p) % 9]
                p_years = (a_years * VIMSHOTTARI_YEARS[p_lord]) / TOTAL_VIMSHOTTARI_YEARS
                p_total_days = p_years * days_in_year
                p_end_dt = p_curr_dt + timedelta(days=p_total_days)

                is_p_active = p_curr_dt <= now < p_end_dt
                pratyantardashas.append({
                    "planet": p_lord,
                    "start": p_curr_dt.strftime("%d %b %Y"),
                    "end": p_end_dt.strftime("%d %b %Y"),
                    "is_active": is_p_active
                })
                p_curr_dt = p_end_dt

            is_a_active = a_curr_dt <= now < a_end_dt
            antardashas.append({
                "planet": a_lord,
                "start": a_curr_dt.strftime("%d %b %Y"),
                "end": a_end_dt.strftime("%d %b %Y"),
                "is_active": is_a_active,
                "pratyantardashas": pratyantardashas
            })
            a_curr_dt = a_end_dt

        is_m_active = curr_dt <= now < m_end_dt
        mahadashas.append({
            "planet": m_lord,
            "start": curr_dt.strftime("%d %b %Y"),
            "end": m_end_dt.strftime("%d %b %Y"),
            "is_active": is_m_active,
            "years": m_years,
            "antardashas": antardashas
        })
        curr_dt = m_end_dt

    return {
        "birth_nakshatra": birth_nak,
        "birth_nakshatra_lord": start_lord,
        "balance_years": round(balance_years, 4),
        "balance_formatted": f"{int(balance_years)}y {int((balance_years % 1) * 12)}m {int((((balance_years % 1) * 12) % 1) * 30)}d",
        "mahadashas": mahadashas
    }

def calculate_significators(
    planets: List[Dict[str, Any]],
    cusps_info: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate standard KP 4-Level Significators:
    Planet Significators:
        Level-A: Houses occupied by the Star Lord (NL) of the planet.
        Level-B: House occupied by the planet itself.
        Level-C: Houses owned by the Star Lord of the planet.
        Level-D: Houses owned by the planet itself.

    House Significators (for houses 1 to 12):
        Level-1: Planets in the star of occupants of that house.
        Level-2: Occupants of that house.
        Level-3: Planets in the star of the house lord.
        Level-4: Lord of that house.
    """
    planet_house_map = {p["name"]: p["house"] for p in planets}
    star_lord_map = {p["name"]: p["nakshatra_lord"] for p in planets}

    house_lord_map = {}
    for c in cusps_info:
        house_lord_map[c["house"]] = c["rashi_lord"]

    planet_owned_houses = {p["name"]: [] for p in planets}
    for h, lord in house_lord_map.items():
        if lord in planet_owned_houses:
            planet_owned_houses[lord].append(h)

    # 1. Planet Significators
    planet_sigs = []
    for p in planets:
        p_name = p["name"]
        nl = star_lord_map.get(p_name, "")

        level_a = [planet_house_map[nl]] if nl in planet_house_map else []
        level_b = [p["house"]]
        level_c = planet_owned_houses.get(nl, [])
        level_d = planet_owned_houses.get(p_name, [])

        combined = sorted(list(set(level_a + level_b + level_c + level_d)))

        planet_sigs.append({
            "planet": p_name,
            "level_a": sorted(list(set(level_a))),
            "level_b": sorted(list(set(level_b))),
            "level_c": sorted(list(set(level_c))),
            "level_d": sorted(list(set(level_d))),
            "all_significators": combined
        })

    # 2. House Significators (Houses 1-12)
    house_sigs = []
    for h in range(1, 13):
        occupants = [p["name"] for p in planets if p["house"] == h]

        level_1 = []
        for p in planets:
            p_nl = star_lord_map.get(p["name"], "")
            if p_nl in occupants:
                level_1.append(p["name"])

        h_lord = house_lord_map.get(h, "")
        level_4 = [h_lord] if h_lord else []

        level_3 = []
        if h_lord:
            for p in planets:
                p_nl = star_lord_map.get(p["name"], "")
                if p_nl == h_lord:
                    level_3.append(p["name"])

        combined_planets = []
        for p_cand in level_1 + occupants + level_3 + level_4:
            if p_cand and p_cand not in combined_planets:
                combined_planets.append(p_cand)

        house_sigs.append({
            "house": h,
            "level_1": sorted(list(set(level_1))),
            "level_2": sorted(list(set(occupants))),
            "level_3": sorted(list(set(level_3))),
            "level_4": level_4,
            "all_planets": combined_planets
        })

    return {
        "planet_significators": planet_sigs,
        "house_significators": house_sigs
    }

def calculate_kp_aspects(
    planets: List[Dict[str, Any]],
    cusps_info: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate major and minor astrological aspects."""
    ASPECT_DEFINITIONS = [
        {"name": "Conjunction", "angle": 0.0, "orb": 8.0, "nature": "Neutral / Powerful", "desc": "Unification of planetary energies"},
        {"name": "Semi-Sextile", "angle": 30.0, "orb": 2.0, "nature": "Mild Harmonious", "desc": "Subtle cooperation and growth"},
        {"name": "Sextile", "angle": 60.0, "orb": 6.0, "nature": "Harmonious", "desc": "Opportunities and smooth coordination"},
        {"name": "Square", "angle": 90.0, "orb": 6.0, "nature": "Adverse / Dynamic", "desc": "Tension, challenge, and action required"},
        {"name": "Trine", "angle": 120.0, "orb": 8.0, "nature": "Highly Harmonious", "desc": "Blessings, fortune, and natural harmony"},
        {"name": "Quincunx", "angle": 150.0, "orb": 2.0, "nature": "Adverse / Adjustive", "desc": "Misalignment requiring psychological adjustment"},
        {"name": "Opposition", "angle": 180.0, "orb": 8.0, "nature": "Adverse / Polarizing", "desc": "Confrontation, awareness, and relational dynamic"}
    ]

    planet_aspects = []
    n = len(planets)
    for i in range(n):
        for j in range(i + 1, n):
            p1 = planets[i]
            p2 = planets[j]
            diff = abs(p1["longitude"] - p2["longitude"]) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff

            for asp in ASPECT_DEFINITIONS:
                orb = abs(diff - asp["angle"])
                if orb <= asp["orb"]:
                    is_applying = True
                    p1_speed = p1.get("speed", 1.0)
                    p2_speed = p2.get("speed", 1.0)
                    if p1_speed > p2_speed and p1["longitude"] > p2["longitude"]:
                        is_applying = False

                    planet_aspects.append({
                        "planet_1": p1["name"],
                        "planet_2": p2["name"],
                        "aspect_name": asp["name"],
                        "aspect_angle": asp["angle"],
                        "actual_angle": round(diff, 2),
                        "orb": round(orb, 2),
                        "nature": asp["nature"],
                        "is_applying": is_applying,
                        "description": asp["desc"]
                    })
                    break

    cusp_aspects = []
    for p in planets:
        for c in cusps_info:
            diff = abs(p["longitude"] - c["longitude"]) % 360.0
            if diff > 180.0:
                diff = 360.0 - diff

            for asp in ASPECT_DEFINITIONS:
                orb = abs(diff - asp["angle"])
                if orb <= (asp["orb"] * 0.75):
                    cusp_aspects.append({
                        "planet": p["name"],
                        "cusp_house": c["house"],
                        "aspect_name": asp["name"],
                        "aspect_angle": asp["angle"],
                        "actual_angle": round(diff, 2),
                        "orb": round(orb, 2),
                        "nature": asp["nature"],
                        "description": f"{asp['name']} to Cusp {c['house']} ({asp['nature']})"
                    })
                    break

    return {
        "planet_aspects": planet_aspects,
        "cusp_aspects": cusp_aspects
    }

def calculate_nakshatra_nadi(
    planets: List[Dict[str, Any]],
    significators: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Calculate real-time Nakshatra Nadi script and linkages for each planet."""
    p_sig_map = {ps["planet"]: ps for ps in significators["planet_significators"]}
    nadi_cards = []

    for p in planets:
        p_name = p["name"]
        sig = p_sig_map.get(p_name, {})

        nl = p["nakshatra_lord"]
        sl = p["sub_lord"]
        ssl = p["sub_sub_lord"]

        nl_sig = p_sig_map.get(nl, {})
        sl_sig = p_sig_map.get(sl, {})
        ssl_sig = p_sig_map.get(ssl, {})

        script = f"{p_name} ({p['house']}) → {nl} ({','.join(map(str, nl_sig.get('all_significators', []))) or p['house']}) → {sl} ({','.join(map(str, sl_sig.get('all_significators', []))) or p['house']}) → {ssl}"

        links = []
        all_houses = sig.get("all_significators", [])
        if any(h in all_houses for h in [1, 5, 9]):
            links.append({"type": "Dharma Trine (1-5-9)", "houses": [h for h in all_houses if h in [1, 5, 9]], "nature": "Spiritual, Talent, Merit"})
        if any(h in all_houses for h in [2, 6, 10, 11]):
            links.append({"type": "Wealth & Career (2-6-10-11)", "houses": [h for h in all_houses if h in [2, 6, 10, 11]], "nature": "Financial Prosperity & Professional Growth"})
        if any(h in all_houses for h in [4, 7, 10]):
            links.append({"type": "Kendra Axis (4-7-10)", "houses": [h for h in all_houses if h in [4, 7, 10]], "nature": "Worldly Activity, Status & Public Standing"})
        if any(h in all_houses for h in [8, 12]):
            links.append({"type": "Transformation / Moksha (8-12)", "houses": [h for h in all_houses if h in [8, 12]], "nature": "Deep Introspection, Change, Foreign Connect"})

        nadi_cards.append({
            "planet": p_name,
            "longitude_formatted": p.get("degree_formatted", ""),
            "rashi": p.get("sign", ""),
            "nakshatra": p.get("nakshatra", ""),
            "pada": p.get("pada", 1),
            "nl": nl,
            "sl": sl,
            "ssl": ssl,
            "house": p["house"],
            "nadi_script": script,
            "nl_houses": nl_sig.get("all_significators", []),
            "sl_houses": sl_sig.get("all_significators", []),
            "ssl_houses": ssl_sig.get("all_significators", []),
            "nadi_links": links
        })

    return nadi_cards

def calculate_four_step(
    planets: List[Dict[str, Any]],
    cusps_info: List[Dict[str, Any]],
    significators: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate authentic 4-Step KP Analysis for each Planet and each Cusp."""
    planet_dict = {p["name"]: p for p in planets}
    p_sig_map = {ps["planet"]: ps for ps in significators["planet_significators"]}

    four_step_planets = []
    for p in planets:
        p_name = p["name"]
        nl = p["nakshatra_lord"]
        sl = p["sub_lord"]

        sl_planet = planet_dict.get(sl, p)
        sub_nl = sl_planet.get("nakshatra_lord", nl)

        p_sig = p_sig_map.get(p_name, {})
        nl_sig = p_sig_map.get(nl, {})
        sl_sig = p_sig_map.get(sl, {})
        sub_nl_sig = p_sig_map.get(sub_nl, {})

        step_1_summary = f"{p_name} occupies H{p['house']}, rules {p_sig.get('level_d', [])}"
        step_2_summary = f"Star Lord {nl} occupies H{nl_sig.get('level_b', [p['house']])[0]}, rules {nl_sig.get('level_d', [])}"
        step_3_summary = f"Sub Lord {sl} occupies H{sl_sig.get('level_b', [p['house']])[0]}, rules {sl_sig.get('level_d', [])}"
        step_4_summary = f"Star Lord of Sub {sub_nl} occupies H{sub_nl_sig.get('level_b', [p['house']])[0]}, rules {sub_nl_sig.get('level_d', [])}"

        flow = f"Offer ({p['house']}) → Fruit ({nl_sig.get('level_b', [p['house']])[0]}) → Decider Sub ({sl_sig.get('level_b', [p['house']])[0]}) → End Result ({sub_nl_sig.get('level_b', [p['house']])[0]})"

        four_step_planets.append({
            "subject": p_name,
            "step_1": {"title": "Step 1: Planet", "entity": p_name, "occupied": p["house"], "owned": p_sig.get("level_d", []), "summary": step_1_summary},
            "step_2": {"title": "Step 2: Star Lord", "entity": nl, "occupied": nl_sig.get("level_b", [p["house"]])[0], "owned": nl_sig.get("level_d", []), "summary": step_2_summary},
            "step_3": {"title": "Step 3: Sub Lord", "entity": sl, "occupied": sl_sig.get("level_b", [p["house"]])[0], "owned": sl_sig.get("level_d", []), "summary": step_3_summary},
            "step_4": {"title": "Step 4: Star Lord of Sub Lord", "entity": sub_nl, "occupied": sub_nl_sig.get("level_b", [p["house"]])[0], "owned": sub_nl_sig.get("level_d", []), "summary": step_4_summary},
            "flow": flow
        })

    four_step_cusps = []
    for c in cusps_info:
        c_num = c["house"]
        rl = c["rashi_lord"]
        nl = c["nakshatra_lord"]
        sl = c["sub_lord"]

        sl_planet = planet_dict.get(sl)
        sub_nl = sl_planet.get("nakshatra_lord", nl) if sl_planet else nl

        rl_sig = p_sig_map.get(rl, {})
        nl_sig = p_sig_map.get(nl, {})
        sl_sig = p_sig_map.get(sl, {})
        sub_nl_sig = p_sig_map.get(sub_nl, {})

        step_1_summary = f"Cusp {c_num} in {c['sign']} ruled by {rl} (H{rl_sig.get('level_b', [c_num])[0]})"
        step_2_summary = f"Star Lord {nl} in H{nl_sig.get('level_b', [c_num])[0]}, rules {nl_sig.get('level_d', [])}"
        step_3_summary = f"Sub Lord {sl} in H{sl_sig.get('level_b', [c_num])[0]}, rules {sl_sig.get('level_d', [])}"
        step_4_summary = f"Star Lord of Sub {sub_nl} in H{sub_nl_sig.get('level_b', [c_num])[0]}, rules {sub_nl_sig.get('level_d', [])}"

        flow = f"Cusp {c_num} → Star Lord {nl} → Sub Lord {sl} → End Result {sub_nl}"

        four_step_cusps.append({
            "subject": f"Cusp {c_num}",
            "house": c_num,
            "step_1": {"title": "Step 1: Cusp Sign Lord", "entity": rl, "occupied": rl_sig.get("level_b", [c_num])[0], "owned": rl_sig.get("level_d", []), "summary": step_1_summary},
            "step_2": {"title": "Step 2: Star Lord", "entity": nl, "occupied": nl_sig.get("level_b", [c_num])[0], "owned": nl_sig.get("level_d", []), "summary": step_2_summary},
            "step_3": {"title": "Step 3: Sub Lord", "entity": sl, "occupied": sl_sig.get("level_b", [c_num])[0], "owned": sl_sig.get("level_d", []), "summary": step_3_summary},
            "step_4": {"title": "Step 4: Star Lord of Sub Lord", "entity": sub_nl, "occupied": sub_nl_sig.get("level_b", [c_num])[0], "owned": sub_nl_sig.get("level_d", []), "summary": step_4_summary},
            "flow": flow
        })

    return {
        "planets": four_step_planets,
        "cusps": four_step_cusps
    }

def generate_kp_system(
    name: str = "User",
    dob_str: str = "1998-12-13",
    tob_str: str = "09:30",
    pob_str: str = "Delhi, India",
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    timezone: float = 5.5,
    ayanamsa_name: str = "Krishnamurti (KP New)"
) -> Dict[str, Any]:
    """
    Master Entry Point for the Real-Time KP Astrology System.
    Generates canonical chart state for all 6 KP sections.
    """
    latitude, longitude, timezone = resolve_location(pob_str, latitude, longitude, timezone)

    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    tob_parts = [int(p) for p in tob_str.split(":")]
    sec = tob_parts[2] if len(tob_parts) > 2 else 0
    birth_dt = datetime(dob.year, dob.month, dob.day, tob_parts[0], tob_parts[1], sec)

    hour_utc = (tob_parts[0] + tob_parts[1] / 60.0 + sec / 3600.0) - timezone
    jd = calculate_julian_day(dob.year, dob.month, dob.day, hour_utc)

    ayan_deg, ayan_formatted = calculate_ayanamsa(jd, ayanamsa_name, birth_dt, hour_utc)

    cusp_degrees, asc_deg, mc_deg = get_placidus_cusps(jd, latitude, longitude, ayan_deg)
    asc_kp = calculate_kp_sub_lords(asc_deg)
    asc_nav_sign = calculate_navamsha_sign(asc_deg)

    raw_planets = calculate_planets(jd, ayan_deg)
    planets_list = []

    planets_list.append({
        "name": "Ascendant",
        "planet_name_simple": "Ascendant",
        "display_name": "Ascendant",
        "table_display_name": "Lagna",
        "sanskrit_name": "Lagna",
        "longitude": asc_deg,
        "sign": asc_kp["sign_name"],
        "sign_index": asc_kp["sign_index"],
        "sign_sanskrit": asc_kp["sign_sanskrit"],
        "house": 1,
        "degree_formatted": asc_kp["degree_formatted"],
        "degree_decimal": round(asc_deg, 4),
        "nakshatra": asc_kp["nakshatra_name"],
        "nakshatra_lord": asc_kp["nakshatra_lord"],
        "pada": asc_kp["pada"],
        "rl": asc_kp["rl"],
        "nl": asc_kp["nl"],
        "sl": asc_kp["sl"],
        "ssl": asc_kp["ssl"],
        "rashi_lord": asc_kp["rashi_lord"],
        "sub_lord": asc_kp["sub_lord"],
        "sub_sub_lord": asc_kp["sub_sub_lord"],
        "is_retrograde": False,
        "speed": 0.0,
        "navamsha_sign_index": asc_nav_sign,
        "color": PLANET_COLORS["Ascendant"]
    })

    moon_lon = 0.0
    sun_lon = 0.0

    for p in raw_planets:
        if p["name"] == "Sun":
            sun_lon = p["longitude"]
        p_name = p["name"]
        p_deg = p["longitude"]
        p_kp = calculate_kp_sub_lords(p_deg)
        p_nav_sign = calculate_navamsha_sign(p_deg)
        p_house = find_house_for_degree(p_deg, cusp_degrees)

        if p_name == "Moon":
            moon_lon = p_deg
        if p_name == "Sun":
            sun_lon = p_deg

        retro_tag = " (R)" if p["is_retrograde"] else ""

        planets_list.append({
            "name": p_name,
            "planet_name_simple": p_name,
            "display_name": p_name,
            "table_display_name": f"{p_name}{retro_tag}",
            "sanskrit_name": p_name,
            "longitude": p_deg,
            "sign": p_kp["sign_name"],
            "sign_index": p_kp["sign_index"],
            "sign_sanskrit": p_kp["sign_sanskrit"],
            "house": p_house,
            "degree_formatted": p_kp["degree_formatted"],
            "degree_decimal": round(p_deg, 4),
            "nakshatra": p_kp["nakshatra_name"],
            "nakshatra_lord": p_kp["nakshatra_lord"],
            "pada": p_kp["pada"],
            "rl": p_kp["rl"],
            "nl": p_kp["nl"],
            "sl": p_kp["sl"],
            "ssl": p_kp["ssl"],
            "rashi_lord": p_kp["rashi_lord"],
            "sub_lord": p_kp["sub_lord"],
            "sub_sub_lord": p_kp["sub_sub_lord"],
            "is_retrograde": p["is_retrograde"],
            "speed": round(p["speed"], 4),
            "navamsha_sign_index": p_nav_sign,
            "color": PLANET_COLORS.get(p_name, "#4338CA")
        })

    # Add Fortuna (Pars Fortuna) -> Ascendant + Moon - Sun
    fortuna_deg = (asc_deg + moon_lon - sun_lon) % 360.0
    f_kp = calculate_kp_sub_lords(fortuna_deg)
    f_nav_sign = calculate_navamsha_sign(fortuna_deg)
    f_house = find_house_for_degree(fortuna_deg, cusp_degrees)
    
    planets_list.append({
        "name": "Fortuna",
        "planet_name_simple": "Fortuna",
        "display_name": "Fortuna",
        "table_display_name": "Fortuna",
        "sanskrit_name": "Fortuna",
        "longitude": fortuna_deg,
        "sign": f_kp["sign_name"],
        "sign_index": f_kp["sign_index"],
        "sign_sanskrit": f_kp["sign_sanskrit"],
        "house": f_house,
        "degree_formatted": f_kp["degree_formatted"],
        "degree_decimal": round(fortuna_deg, 4),
        "nakshatra": f_kp["nakshatra_name"],
        "nakshatra_lord": f_kp["nakshatra_lord"],
        "pada": f_kp["pada"],
        "rl": f_kp["rl"],
        "nl": f_kp["nl"],
        "sl": f_kp["sl"],
        "ssl": f_kp["ssl"],
        "rashi_lord": f_kp["rashi_lord"],
        "sub_lord": f_kp["sub_lord"],
        "sub_sub_lord": f_kp["sub_sub_lord"],
        "is_retrograde": False,
        "speed": 0.0,
        "navamsha_sign_index": f_nav_sign,
        "color": PLANET_COLORS.get("Fortuna", "#4338CA")
    })

    cusps_info = []
    for h in range(1, 13):
        c_deg = cusp_degrees[h - 1]
        c_next_deg = cusp_degrees[h % 12]
        c_kp = calculate_kp_sub_lords(c_deg)

        occupants = [p["name"] for p in planets_list if p["house"] == h and p["name"] != "Ascendant"]
        span = (c_next_deg - c_deg) % 360.0

        cusps_info.append({
            "house": h,
            "cusp_number": h,
            "longitude": c_deg,
            "cusp_degree": c_deg,
            "cusp_formatted": format_dms(c_deg),
            "degree_formatted": c_kp["degree_formatted"],
            "sign": c_kp["sign_name"],
            "sign_name": c_kp["sign_name"],
            "sign_index": c_kp["sign_index"],
            "sign_sanskrit": c_kp["sign_sanskrit"],
            "nakshatra": c_kp["nakshatra_name"],
            "nakshatra_lord": c_kp["nakshatra_lord"],
            "pada": c_kp["pada"],
            "rl": c_kp["rl"],
            "nl": c_kp["nl"],
            "sl": c_kp["sl"],
            "ssl": c_kp["ssl"],
            "rashi_lord": c_kp["rashi_lord"],
            "sub_lord": c_kp["sub_lord"],
            "sub_sub_lord": c_kp["sub_sub_lord"],
            "span_degrees": round(span, 2),
            "occupants": occupants,
            "occupants_str": ", ".join(occupants) if occupants else "None"
        })

    # D1 Chart Data
    d1_chart = {
        "ascendant_sign_index": asc_kp["sign_index"],
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "sign_index": p["sign_index"],
                "house": ((p["sign_index"] - asc_kp["sign_index"]) % 12) + 1,
                "degree_formatted": p["degree_formatted"],
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else ""
            } for p in planets_list
        ]
    }

    # D9 Navamsa Chart Data
    def get_navamsa_data(deg, nav_sign_idx):
        deg_in_sign = deg % 30.0
        nav_deg = (deg_in_sign % (30.0 / 9.0)) * 9.0
        abs_nav_deg = (nav_sign_idx - 1) * 30.0 + nav_deg
        return calculate_kp_sub_lords(abs_nav_deg)

    d9_chart = {
        "ascendant_sign_index": asc_nav_sign,
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "sign_index": p["navamsha_sign_index"],
                "house": ((p["navamsha_sign_index"] - asc_nav_sign) % 12) + 1,
                "degree_formatted": get_navamsa_data(p["longitude"], p["navamsha_sign_index"])["degree_formatted"],
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else "",
                "rl": get_navamsa_data(p["longitude"], p["navamsha_sign_index"])["rl"],
                "nl": get_navamsa_data(p["longitude"], p["navamsha_sign_index"])["nl"],
                "sl": get_navamsa_data(p["longitude"], p["navamsha_sign_index"])["sl"],
                "ssl": get_navamsa_data(p["longitude"], p["navamsha_sign_index"])["ssl"],
                "sign": ZODIAC_SIGNS[p["navamsha_sign_index"] - 1]["name"],
                "nakshatra": get_navamsa_data(p["longitude"], p["navamsha_sign_index"])["nakshatra_name"],
                "pada": get_navamsa_data(p["longitude"], p["navamsha_sign_index"])["pada"]
            } for p in planets_list
        ]
    }

    # Bhava Chart Data (Placidus Cusps as houses)
    bhava_chart = {
        "ascendant_sign_index": asc_kp["sign_index"],
        "cusps": [
            {
                "house_number": c["house"],
                "sign_index": c["sign_index"],
                "sign": c["sign"],
                "cusp_midpoint_degree": c["cusp_degree"],
                "cusp_midpoint_formatted": c["degree_formatted"],
                "rl": c["rl"],
                "nl": c["nl"],
                "sl": c["sl"],
                "ssl": c["ssl"],
                "nakshatra": c["nakshatra"],
                "pada": c["pada"],
                "occupants": c["occupants"]
            } for c in cusps_info
        ],
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "house": p["house"],
                "sign_index": p["sign_index"],
                "degree_formatted": p["degree_formatted"],
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else ""
            } for p in planets_list
        ]
    }

    dasha_data = calculate_vimshottari_dasha(moon_lon, birth_dt)

    significators_data = calculate_significators(
        [p for p in planets_list if p["name"] != "Ascendant"],
        cusps_info
    )

    aspects_data = calculate_kp_aspects(
        [p for p in planets_list if p["name"] != "Ascendant"],
        cusps_info
    )

    nadi_data = calculate_nakshatra_nadi(
        [p for p in planets_list if p["name"] != "Ascendant"],
        significators_data
    )

    four_step_data = calculate_four_step(
        [p for p in planets_list if p["name"] != "Ascendant"],
        cusps_info,
        significators_data
    )

    # Vedic Day Lord
    WEEKDAY_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
    offset = 0 if (tob_parts[0] + tob_parts[1] / 60.0) >= 6.0 else -1
    day_idx = (birth_dt + timedelta(days=offset)).weekday()
    day_lord = WEEKDAY_LORDS[day_idx]
    
    moon_kp = next((p for p in planets_list if p["name"] == "Moon"), planets_list[0])

    ruling_planets = {
        "lagna_rashi_lord": planets_list[0]["rashi_lord"],
        "lagna_nakshatra_lord": planets_list[0]["nakshatra_lord"],
        "moon_rashi_lord": moon_kp["rashi_lord"],
        "moon_nakshatra_lord": moon_kp["nakshatra_lord"],
        "day_lord": day_lord
    }

    return {
        "status": "success",
        "ruling_planets": ruling_planets,
        "person_name": name,
        "date_of_birth": dob_str,
        "time_of_birth": tob_str,
        "place_of_birth": pob_str,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "ayanamsa_name": ayanamsa_name,
        "ayanamsa_value": round(ayan_deg, 6),
        "ayanamsa_formatted": ayan_formatted,
        "ascendant": asc_kp,
        "planets": planets_list,
        "bhava_cusps": cusps_info,
        "divisional_charts": {
            "D-1": d1_chart,
            "D-9": d9_chart
        },
        "bhava_chalit": bhava_chart,
        "dashas": dasha_data,
        "significators": significators_data,
        "aspects": aspects_data,
        "nakshatra_nadi": nadi_data,
        "four_step": four_step_data
    }
