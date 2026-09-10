import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.services.vedic_engine import ZODIAC_SIGNS, NAKSHATRAS

# Rashi duration years in Kala Chakra Dasha
KC_YEARS = {
    "Aries": 7, "Taurus": 16, "Gemini": 9, "Cancer": 21,
    "Leo": 5, "Virgo": 9, "Libra": 16, "Scorpio": 7,
    "Sagittarius": 10, "Capricorn": 4, "Aquarius": 4, "Pisces": 10
}

# The 27 Nakshatras mapped to Savya/Apasavya
# 1-3 Savya, 4-6 Apasavya, 7-9 Savya, etc.
def is_savya(nak_idx: int) -> bool:
    # nak_idx is 1-indexed (1=Ashwini)
    group = (nak_idx - 1) // 3
    return (group % 2) == 0

# Base Padas (Navamsa mappings)
# Savya Padas:
SAVYA_PADA_1 = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"]
SAVYA_PADA_2 = ["Capricorn", "Aquarius", "Pisces", "Scorpio", "Libra", "Virgo", "Cancer", "Leo", "Gemini"]
SAVYA_PADA_3 = ["Taurus", "Aries", "Pisces", "Aquarius", "Capricorn", "Sagittarius", "Aries", "Taurus", "Gemini"]
SAVYA_PADA_4 = ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Apasavya Padas (Reverse order of sequences):
APASAVYA_PADA_1 = ["Scorpio", "Libra", "Virgo", "Cancer", "Leo", "Gemini", "Taurus", "Aries", "Pisces"]
APASAVYA_PADA_2 = ["Aquarius", "Capricorn", "Sagittarius", "Scorpio", "Libra", "Virgo", "Cancer", "Leo", "Gemini"]
APASAVYA_PADA_3 = ["Taurus", "Aries", "Pisces", "Aquarius", "Capricorn", "Sagittarius", "Aries", "Taurus", "Gemini"]
APASAVYA_PADA_4 = ["Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def get_kalachakra_sequence(is_savya_motion: bool, pada: int) -> List[str]:
    if is_savya_motion:
        if pada == 1: return SAVYA_PADA_1
        if pada == 2: return SAVYA_PADA_2
        if pada == 3: return SAVYA_PADA_3
        if pada == 4: return SAVYA_PADA_4
    else:
        if pada == 1: return APASAVYA_PADA_1
        if pada == 2: return APASAVYA_PADA_2
        if pada == 3: return APASAVYA_PADA_3
        if pada == 4: return APASAVYA_PADA_4
    return SAVYA_PADA_1

def get_deha_jeeva(sequence: List[str], is_savya_motion: bool) -> tuple:
    if is_savya_motion:
        return sequence[0], sequence[-1]
    else:
        return sequence[-1], sequence[0]

def calculate_kalachakra_dasha(
    moon_longitude: float,
    birth_date: datetime,
    days_in_year: float = 365.256364
) -> Dict[str, Any]:
    
    # Calculate Nakshatra (27 system)
    nak_idx = int(moon_longitude / (360.0 / 27.0)) + 1
    deg_inside = moon_longitude - ((nak_idx - 1) * (360.0 / 27.0))
    
    # Calculate Pada EXACTLY
    pada = math.floor(deg_inside / (360.0 / 108.0)) + 1
    if pada > 4: pada = 4
    
    deg_inside_pada = deg_inside - ((pada - 1) * (360.0 / 108.0))
    fraction_elapsed = deg_inside_pada / (360.0 / 108.0)
    fraction_remaining = 1.0 - fraction_elapsed
    
    nak_name = NAKSHATRAS[nak_idx - 1]["name"]
    nak_lord = NAKSHATRAS[nak_idx - 1]["lord"]
    
    savya = is_savya(nak_idx)
    direction = "Savya (Forward)" if savya else "Apasavya (Reverse)"
    
    seq = get_kalachakra_sequence(savya, pada)
    deha, jeeva = get_deha_jeeva(seq, savya)
    
    # Calculate total paramayur (total cycle lifespan)
    total_years = sum(KC_YEARS[rashi] for rashi in seq)
    
    # First Dasha balance
    start_rashi = seq[0]
    balance_years = KC_YEARS[start_rashi] * fraction_remaining
    
    timeline = []
    current_date = birth_date
    current_dasha = None
    
    # Generate Mahadasha
    for i, rashi in enumerate(seq):
        duration = balance_years if i == 0 else KC_YEARS[rashi]
        end_date = current_date + timedelta(days=duration * days_in_year)
        
        # Calculate Antardashas
        antardashas = []
        ad_current_date = current_date
        for ad_rashi in seq:
            ad_duration = duration * (KC_YEARS[ad_rashi] / total_years)
            ad_end_date = ad_current_date + timedelta(days=ad_duration * days_in_year)
            
            antardashas.append({
                "lord": ad_rashi,
                "start_date": ad_current_date.strftime("%Y-%m-%d"),
                "end_date": ad_end_date.strftime("%Y-%m-%d"),
                "duration_years": round(ad_duration, 4)
            })
            ad_current_date = ad_end_date
            
        md_obj = {
            "lord": rashi,
            "start_date": current_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "duration_years": round(duration, 4),
            "antardashas": antardashas
        }
        timeline.append(md_obj)
        current_date = end_date
        
    # Find current period for Prashna (assuming birth_date passed is Prashna time)
    # Wait, the Prashna date IS the birth date in the context of a Prashna chart!
    # Thus the current dasha is always the first one initially.
    # But for a timeline, the "current" is the one active at `birth_date`.
    
    now_date = birth_date # Since this is Prashna, "now" is the chart's date.
    
    active_md = timeline[0]["lord"]
    active_ad = timeline[0]["antardashas"][0]["lord"]
    
    return {
        "moon_nakshatra": nak_name,
        "pada": pada,
        "nakshatra_lord": nak_lord,
        "direction": direction,
        "deha": deha,
        "jeeva": jeeva,
        "total_cycle_years": total_years,
        "first_dasha_rashi": start_rashi,
        "starting_balance_years": round(balance_years, 4),
        "timeline": timeline,
        "current_period": {
            "mahadasha": active_md,
            "antardasha": active_ad
        }
    }
