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
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional

try:
    from app.services.vedic_engine import _SWE_AYANAMSA_LOCK, calculate_all_divisional_charts, calculate_parashara_ashtakvarga, set_swisseph_sidereal_mode, calculate_lahiri_ayanamsa
except ImportError:
    _SWE_AYANAMSA_LOCK = threading.Lock()

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

def calculate_ayanamsa(jd: float, ayanamsa_name: str, birth_dt: datetime = None, hour_utc: float = None) -> Tuple[float, str]:
    """
    Calculate exact Ayanamsa value in degrees and formatted string for all supported systems:
    LAHIRI, BV_RAMAN, KP_OLD, SRI_YUKTESWAR, DE_LUCE, USHA_SHASHI, DJWHAL_KHOOL, JN_BHASIN, FAGAN_BRADLEY, TROPICAL,
    KP_NEW, KP_STRAIGHT_LINE, KHULLAR, CHANDRA_HARI
    """
    norm = ayanamsa_name.strip().upper() if ayanamsa_name else "KP_NEW"
    
    key_map = {
        "KRISHNAMURTI (KP NEW)": "KP_NEW",
        "KRISHNAMURTI (KP OLD)": "KP_OLD",
        "KP STRAIGHT LINE": "KP_STRAIGHT_LINE",
        "KHULLAR": "KHULLAR",
        "TROPICAL (SAYANA)": "TROPICAL",
        "LAHIRI (CHITAPAKSHA)": "LAHIRI",
        "LAHIRI (CHITRAPAKSHA)": "LAHIRI",
        "B.V. RAMAN": "BV_RAMAN",
        "SRI YUKTESWAR": "SRI_YUKTESWAR",
        "DE LUCE": "DE_LUCE",
        "USHA SHASHI": "USHA_SHASHI",
        "USHA-SHASHI": "USHA_SHASHI",
        "DJWHAL KHOOL": "DJWHAL_KHOOL",
        "J.N. BHASIN": "JN_BHASIN",
        "FAGAN BRADLEY": "FAGAN_BRADLEY",
        "FAGAN-BRADLEY": "FAGAN_BRADLEY",
        "CHANDRA HARI": "CHANDRA_HARI",
    }
    if norm in key_map:
        norm = key_map[norm]
        
    valid_keys = [
        "LAHIRI", "BV_RAMAN", "KP_OLD", "SRI_YUKTESWAR", "DE_LUCE",
        "USHA_SHASHI", "DJWHAL_KHOOL", "JN_BHASIN", "FAGAN_BRADLEY",
        "TROPICAL", "KP_NEW", "KP_STRAIGHT_LINE", "KHULLAR", "CHANDRA_HARI"
    ]
    if norm not in valid_keys:
        norm = "KP_NEW"
        
    if norm in ("TROPICAL", "SAYANA"):
        return 0.0, "00° 00' 00\" (Sayana)"

    from app.services.vedic_engine import calculate_lahiri_ayanamsa
    try:
        ayan_deg = calculate_lahiri_ayanamsa(jd, ayanamsa_key=norm)
        return float(ayan_deg), f"{norm} {format_dms(float(ayan_deg))}"
    except Exception:
        t = (jd - 2451545.0) / 36525.0
        if norm == "KP_OLD":
            ayan_deg = 23.76024 + (t * 1.396971)
        elif norm == "BV_RAMAN":
            ayan_deg = 22.41079 + (t * 1.396971)
        elif norm == "SRI_YUKTESWAR":
            ayan_deg = 22.85279 + (t * 1.396971)
        elif norm == "KP_NEW":
            ayan_deg = 23.78036 + (t * 1.396971)
        elif norm == "KP_STRAIGHT_LINE":
            ayan_deg = 23.84842 + (t * 1.395524)
        elif norm == "KHULLAR":
            ayan_deg = 23.83903 + (t * 1.395524)
        else:
            ayan_deg = 23.85709 + (t * 1.396971) - (0.000308 * (t ** 2))
        return float(ayan_deg), f"{norm} {format_dms(float(ayan_deg))}"

