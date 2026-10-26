"""
High-Precision Varshaphal / Annual Horoscope (Solar Return / Varsha Kundli) Engine.
Classical Tajika System powered by Swiss Ephemeris (pyswisseph).

Provides comprehensive Tajika calculations including:
- High-precision root-finding for exact Solar Return instant (Varshapravesha)
- Annual Lagna (Varsha Lagna), Chalit, Moon chart, Navamsha & divisional charts
- Annual Planetary Positions (Sign, Degree DMS, House, Nakshatra, Pada, Dignity, Retrograde, Combust)
- Comparison with Natal Placements
- Panchadhikari (5 Office Bearers) & Varshesha (Year Lord) selection with audit trail
- Muntha (Sign, House, Lord, Lord House, Progression, & Classical Interpretations)
- Panchavargeeya Bala (Kshetra/Graha, Uchcha, Hudda, Drekkana, Navamsha & Vishwa Bala)
- Harsha Bala (4 Joy Balas + Total)
- Annual Mudda Vimshottari Dasha (Mahadasha, Antardasha, house placements & classical predictions)
- Nav Tara Chakra (from Natal Moon with 9 Taras, 27 Nakshatras & transit analysis)
- Graha Maitri (Naisargika, Tatkalika, & Panchadha Compound Friendship/Enmity Matrix)
- 40 Classical Tajika Sahams (Punya, Guru, Prasava, Yasa, Mitra, Mahatmya, etc.)
- Tajika Yogas (Ithasala, Isarpha, Nakta, Yamaya, Manahoo, Kamboola, etc.)
- Tripataki Chakra with Vedhas calculation & Moon Vedha results
- 12 Monthly Solar Return Charts (Masa Pravesha)
"""

import math
import threading
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

from app.utils.constants import ZODIAC_SIGNS, NAKSHATRAS, PLANETS_INFO, VIMSHOTTARI_SEQUENCE
from app.services.vedic_engine import (
    calculate_julian_day,
    calculate_lahiri_ayanamsa,
    calculate_navamsha,
    calculate_kp_lords,
    calculate_dignity,
    calculate_combustion,
    calculate_bhava_chalit,
    set_swisseph_sidereal_mode,
    _SWE_AYANAMSA_LOCK
)

# -----------------------------------------------------------------------------
# CONSTANTS & DICTIONARIES
# -----------------------------------------------------------------------------

PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SEVEN_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

SIGN_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
}

# Tajika Trirashi (Triplicity) Lords by element & Day/Night
TRIRASHI_LORDS = {
    # Fire signs (1, 5, 9)
    1: {"day": "Sun", "night": "Jupiter"},
    5: {"day": "Sun", "night": "Jupiter"},
    9: {"day": "Sun", "night": "Jupiter"},
    # Earth signs (2, 6, 10)
    2: {"day": "Venus", "night": "Moon"},
    6: {"day": "Venus", "night": "Moon"},
    10: {"day": "Venus", "night": "Moon"},
    # Air signs (3, 7, 11)
    3: {"day": "Saturn", "night": "Mercury"},
    7: {"day": "Saturn", "night": "Mercury"},
    11: {"day": "Saturn", "night": "Mercury"},
    # Water signs (4, 8, 12)
    4: {"day": "Venus", "night": "Mars"},
    8: {"day": "Venus", "night": "Mars"},
    12: {"day": "Venus", "night": "Mars"},
}

# Egyptian / Tajika Haddas (Terms) boundaries & lords for each sign (1 to 12)
HUDDA_BOUNDARIES = {
    1: [(6, "Jupiter"), (12, "Venus"), (20, "Mercury"), (25, "Mars"), (30, "Saturn")],
    2: [(8, "Venus"), (14, "Mercury"), (22, "Jupiter"), (27, "Saturn"), (30, "Mars")],
    3: [(6, "Mercury"), (12, "Jupiter"), (17, "Venus"), (24, "Mars"), (30, "Saturn")],
    4: [(7, "Mars"), (13, "Venus"), (19, "Mercury"), (26, "Jupiter"), (30, "Saturn")],
    5: [(6, "Jupiter"), (11, "Venus"), (18, "Saturn"), (24, "Mercury"), (30, "Mars")],
    6: [(7, "Mercury"), (17, "Venus"), (21, "Jupiter"), (28, "Mars"), (30, "Saturn")],
    7: [(6, "Saturn"), (14, "Mercury"), (21, "Jupiter"), (28, "Venus"), (30, "Mars")],
    8: [(7, "Mars"), (11, "Venus"), (19, "Mercury"), (24, "Jupiter"), (30, "Saturn")],
    9: [(12, "Jupiter"), (17, "Venus"), (21, "Mercury"), (26, "Saturn"), (30, "Mars")],
    10: [(7, "Mercury"), (14, "Jupiter"), (22, "Venus"), (26, "Saturn"), (30, "Mars")],
    11: [(7, "Mercury"), (13, "Venus"), (20, "Jupiter"), (25, "Mars"), (30, "Saturn")],
    12: [(12, "Venus"), (16, "Jupiter"), (19, "Mercury"), (28, "Mars"), (30, "Saturn")],
}

# Exaltation & Debilitation Degrees for deep uchcha bala
EXALTATION_INFO = {
    "Sun": {"exalt_sign": 1, "exalt_deg": 10.0, "debil_sign": 7, "debil_deg": 10.0},
    "Moon": {"exalt_sign": 2, "exalt_deg": 3.0, "debil_sign": 8, "debil_deg": 3.0},
    "Mars": {"exalt_sign": 10, "exalt_deg": 28.0, "debil_sign": 4, "debil_deg": 28.0},
    "Mercury": {"exalt_sign": 6, "exalt_deg": 15.0, "debil_sign": 12, "debil_deg": 15.0},
    "Jupiter": {"exalt_sign": 4, "exalt_deg": 5.0, "debil_sign": 10, "debil_deg": 5.0},
    "Venus": {"exalt_sign": 12, "exalt_deg": 27.0, "debil_sign": 6, "debil_deg": 27.0},
    "Saturn": {"exalt_sign": 7, "exalt_deg": 20.0, "debil_sign": 1, "debil_deg": 20.0},
}

# Deeptamsha (Orb of influence) for Tajika aspects & yogas
TAJIKA_ORBS = {
    "Sun": 15.0,
    "Moon": 12.0,
    "Mars": 8.0,
    "Mercury": 7.0,
    "Jupiter": 9.0,
    "Venus": 7.0,
    "Saturn": 9.0,
    "Rahu": 8.0,
    "Ketu": 8.0
}

# Natural Friendship (Naisargika Maitri)
NATURAL_FRIENDSHIPS = {
    "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "neutrals": ["Mercury"], "enemies": ["Venus", "Saturn"]},
    "Moon": {"friends": ["Sun", "Mercury"], "neutrals": ["Mars", "Jupiter", "Venus", "Saturn"], "enemies": []},
    "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "neutrals": ["Venus", "Saturn"], "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun", "Venus"], "neutrals": ["Mars", "Jupiter", "Saturn"], "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "neutrals": ["Saturn"], "enemies": ["Mercury", "Venus"]},
    "Venus": {"friends": ["Mercury", "Saturn"], "neutrals": ["Mars", "Jupiter"], "enemies": ["Sun", "Moon"]},
    "Saturn": {"friends": ["Mercury", "Venus"], "neutrals": ["Jupiter"], "enemies": ["Sun", "Moon", "Mars"]},
}

# Mudda Vimshottari Dasha durations in days for a 365.25 day annual period
MUDDA_DASHA_DAYS = {
    "Sun": 18.2628,     # 6 / 120 * 365.25
    "Moon": 30.4380,    # 10 / 120 * 365.25
    "Mars": 21.3066,    # 7 / 120 * 365.25
    "Rahu": 54.7884,    # 18 / 120 * 365.25
    "Jupiter": 48.7008, # 16 / 120 * 365.25
    "Saturn": 57.8322,  # 19 / 120 * 365.25
    "Mercury": 51.7446, # 17 / 120 * 365.25
    "Ketu": 21.3066,    # 7 / 120 * 365.25
    "Venus": 60.8760,   # 20 / 120 * 365.25
}

