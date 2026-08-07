"""Astronomical Ephemeris & Ayanamsa Calculation Engine powered by Swiss Ephemeris."""
import math
from datetime import datetime
from typing import Dict, Any, List
from app.utils.constants import ZODIAC_SIGNS, NAKSHATRAS
from app.services.vedic_engine import (
    calculate_julian_day,
    calculate_lahiri_ayanamsa,
    get_planet_approx_longitudes,
    degree_to_sign_and_dms,
    get_nakshatra_info,
    SWISSEPH_AVAILABLE
)

try:
    import swisseph as swe
except ImportError:
    try:
        import pyswisseph as swe
    except ImportError:
        swe = None


def format_dms(val: float, is_signed: bool = False) -> str:
    """Format decimal degrees into DMS notation string."""
    sign = "+" if val >= 0 else "-"
    val = abs(val)
    deg = int(val)
    mins = int((val - deg) * 60)
    secs = int((((val - deg) * 60) - mins) * 60)
    if is_signed:
        return f"{sign}{deg:02d}° {mins:02d}' {secs:02d}\""
    return f"{deg:03d}° {mins:02d}' {secs:02d}\""


def get_ayanamsa_offsets(year: int) -> Dict[str, Any]:
    """Calculate values for standard Ayanamsa systems for a given Gregorian year."""
    if SWISSEPH_AVAILABLE and swe is not None:
        jd = swe.julday(year, 1, 1, 0.0)
        
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        lahiri_val = swe.get_ayanamsa_ut(jd)
        
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        kp_val = swe.get_ayanamsa_ut(jd)
        
        swe.set_sid_mode(swe.SIDM_RAMAN)
        raman_val = swe.get_ayanamsa_ut(jd)
        
        swe.set_sid_mode(swe.SIDM_YUKTESHWAR)
        yukteshwar_val = swe.get_ayanamsa_ut(jd)
        
        swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
        fagan_val = swe.get_ayanamsa_ut(jd)
        
        swe.set_sid_mode(getattr(swe, 'SIDM_TRUE_CITRA', swe.SIDM_LAHIRI))
        true_chitra_val = swe.get_ayanamsa_ut(jd)

        swe.set_sid_mode(getattr(swe, 'SIDM_HIPPARCHOS', swe.SIDM_LAHIRI))
        hipparchus_val = swe.get_ayanamsa_ut(jd)

        swe.set_sid_mode(getattr(swe, 'SIDM_SURYASIDDHANTA', swe.SIDM_LAHIRI))
        suryasiddhanta_val = swe.get_ayanamsa_ut(jd)

        systems = {
            "Lahiri (Chitra Paksha)": format_dms(lahiri_val),
            "Krishnamurti (KP)": format_dms(kp_val),
            "B.V. Raman": format_dms(raman_val),
            "Fagan / Bradley": format_dms(fagan_val),
            "Yukteshwar": format_dms(yukteshwar_val),
            "True Chitra / Spica": format_dms(true_chitra_val),
            "Hipparchus": format_dms(hipparchus_val),
            "Suryasiddhanta": format_dms(suryasiddhanta_val)
        }

        ayanamsas_list = [
            {"name": "Lahiri (Chitra Paksha)", "degree": format_dms(lahiri_val), "system": "Government of India Standard", "is_recommended": True},
            {"name": "Krishnamurti (KP)", "degree": format_dms(kp_val), "system": "KP Stellar Astrology", "is_recommended": False},
            {"name": "B.V. Raman", "degree": format_dms(raman_val), "system": "Classical South Indian", "is_recommended": False},
            {"name": "Fagan / Bradley", "degree": format_dms(fagan_val), "system": "Western Sidereal", "is_recommended": False},
            {"name": "Yukteshwar", "degree": format_dms(yukteshwar_val), "system": "Holy Science Alignment", "is_recommended": False},
            {"name": "True Chitra / Spica", "degree": format_dms(true_chitra_val), "system": "Stellar Spica Zero Point", "is_recommended": False},
            {"name": "Hipparchus", "degree": format_dms(hipparchus_val), "system": "Hellenistic Sidereal", "is_recommended": False},
            {"name": "Suryasiddhanta", "degree": format_dms(suryasiddhanta_val), "system": "Ancient Surya Siddhanta", "is_recommended": False}
        ]

        return {
            "year": year,
            "lahiri_ayanamsa": format_dms(lahiri_val),
            "kp_ayanamsa": format_dms(kp_val),
            "raman_ayanamsa": format_dms(raman_val),
            "yukteshwar_ayanamsa": format_dms(yukteshwar_val),
            "fagan_ayanamsa": format_dms(fagan_val),
            "true_chitra_ayanamsa": format_dms(true_chitra_val),
            "systems": systems,
            "ayanamsas": ayanamsas_list
        }

    # Fallback
    delta_years = year - 2000
    precession_deg_per_year = 50.29 / 3600.0
    lahiri = 23.8565 + (delta_years * precession_deg_per_year)
    kp = lahiri + 0.0988
    raman = 22.392 + (delta_years * precession_deg_per_year)
    yukteshwar = 21.05 + (delta_years * precession_deg_per_year)

    systems = {
        "Lahiri (Chitra Paksha)": format_dms(lahiri),
        "Krishnamurti (KP)": format_dms(kp),
        "B.V. Raman": format_dms(raman),
        "Yukteshwar": format_dms(yukteshwar)
    }

    return {
        "year": year,
        "lahiri_ayanamsa": format_dms(lahiri),
        "kp_ayanamsa": format_dms(kp),
        "raman_ayanamsa": format_dms(raman),
        "yukteshwar_ayanamsa": format_dms(yukteshwar),
        "systems": systems,
        "ayanamsas": [
            {"name": "Lahiri (Chitra Paksha)", "degree": format_dms(lahiri), "system": "Government Standard", "is_recommended": True},
            {"name": "Krishnamurti (KP)", "degree": format_dms(kp), "system": "Stellar", "is_recommended": False},
            {"name": "B.V. Raman", "degree": format_dms(raman), "system": "Classical", "is_recommended": False},
            {"name": "Yukteshwar", "degree": format_dms(yukteshwar), "system": "Yogic", "is_recommended": False}
        ]
    }