def calculate_kp_sub_lords(degree: float) -> Dict[str, Any]:
    """
    Calculate exact KP Sign Lord (RL), Nakshatra Lord (NL), Sub Lord (SL),
    and Sub-Sub Lord (SSL) using Vimshottari proportional divisions.
    Preserves full precision across all 360 degrees and at boundary conditions.
    """
    deg = float(degree) % 360.0
    sign_idx = int(deg // 30) + 1
    if sign_idx > 12: sign_idx = 12
    sign_info = ZODIAC_SIGNS[sign_idx - 1]
    rl_name = sign_info["lord"]

    nak_span = 360.0 / 27.0 # 13.333333333333334 degrees = 800 arcminutes
    nak_idx = int(deg / nak_span)
    if nak_idx >= 27: nak_idx = 26
    nak_name = NAKSHATRA_NAMES[nak_idx]
    nl_name = VIMSHOTTARI_LORDS[nak_idx % 9]

    pos_in_nak = deg - (nak_idx * nak_span)
    if pos_in_nak < 0.0: pos_in_nak = 0.0
    if pos_in_nak >= nak_span: pos_in_nak = nak_span - 1e-12

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
        if i == 8 or (accum_sub <= pos_in_nak < accum_sub + span):
            sl_name = cand_sl
            sub_span = span
            pos_in_sub = max(0.0, pos_in_nak - accum_sub)
            break
        accum_sub += span

    # Sub-Sub Lord (SSL)
    ss_idx = VIMSHOTTARI_LORDS.index(sl_name)
    accum_ssl = 0.0
    ssl_name = sl_name

    for j in range(9):
        cand_ssl = VIMSHOTTARI_LORDS[(ss_idx + j) % 9]
        span_ss = sub_span * (VIMSHOTTARI_YEARS[cand_ssl] / TOTAL_VIMSHOTTARI_YEARS)
        if j == 8 or (accum_ssl <= pos_in_sub < accum_ssl + span_ss):
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
    deg = float(deg) % 360.0
    sign_idx = int(deg // 30) + 1
    deg_in_sign = deg % 30.0
    pada = int(deg_in_sign / (30.0 / 9.0))
    if pada > 8: pada = 8
    sign_element = (sign_idx - 1) % 4
    if sign_element == 0: start_sign = 1
    elif sign_element == 1: start_sign = 10
    elif sign_element == 2: start_sign = 7
    else: start_sign = 4
    return ((start_sign - 1 + pada) % 12) + 1

def get_placidus_cusps(jd: float, lat: float, lon: float, is_sidereal: bool = True) -> Tuple[List[float], float, float]:
    """
    Compute high-precision Placidus house cusps (1-12), Ascendant, and MC
    directly via Swiss Ephemeris.
    """
    if SWISSEPH_AVAILABLE and swe:
        try:
            flags = swe.FLG_SIDEREAL if is_sidereal else 0
            cusps, ascmc = swe.houses_ex(jd, lat, lon, b'P', flags)
            sid_cusps = [float(c % 360.0) for c in cusps]
            asc_sid = float(ascmc[0] % 360.0)
            mc_sid = float(ascmc[1] % 360.0)
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
    mc_trop = (math.degrees(math.atan2(math.sin(ramc_rad), math.cos(ramc_rad) * math.cos(eps_rad)))) % 360.0
    cusps = [(asc_trop + i * 30.0) % 360.0 for i in range(12)]
    return cusps, asc_trop, mc_trop


def get_horary_placidus_cusps(asc_sidereal: float, lat: float, aya: float, jd: float) -> Tuple[List[float], float, float]:
    """
    Compute KP Horary Placidus house cusps where Cusp 1 (Ascendant) is fixed
    by the Horary Seed Number, and Cusps 2-12 are calculated via Placidus
    house division for the query latitude using Swiss Ephemeris.
    """
    asc_sidereal = float(asc_sidereal) % 360.0
    if SWISSEPH_AVAILABLE and swe:
        try:
            asc_trop = (asc_sidereal + aya) % 360.0
            t = (jd - 2451545.0) / 36525.0
            eps = 23.4392911 - 0.0130042 * t
            best_armc = 0.0
            best_diff = 999.0
            for deg in range(0, 360):
                cusps, ascmc = swe.houses_armc(float(deg), lat, eps, b'P')
                diff = abs((ascmc[0] - asc_trop + 180.0) % 360.0 - 180.0)
                if diff < best_diff:
                    best_diff = diff
                    best_armc = float(deg)
            low = best_armc - 1.0
            high = best_armc + 1.0
            for _ in range(25):
                mid = (low + high) / 2.0
                cusps, ascmc = swe.houses_armc(mid, lat, eps, b'P')
                diff = (ascmc[0] - asc_trop + 180.0) % 360.0 - 180.0
                if abs(diff) < 1e-6:
                    best_armc = mid
                    break
                cusps2, ascmc2 = swe.houses_armc(mid + 0.001, lat, eps, b'P')
                slope = ((ascmc2[0] - ascmc[0] + 180.0) % 360.0 - 180.0) / 0.001
                if slope > 0:
                    if diff < 0: low = mid
                    else: high = mid
                else:
                    if diff < 0: high = mid
                    else: low = mid
                best_armc = mid
            cusps, ascmc = swe.houses_armc(best_armc, lat, eps, b'P')
            sid_cusps = [float((c - aya) % 360.0) for c in cusps]
            sid_cusps[0] = asc_sidereal
            mc_sid = float((ascmc[1] - aya) % 360.0)
            return sid_cusps, asc_sidereal, mc_sid
        except Exception:
            pass

    cusps = [(asc_sidereal + i * 30.0) % 360.0 for i in range(12)]
    mc = (asc_sidereal + 270.0) % 360.0
    return cusps, asc_sidereal, mc

def find_house_for_degree(deg: float, cusps: List[float]) -> int:
    """
    In KP Astrology, House N begins at Cusp N and ends at Cusp N+1.
    Find which house a given planetary longitude falls into.
    """
    deg = float(deg) % 360.0
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

def calculate_planets(jd: float, is_sidereal: bool = True, node_type: str = "true") -> List[Dict[str, Any]]:
    """Calculate accurate longitudes, speeds, and retrograde markers for planets."""
    rahu_node_id = (swe.TRUE_NODE if node_type == "true" else swe.MEAN_NODE) if SWISSEPH_AVAILABLE and swe else 10
    planet_ids = [
        ("Sun", swe.SUN if SWISSEPH_AVAILABLE and swe else 0),
        ("Moon", swe.MOON if SWISSEPH_AVAILABLE and swe else 1),
        ("Mars", swe.MARS if SWISSEPH_AVAILABLE and swe else 4),
        ("Mercury", swe.MERCURY if SWISSEPH_AVAILABLE and swe else 2),
        ("Jupiter", swe.JUPITER if SWISSEPH_AVAILABLE and swe else 5),
        ("Venus", swe.VENUS if SWISSEPH_AVAILABLE and swe else 3),
        ("Saturn", swe.SATURN if SWISSEPH_AVAILABLE and swe else 6),
        ("Rahu", rahu_node_id),
        ("Uranus", swe.URANUS if SWISSEPH_AVAILABLE and swe else 7),
        ("Neptune", swe.NEPTUNE if SWISSEPH_AVAILABLE and swe else 8),
        ("Pluto", swe.PLUTO if SWISSEPH_AVAILABLE and swe else 9)
    ]

    flags = swe.FLG_SWIEPH | swe.FLG_SPEED | (swe.FLG_SIDEREAL if is_sidereal else 0) if SWISSEPH_AVAILABLE and swe else 0
    results = []
    rahu_deg = 0.0

    for name, p_id in planet_ids:
        if SWISSEPH_AVAILABLE and swe:
            try:
                res, flag = swe.calc_ut(jd, p_id, flags)
                lon = float(res[0] % 360.0)
                speed = float(res[3])
                is_retro = bool(speed < 0.0)
            except Exception:
                lon, speed, is_retro = 0.0, 1.0, False
        else:
            lon, speed, is_retro = 0.0, 1.0, False

        if name == "Rahu":
            rahu_deg = lon
            is_retro = True

        results.append({
            "name": name,
            "longitude": lon,
            "speed": speed,
            "is_retrograde": is_retro
        })

    # Ketu is always exactly 180 degrees opposite Rahu
    ketu_deg = float((rahu_deg + 180.0) % 360.0)
    results.append({
        "name": "Ketu",
        "longitude": ketu_deg,
        "speed": results[-1]["speed"] if results else -0.05,
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
        {"name": "Conjunction", "short_name": "Conj", "angle": 0.0, "orb": 15.0, "nature": "Yellow"},
        {"name": "Vigintile", "short_name": "Vigi", "angle": 18.0, "orb": 2.0, "nature": "Green"},
        {"name": "Quin-decile", "short_name": "Qdec", "angle": 24.0, "orb": 2.0, "nature": "Green"},
        {"name": "Semi-Sextile", "short_name": "Semi", "angle": 30.0, "orb": 2.0, "nature": "Green"},
        {"name": "Semi-quintile", "short_name": "Squi", "angle": 36.0, "orb": 2.0, "nature": "Green"},
        {"name": "Semi-Square", "short_name": "Ssqu", "angle": 45.0, "orb": 4.0, "nature": "LightRed"},
        {"name": "Degrees 54", "short_name": "D54", "angle": 54.0, "orb": 2.0, "nature": "LightRed"},
        {"name": "Sextile", "short_name": "Sext", "angle": 60.0, "orb": 6.0, "nature": "Green"},
        {"name": "Quintile", "short_name": "Quin", "angle": 72.0, "orb": 4.0, "nature": "Green"},
        {"name": "Square", "short_name": "Squr", "angle": 90.0, "orb": 9.0, "nature": "Red"},
        {"name": "Tredecile", "short_name": "Tred", "angle": 108.0, "orb": 3.0, "nature": "Green"},
        {"name": "Trine", "short_name": "Trin", "angle": 120.0, "orb": 9.0, "nature": "DarkGreen"},
        {"name": "Degrees 126", "short_name": "D126", "angle": 126.0, "orb": 2.0, "nature": "DarkGreen"},
        {"name": "Sesquiquadrate", "short_name": "Ssqu", "angle": 135.0, "orb": 3.0, "nature": "LightRed"},
        {"name": "Bi-quintile", "short_name": "Bqui", "angle": 144.0, "orb": 3.0, "nature": "DarkGreen"},
        {"name": "Quincunx", "short_name": "Quin", "angle": 150.0, "orb": 3.0, "nature": "Red"},
        {"name": "Degree 162", "short_name": "D162", "angle": 162.0, "orb": 2.0, "nature": "Green"},
        {"name": "Opposition", "short_name": "Oppn", "angle": 180.0, "orb": 15.0, "nature": "Red"}
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
                        "short_name": asp.get("short_name", asp["name"][:4]),
                        "aspect_angle": asp["angle"],
                        "actual_angle": round(diff, 2),
                        "orb": round(orb, 2),
                        "strength": round(asp["orb"] - orb, 2),
                        "nature": asp["nature"],
                        "is_applying": is_applying,
                        "description": asp.get("desc", "")
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

        script = f"{p_name} ({p['house']}) -> {nl} ({','.join(map(str, nl_sig.get('all_significators', []))) or p['house']}) -> {sl} ({','.join(map(str, sl_sig.get('all_significators', []))) or p['house']}) -> {ssl}"

        links = []
        all_houses = set(sig.get("all_significators", []))
        if len(all_houses.intersection({1, 5, 9})) >= 2:
            links.append({"type": "Dharma Trine (1-5-9)", "houses": list(all_houses.intersection({1, 5, 9})), "nature": "Spiritual, Talent, Merit"})
        if len(all_houses.intersection({2, 6, 10, 11})) >= 2:
            links.append({"type": "Wealth & Career (2-6-10-11)", "houses": list(all_houses.intersection({2, 6, 10, 11})), "nature": "Financial Prosperity & Professional Growth"})
        if len(all_houses.intersection({4, 7, 10})) >= 2:
            links.append({"type": "Kendra Axis (4-7-10)", "houses": list(all_houses.intersection({4, 7, 10})), "nature": "Worldly Activity, Status & Public Standing"})
        if len(all_houses.intersection({8, 12})) == 2:
            links.append({"type": "Transformation / Moksha (8-12)", "houses": list(all_houses.intersection({8, 12})), "nature": "Deep Introspection, Change, Foreign Connect"})

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

        flow = f"Offer ({p['house']}) -> Fruit ({nl_sig.get('level_b', [p['house']])[0]}) -> Decider Sub ({sl_sig.get('level_b', [p['house']])[0]}) -> End Result ({sub_nl_sig.get('level_b', [p['house']])[0]})"

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

        flow = f"Cusp {c_num} -> Star Lord {nl} -> Sub Lord {sl} -> End Result {sub_nl}"

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
    dob_str: str = "",
    tob_str: str = "",
    pob_str: str = "Delhi, India",
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    timezone: float = 5.5,
    ayanamsa_name: str = "Krishnamurti (KP New)",
    transit_datetime_str: str = None,
    transit_timezone: float = None,
    transit_latitude: float = None,
    transit_longitude: float = None,
    node_type: str = "true",
    horary_number: Optional[int] = None,
    horary_mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    Master Entry Point for the Real-Time KP Astrology System.
    Generates authoritative chart state for all KP sections,
    strictly distinguishing inner Natal chart and outer Transit chart.
    """
    latitude, longitude, timezone = resolve_location(pob_str, latitude, longitude, timezone)

    # 1. Parse Natal Birth Details
    dob = datetime.strptime(dob_str, "%Y-%m-%d") if dob_str else datetime(2000, 1, 1)
    tob_parts = [int(p) for p in tob_str.split(":")] if tob_str else [12, 0, 0]
    sec = tob_parts[2] if len(tob_parts) > 2 else 0
    birth_dt = datetime(dob.year, dob.month, dob.day, tob_parts[0], tob_parts[1], sec)

    natal_utc_dt = birth_dt - timedelta(hours=timezone)
    natal_hour_utc = natal_utc_dt.hour + natal_utc_dt.minute / 60.0 + natal_utc_dt.second / 3600.0 + natal_utc_dt.microsecond / 3600000000.0
    jd_natal = swe.julday(natal_utc_dt.year, natal_utc_dt.month, natal_utc_dt.day, natal_hour_utc) if (SWISSEPH_AVAILABLE and swe) else calculate_julian_day(natal_utc_dt.year, natal_utc_dt.month, natal_utc_dt.day, natal_hour_utc)

    # Determine Sidereal Mode
    norm_ayanamsa = ayanamsa_name.strip().upper() if ayanamsa_name else "KP_NEW"
    is_sidereal = (norm_ayanamsa not in ("TROPICAL", "SAYANA"))
    ayan_deg, ayan_formatted = calculate_ayanamsa(jd_natal, ayanamsa_name)

    # Calculate Natal Cusps, Ascendant, and Planets with Thread Lock
    with _SWE_AYANAMSA_LOCK:
        set_swisseph_sidereal_mode(ayanamsa_name)
        if horary_number is not None and str(horary_number).strip() != '' and horary_mode != 'current_time':
            from app.api.v1.horary import KP_249_TABLE, KP_2193_TABLE
            num = int(horary_number)
            if horary_mode == 'range_2193' or num > 249:
                if 1 <= num <= len(KP_2193_TABLE):
                    target_asc = KP_2193_TABLE[num - 1]['start']
                else:
                    target_asc = KP_2193_TABLE[0]['start']
            elif 1 <= num <= len(KP_249_TABLE):
                target_asc = KP_249_TABLE[num - 1]['start']
            else:
                target_asc = KP_249_TABLE[0]['start']
            cusp_degrees, asc_deg, mc_deg = get_horary_placidus_cusps(target_asc, latitude, ayan_deg, jd_natal)
        else:
            cusp_degrees, asc_deg, mc_deg = get_placidus_cusps(jd_natal, latitude, longitude, is_sidereal)
        raw_planets = calculate_planets(jd_natal, is_sidereal, node_type=node_type)

    asc_kp = calculate_kp_sub_lords(asc_deg)
    asc_nav_sign = calculate_navamsha_sign(asc_deg)

    planets_list = []
    planets_list.append({
        "name": "Ascendant",
        "planet_name_simple": "Ascendant",
        "display_name": "Ascendant",
        "table_display_name": "Lagna",
        "sanskrit_name": "Lagna",
        "longitude": asc_deg,
        "sign": asc_kp["sign_name"],
        "sign_name": asc_kp["sign_name"],
        "sign_index": asc_kp["sign_index"],
        "sign_id": asc_kp["sign_index"],
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
        p_name = p["name"]
        p_deg = p["longitude"]
        if p_name == "Sun":
            sun_lon = p_deg
        if p_name == "Moon":
            moon_lon = p_deg

        p_kp = calculate_kp_sub_lords(p_deg)
        p_nav_sign = calculate_navamsha_sign(p_deg)
        p_house = find_house_for_degree(p_deg, cusp_degrees)
        retro_tag = " (R)" if p["is_retrograde"] else ""

        planets_list.append({
            "name": p_name,
            "planet_name_simple": p_name,
            "display_name": p_name,
            "table_display_name": f"{p_name}{retro_tag}",
            "sanskrit_name": p_name,
            "longitude": p_deg,
            "sign": p_kp["sign_name"],
            "sign_name": p_kp["sign_name"],
            "sign_index": p_kp["sign_index"],
            "sign_id": p_kp["sign_index"],
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

    # Add Fortuna (Pars Fortuna)
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
            "navamsha_sign_index": calculate_navamsha_sign(c_deg),
            "occupants_str": ", ".join(occupants) if occupants else "None"
        })

    def get_navamsa_deg(deg):
        deg_in_sign = deg % 30.0
        nav_deg = (deg_in_sign % (30.0 / 9.0)) * 9.0
        return format_deg_in_sign(nav_deg)

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

    d9_chart = {
        "ascendant_sign_index": asc_nav_sign,
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "sign_index": p["navamsha_sign_index"],
                "house": ((p["navamsha_sign_index"] - asc_nav_sign) % 12) + 1,
                "degree_formatted": get_navamsa_deg(p["longitude"]),
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else "",
                "rl": p.get("rl", "-"),
                "nl": p.get("nl", "-"),
                "sl": p.get("sl", "-"),
                "ssl": p.get("ssl", "-"),
                "sign": ZODIAC_SIGNS[p["navamsha_sign_index"] - 1]["name"],
                "nakshatra": p.get("nakshatra", "-"),
                "pada": p.get("pada", "-")
            } for p in planets_list
        ]
    }

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
                "sign_index": cusps_info[p["house"] - 1]["sign_index"] if p.get("house") else p["sign_index"],
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
    aspects_data = calculate_kp_aspects(planets_list, cusps_info)
    nadi_data = calculate_nakshatra_nadi([p for p in planets_list if p["name"] != "Ascendant"], significators_data)
    four_step_data = calculate_four_step([p for p in planets_list if p["name"] != "Ascendant"], cusps_info, significators_data)

    # -------------------------------------------------------------
    # 2. TRANSIT CALCULATION (Independent, separate, full-precision)
    # -------------------------------------------------------------
    t_lat = transit_latitude if transit_latitude is not None else latitude
    t_lon = transit_longitude if transit_longitude is not None else longitude
    t_tz = transit_timezone if transit_timezone is not None else timezone

    if transit_datetime_str:
        try:
            now_dt = datetime.strptime(transit_datetime_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                now_dt = datetime.strptime(transit_datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    now_dt = datetime.fromisoformat(transit_datetime_str.replace("Z", "+00:00"))
                except Exception:
                    now_dt = datetime.now()
    else:
        now_dt = datetime.now()

    t_utc_dt = now_dt - timedelta(hours=t_tz)
    t_hour_utc = t_utc_dt.hour + t_utc_dt.minute / 60.0 + t_utc_dt.second / 3600.0 + t_utc_dt.microsecond / 3600000000.0
    jd_ut_now = swe.julday(t_utc_dt.year, t_utc_dt.month, t_utc_dt.day, t_hour_utc) if (SWISSEPH_AVAILABLE and swe) else calculate_julian_day(t_utc_dt.year, t_utc_dt.month, t_utc_dt.day, t_hour_utc)

    with _SWE_AYANAMSA_LOCK:
        set_swisseph_sidereal_mode(ayanamsa_name)
        transit_ayan_deg = float(swe.get_ayanamsa_ut(jd_ut_now)) if is_sidereal else 0.0
        curr_cusps, curr_asc_deg, curr_mc_deg = get_placidus_cusps(jd_ut_now, t_lat, t_lon, is_sidereal)
        raw_transit_planets = calculate_planets(jd_ut_now, is_sidereal, node_type=node_type)

    curr_asc_kp = calculate_kp_sub_lords(curr_asc_deg)
    curr_asc_kp['degree_decimal'] = round(curr_asc_deg, 4)
    curr_asc_kp['longitude'] = curr_asc_deg
    curr_asc_nav_sign = calculate_navamsha_sign(curr_asc_deg)

    transit_planets = []
    # Add Transit Ascendant to transit planets
    transit_planets.append({
        "name": "Ascendant",
        "planet_name_simple": "Ascendant",
        "display_name": "Ascendant",
        "table_display_name": "Transit Lagna",
        "sanskrit_name": "Lagna",
        "longitude": curr_asc_deg,
        "sign": curr_asc_kp["sign_name"],
        "sign_name": curr_asc_kp["sign_name"],
        "sign_index": curr_asc_kp["sign_index"],
        "sign_id": curr_asc_kp["sign_index"],
        "sign_sanskrit": curr_asc_kp["sign_sanskrit"],
        "house": 1,
        "transit_house": 1,
        "natal_house": find_house_for_degree(curr_asc_deg, cusp_degrees),
        "degree_formatted": curr_asc_kp["degree_formatted"],
        "degree_decimal": round(curr_asc_deg, 4),
        "nakshatra": curr_asc_kp["nakshatra_name"],
        "nakshatra_lord": curr_asc_kp["nakshatra_lord"],
        "pada": curr_asc_kp["pada"],
        "rl": curr_asc_kp["rl"],
        "nl": curr_asc_kp["nl"],
        "sl": curr_asc_kp["sl"],
        "ssl": curr_asc_kp["ssl"],
        "rashi_lord": curr_asc_kp["rashi_lord"],
        "sub_lord": curr_asc_kp["sub_lord"],
        "sub_sub_lord": curr_asc_kp["sub_sub_lord"],
        "is_retrograde": False,
        "speed": 0.0,
        "navamsha_sign_index": curr_asc_nav_sign,
        "color": PLANET_COLORS["Ascendant"]
    })

    for tp in raw_transit_planets:
        p_name = tp["name"]
        p_deg = tp["longitude"]
        p_kp = calculate_kp_sub_lords(p_deg)
        p_nav_sign = calculate_navamsha_sign(p_deg)
        t_house = find_house_for_degree(p_deg, curr_cusps)
        n_house = find_house_for_degree(p_deg, cusp_degrees)
        retro_tag = " (R)" if tp["is_retrograde"] else ""

        transit_planets.append({
            "name": p_name,
            "planet_name_simple": p_name,
            "display_name": p_name,
            "table_display_name": f"{p_name}{retro_tag}",
            "sanskrit_name": p_name,
            "longitude": p_deg,
            "sign": p_kp["sign_name"],
            "sign_name": p_kp["sign_name"],
            "sign_index": p_kp["sign_index"],
            "sign_id": p_kp["sign_index"],
            "sign_sanskrit": p_kp["sign_sanskrit"],
            "house": t_house,
            "transit_house": t_house,
            "natal_house": n_house,
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
            "is_retrograde": tp["is_retrograde"],
            "speed": round(tp["speed"], 4),
            "navamsha_sign_index": p_nav_sign,
            "color": PLANET_COLORS.get(p_name, "#4338CA")
        })

    # Transit cusps info
    transit_cusps_info = []
    for h in range(1, 13):
        tc_deg = curr_cusps[h - 1]
        tc_next_deg = curr_cusps[h % 12]
        tc_kp = calculate_kp_sub_lords(tc_deg)
        t_occupants = [p["name"] for p in transit_planets if p.get("transit_house") == h and p["name"] != "Ascendant"]
        tc_span = (tc_next_deg - tc_deg) % 360.0

        transit_cusps_info.append({
            "house": h,
            "cusp_number": h,
            "longitude": tc_deg,
            "cusp_degree": tc_deg,
            "cusp_formatted": format_dms(tc_deg),
            "degree_formatted": tc_kp["degree_formatted"],
            "sign": tc_kp["sign_name"],
            "sign_name": tc_kp["sign_name"],
            "sign_index": tc_kp["sign_index"],
            "sign_sanskrit": tc_kp["sign_sanskrit"],
            "nakshatra": tc_kp["nakshatra_name"],
            "nakshatra_lord": tc_kp["nakshatra_lord"],
            "pada": tc_kp["pada"],
            "rl": tc_kp["rl"],
            "nl": tc_kp["nl"],
            "sl": tc_kp["sl"],
            "ssl": tc_kp["ssl"],
            "rashi_lord": tc_kp["rashi_lord"],
            "sub_lord": tc_kp["sub_lord"],
            "sub_sub_lord": tc_kp["sub_sub_lord"],
            "span_degrees": round(tc_span, 2),
            "occupants": t_occupants,
            "navamsha_sign_index": calculate_navamsha_sign(tc_deg),
            "occupants_str": ", ".join(t_occupants) if t_occupants else "None"
        })

    # Transit Charts
    transit_d1_chart = {
        "ascendant_sign_index": curr_asc_kp["sign_index"],
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "sign_index": p["sign_index"],
                "house": ((p["sign_index"] - curr_asc_kp["sign_index"]) % 12) + 1,
                "degree_formatted": p["degree_formatted"],
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else ""
            } for p in transit_planets
        ]
    }

    transit_d9_chart = {
        "ascendant_sign_index": curr_asc_nav_sign,
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "sign_index": p["navamsha_sign_index"],
                "house": ((p["navamsha_sign_index"] - curr_asc_nav_sign) % 12) + 1,
                "degree_formatted": get_navamsa_deg(p["longitude"]),
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else "",
                "rl": p.get("rl", "-"),
                "nl": p.get("nl", "-"),
                "sl": p.get("sl", "-"),
                "ssl": p.get("ssl", "-"),
                "sign": ZODIAC_SIGNS[p["navamsha_sign_index"] - 1]["name"],
                "nakshatra": p.get("nakshatra", "-"),
                "pada": p.get("pada", "-")
            } for p in transit_planets
        ]
    }

    transit_bhava_chart = {
        "ascendant_sign_index": curr_asc_kp["sign_index"],
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
            } for c in transit_cusps_info
        ],
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "house": p["house"],
                "sign_index": transit_cusps_info[p["house"] - 1]["sign_index"] if p.get("house") else p["sign_index"],
                "degree_formatted": p["degree_formatted"],
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else ""
            } for p in transit_planets
        ]
    }

    from app.services.vedic_engine import calculate_upagrahas
    transit_divisional_charts = calculate_all_divisional_charts(transit_planets, curr_asc_deg, [], [], None)

    transit_chart_data = {
        "status": "success",
        "is_transit": True,
        "ascendant": curr_asc_kp,
        "ascendant_sign_index": curr_asc_kp["sign_index"],
        "ascendant_sign": curr_asc_kp["sign_name"],
        "ascendant_degree": curr_asc_kp["degree_decimal"],
        "ascendant_degree_formatted": curr_asc_kp["degree_formatted"],
        "planets": transit_planets,
        "bhava_cusps": transit_cusps_info,
        "bhava_chalit": transit_bhava_chart,
        "divisional_charts": transit_divisional_charts,
        "d1_chart": transit_d1_chart,
        "d9_chart": transit_d9_chart,
        "ayanamsa_name": norm_ayanamsa,
        "ayanamsa_value": round(transit_ayan_deg, 6),
        "ayanamsa_formatted": f"{norm_ayanamsa} {format_dms(transit_ayan_deg)}",
        "datetime": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "latitude": t_lat,
        "longitude": t_lon,
        "timezone": t_tz
    }

    # Transit Chart with Natal Cusps (Transit planets mapped onto Natal Lagna & Natal Cusps)
    transit_natal_d1_chart = {
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
            } for p in transit_planets
        ]
    }

    transit_natal_d9_chart = {
        "ascendant_sign_index": asc_nav_sign,
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "sign_index": p["navamsha_sign_index"],
                "house": ((p["navamsha_sign_index"] - asc_nav_sign) % 12) + 1,
                "degree_formatted": get_navamsa_deg(p["longitude"]),
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else "",
                "rl": p.get("rl", "-"),
                "nl": p.get("nl", "-"),
                "sl": p.get("sl", "-"),
                "ssl": p.get("ssl", "-"),
                "sign": ZODIAC_SIGNS[p["navamsha_sign_index"] - 1]["name"],
                "nakshatra": p.get("nakshatra", "-"),
                "pada": p.get("pada", "-")
            } for p in transit_planets
        ]
    }

    transit_natal_cusps_info = []
    for c in cusps_info:
        h = c["house"]
        t_occupants = [p["name"] for p in transit_planets if p.get("natal_house") == h and p["name"] != "Ascendant"]
        c_copy = dict(c)
        c_copy["occupants"] = t_occupants
        c_copy["occupants_str"] = ", ".join(t_occupants) if t_occupants else "None"
        transit_natal_cusps_info.append(c_copy)

    transit_natal_bhava_chart = {
        "ascendant_sign_index": asc_kp["sign_index"],
        "cusps": transit_natal_cusps_info,
        "planets": [
            {
                "planet": p["name"],
                "name": p["name"],
                "house": p.get("natal_house", p.get("house")),
                "sign_index": cusps_info[p["natal_house"] - 1]["sign_index"] if p.get("natal_house") and p["natal_house"] <= len(cusps_info) else p["sign_index"],
                "degree_formatted": p["degree_formatted"],
                "is_retrograde": p["is_retrograde"],
                "status_marker": " (R)" if p["is_retrograde"] else ""
            } for p in transit_planets
        ]
    }

    transit_planets_for_natal = [
        dict(p, house=p.get("natal_house", p.get("house"))) for p in transit_planets
    ]

    transit_natal_cusps_chart = {
        "status": "success",
        "is_transit": True,
        "is_natal_cusps": True,
        "ascendant": asc_kp,
        "ascendant_sign_index": asc_kp["sign_index"],
        "ascendant_sign": asc_kp["sign_name"],
        "ascendant_degree": round(asc_deg, 4),
        "ascendant_degree_formatted": asc_kp.get("degree_formatted", format_dms(asc_deg % 30.0)),
        "planets": transit_planets_for_natal,
        "bhava_cusps": transit_natal_cusps_info,
        "bhava_chalit": transit_natal_bhava_chart,
        "divisional_charts": calculate_all_divisional_charts(transit_planets_for_natal, asc_deg, [], [], None),
        "d1_chart": transit_natal_d1_chart,
        "d9_chart": transit_natal_d9_chart,
        "ayanamsa_name": norm_ayanamsa,
        "ayanamsa_value": round(transit_ayan_deg, 6),
        "ayanamsa_formatted": f"{norm_ayanamsa} {format_dms(transit_ayan_deg)}",
        "datetime": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "latitude": t_lat,
        "longitude": t_lon,
        "timezone": t_tz
    }
    transit_chart_data["transit_natal_cusps_chart"] = transit_natal_cusps_chart

    # Custom transit aspects
    ASPECT_DEFINITIONS = [
        {"name": "Conjunction", "short_name": "Conj", "angle": 0.0, "orb": 15.0, "nature": "Yellow"},
        {"name": "Vigintile", "short_name": "Vigi", "angle": 18.0, "orb": 2.0, "nature": "Green"},
        {"name": "Quin-decile", "short_name": "Qdec", "angle": 24.0, "orb": 2.0, "nature": "Green"},
        {"name": "Semi-Sextile", "short_name": "Semi", "angle": 30.0, "orb": 2.0, "nature": "Green"},
        {"name": "Semi-quintile", "short_name": "Squi", "angle": 36.0, "orb": 2.0, "nature": "Green"},
        {"name": "Semi-Square", "short_name": "Ssqu", "angle": 45.0, "orb": 4.0, "nature": "LightRed"},
        {"name": "Degrees 54", "short_name": "D54", "angle": 54.0, "orb": 2.0, "nature": "LightRed"},
        {"name": "Sextile", "short_name": "Sext", "angle": 60.0, "orb": 6.0, "nature": "Green"},
        {"name": "Quintile", "short_name": "Quin", "angle": 72.0, "orb": 4.0, "nature": "Green"},
        {"name": "Square", "short_name": "Squr", "angle": 90.0, "orb": 9.0, "nature": "Red"},
        {"name": "Tredecile", "short_name": "Tred", "angle": 108.0, "orb": 3.0, "nature": "Green"},
        {"name": "Trine", "short_name": "Trin", "angle": 120.0, "orb": 9.0, "nature": "DarkGreen"},
        {"name": "Degrees 126", "short_name": "D126", "angle": 126.0, "orb": 2.0, "nature": "DarkGreen"},
        {"name": "Sesquiquadrate", "short_name": "Ssqu", "angle": 135.0, "orb": 3.0, "nature": "LightRed"},
        {"name": "Bi-quintile", "short_name": "Bqui", "angle": 144.0, "orb": 3.0, "nature": "DarkGreen"},
        {"name": "Quincunx", "short_name": "Quin", "angle": 150.0, "orb": 3.0, "nature": "Red"},
        {"name": "Degree 162", "short_name": "D162", "angle": 162.0, "orb": 2.0, "nature": "Green"},
        {"name": "Opposition", "short_name": "Oppn", "angle": 180.0, "orb": 15.0, "nature": "Red"}
    ]

    transit_planet_aspects = []
    for tp in transit_planets:
        if tp["name"] == "Ascendant": continue
        for np in planets_list:
            if np["name"] == "Ascendant": continue
            diff = abs(tp["longitude"] - np["longitude"]) % 360.0
            if diff > 180.0: diff = 360.0 - diff
            for asp in ASPECT_DEFINITIONS:
                orb = abs(diff - asp["angle"])
                if orb <= asp["orb"]:
                    is_applying = True
                    p1_speed = tp.get("speed", 1.0)
                    p2_speed = np.get("speed", 1.0)
                    if p1_speed > p2_speed and tp["longitude"] > np["longitude"]:
                        is_applying = False
                    transit_planet_aspects.append({
                        "transit_planet": tp["name"],
                        "natal_planet": np["name"],
                        "aspect_name": asp["name"],
                        "short_name": asp.get("short_name", asp["name"][:4]),
                        "aspect_angle": asp["angle"],
                        "actual_angle": round(diff, 2),
                        "orb": round(orb, 2),
                        "strength": round(asp["orb"] - orb, 2),
                        "nature": asp["nature"],
                        "is_applying": is_applying,
                        "description": asp.get("desc", "")
                    })
                    break

    transit_cusp_aspects = []
    for tp in transit_planets:
        if tp["name"] == "Ascendant": continue
        for c in cusps_info:
            diff = abs(tp["longitude"] - c["longitude"]) % 360.0
            if diff > 180.0: diff = 360.0 - diff
            for asp in ASPECT_DEFINITIONS:
                orb = abs(diff - asp["angle"])
                if orb <= asp["orb"]:
                    transit_cusp_aspects.append({
                        "transit_planet": tp["name"],
                        "natal_cusp": c["house"],
                        "aspect_name": asp["name"],
                        "aspect_angle": asp["angle"],
                        "actual_angle": round(diff, 2),
                        "orb": round(orb, 2),
                        "nature": asp["nature"]
                    })
                    break

    # Exact Vedic Day Lord & Hora Lord for Natal
    WEEKDAY_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
    HORA_ORDER = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
    try:
        if SWISSEPH_AVAILABLE and swe is not None:
            geopos = (longitude, latitude, 0.0)
            jd_ut_start = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day, 0.0)
            res_rise = swe.rise_trans(jd_ut_start, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geopos)
            sunrise_jd = res_rise[1][0]
            if jd_natal < sunrise_jd:
                res_rise_prev = swe.rise_trans(jd_ut_start - 1.0, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geopos)
                sunrise_jd = res_rise_prev[1][0]
                adjusted_dt = birth_dt - timedelta(days=1)
            else:
                adjusted_dt = birth_dt
            day_lord = WEEKDAY_LORDS[adjusted_dt.weekday()]
            start_idx = HORA_ORDER.index(day_lord)
            res_set = swe.rise_trans(sunrise_jd, swe.SUN, swe.CALC_SET | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geopos)
            sunset_jd = res_set[1][0]
            if sunrise_jd <= jd_natal < sunset_jd:
                day_hora_len = (sunset_jd - sunrise_jd) / 12.0
                hora_idx = int((jd_natal - sunrise_jd) / max(day_hora_len, 1e-6)) % 12
                hora_lord = HORA_ORDER[(start_idx + hora_idx) % 7]
            else:
                res_rise_next = swe.rise_trans(sunset_jd, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geopos)
                next_sunrise_jd = res_rise_next[1][0]
                night_hora_len = (next_sunrise_jd - sunset_jd) / 12.0
                hora_idx = int((jd_natal - sunset_jd) / max(night_hora_len, 1e-6)) % 12
                start_idx_night = (start_idx + 12) % 7
                hora_lord = HORA_ORDER[(start_idx_night + hora_idx) % 7]
        else:
            raise Exception("Swiss Ephemeris not available")
    except Exception:
        tob_hours = tob_parts[0] + tob_parts[1] / 60.0 + sec / 3600.0
        offset = 0 if tob_hours >= 6.0 else -1
        day_idx = (birth_dt + timedelta(days=offset)).weekday()
        day_lord = WEEKDAY_LORDS[day_idx]
        hours_from_sunrise = (tob_hours - 6.0) % 24.0
        hora_idx_in_day = int(hours_from_sunrise) % 24
        start_hora_idx = HORA_ORDER.index(day_lord) if day_lord in HORA_ORDER else 0
        hora_lord = HORA_ORDER[(start_hora_idx + hora_idx_in_day) % 7]

    moon_kp = next((p for p in planets_list if p["name"] == "Moon"), planets_list[0])

    # Ruling Planets at transit time
    try:
        curr_moon_p = next((p for p in transit_planets if p["name"] == "Moon"), None)
        curr_moon_kp = calculate_kp_sub_lords(curr_moon_p["longitude"]) if curr_moon_p else moon_kp

        geopos_curr = (t_lon, t_lat, 0.0)
        jd_ut_start_curr = swe.julday(now_dt.year, now_dt.month, now_dt.day, 0.0)
        res_rise_curr = swe.rise_trans(jd_ut_start_curr, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geopos_curr)
        curr_sunrise_jd = res_rise_curr[1][0]
        if jd_ut_now < curr_sunrise_jd:
            res_prev = swe.rise_trans(jd_ut_start_curr - 1.0, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geopos_curr)
            curr_sunrise_jd = res_prev[1][0]
            adjusted_curr_dt = now_dt - timedelta(days=1)
        else:
            adjusted_curr_dt = now_dt
        curr_day_lord = WEEKDAY_LORDS[adjusted_curr_dt.weekday()]
        start_idx_curr = HORA_ORDER.index(curr_day_lord)
        res_set_curr = swe.rise_trans(curr_sunrise_jd, swe.SUN, swe.CALC_SET | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geopos_curr)
        curr_sunset_jd = res_set_curr[1][0]
        if curr_sunrise_jd <= jd_ut_now < curr_sunset_jd:
            day_hora_len = (curr_sunset_jd - curr_sunrise_jd) / 12.0
            hora_idx = int((jd_ut_now - curr_sunrise_jd) / max(day_hora_len, 1e-6)) % 12
            curr_hora_lord = HORA_ORDER[(start_idx_curr + hora_idx) % 7]
        else:
            res_rise_next = swe.rise_trans(curr_sunset_jd, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION, geopos_curr)
            next_sunrise_jd = res_rise_next[1][0]
            night_hora_len = (next_sunrise_jd - curr_sunset_jd) / 12.0
            hora_idx = int((jd_ut_now - curr_sunset_jd) / max(night_hora_len, 1e-6)) % 12
            start_idx_night = (start_idx_curr + 12) % 7
            curr_hora_lord = HORA_ORDER[(start_idx_night + hora_idx) % 7]
    except Exception:
        curr_day_lord = day_lord
        curr_hora_lord = hora_lord
        curr_moon_kp = moon_kp

    chart_ruling_planets = [
        {"role": "Ascendant Sign Lord (RL)", "planet": asc_kp["rashi_lord"], "short_code": asc_kp["rl"]},
        {"role": "Ascendant Star Lord (NL)", "planet": asc_kp["nakshatra_lord"], "short_code": asc_kp["nl"]},
        {"role": "Ascendant Sub Lord (SL)", "planet": asc_kp["sub_lord"], "short_code": asc_kp["sl"]},
        {"role": "Moon Sign Lord (RL)", "planet": moon_kp["rashi_lord"], "short_code": moon_kp["rl"]},
        {"role": "Moon Star Lord (NL)", "planet": moon_kp["nakshatra_lord"], "short_code": moon_kp["nl"]},
        {"role": "Moon Sub Lord (SL)", "planet": moon_kp["sub_lord"], "short_code": moon_kp["sl"]},
        {"role": "Day Lord (DL)", "planet": day_lord, "short_code": get_lord_short(day_lord)},
        {"role": "Hora Lord", "planet": hora_lord, "short_code": get_lord_short(hora_lord)}
    ]

    current_ruling_planets = [
        {"role": "Ascendant Sign Lord (RL)", "planet": curr_asc_kp["rashi_lord"], "short_code": curr_asc_kp["rl"]},
        {"role": "Ascendant Star Lord (NL)", "planet": curr_asc_kp["nakshatra_lord"], "short_code": curr_asc_kp["nl"]},
        {"role": "Ascendant Sub Lord (SL)", "planet": curr_asc_kp["sub_lord"], "short_code": curr_asc_kp["sl"]},
        {"role": "Moon Sign Lord (RL)", "planet": curr_moon_kp["rashi_lord"], "short_code": curr_moon_kp["rl"]},
        {"role": "Moon Star Lord (NL)", "planet": curr_moon_kp["nakshatra_lord"], "short_code": curr_moon_kp["nl"]},
        {"role": "Moon Sub Lord (SL)", "planet": curr_moon_kp["sub_lord"], "short_code": curr_moon_kp["sl"]},
        {"role": "Day Lord (DL)", "planet": curr_day_lord, "short_code": get_lord_short(curr_day_lord)},
        {"role": "Hora Lord", "planet": curr_hora_lord, "short_code": get_lord_short(curr_hora_lord)}
    ]

    ruling_planets = chart_ruling_planets

    upagrahas_list = calculate_upagrahas(sun_lon, asc_deg, birth_dt, latitude, longitude, timezone, ayan_deg)
    planet_sign_indices = { p["name"]: p["sign_index"] for p in planets_list if p["name"] not in ["Rahu", "Ketu", "Uranus", "Neptune", "Pluto", "Ascendant", "Fortuna"] }
    ashtakavarga_data = calculate_parashara_ashtakvarga(asc_kp["sign_index"], planet_sign_indices)

    return {
        "status": "success",
        "ruling_planets": ruling_planets,
        "chart_ruling_planets": chart_ruling_planets,
        "current_ruling_planets": current_ruling_planets,
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
        "transit_planets": transit_planets,
        "transit_chart": transit_chart_data,
        "transit_natal_cusps_chart": transit_natal_cusps_chart,
        "transit_planet_aspects": transit_planet_aspects,
        "transit_cusp_aspects": transit_cusp_aspects,
        "upagrahas": upagrahas_list,
        "bhava_cusps": cusps_info,
        "divisional_charts": calculate_all_divisional_charts(planets_list, asc_deg, upagrahas_list, [], None),
        "bhava_chalit": bhava_chart,
        "dashas": dasha_data,
        "significators": significators_data,
        "aspects": aspects_data,
        "nakshatra_nadi": nadi_data,
        "four_step": four_step_data,
        "ashtakavarga": ashtakavarga_data
    }