VIMSHOTTARI_CYCLE_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def angle_diff(a: float, b: float) -> float:
    """Returns angular difference (a - b) normalized to [-180, 180]."""
    diff = (a - b) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return diff

def format_dms(deg_float: float) -> str:
    """Format decimal degrees into DD°MM'SS\"."""
    d = int(deg_float)
    rem = (deg_float - d) * 60.0
    m = int(rem)
    s = round((rem - m) * 60.0)
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        d += 1
    return f"{d:02d}°{m:02d}'{s:02d}\""

def get_sign_info(abs_deg: float) -> Dict[str, Any]:
    """Returns sign index (1-12), name, and degree inside sign."""
    norm = abs_deg % 360.0
    sign_idx = int(norm / 30.0) + 1
    deg_in_sign = norm % 30.0
    sign_name = ZODIAC_SIGNS[sign_idx - 1]["name"]
    return {
        "sign_index": sign_idx,
        "sign_name": sign_name,
        "sign_lord": SIGN_LORDS[sign_idx],
        "degree_in_sign": deg_in_sign,
        "formatted": format_dms(deg_in_sign),
        "abs_degree": norm
    }

def get_hadda_lord(sign_idx: int, deg_in_sign: float) -> str:
    """Returns the Hadda (Term) lord for a given sign and degree."""
    boundaries = HUDDA_BOUNDARIES.get(sign_idx, [])
    for max_deg, lord in boundaries:
        if deg_in_sign <= max_deg:
            return lord
    return boundaries[-1][1] if boundaries else "Jupiter"

def get_drekkana_lord(sign_idx: int, deg_in_sign: float) -> str:
    """Returns Drekkana (D3) sign lord."""
    decan = int(deg_in_sign / 10.0)
    target_sign = (sign_idx - 1 + decan * 4) % 12 + 1
    return SIGN_LORDS[target_sign]

def get_navamsha_lord(deg_in_sign: float, sign_idx: int) -> str:
    """Returns Navamsha (D9) sign lord."""
    d9_info = calculate_navamsha(deg_in_sign, sign_idx)
    d9_sign_idx = d9_info.get("navamsha_sign_idx", 1)
    return SIGN_LORDS[d9_sign_idx]

def get_relationship_status(planet: str, target_planet: str) -> str:
    """Returns 'Own', 'Friend', 'Neutral', or 'Enemy' for natural friendship."""
    if planet == target_planet:
        return "Own"
    info = NATURAL_FRIENDSHIPS.get(planet, {})
    if target_planet in info.get("friends", []):
        return "Friend"
    if target_planet in info.get("enemies", []):
        return "Enemy"
    return "Neutral"

# -----------------------------------------------------------------------------
# 1. SOLAR RETURN INSTANT FINDER (VARSHAPRAVESHA)
# -----------------------------------------------------------------------------

def find_solar_return_instant(
    jd_birth: float,
    birth_year: int,
    target_year: int,
    ayanamsa_mode: str = "LAHIRI",
    custom_ayanamsa: Optional[float] = None
) -> Tuple[float, float]:
    """
    Finds the exact Julian Day when the transiting Sun returns to the natal Sun's
    exact sidereal longitude for the target year.
    Uses high-precision Newton-Raphson iteration with Swiss Ephemeris.
    """
    with _SWE_AYANAMSA_LOCK:
        set_swisseph_sidereal_mode(ayanamsa_mode)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

        # 1. Natal Sun Longitude
        res, _ = swe.calc_ut(jd_birth, swe.SUN, flag)
        natal_sun_lon = res[0]

        # 2. Approximate return JD using mean sidereal year
        years_diff = target_year - birth_year
        approx_jd = jd_birth + (years_diff * 365.256363004)

        # 3. Newton-Raphson solver to reach exact return instant
        cur_jd = approx_jd
        for _ in range(25):
            res, _ = swe.calc_ut(cur_jd, swe.SUN, flag)
            cur_lon = res[0]
            sun_speed = res[3] if abs(res[3]) > 0.1 else 0.9856
            diff = angle_diff(cur_lon, natal_sun_lon)
            if abs(diff) < 1e-8: # ~0.000036 arcseconds precision
                break
            cur_jd -= (diff / sun_speed)

        return cur_jd, natal_sun_lon

# -----------------------------------------------------------------------------
# 2. PLANETARY POSITIONS AT SOLAR RETURN
# -----------------------------------------------------------------------------

SWE_PLANET_MAP = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO
}