def calculate_ephemeris(
    date_str: str,
    time_str: str = "12:00",
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    ayanamsa_type: str = "lahiri"
) -> Dict[str, Any]:
    """Generate astronomical planetary ephemeris table using Swiss Ephemeris."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    t_parts = [int(p) for p in time_str.split(":")]
    hour_utc = (t_parts[0] + t_parts[1] / 60.0) - 5.5
    
    jd = calculate_julian_day(dt.year, dt.month, dt.day, hour_utc)
    is_tropical = ayanamsa_type.lower() in ["tropical", "sayana", "none"]
    
    if SWISSEPH_AVAILABLE and swe is not None:
        if not is_tropical:
            if ayanamsa_type.lower() in ["kp", "krishnamurti"]:
                swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
            elif ayanamsa_type.lower() in ["raman", "bvraman"]:
                swe.set_sid_mode(swe.SIDM_RAMAN)
            elif ayanamsa_type.lower() in ["yukteshwar"]:
                swe.set_sid_mode(swe.SIDM_YUKTESHWAR)
            elif ayanamsa_type.lower() in ["fagan", "fagan_bradley"]:
                swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
            else:
                swe.set_sid_mode(swe.SIDM_LAHIRI)
            ayanamsa_val = swe.get_ayanamsa_ut(jd)
        else:
            ayanamsa_val = 0.0

        planet_defs = [
            ("Sun ☉", swe.SUN),
            ("Moon ☽", swe.MOON),
            ("Mercury ☿", swe.MERCURY),
            ("Venus ♀", swe.VENUS),
            ("Mars ♂", swe.MARS),
            ("Jupiter ♃", swe.JUPITER),
            ("Saturn ♄", swe.SATURN),
            ("Uranus ♅", swe.URANUS),
            ("Neptune ♆", swe.NEPTUNE),
            ("Pluto ♇", swe.PLUTO),
            ("True Rahu ☊", swe.TRUE_NODE),
        ]

        entries = []
        flag = swe.FLG_SWIEPH | swe.FLG_SPEED | (swe.FLG_SIDEREAL if not is_tropical else 0)

        for p_label, pid in planet_defs:
            res_ecl, _ = swe.calc_ut(jd, pid, flag)
            res_eq, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL | swe.FLG_SPEED)
            
            p_deg = res_ecl[0] % 360.0
            p_speed = res_ecl[3]
            p_dec = res_eq[1]
            is_retro = p_speed < 0
            
            entries.append({
                "planet": p_label,
                "longitude": format_dms(p_deg),
                "longitude_degrees": round(p_deg, 4),
                "declination": format_dms(p_dec, is_signed=True),
                "speed": f"{'+' if p_speed >= 0 else ''}{format_dms(p_speed)}/d",
                "motion": "Retrograde" if is_retro else "Direct",
                "is_retrograde": is_retro
            })
            
        # Add Ketu
        rahu_entry = next(e for e in entries if "Rahu" in e["planet"])
        ketu_deg = (rahu_entry["longitude_degrees"] + 180.0) % 360.0
        entries.append({
            "planet": "True Ketu ☋",
            "longitude": format_dms(ketu_deg),
            "longitude_degrees": round(ketu_deg, 4),
            "declination": "+00° 00' 00\"",
            "speed": rahu_entry["speed"],
            "motion": "Retrograde",
            "is_retrograde": True
        })

        return {
            "date": f"{date_str} {time_str}",
            "julian_day": round(jd, 4),
            "ayanamsa_name": "Tropical Sayana" if is_tropical else ayanamsa_type.capitalize(),
            "ayanamsa_value": "00° 00' 00\" (Sayana Tropical)" if is_tropical else format_dms(ayanamsa_val),
            "ayanamsa_degrees": round(ayanamsa_val, 4),
            "planets": entries
        }

    # Fallback
    ayanamsa_val = calculate_lahiri_ayanamsa(jd) if not is_tropical else 0.0
    raw_planets = get_planet_approx_longitudes(jd, ayanamsa_val)
    entries = []
    for name, (p_deg, speed, is_retro) in raw_planets.items():
        entries.append({
            "planet": name,
            "longitude": format_dms(p_deg),
            "longitude_degrees": round(p_deg, 4),
            "declination": "+00° 00' 00\"",
            "speed": f"{'+' if speed >= 0 else ''}{format_dms(speed)}/d",
            "motion": "Retrograde" if is_retro else "Direct",
            "is_retrograde": is_retro
        })

    return {
        "date": f"{date_str} {time_str}",
        "julian_day": round(jd, 4),
        "ayanamsa_name": ayanamsa_type.capitalize(),
        "ayanamsa_value": format_dms(ayanamsa_val),
        "ayanamsa_degrees": round(ayanamsa_val, 4),
        "planets": entries
    }
