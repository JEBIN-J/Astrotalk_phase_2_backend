"""Astronomical Ephemeris & Ayanamsa Calculation Engine."""
from datetime import datetime
from typing import Dict, Any, List
from app.utils.constants import ZODIAC_SIGNS, NAKSHATRAS
from app.services.vedic_engine import (
    calculate_julian_day,
    calculate_lahiri_ayanamsa,
    get_planet_approx_longitudes,
    degree_to_sign_and_dms,
    get_nakshatra_info
)


def get_ayanamsa_offsets(year: int) -> Dict[str, Any]:
    """Calculate values for standard Ayanamsa systems for a given Gregorian year."""
    # J2000 base reference values and annual precession rate (~50.29 arcsec/year)
    delta_years = year - 2000
    precession_deg_per_year = 50.29 / 3600.0  # ~0.013969° per year
    
    lahiri = 23.8565 + (delta_years * precession_deg_per_year)
    kp = lahiri + 0.0988  # Krishnamurti offset
    raman = 22.392 + (delta_years * precession_deg_per_year)  # BV Raman
    yukteshwar = 21.05 + (delta_years * precession_deg_per_year)  # Sri Yukteshwar

    def format_deg(val: float) -> str:
        deg = int(val)
        mins = int((val - deg) * 60)
        secs = int((((val - deg) * 60) - mins) * 60)
        return f"{deg:02d}° {mins:02d}' {secs:02d}\""

    return {
        "year": year,
        "lahiri_ayanamsa": format_deg(lahiri),
        "kp_ayanamsa": format_deg(kp),
        "raman_ayanamsa": format_deg(raman),
        "yukteshwar_ayanamsa": format_deg(yukteshwar),
        "definitions": {
            "lahiri": "Chitrapaksha / Lahiri - Official Government of India calendar standard.",
            "kp": "Krishnamurti Padhdhati - Precise stellar astrology division.",
            "raman": "Prof. B.V. Raman - Traditional South Indian astrological standard.",
            "yukteshwar": "Swami Sri Yukteshwar Giri astronomical epoch alignment."
        }
    }


def calculate_ephemeris(
    date_str: str,
    time_str: str = "12:00",
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    ayanamsa_type: str = "lahiri"
) -> Dict[str, Any]:
    """Generate astronomical planetary ephemeris table for given epoch."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    t_parts = [int(p) for p in time_str.split(":")]
    hour_utc = (t_parts[0] + t_parts[1] / 60.0) - 5.5
    
    jd = calculate_julian_day(dt.year, dt.month, dt.day, hour_utc)
    ayanamsa_val = calculate_lahiri_ayanamsa(jd)
    
    if ayanamsa_type.lower() == "kp":
        ayanamsa_val += 0.0988
    elif ayanamsa_type.lower() == "raman":
        ayanamsa_val -= 1.4645
    elif ayanamsa_type.lower() == "yukteshwar":
        ayanamsa_val -= 2.8065

    raw_planets = get_planet_approx_longitudes(jd, ayanamsa_val)
    entries = []

    for name, (p_deg, speed, is_retro) in raw_planets.items():
        _, sign_name, dms, _ = degree_to_sign_and_dms(p_deg)
        nak_name, _, pada, _ = get_nakshatra_info(p_deg)
        
        entries.append({
            "planet": name,
            "longitude_degrees": round(p_deg, 4),
            "formatted_longitude": dms,
            "sign": sign_name,
            "speed_deg_per_day": round(speed, 4),
            "is_retrograde": is_retro,
            "nakshatra": nak_name,
            "pada": pada
        })

    def format_deg(val: float) -> str:
        deg = int(val)
        mins = int((val - deg) * 60)
        secs = int((((val - deg) * 60) - mins) * 60)
        return f"{deg:02d}° {mins:02d}' {secs:02d}\""

    return {
        "date": f"{date_str} {time_str}",
        "julian_day": round(jd, 4),
        "ayanamsa_name": ayanamsa_type.capitalize(),
        "ayanamsa_value": format_deg(ayanamsa_val),
        "ayanamsa_degrees": round(ayanamsa_val, 4),
        "planets": entries
    }