def calculate_chart_at_jd(
    jd: float,
    latitude: float,
    longitude: float,
    ayanamsa_mode: str = "LAHIRI"
) -> Dict[str, Any]:
    with _SWE_AYANAMSA_LOCK:
        set_swisseph_sidereal_mode(ayanamsa_mode)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

        cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'P', swe.FLG_SIDEREAL)
        asc_deg = ascmc[0] % 360.0
        asc_sign_idx = int(asc_deg / 30.0) + 1
        asc_deg_in_sign = asc_deg % 30.0

        planets_list = []
        sun_deg = 0.0

        for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]:
            p_id = SWE_PLANET_MAP[p_name]
            res, _ = swe.calc_ut(jd, p_id, flag)
            lon = res[0] % 360.0
            speed = res[3]
            is_retro = speed < 0.0

            if p_name == "Sun":
                sun_deg = lon

            sign_idx = int(lon / 30.0) + 1
            deg_in_sign = lon % 30.0
            house = (sign_idx - asc_sign_idx) % 12 + 1

            nak_float = (lon * 27.0) / 360.0
            nak_idx = int(nak_float)
            pada = int((nak_float - nak_idx) * 4) + 1
            nak_name = NAKSHATRAS[nak_idx % 27]["name"] if nak_idx < 27 else "Ashwini"
            nak_lord = NAKSHATRAS[nak_idx % 27]["lord"] if nak_idx < 27 else "Ketu"

            kp_lords = calculate_kp_lords(lon)
            dignity = calculate_dignity(p_name, sign_idx, deg_in_sign)

            planets_list.append({
                "planet": p_name,
                "name": p_name,
                "planet_name_simple": p_name,
                "longitude": lon,
                "abs_degree": lon,
                "sign_index": sign_idx,
                "sign_name": ZODIAC_SIGNS[sign_idx - 1]["name"],
                "sign_lord": SIGN_LORDS[sign_idx],
                "degree_in_sign": deg_in_sign,
                "degree_formatted": format_dms(deg_in_sign),
                "house": house,
                "speed": speed,
                "is_retrograde": is_retro,
                "is_combust": False,
                "dignity": dignity,
                "nakshatra": nak_name,
                "pada": pada,
                "nakshatra_lord": nak_lord,
                "star_lord": kp_lords.get("star_lord", nak_lord),
                "sub_lord": kp_lords.get("sub_lord", "")
            })

        # Calculate Ketu
        rahu = next(p for p in planets_list if p["planet"] == "Rahu")
        ketu_lon = (rahu["longitude"] + 180.0) % 360.0
        ketu_sign_idx = int(ketu_lon / 30.0) + 1
        ketu_deg_in_sign = ketu_lon % 30.0
        ketu_house = (ketu_sign_idx - asc_sign_idx) % 12 + 1
        ketu_nak_float = (ketu_lon * 27.0) / 360.0
        ketu_nak_idx = int(ketu_nak_float)
        ketu_pada = int((ketu_nak_float - ketu_nak_idx) * 4) + 1
        ketu_nak_name = NAKSHATRAS[ketu_nak_idx % 27]["name"]
        ketu_nak_lord = NAKSHATRAS[ketu_nak_idx % 27]["lord"]
        ketu_kp = calculate_kp_lords(ketu_lon)

        planets_list.append({
            "planet": "Ketu",
            "name": "Ketu",
            "planet_name_simple": "Ketu",
            "longitude": ketu_lon,
            "abs_degree": ketu_lon,
            "sign_index": ketu_sign_idx,
            "sign_name": ZODIAC_SIGNS[ketu_sign_idx - 1]["name"],
            "sign_lord": SIGN_LORDS[ketu_sign_idx],
            "degree_in_sign": ketu_deg_in_sign,
            "degree_formatted": format_dms(ketu_deg_in_sign),
            "house": ketu_house,
            "speed": rahu["speed"],
            "is_retrograde": rahu["is_retrograde"],
            "is_combust": False,
            "dignity": calculate_dignity("Ketu", ketu_sign_idx, ketu_deg_in_sign),
            "nakshatra": ketu_nak_name,
            "pada": ketu_pada,
            "nakshatra_lord": ketu_nak_lord,
            "star_lord": ketu_kp.get("star_lord", ketu_nak_lord),
            "sub_lord": ketu_kp.get("sub_lord", "")
        })

        # Outer planets
        for out_name in ["Uranus", "Neptune", "Pluto"]:
            res, _ = swe.calc_ut(jd, SWE_PLANET_MAP[out_name], flag)
            out_lon = res[0] % 360.0
            out_sign = int(out_lon / 30.0) + 1
            out_deg = out_lon % 30.0
            out_house = (out_sign - asc_sign_idx) % 12 + 1
            planets_list.append({
                "planet": out_name,
                "name": out_name,
                "planet_name_simple": out_name,
                "longitude": out_lon,
                "abs_degree": out_lon,
                "sign_index": out_sign,
                "sign_name": ZODIAC_SIGNS[out_sign - 1]["name"],
                "sign_lord": SIGN_LORDS[out_sign],
                "degree_in_sign": out_deg,
                "degree_formatted": format_dms(out_deg),
                "house": out_house,
                "speed": res[3],
                "is_retrograde": res[3] < 0,
                "is_combust": False,
                "dignity": "Neutral",
                "nakshatra": "",
                "pada": 1,
                "nakshatra_lord": "",
                "star_lord": "",
                "sub_lord": ""
            })

        calculate_combustion(planets_list, sun_deg)

        # Navamsha chart (D9)
        d9_planets = []
        for p in planets_list:
            d9_info = calculate_navamsha(p["degree_in_sign"], p["sign_index"])
            d9_planets.append({
                "planet": p["planet"],
                "sign_index": d9_info.get("navamsha_sign_idx", 1),
                "sign_name": d9_info.get("navamsha_sign", "Aries"),
                "degree_formatted": p["degree_formatted"],
                "is_retrograde": p["is_retrograde"],
                "is_combust": p["is_combust"]
            })
        asc_d9_info = calculate_navamsha(asc_deg_in_sign, asc_sign_idx)

        bhava_chalit = calculate_bhava_chalit(
            asc_deg=asc_deg,
            planets_list=planets_list,
            jd=jd,
            latitude=latitude,
            longitude=longitude
        )

        return {
            "ascendant": {
                "longitude": asc_deg,
                "sign_index": asc_sign_idx,
                "sign_name": ZODIAC_SIGNS[asc_sign_idx - 1]["name"],
                "sign_lord": SIGN_LORDS[asc_sign_idx],
                "degree_in_sign": asc_deg_in_sign,
                "degree_formatted": format_dms(asc_deg_in_sign),
                "nakshatra": NAKSHATRAS[int(asc_deg * 27 / 360) % 27]["name"],
                "pada": int((asc_deg * 27 / 360 - int(asc_deg * 27 / 360)) * 4) + 1
            },
            "planets": planets_list,
            "bhava_chalit": bhava_chalit,
            "divisional_charts": {
                "D-1": {
                    "ascendant": asc_sign_idx,
                    "planets": planets_list
                },
                "D-9": {
                    "ascendant": asc_d9_info.get("navamsha_sign_idx", 1),
                    "planets": d9_planets
                }
            }
        }

# -----------------------------------------------------------------------------
# 3. PANCHAVARGEEYA BALA & HARSHA BALA
# -----------------------------------------------------------------------------

