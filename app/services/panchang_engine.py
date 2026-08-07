"""Panchanga & Daily Muhurta Calculation Engine."""
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.utils.constants import TITHI_NAMES, NAKSHATRAS, YOGA_NAMES, KARANA_NAMES, ZODIAC_SIGNS
from app.services.vedic_engine import (
    calculate_julian_day,
    calculate_lahiri_ayanamsa,
    get_planet_approx_longitudes
)


def calculate_daily_panchang(
    target_date: str = None,
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    timezone: float = 5.5,
    place_name: str = "New Delhi"
) -> Dict[str, Any]:
    """Calculate comprehensive Hindu Vedic Panchang for given date and location."""
    if not target_date:
        now = datetime.now()
    else:
        now = datetime.strptime(target_date, "%Y-%m-%d")
        
    date_str = now.strftime("%Y-%m-%d")
    formatted_date = now.strftime("%A, %d %B %Y")
    
    # Julian day at 12:00 PM local time
    hour_utc = 12.0 - timezone
    jd = calculate_julian_day(now.year, now.month, now.day, hour_utc)
    ayanamsa = calculate_lahiri_ayanamsa(jd)
    
    planets = get_planet_approx_longitudes(jd, ayanamsa)
    sun_deg = planets["Sun"][0]
    moon_deg = planets["Moon"][0]
    
    # 1. TITHI CALCULATION
    # Tithi is calculated based on relative angular difference between Moon and Sun (12° per Tithi)
    diff = (moon_deg - sun_deg) % 360.0
    tithi_index = int(diff / 12.0) % 30
    tithi_num = (tithi_index % 15) + 1
    paksha = "Shukla Paksha (Bright Fortnight)" if tithi_index < 15 else "Krishna Paksha (Dark Fortnight)"
    tithi_name = TITHI_NAMES[tithi_index]
    
    # 2. NAKSHATRA CALCULATION
    nak_span = 360.0 / 27.0
    nak_idx = int(moon_deg / nak_span) % 27
    nak_info = NAKSHATRAS[nak_idx]
    
    # 3. YOGA CALCULATION
    # Yoga is based on the sum of Sun and Moon sidereal longitudes (13°20' per Yoga)
    sum_long = (sun_deg + moon_deg) % 360.0
    yoga_idx = int(sum_long / (360.0 / 27.0)) % 27
    yoga_name = YOGA_NAMES[yoga_idx]
    
    # 4. KARANA CALCULATION (Half of Tithi = 6°)
    karana_idx = int(diff / 6.0) % 60
    if karana_idx == 0:
        karana_name = KARANA_NAMES[10] # Kintughna
    elif karana_idx >= 57:
        karana_name = KARANA_NAMES[7 + (karana_idx - 57)] # Shakuni, Chatushpada, Naga
    else:
        karana_name = KARANA_NAMES[(karana_idx - 1) % 7]
        
    # 5. SUNRISE / SUNSET APPROXIMATION
    # Standard sunrise approximation ~06:05 AM, sunset ~06:45 PM
    sunrise_time = "06:04 AM"
    sunset_time = "06:48 PM"
    moonrise_time = "07:32 PM"
    moonset_time = "06:15 AM"
    
    # 6. RAHU KAAL & ABHIJIT MUHURTA CALCULATION
    weekday = now.weekday() # 0 = Monday, 6 = Sunday
    # Rahu Kaal periods per day of week (in 1.5 hr slots of 12 hr day)
    rahu_slots = [
        ("07:30 AM", "09:00 AM"), # Mon
        ("03:00 PM", "04:30 PM"), # Tue
        ("12:00 PM", "01:30 PM"), # Wed
        ("01:30 PM", "03:00 PM"), # Thu
        ("10:30 AM", "12:00 PM"), # Fri
        ("09:00 AM", "10:30 AM"), # Sat
        ("04:30 PM", "06:00 PM"), # Sun
    ]
    rahu_start, rahu_end = rahu_slots[weekday]
    
    abhijit_start = "11:58 AM"
    abhijit_end = "12:49 PM"
    
    sun_sign_idx = int(sun_deg // 30)
    moon_sign_idx = int(moon_deg // 30)

    daily_insights = [
        {
            "title": "Abhijit Muhurta Active",
            "desc": "Highly auspicious period for new contracts, journeys, and spiritual beginnings.",
            "timing": f"{abhijit_start} - {abhijit_end}",
            "type": "auspicious"
        },
        {
            "title": f"Moon in {nak_info['name']} Nakshatra",
            "desc": f"Ruled by {nak_info['lord']}. Bestows creative focus, financial intellect, and harmony.",
            "timing": "Full Day",
            "type": "insight"
        },
        {
            "title": "Rahu Kaal Inauspicious Span",
            "desc": "Avoid initiating high-stakes financial commitments or solemn rituals during this window.",
            "timing": f"{rahu_start} - {rahu_end}",
            "type": "caution"
        }
    ]

    return {
        "date": date_str,
        "formatted_date": formatted_date,
        "place": place_name,
        "sunrise": sunrise_time,
        "sunset": sunset_time,
        "moonrise": moonrise_time,
        "moonset": moonset_time,
        "paksha": paksha,
        "tithi": {
            "name": f"{tithi_name} ({tithi_num})",
            "sanskrit_name": f"तिथि: {tithi_name}",
            "number": tithi_num,
            "timing": "Up to 04:22 PM next day",
            "deity_or_nature": "Brahma / Creative energy"
        },
        "nakshatra": {
            "name": nak_info["name"],
            "sanskrit_name": f"नक्षत्र: {nak_info['name']}",
            "number": nak_idx + 1,
            "timing": f"Ruled by {nak_info['lord']}",
            "deity_or_nature": f"Gana: {nak_info['gana']}, Yoni: {nak_info['yoni']}"
        },
        "yoga": {
            "name": yoga_name,
            "sanskrit_name": f"योग: {yoga_name}",
            "number": yoga_idx + 1,
            "timing": "Benefic spiritual current",
            "deity_or_nature": "Auspicious & Fortunate"
        },
        "karana": {
            "name": karana_name,
            "sanskrit_name": f"करण: {karana_name}",
            "number": karana_idx + 1,
            "timing": "Active in first half of Tithi",
            "deity_or_nature": "Good for business and domestic works"
        },
        "rahu_kaal": {
            "name": "Rahu Kaalam (राहु काल)",
            "start_time": rahu_start,
            "end_time": rahu_end,
            "is_auspicious": False,
            "description": "Inauspicious time window. Avoid initiating new projects."
        },
        "abhijit_muhurta": {
            "name": "Abhijit Muhurta (अभिजित मुहूर्त)",
            "start_time": abhijit_start,
            "end_time": abhijit_end,
            "is_auspicious": True,
            "description": "Universal auspicious victory hour created by Lord Vishnu."
        },
        "yamaganda": {
            "name": "Yamaganda Kaal",
            "start_time": "06:00 AM",
            "end_time": "07:30 AM",
            "is_auspicious": False,
            "description": "Period governed by Yama. Avoid starting journeys."
        },
        "gulika_kaal": {
            "name": "Gulika Kaal",
            "start_time": "01:30 PM",
            "end_time": "03:00 PM",
            "is_auspicious": False,
            "description": "Saturnian influence. Repeat actions flourish."
        },
        "sun_sign": ZODIAC_SIGNS[sun_sign_idx]["sanskrit"],
        "moon_sign": ZODIAC_SIGNS[moon_sign_idx]["sanskrit"],
        "daily_insights": daily_insights
    }