def calculate_panchavargeeya_bala(planets_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    balas = {}
    p_dict = {p["planet"]: p for p in planets_list if p["planet"] in SEVEN_PLANETS}

    for p_name in SEVEN_PLANETS:
        p_data = p_dict.get(p_name)
        if not p_data:
            continue

        sign_idx = p_data["sign_index"]
        deg_in_sign = p_data["degree_in_sign"]
        sign_lord = p_data["sign_lord"]

        # 1. Graha Bala (Kshetra Bala)
        rel_sign = get_relationship_status(p_name, sign_lord)
        if rel_sign == "Own":
            graha_b = 30.0
        elif rel_sign == "Friend":
            graha_b = 22.50
        elif rel_sign == "Neutral":
            graha_b = 15.00
        else:
            graha_b = 7.50

        # 2. Uchcha Bala
        ex_info = EXALTATION_INFO[p_name]
        debil_deg_abs = (ex_info["debil_sign"] - 1) * 30.0 + ex_info["debil_deg"]
        cur_deg_abs = p_data["abs_degree"]
        diff = abs(angle_diff(cur_deg_abs, debil_deg_abs))
        uchcha_b = round((diff / 180.0) * 20.0, 2)

        # 3. Hudda Bala
        hudda_lord = get_hadda_lord(sign_idx, deg_in_sign)
        rel_hudda = get_relationship_status(p_name, hudda_lord)
        if rel_hudda == "Own":
            hudda_b = 15.00
        elif rel_hudda == "Friend":
            hudda_b = 11.25
        elif rel_hudda == "Neutral":
            hudda_b = 7.50
        else:
            hudda_b = 3.75

        # 4. Drekkana Bala
        drek_lord = get_drekkana_lord(sign_idx, deg_in_sign)
        rel_drek = get_relationship_status(p_name, drek_lord)
        if rel_drek == "Own":
            drek_b = 10.00
        elif rel_drek == "Friend":
            drek_b = 7.50
        elif rel_drek == "Neutral":
            drek_b = 5.00
        else:
            drek_b = 2.50

        # 5. Navamsha Bala
        nav_lord = get_navamsha_lord(deg_in_sign, sign_idx)
        rel_nav = get_relationship_status(p_name, nav_lord)
        if rel_nav == "Own":
            nav_b = 5.00
        elif rel_nav == "Friend":
            nav_b = 3.75
        elif rel_nav == "Neutral":
            nav_b = 2.50
        else:
            nav_b = 1.25

        total = round((graha_b + uchcha_b + hudda_b + drek_b + nav_b) / 4.0, 2)

        balas[p_name] = {
            "graha_bala": graha_b,
            "uchcha_bala": uchcha_b,
            "hudda_bala": hudda_b,
            "drekkana_bala": drek_b,
            "navamsha_bala": nav_b,
            "total_vishwa_bala": total
        }

    return balas

def calculate_harsha_bala(
    planets_list: List[Dict[str, Any]],
    is_day_return: bool
) -> Dict[str, Any]:
    JOY_HOUSES = {
        "Sun": 9, "Moon": 3, "Mars": 6, "Mercury": 1,
        "Jupiter": 11, "Venus": 5, "Saturn": 12
    }
    MASCULINE_PLANETS = ["Sun", "Mars", "Jupiter"]
    FEMININE_PLANETS = ["Moon", "Venus", "Saturn"]

    p_dict = {p["planet"]: p for p in planets_list if p["planet"] in SEVEN_PLANETS}
    harsha_results = {}

    for p_name in SEVEN_PLANETS:
        p_data = p_dict.get(p_name)
        if not p_data:
            continue

        h = p_data["house"]
        sign_idx = p_data["sign_index"]
        is_odd_sign = (sign_idx % 2 != 0)

        b1 = 5 if h == JOY_HOUSES.get(p_name) else 0

        is_own = (SIGN_LORDS[sign_idx] == p_name)
        is_exalt = (EXALTATION_INFO[p_name]["exalt_sign"] == sign_idx)
        b2 = 5 if (is_own or is_exalt) else 0

        if p_name in MASCULINE_PLANETS:
            b3 = 5 if is_odd_sign else 0
        elif p_name in FEMININE_PLANETS:
            b3 = 5 if not is_odd_sign else 0
        else:
            b3 = 5 if is_odd_sign else 0

        if is_day_return:
            b4 = 5 if p_name in ["Sun", "Jupiter", "Venus", "Mercury"] else 0
        else:
            b4 = 5 if p_name in ["Moon", "Mars", "Saturn", "Mercury"] else 0

        total = b1 + b2 + b3 + b4
        rating = "Strong" if total >= 15 else ("Medium" if total >= 10 else "Weak")

        harsha_results[p_name] = {
            "first_bala": b1,
            "second_bala": b2,
            "third_bala": b3,
            "fourth_bala": b4,
            "total": total,
            "rating": rating
        }

    return harsha_results

# -----------------------------------------------------------------------------
# 4. PANCHADHIKARI & VARSHESHA (YEAR LORD) SELECTION
# -----------------------------------------------------------------------------

def calculate_panchadhikari_and_varshesha(
    natal_asc_sign_idx: int,
    varsha_asc_sign_idx: int,
    muntha_sign_idx: int,
    sun_sign_idx: int,
    moon_sign_idx: int,
    is_day_return: bool,
    panchavargeeya_balas: Dict[str, Any],
    planets_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    muntha_lord = SIGN_LORDS[muntha_sign_idx]
    janma_lagna_lord = SIGN_LORDS[natal_asc_sign_idx]
    varsha_lagna_lord = SIGN_LORDS[varsha_asc_sign_idx]

    trirashi_info = TRIRASHI_LORDS[varsha_asc_sign_idx]
    trirashi_lord = trirashi_info["day"] if is_day_return else trirashi_info["night"]

    dinaratri_lord = SIGN_LORDS[sun_sign_idx] if is_day_return else SIGN_LORDS[moon_sign_idx]

    candidates_list = [
        {"role": "Muntha Lord", "planet": muntha_lord},
        {"role": "Janma Lagna Lord", "planet": janma_lagna_lord},
        {"role": "Varsha Lagna Lord", "planet": varsha_lagna_lord},
        {"role": "Trirashi Lord", "planet": trirashi_lord},
        {"role": "Dinaratri Lord", "planet": dinaratri_lord},
    ]

    p_house_map = {p["planet"]: p["house"] for p in planets_list}
    ASPECTING_HOUSES = {1, 3, 4, 5, 7, 9, 10, 11}

    candidate_results = []
    eligible_candidates = []

    for c in candidates_list:
        p = c["planet"]
        strength = panchavargeeya_balas.get(p, {}).get("total_vishwa_bala", 0.0)
        house = p_house_map.get(p, 1)
        aspects_lagna = house in ASPECTING_HOUSES

        entry = {
            "role": c["role"],
            "planet": p,
            "strength": strength,
            "house": house,
            "aspects_lagna": aspects_lagna,
            "eligibility_status": "Eligible (Aspects Lagna)" if aspects_lagna else "Ineligible (No Tajika Aspect on Lagna)"
        }
        candidate_results.append(entry)
        if aspects_lagna:
            eligible_candidates.append(entry)

    if eligible_candidates:
        varshesha_entry = max(eligible_candidates, key=lambda x: x["strength"])
        selection_reason = f"{varshesha_entry['planet']} holds the highest Panchavargeeya Vishwa Bala ({varshesha_entry['strength']}) among the Panchadhikari candidates casting a direct Tajika aspect on the Varsha Lagna."
    else:
        varshesha_entry = next(c for c in candidate_results if c["role"] == "Varsha Lagna Lord")
        selection_reason = f"No candidate casts a classic Tajika aspect; hence Varsha Lagna Lord {varshesha_entry['planet']} assumes office as Varshesha."

    return {
        "varshesha": varshesha_entry["planet"],
        "varshesha_role": varshesha_entry["role"],
        "varshesha_strength": varshesha_entry["strength"],
        "selection_explanation": selection_reason,
        "panchadhikari": candidate_results
    }

# -----------------------------------------------------------------------------
# 5. MUNTHA CALCULATION & INTERPRETATIONS
# -----------------------------------------------------------------------------

MUNTHA_HOUSE_PREDICTIONS = {
    1: "In the 1st house, Muntha brings vitality, honor, social promotion, and success in ventures. Self-confidence and public recognition increase significantly.",
    2: "In the 2nd house, Muntha indicates financial accumulation, prosperity through trade, acquisition of precious assets, and cordial domestic relations.",
    3: "In the 3rd house, Muntha confers courage, fruitful short travels, victory over competitors, assistance from siblings and associates, and accomplishment of projects.",
    4: "In the 4th house, Muntha indicates mental unease, domestic unrest, property concerns, or family health issues. Requires patience and emotional stability.",
    5: "In the 5th house, Muntha brings creative intelligence, academic distinction, romance, auspicious celebration, and success through wise speculation.",
    6: "In the 6th house, Muntha causes conflicts, health challenges, litigation, or workplace opposition. Diligence, care in health, and caution in disputes are vital.",
    7: "In the 7th house, Muntha highlights marital and partnership dynamics. Opportunities for travel, trade agreements, and public connections flourish.",
    8: "In the 8th house, Muntha warns of unexpected disruptions, health vulnerabilities, financial sluggishness, and secret adversaries. Spiritual pursuits yield inner growth.",
    9: "In the 9th house, Muntha grants high fortune, spiritual initiation, blessings of preceptors, long-distance pilgrimages, and widespread renown.",
    10: "In the 10th house, Muntha bestows professional elevation, executive authority, government recognition, career breakthroughs, and immense prosperity.",
    11: "In the 11th house, Muntha guarantees fulfillment of ambitions, generous monetary gains, powerful friendships, and expansion in business networks.",
    12: "In the 12th house, Muntha indicates heavy expenditures, foreign relocation, isolation, and spiritual renunciation. Financial discipline is necessary."
}

def calculate_muntha(
    natal_asc_sign_idx: int,
    varsha_asc_sign_idx: int,
    birth_year: int,
    target_year: int,
    planets_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    completed_years = target_year - birth_year
    muntha_sign_idx = (natal_asc_sign_idx - 1 + completed_years) % 12 + 1
    muntha_sign_name = ZODIAC_SIGNS[muntha_sign_idx - 1]["name"]
    muntha_lord = SIGN_LORDS[muntha_sign_idx]
    muntha_house = (muntha_sign_idx - varsha_asc_sign_idx) % 12 + 1

    lord_planet = next((p for p in planets_list if p["planet"] == muntha_lord), None)
    muntha_lord_house = lord_planet["house"] if lord_planet else 1
    muntha_lord_sign = lord_planet["sign_name"] if lord_planet else "Aries"

    prediction = MUNTHA_HOUSE_PREDICTIONS.get(
        muntha_house,
        f"Muntha resides in house {muntha_house} of the Varsha Lagna."
    )

    return {
        "completed_years": completed_years,
        "sign_index": muntha_sign_idx,
        "sign_name": muntha_sign_name,
        "house": muntha_house,
        "muntha_lord": muntha_lord,
        "muntha_lord_house": muntha_lord_house,
        "muntha_lord_sign": muntha_lord_sign,
        "prediction": prediction
    }

# -----------------------------------------------------------------------------
# 6. MUDDA VIMSHOTTARI DASHA FOR VARSHAPHAL
# -----------------------------------------------------------------------------

MUDDA_PREDICTIONS = {
    ("Sun", 1): "Solar energy elevates personal authority, health, and status.",
    ("Sun", 6): "Success in endeavors, defeat of adversaries, and promotion in workplace.",
    ("Sun", 8): "Unexpected expenses, physical exhaustion, and health vigilance needed.",
    ("Moon", 7): "Acquisition of wealth, harmonious partnerships, and public appreciation.",
    ("Moon", 8): "Emotional vulnerability, domestic tensions, and caution in travel.",
    ("Moon", 10): "Constructive progress, executive support, and fulfillment of plans.",
    ("Mars", 6): "Happiness, victory over obstacles, and courage to surmount resistance.",
    ("Mars", 10): "Business expansion, public honor, and forceful achievement.",
    ("Mars", 12): "High expenditure, irritation, and need to avoid impulsive disputes.",
    ("Mercury", 3): "Intellectual success, trade gains, fruitful communication, and sibling support.",
    ("Mercury", 6): "Heavy workload, detailed tasks, and need to curb excessive spending.",
    ("Mercury", 12): "Mental restlessness, secret planning, and sudden expenses.",
    ("Jupiter", 2): "Financial abundance, family blessings, and cultural/artistic joy.",
    ("Jupiter", 5): "Superb intellectual confidence, spiritual merits, and romantic joy.",
    ("Jupiter", 10): "Professional breakthrough, high prestige, and royal/governmental favors.",
    ("Jupiter", 11): "Fulfillment of desires, foreign gains, and multi-stream prosperity.",
    ("Venus", 1): "Pleasure, artistic accomplishments, comforts, and luxury.",
    ("Venus", 6): "Fatigue, excessive desires, and work tension.",
    ("Saturn", 5): "Creative blocks, children's health, and need for disciplined choices.",
    ("Saturn", 8): "Mental strain, trade delays, and need for patient endurance.",
    ("Saturn", 11): "Substantial material gains, elder support, and steady accomplishments.",
    ("Rahu", 3): "Tremendous power, ambition, and social recognition.",
    ("Rahu", 7): "Partnership friction, legal vigilance, and stomach/health care.",
    ("Rahu", 12): "Relocation, foreign contacts, and unexpected expenses.",
    ("Ketu", 1): "Spiritual inclinations, mood swings, and caution in partnerships.",
    ("Ketu", 6): "Triumph in competitions, surprising gains, and recognition.",
    ("Ketu", 9): "Pilgrimages, respect among learned persons, and philosophical outlook."
}

def calculate_mudda_dasha(
    varsha_pravesha_dt: datetime,
    birth_year: int,
    target_year: int,
    planets_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    completed_years = target_year - birth_year
    start_index = completed_years % 9
    running_now = datetime.now()

    p_house_map = {p["planet"]: p["house"] for p in planets_list}
    timeline = []
    current_start = varsha_pravesha_dt

    for i in range(9):
        p_idx = (start_index + i) % 9
        planet = VIMSHOTTARI_CYCLE_ORDER[p_idx]
        days = MUDDA_DASHA_DAYS[planet]
        end_dt = current_start + timedelta(days=days)

        house = p_house_map.get(planet, 1)
        pred = MUDDA_PREDICTIONS.get(
            (planet, house),
            f"During the {planet} Mudda period, results will predominantly manifest through the themes of the {house}th house in the Varsha Lagna."
        )

        is_current = current_start <= running_now < end_dt

        # Calculate Antardashas
        antardashas = []
        sub_start = current_start
        for j in range(9):
            sub_idx = (p_idx + j) % 9
            sub_planet = VIMSHOTTARI_CYCLE_ORDER[sub_idx]
            sub_days = days * (MUDDA_DASHA_DAYS[sub_planet] / 365.25)
            sub_end = sub_start + timedelta(days=sub_days)
            sub_current = sub_start <= running_now < sub_end

            antardashas.append({
                "sub_lord": sub_planet,
                "start_date": sub_start.strftime("%d/%m/%Y"),
                "end_date": sub_end.strftime("%d/%m/%Y"),
                "duration_days": round(sub_days, 1),
                "is_current": sub_current
            })
            sub_start = sub_end

        timeline.append({
            "order": i + 1,
            "lord": planet,
            "house": house,
            "start_date": current_start.strftime("%d/%m/%Y"),
            "end_date": end_dt.strftime("%d/%m/%Y"),
            "start_iso": current_start.isoformat(),
            "end_iso": end_dt.isoformat(),
            "duration_days": round(days, 1),
            "is_current": is_current,
            "prediction": pred,
            "antardashas": antardashas
        })
        current_start = end_dt

    return timeline

# -----------------------------------------------------------------------------
# 7. NAV TARA CHAKRA (FROM MOON)
# -----------------------------------------------------------------------------

TARA_NAMES = [
    {"num": 1, "name": "Janma", "sanskrit": "जन्म", "nature": "Auspicious/Neutral", "meaning": "Birth, physical vitality, self-identity, foundation of action."},
    {"num": 2, "name": "Sampat", "sanskrit": "सम्पत्", "nature": "Highly Auspicious", "meaning": "Wealth, prosperity, material fulfillment, success in commerce."},
    {"num": 3, "name": "Vipat", "sanskrit": "विपत्", "nature": "Inauspicious", "meaning": "Danger, obstacles, unexpected delays, potential setbacks."},
    {"num": 4, "name": "Kshema", "sanskrit": "क्षेम", "nature": "Auspicious", "meaning": "Well-being, security, protection, peace of mind, family comfort."},
    {"num": 5, "name": "Pratyak", "sanskrit": "प्रत्यक्", "nature": "Inauspicious", "meaning": "Obstacles, opposition, disagreements, friction in endeavors."},
    {"num": 6, "name": "Sadhana", "sanskrit": "साधना", "nature": "Highly Auspicious", "meaning": "Achievement, accomplishment, spiritual practice, goal realization."},
    {"num": 7, "name": "Naidhana / Vadha", "sanskrit": "निधन", "nature": "Critical/Adverse", "meaning": "Destruction, acute distress, vulnerability, major transformation."},
    {"num": 8, "name": "Mitra", "sanskrit": "मित्र", "nature": "Auspicious", "meaning": "Friendship, companionship, helpful allies, cordial relationships."},
    {"num": 9, "name": "Param Mitra", "sanskrit": "परम मित्र", "nature": "Supreme Auspicious", "meaning": "Supreme friend, patron, greatest benefit, divine assistance."}
]

def calculate_nav_tara_chakra(
    natal_moon_nak_idx: int,
    varsha_moon_nak_idx: int
) -> Dict[str, Any]:
    tara_table = []
    annual_moon_tara = None

    for i, t in enumerate(TARA_NAMES):
        tara_num = i + 1
        nak_indices = [
            (natal_moon_nak_idx + i) % 27,
            (natal_moon_nak_idx + i + 9) % 27,
            (natal_moon_nak_idx + i + 18) % 27,
        ]

        nak_details = []
        for n_idx in nak_indices:
            nak_info = NAKSHATRAS[n_idx]
            is_annual_moon = (n_idx == varsha_moon_nak_idx)
            if is_annual_moon:
                annual_moon_tara = t["name"]

            nak_details.append({
                "nakshatra_number": n_idx + 1,
                "name": nak_info["name"],
                "lord": nak_info["lord"],
                "is_annual_moon": is_annual_moon
            })

        tara_table.append({
            "tara_number": tara_num,
            "tara_name": t["name"],
            "sanskrit": t["sanskrit"],
            "nature": t["nature"],
            "meaning": t["meaning"],
            "nakshatras": nak_details
        })

    natal_ref_nak = NAKSHATRAS[natal_moon_nak_idx]["name"]
    varsha_ref_nak = NAKSHATRAS[varsha_moon_nak_idx]["name"]

    return {
        "reference_natal_moon_nakshatra": natal_ref_nak,
        "annual_moon_nakshatra": varsha_ref_nak,
        "annual_moon_tara": annual_moon_tara or "Janma",
        "taras": tara_table
    }

# -----------------------------------------------------------------------------
# 8. GRAHA MAITRI (FRIENDSHIP & ENMITY MATRIX)
# -----------------------------------------------------------------------------

def calculate_graha_maitri(
    planets_list: List[Dict[str, Any]],
    chart_context: str = "annual"
) -> Dict[str, Any]:
    p_houses = {p["planet"]: p["house"] for p in planets_list if p["planet"] in SEVEN_PLANETS}
    matrix = {}

    for p1 in SEVEN_PLANETS:
        matrix[p1] = {}
        for p2 in SEVEN_PLANETS:
            if p1 == p2:
                matrix[p1][p2] = {
                    "natural": "Self",
                    "temporary": "Self",
                    "compound": "Self",
                    "score": 0
                }
                continue

            nat_status = get_relationship_status(p1, p2)
            h1 = p_houses.get(p1, 1)
            h2 = p_houses.get(p2, 1)
            diff_h = (h2 - h1) % 12 + 1
            is_temp_friend = diff_h in [2, 3, 4, 10, 11, 12]
            temp_status = "Friend" if is_temp_friend else "Enemy"

            if nat_status == "Friend":
                compound = "Adhi Mitra" if temp_status == "Friend" else "Sama"
            elif nat_status == "Neutral":
                compound = "Mitra" if temp_status == "Friend" else "Shatru"
            else:
                compound = "Sama" if temp_status == "Friend" else "Adhi Shatru"

            matrix[p1][p2] = {
                "natural": nat_status,
                "temporary": temp_status,
                "compound": compound,
                "relative_house": diff_h
            }

    return {
        "context": chart_context,
        "planets": SEVEN_PLANETS,
        "matrix": matrix
    }

# -----------------------------------------------------------------------------
# 9. 40 CLASSICAL TAJIKA SAHAMS
# -----------------------------------------------------------------------------

SAHAM_DEFINITIONS = [
    ("Punya", "Fortune & Auspiciousness", ("M", "S", "A"), ("S", "M", "A")),
    ("Guru", "Teacher & Preceptor", ("J", "S", "A"), ("S", "J", "A")),
    ("Prasava", "Delivery of Child & Offspring", ("J", "M", "A"), ("M", "J", "A")),
    ("Yasa", "Fame & Renown", ("J", "P", "A"), ("P", "J", "A")),
    ("Mitra", "Friendship & Allies", ("J", "P", "A"), ("P", "J", "A")),
    ("Mahatmya", "Greatness & Status", ("P", "Ma", "A"), ("Ma", "P", "A")),
    ("Asha", "Desire & Ambition", ("Sa", "Ma", "A"), ("Ma", "Sa", "A")),
    ("Pitru", "Father & Paternal Elders", ("Sa", "S", "A"), ("S", "Sa", "A")),
    ("Matru", "Mother & Maternal Elders", ("M", "V", "A"), ("V", "M", "A")),
    ("Jeeva", "Life & Vitality", ("Sa", "J", "A"), ("J", "Sa", "A")),
    ("Karma", "Action, Duty & Profession", ("Ma", "M", "A"), ("M", "Ma", "A")),
    ("Kali", "Strife, Quarrels & Opposition", ("Sa", "Ma", "A"), ("Ma", "Sa", "A")),
    ("Shastra", "Science, Literature & Learning", ("J", "Sa", "A"), ("Sa", "J", "A")),
    ("Bandak", "Prisoner & Confinement", ("P", "Sa", "A"), ("Sa", "P", "A")),
    ("Jadya", "Chronic Disease & Sluggishness", ("Ma", "Sa", "A"), ("Sa", "Ma", "A")),
    ("Shatru", "Enemies & Adversaries", ("Ma", "Sa", "A"), ("Sa", "Ma", "A")),
    ("Bandhana", "Imprisonment & Restriction", ("Sa", "M", "A"), ("M", "Sa", "A")),
    ("Samartha", "Ability & Competence", ("J", "Ma", "A"), ("Ma", "J", "A")),
    ("Kama", "Desire & Sensual Pleasure", ("V", "S", "A"), ("S", "V", "A")),
    ("Gaurava", "Respect & Honor", ("J", "M", "A"), ("M", "J", "A")),
    ("Karyasiddhi", "Success in Undertakings", ("Sa", "S", "A"), ("S", "Sa", "A")),
    ("Ashva", "Conveyance, Vehicles & Travel", ("Sa", "M", "A"), ("M", "Sa", "A")),
    ("Bhratra", "Brothers & Siblings", ("J", "Sa", "A"), ("Sa", "J", "A")),
    ("Putra", "Children & Posterity", ("J", "M", "A"), ("M", "J", "A")),
    ("Roga", "Disease & Infirmity", ("Sa", "M", "A"), ("M", "Sa", "A")),
    ("Bandhu", "Relatives & Kinship", ("Me", "M", "A"), ("M", "Me", "A")),
    ("Mrityu", "Death & Endings", ("Sa", "M", "A"), ("M", "Sa", "A")),
    ("Artha", "Wealth & Finance", ("Sa", "Ma", "A"), ("Ma", "Sa", "A")),
    ("Paradara", "Adultery & Illicit Relations", ("V", "S", "A"), ("S", "V", "A")),
    ("Vanik", "Trade, Commerce & Profit", ("Me", "M", "A"), ("M", "Me", "A")),
    ("Vivaha", "Marriage & Conjugal Union", ("V", "Sa", "A"), ("Sa", "V", "A")),
    ("Santapa", "Sorrow & Grief", ("Sa", "M", "A"), ("M", "Sa", "A")),
    ("Sraddha", "Devotion & Faith", ("V", "Ma", "A"), ("Ma", "V", "A")),
    ("Preeti", "Love & Affection", ("V", "M", "A"), ("M", "V", "A")),
    ("Vyapara", "Business & Enterprise", ("Me", "J", "A"), ("J", "Me", "A")),
    ("Kanya", "Daughter & Young Females", ("M", "V", "A"), ("V", "M", "A")),
    ("Paradesa", "Foreign Lands & Foreign Travel", ("Sa", "J", "A"), ("J", "Sa", "A")),
    ("Apamrityu", "Accidental Death & Accidents", ("Sa", "Ma", "A"), ("Ma", "Sa", "A")),
    ("Labha", "Gains & Monetary Profit", ("J", "P", "A"), ("P", "J", "A")),
    ("Jalapatha", "Sea Voyages & Water Journeys", ("Sa", "M", "A"), ("M", "Sa", "A")),
]

def calculate_sahams(
    planets_list: List[Dict[str, Any]],
    asc_deg: float,
    is_day_return: bool
) -> List[Dict[str, Any]]:
    p_deg = {p["planet"]: p["longitude"] for p in planets_list}
    p_deg["A"] = asc_deg

    sahams_result = []
    punya_deg = 0.0

    for name, meaning, day_rule, night_rule in SAHAM_DEFINITIONS:
        rule = day_rule if is_day_return else night_rule
        p_a_key, p_b_key, ref_key = rule

        deg_a = punya_deg if p_a_key == "P" else p_deg.get(p_a_key, asc_deg)
        deg_b = punya_deg if p_b_key == "P" else p_deg.get(p_b_key, asc_deg)
        deg_ref = p_deg.get(ref_key, asc_deg)

        diff = (deg_a - deg_b) % 360.0
        arc_contains_lagna = False
        if deg_b <= deg_a:
            arc_contains_lagna = (deg_b <= asc_deg <= deg_a)
        else:
            arc_contains_lagna = (asc_deg >= deg_b or asc_deg <= deg_a)

        saham_val = (deg_ref + diff) % 360.0
        if not arc_contains_lagna:
            saham_val = (saham_val + 30.0) % 360.0

        if name == "Punya":
            punya_deg = saham_val

        sign_info = get_sign_info(saham_val)
        house = (sign_info["sign_index"] - (int(asc_deg / 30.0) + 1)) % 12 + 1

        sahams_result.append({
            "name": name,
            "significance": meaning,
            "sign_name": sign_info["sign_name"],
            "sign_index": sign_info["sign_index"],
            "degree_formatted": sign_info["formatted"],
            "abs_degree": saham_val,
            "saham_lord": sign_info["sign_lord"],
            "house": house
        })

    return sahams_result

# -----------------------------------------------------------------------------
# 10. TAJIKA YOGAS
# -----------------------------------------------------------------------------

def calculate_tajika_yogas(planets_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    p_dict = {p["planet"]: p for p in planets_list if p["planet"] in SEVEN_PLANETS}
    detected_yogas = []
    SPEED_RANK = {"Moon": 1, "Mercury": 2, "Venus": 3, "Sun": 4, "Mars": 5, "Jupiter": 6, "Saturn": 7}

    for i, p1 in enumerate(SEVEN_PLANETS):
        for j in range(i + 1, len(SEVEN_PLANETS)):
            p2 = SEVEN_PLANETS[j]
            d1 = p_dict[p1]
            d2 = p_dict[p2]

            diff_sign = abs(d1["sign_index"] - d2["sign_index"])
            is_aspecting = diff_sign in [0, 2, 3, 4, 6, 8, 9, 10]
            if not is_aspecting:
                continue

            mean_orb = (TAJIKA_ORBS[p1] + TAJIKA_ORBS[p2]) / 2.0
            deg_diff = abs(d1["degree_in_sign"] - d2["degree_in_sign"])

            if deg_diff <= mean_orb:
                faster = p1 if SPEED_RANK[p1] < SPEED_RANK[p2] else p2
                slower = p2 if faster == p1 else p1

                deg_faster = p_dict[faster]["degree_in_sign"]
                deg_slower = p_dict[slower]["degree_in_sign"]

                if deg_faster < deg_slower:
                    detected_yogas.append({
                        "yoga_name": "Ithasala (Muthasila)",
                        "planets": [faster, slower],
                        "type": "Benefic / Applying",
                        "orb_separation": round(deg_diff, 2),
                        "max_orb": mean_orb,
                        "status": "Applying",
                        "description": f"Faster {faster} is applying towards slower {slower} within orb {round(deg_diff, 2)}°, indicating fulfillment of desire and mutual cooperation."
                    })
                else:
                    detected_yogas.append({
                        "yoga_name": "Eesarpha (Musaripha)",
                        "planets": [faster, slower],
                        "type": "Separating",
                        "orb_separation": round(deg_diff, 2),
                        "max_orb": mean_orb,
                        "status": "Separating",
                        "description": f"Faster {faster} has moved past slower {slower} by {round(deg_diff, 2)}°, indicating fading influence or missed timing."
                    })

    ithasalas = [y for y in detected_yogas if y["yoga_name"].startswith("Ithasala")]
    for ith in ithasalas:
        p1, p2 = ith["planets"]
        if "Moon" in [p1, p2]:
            detected_yogas.append({
                "yoga_name": "Kamboola Yoga",
                "planets": [p1, p2, "Moon"],
                "type": "Highly Auspicious",
                "status": "Active",
                "description": f"The Moon actively participates in the {p1}-{p2} Ithasala, tremendously empowering and guaranteeing the fruition of the yoga."
            })

    return detected_yogas

# -----------------------------------------------------------------------------
# 11. TRIPATAKI CHAKRA & VEDHAS
# -----------------------------------------------------------------------------

MOON_VEDHA_RESULTS = {
    "Sun": "Obstacles due to shortage of money, high fever, mental tensions, disappointments and diseases related to blood.",
    "Moon": "Irritation, short temper, blood disorders, injuries, fear from enemies, obstacles and quarrels.",
    "Mars": "Financial gains, intellectual expansion, acquiring knowledge, disputes with brothers, differences within family and fear from enemies.",
    "Mercury": "Sudden gain in wealth, promotion, pilgrimages, victory in disputes, inclination towards religious deeds and childbirth.",
    "Jupiter": "Victory over enemies, sexual pleasures, rise in income, gaining knowledge, fear from water and success in examinations.",
    "Venus": "Health problems, loss of position and status, association with the low class and loss of wealth due to being cheated by someone close.",
    "Saturn": "Disappointments and failures, dishonour, image being tarnished, loss of wealth and severe health problems.",
    "Rahu": "Falling ill, disappointments and depression, and involvement in public scandals.",
    "Ketu": "Sudden anxieties, spiritual detachment, health vulnerabilities, and unforeseen domestic obstacles."
}

def calculate_tripataki_chakra(
    varsha_asc_sign_idx: int,
    planets_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    vedhas = {}
    TRIPATAKI_OPPOSITES = {
        1: [7, 6, 8], 2: [8, 7, 9], 3: [9, 8, 10], 4: [10, 9, 11],
        5: [11, 10, 12], 6: [12, 11, 1], 7: [1, 12, 2], 8: [2, 1, 3],
        9: [3, 2, 4], 10: [4, 3, 5], 11: [5, 4, 6], 12: [6, 5, 7]
    }

    asc_opps = TRIPATAKI_OPPOSITES.get(varsha_asc_sign_idx, [])
    asc_vedha_planets = [p["planet"] for p in planets_list if p["sign_index"] in asc_opps]
    vedhas["Ascendant"] = asc_vedha_planets

    for p in planets_list:
        p_name = p["planet"]
        sign = p["sign_index"]
        opp_signs = TRIPATAKI_OPPOSITES.get(sign, [])
        hitting_planets = [other["planet"] for other in planets_list if other["planet"] != p_name and other["sign_index"] in opp_signs]
        vedhas[p_name] = hitting_planets

    moon_vedhas = vedhas.get("Moon", [])
    moon_results = []
    for hitter in moon_vedhas:
        if hitter in MOON_VEDHA_RESULTS:
            moon_results.append({
                "planet": hitter,
                "result": MOON_VEDHA_RESULTS[hitter]
            })

    return {
        "vedhas_table": vedhas,
        "moon_vedha_planets": moon_vedhas,
        "results_on_moon": moon_results
    }

# -----------------------------------------------------------------------------
# 12. MONTHLY MASA PRAVESHA CHARTS
# -----------------------------------------------------------------------------

def calculate_monthly_returns(
    jd_annual_return: float,
    natal_sun_lon: float,
    latitude: float,
    longitude: float,
    ayanamsa_mode: str = "LAHIRI"
) -> List[Dict[str, Any]]:
    monthly_charts = []
    with _SWE_AYANAMSA_LOCK:
        set_swisseph_sidereal_mode(ayanamsa_mode)
        flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

        cur_jd = jd_annual_return
        for m in range(1, 13):
            target_deg = (natal_sun_lon + (m - 1) * 30.0) % 360.0

            for _ in range(10):
                res, _ = swe.calc_ut(cur_jd, swe.SUN, flag)
                diff = angle_diff(res[0], target_deg)
                if abs(diff) < 1e-7:
                    break
                cur_jd -= (diff / (res[3] if abs(res[3]) > 0.1 else 0.9856))

            jd_local = cur_jd + (5.5 / 24.0)
            y, mo, d, h_float = swe.revjul(jd_local)
            h = int(h_float)
            minute = int((h_float - h) * 60)
            sec = round(((h_float - h) * 60 - minute) * 60)

            cusps, ascmc = swe.houses_ex(cur_jd, latitude, longitude, b'P', swe.FLG_SIDEREAL)
            asc_idx = int((ascmc[0] % 360.0) / 30.0) + 1

            monthly_charts.append({
                "month_number": m,
                "title": f"Month {m} (Masa {m})",
                "pravesha_date": f"{d:02d}/{mo:02d}/{y} {h:02d}:{minute:02d}:{sec:02d}",
                "solar_sign": ZODIAC_SIGNS[int(target_deg / 30.0)]["name"],
                "masa_lagna": ZODIAC_SIGNS[asc_idx - 1]["name"],
                "masa_lagna_lord": SIGN_LORDS[asc_idx]
            })

            cur_jd += 30.43

    return monthly_charts

# -----------------------------------------------------------------------------
# 13. MASTER VARSHAPHAL CALCULATION PIPELINE
# -----------------------------------------------------------------------------

def generate_varshaphal(
    name: str,
    date_of_birth: str,
    time_of_birth: str,
    place_of_birth: str,
    latitude: float,
    longitude: float,
    timezone: float,
    target_year: int,
    return_place: Optional[str] = None,
    return_latitude: Optional[float] = None,
    return_longitude: Optional[float] = None,
    return_timezone: Optional[float] = None,
    ayanamsa: str = "LAHIRI",
    custom_ayanamsa: Optional[float] = None,
    house_system: str = "Sripathi"
) -> Dict[str, Any]:
    dt_birth = datetime.strptime(f"{date_of_birth} {time_of_birth}", "%Y-%m-%d %H:%M:%S" if len(time_of_birth.split(':')) == 3 else "%Y-%m-%d %H:%M")
    hour_utc_birth = dt_birth.hour + dt_birth.minute / 60.0 + dt_birth.second / 3600.0 - timezone
    jd_birth = calculate_julian_day(dt_birth.year, dt_birth.month, dt_birth.day, hour_utc_birth)

    ret_lat = return_latitude if return_latitude is not None else latitude
    ret_lon = return_longitude if return_longitude is not None else longitude
    ret_tz = return_timezone if return_timezone is not None else timezone
    ret_place = return_place if return_place else place_of_birth

    natal_chart = calculate_chart_at_jd(jd_birth, latitude, longitude, ayanamsa)
    natal_asc_sign = natal_chart["ascendant"]["sign_index"]
    natal_moon = next(p for p in natal_chart["planets"] if p["planet"] == "Moon")
    natal_moon_nak_idx = int(natal_moon["longitude"] * 27 / 360) % 27

    jd_return, natal_sun_lon = find_solar_return_instant(
        jd_birth, dt_birth.year, target_year, ayanamsa, custom_ayanamsa
    )

    jd_ret_local = jd_return + (ret_tz / 24.0)
    ret_y, ret_mo, ret_d, ret_h_float = swe.revjul(jd_ret_local)
    ret_h = int(ret_h_float)
    ret_m = int((ret_h_float - ret_h) * 60)
    ret_s = round(((ret_h_float - ret_h) * 60 - ret_m) * 60)
    if ret_s >= 60:
        ret_s -= 60
        ret_m += 1
    if ret_m >= 60:
        ret_m -= 60
        ret_h += 1

    return_dt = datetime(ret_y, ret_mo, ret_d, ret_h, ret_m, ret_s)
    day_of_week = return_dt.strftime("%A")

    annual_chart = calculate_chart_at_jd(jd_return, ret_lat, ret_lon, ayanamsa)
    varsha_asc_sign = annual_chart["ascendant"]["sign_index"]
    sun_sign = next(p for p in annual_chart["planets"] if p["planet"] == "Sun")["sign_index"]
    moon_planet = next(p for p in annual_chart["planets"] if p["planet"] == "Moon")
    moon_sign = moon_planet["sign_index"]
    varsha_moon_nak_idx = int(moon_planet["longitude"] * 27 / 360) % 27

    sun_house = next(p for p in annual_chart["planets"] if p["planet"] == "Sun")["house"]
    is_day_return = sun_house in [7, 8, 9, 10, 11, 12]

    panchavargeeya_balas = calculate_panchavargeeya_bala(annual_chart["planets"])
    harsha_balas = calculate_harsha_bala(annual_chart["planets"], is_day_return)

    completed_years = target_year - dt_birth.year
    muntha_sign = (natal_asc_sign - 1 + completed_years) % 12 + 1
    panchadhikari_info = calculate_panchadhikari_and_varshesha(
        natal_asc_sign, varsha_asc_sign, muntha_sign, sun_sign, moon_sign,
        is_day_return, panchavargeeya_balas, annual_chart["planets"]
    )

    muntha_info = calculate_muntha(
        natal_asc_sign, varsha_asc_sign, dt_birth.year, target_year, annual_chart["planets"]
    )

    mudda_timeline = calculate_mudda_dasha(
        return_dt, dt_birth.year, target_year, annual_chart["planets"]
    )

    nav_tara_info = calculate_nav_tara_chakra(natal_moon_nak_idx, varsha_moon_nak_idx)

    graha_maitri_annual = calculate_graha_maitri(annual_chart["planets"], "annual")
    graha_maitri_natal = calculate_graha_maitri(natal_chart["planets"], "natal")

    sahams_list = calculate_sahams(annual_chart["planets"], annual_chart["ascendant"]["longitude"], is_day_return)
    tajika_yogas = calculate_tajika_yogas(annual_chart["planets"])
    tripataki_info = calculate_tripataki_chakra(varsha_asc_sign, annual_chart["planets"])
    monthly_charts = calculate_monthly_returns(jd_return, natal_sun_lon, ret_lat, ret_lon, ayanamsa)

    current_mudda = next((m for m in mudda_timeline if m["is_current"]), mudda_timeline[0])

    return {
        "status": "success",
        "metadata": {
            "name": name,
            "date_of_birth": date_of_birth,
            "time_of_birth": time_of_birth,
            "place_of_birth": place_of_birth,
            "target_year": target_year,
            "annual_period": f"{target_year} - {target_year + 1}",
            "return_place": ret_place,
            "return_latitude": ret_lat,
            "return_longitude": ret_lon,
            "return_timezone": ret_tz,
            "ayanamsa": ayanamsa,
            "house_system": house_system,
            "calculation_convention": "Mean / True Solar Return (Swiss Ephemeris Root Finding)",
            "calculation_engine_version": "Tajika Vedic Core 2.0"
        },
        "pravesha_details": {
            "date": return_dt.strftime("%d/%m/%Y"),
            "time": return_dt.strftime("%H:%M:%S"),
            "iso_timestamp": return_dt.isoformat(),
            "day_of_week": day_of_week,
            "is_day_return": is_day_return,
            "julian_day": jd_return,
            "varsha_lagna": annual_chart["ascendant"]["sign_name"],
            "varsha_lagna_lord": annual_chart["ascendant"]["sign_lord"],
            "varsha_lagna_degree": annual_chart["ascendant"]["degree_formatted"],
            "varshesha": panchadhikari_info["varshesha"],
            "varshesha_role": panchadhikari_info["varshesha_role"],
            "muntha_sign": muntha_info["sign_name"],
            "muntha_house": muntha_info["house"],
            "running_mudda_lord": current_mudda["lord"],
            "running_mudda_dates": f"{current_mudda['start_date']} - {current_mudda['end_date']}"
        },
        "annual_chart": annual_chart,
        "natal_chart": natal_chart,
        "panchadhikari_and_varshesha": panchadhikari_info,
        "muntha": muntha_info,
        "panchavargeeya_bala": panchavargeeya_balas,
        "harsha_bala": harsha_balas,
        "mudda_dasha": {
            "timeline": mudda_timeline,
            "current_period": current_mudda
        },
        "nav_tara_chakra": nav_tara_info,
        "graha_maitri": {
            "annual": graha_maitri_annual,
            "natal": graha_maitri_natal
        },
        "sahams": sahams_list,
        "tajika_yogas": tajika_yogas,
        "tripataki_chakra": tripataki_info,
        "monthly_charts": monthly_charts
    }
