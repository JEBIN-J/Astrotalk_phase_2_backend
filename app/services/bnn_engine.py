from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import copy
from app.services.vedic_engine import generate_full_kundli
from app.services.bnn_rules import BNN_KARAKAS, BNN_TRINE_GROUPS, get_bnn_relationship, BNN_EVENTS, analyze_bnn_combination

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
}

OWN_SIGNS = {
    "Mars": [1, 8], "Venus": [2, 7], "Mercury": [3, 6], "Moon": [4],
    "Sun": [5], "Jupiter": [9, 12], "Saturn": [10, 11]
}

def normalize_sign(idx: int) -> int:
    """Ensures sign index is strictly between 1 and 12."""
    return ((int(idx) - 1) % 12) + 1

def calculate_period_dates(dob_str: str, age_start: float, age_end: float) -> Tuple[str, str]:
    """
    Converts age in decimal years into exact calendar start_date and end_date.
    Uses accurate timedelta based on 365.25 days/year from the natal birth date.
    """
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        d_start = dob + timedelta(days=int(round(age_start * 365.25)))
        d_end = dob + timedelta(days=int(round(age_end * 365.25)))
        return d_start.strftime("%Y-%m-%d"), d_end.strftime("%Y-%m-%d")
    except Exception:
        return "N/A", "N/A"

def populate_progression_hierarchy(
    major_timeline: List[Dict[str, Any]],
    current_age: float,
    dob_str: str,
    rate_name: str,
    micro_rate_name: str,
    is_reverse: bool = False
) -> Dict[str, Any]:
    """
    Subdivides each Major BNN period into 12 deterministic Minor periods,
    and each Minor period into 12 deterministic Micro periods.
    Identifies the active Major, Minor, and Micro periods for the current age.
    """
    active_major = None
    active_minor = None
    active_micro = None

    for maj in major_timeline:
        m_start_date, m_end_date = calculate_period_dates(dob_str, maj["age_start"], maj["age_end"])
        maj["start_date"] = m_start_date
        maj["end_date"] = m_end_date
        maj["is_current"] = (maj["age_start"] <= current_age < maj["age_end"])
        maj["is_active"] = maj["is_current"]
        
        maj_dur = maj["duration"]
        step_dur = maj_dur / 12.0
        minor_periods = []
        for m in range(12):
            min_s_idx = normalize_sign(maj["sign_index"] - m if is_reverse else maj["sign_index"] + m)
            min_age_start = round(maj["age_start"] + m * step_dur, 2)
            min_age_end = round(min(maj["age_end"], maj["age_start"] + (m + 1) * step_dur), 2) if m < 11 else maj["age_end"]
            min_start_date, min_end_date = calculate_period_dates(dob_str, min_age_start, min_age_end)
            is_min_active = maj["is_current"] and (
                (min_age_start <= current_age < min_age_end) or (m == 11 and current_age >= min_age_start)
            )

            # Micro periods (12 subdivisions of this minor period)
            min_dur = min_age_end - min_age_start
            micro_step_dur = min_dur / 12.0
            micro_periods = []
            for k in range(12):
                mic_s_idx = normalize_sign(min_s_idx - k if is_reverse else min_s_idx + k)
                mic_age_start = round(min_age_start + k * micro_step_dur, 3)
                mic_age_end = round(min(min_age_end, min_age_start + (k + 1) * micro_step_dur), 3) if k < 11 else min_age_end
                mic_start_date, mic_end_date = calculate_period_dates(dob_str, mic_age_start, mic_age_end)
                is_mic_active = is_min_active and (
                    (mic_age_start <= current_age < mic_age_end) or (k == 11 and current_age >= mic_age_start)
                )

                mic_item = {
                    "step": k + 1,
                    "level": "micro",
                    "sign_index": mic_s_idx,
                    "sign_name": SIGNS[mic_s_idx - 1],
                    "age_start": mic_age_start,
                    "age_end": mic_age_end,
                    "duration": round(mic_age_end - mic_age_start, 3),
                    "start_date": mic_start_date,
                    "end_date": mic_end_date,
                    "is_current": is_mic_active,
                    "is_active": is_mic_active
                }
                micro_periods.append(mic_item)
                if is_mic_active and active_micro is None:
                    active_micro = mic_item

            min_item = {
                "step": m + 1,
                "level": "minor",
                "sign_index": min_s_idx,
                "sign_name": SIGNS[min_s_idx - 1],
                "age_start": min_age_start,
                "age_end": min_age_end,
                "duration": round(min_age_end - min_age_start, 2),
                "start_date": min_start_date,
                "end_date": min_end_date,
                "is_current": is_min_active,
                "is_active": is_min_active,
                "micro_periods": micro_periods
            }
            minor_periods.append(min_item)
            if is_min_active and active_minor is None:
                active_minor = min_item

        maj["minor_periods"] = minor_periods
        if maj["is_current"] and active_major is None:
            active_major = maj

    # Fallback if before age 0 or beyond timeline
    if not active_major and major_timeline:
        active_major = major_timeline[0]
        active_major["is_current"] = True
        active_major["is_active"] = True
    if not active_minor and active_major and active_major.get("minor_periods"):
        active_minor = active_major["minor_periods"][0]
        active_minor["is_current"] = True
        active_minor["is_active"] = True
    if not active_micro and active_minor and active_minor.get("micro_periods"):
        active_micro = active_minor["micro_periods"][0]
        active_micro["is_current"] = True
        active_micro["is_active"] = True

    return {
        "active_major": active_major,
        "active_minor": active_minor,
        "active_micro": active_micro
    }


def calculate_current_age(dob_str: str, target_date_str: str = None) -> float:
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    now = datetime.strptime(target_date_str, "%Y-%m-%d") if target_date_str else datetime.utcnow() + __import__('datetime').timedelta(hours=5.5)
    days_alive = (now - dob).days
    return max(0.0, days_alive / 365.25)

def get_dispositor(sign_index: int, planets: List[Dict]) -> Optional[Dict]:
    lord_name = SIGN_LORDS.get(sign_index)
    return next((p for p in planets if p.get("planet_name_simple") == lord_name), None)

def check_parivartana(planet_name: str, planets: List[Dict]) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Detects Parivartana Yoga (Exchange of Signs / Mutual Reception).
    Returns (has_exchange, exchange_partner_planet_name, own_sign_where_partner_is_located).
    """
    p = next((x for x in planets if x.get("planet") == planet_name or x.get("name") == planet_name), None)
    if not p:
        return False, None, None
        
    p_sign = p.get("sign_index", 1)
    disp_lord = SIGN_LORDS.get(p_sign)
    if not disp_lord or disp_lord == planet_name:
        return False, None, None
        
    other_p = next((x for x in planets if x.get("planet") == disp_lord or x.get("name") == disp_lord), None)
    if not other_p:
        return False, None, None
        
    other_sign = other_p.get("sign_index", 1)
    # Check if other planet is in a sign ruled by planet_name
    if SIGN_LORDS.get(other_sign) == planet_name:
        return True, disp_lord, other_sign
        
    return False, None, None

def calculate_jupiter_progression(jupiter: Dict, planets: List[Dict], current_age: float, dob_str: str = "1990-01-01") -> Dict[str, Any]:
    """
    Calculates BNN Jupiter Progression based strictly on PROGRESSION RULES.pdf:
    - Direct: 1st = (30 - degree) * 0.4 yrs in natal sign. Then 12 yrs each in next sign in zodiacal order.
    - Retrograde: 1st = (30 - degree) * 0.4 yrs in natal sign. 2nd = 12 yrs from previous sign (sign - 1).
      3rd = 12 yrs in next sign to natal position (sign + 1), and forward thereafter.
    - Exchange (Parivartana): Normal rules up to 36 yrs (4th progression stops at 36 yrs).
      After 36 yrs, shift Jupiter to its own sign, progressing 12 yrs each forward (36-48, 48-60, 60-72...).
    - Minor Progression: Each sign takes 1.0 year, starting from the active major progression sign.
    """
    deg = float(jupiter.get("degree_decimal", 0.0)) % 30.0
    natal_sign = int(jupiter.get("sign_index", 1))
    is_retro = bool(jupiter.get("retrograde", False))
    
    has_exchange, exchange_partner, exchange_own_sign = check_parivartana("Jupiter", planets)
    if not exchange_own_sign:
        exchange_own_sign = 9  # Default Moolatrikona (Sagittarius)
        
    dur1 = (30.0 - deg) * 0.4
    timeline = []
    
    # 1st Major Progression
    t_start = 0.0
    t_end = dur1
    sign1 = natal_sign
    timeline.append({
        "progression_number": 1,
        "sign_index": sign1,
        "sign_name": SIGNS[sign1 - 1],
        "age_start": round(t_start, 2),
        "age_end": round(t_end, 2),
        "duration": round(t_end - t_start, 2),
        "rule_detail": f"(30 - {deg:.2f}°) × 0.4 = {dur1:.2f} yrs in Natal {SIGNS[sign1 - 1]}",
        "is_exchange": False
    })
    
    if has_exchange:
        # Page 4: 1st and 4th progression are incomplete; 4th stops at 36 yrs.
        # 2nd Progression: 12 yrs
        t_start = t_end
        t_end = t_start + 12.0
        sign2 = normalize_sign(natal_sign - 1 if is_retro else natal_sign + 1)
        timeline.append({
            "progression_number": 2,
            "sign_index": sign2,
            "sign_name": SIGNS[sign2 - 1],
            "age_start": round(t_start, 2),
            "age_end": round(t_end, 2),
            "duration": round(t_end - t_start, 2),
            "rule_detail": f"12 yrs from {'Previous Sign' if is_retro else 'Next Sign'}",
            "is_exchange": False
        })
        
        # 3rd Progression: 12 yrs
        t_start = t_end
        t_end = t_start + 12.0
        sign3 = normalize_sign(natal_sign + 1 if is_retro else natal_sign + 2)
        timeline.append({
            "progression_number": 3,
            "sign_index": sign3,
            "sign_name": SIGNS[sign3 - 1],
            "age_start": round(t_start, 2),
            "age_end": round(t_end, 2),
            "duration": round(t_end - t_start, 2),
            "rule_detail": f"12 yrs from {'Next Sign to Natal' if is_retro else 'Forward Sign'}",
            "is_exchange": False
        })
        
        # 4th Progression: stops at 36 yrs!
        t_start = t_end
        t_end = 36.0
        dur4 = max(0.0, t_end - t_start)
        sign4 = normalize_sign(natal_sign + 2 if is_retro else natal_sign + 3)
        timeline.append({
            "progression_number": 4,
            "sign_index": sign4,
            "sign_name": SIGNS[sign4 - 1],
            "age_start": round(t_start, 2),
            "age_end": round(t_end, 2),
            "duration": round(dur4, 2),
            "rule_detail": f"Stops at age 36 for Parivartana exchange with {exchange_partner}",
            "is_exchange": False
        })
        
        # 5th Progression onward: from own sign, 12 years each forward
        p_num = 5
        curr_s = exchange_own_sign
        t_curr = 36.0
        while t_curr < 120.0:
            timeline.append({
                "progression_number": p_num,
                "sign_index": curr_s,
                "sign_name": SIGNS[curr_s - 1],
                "age_start": round(t_curr, 2),
                "age_end": round(t_curr + 12.0, 2),
                "duration": 12.0,
                "rule_detail": f"Exchange Shift: 12 yrs in {SIGNS[curr_s - 1]} (Own Sign)" if p_num == 5 else f"12 yrs forward in {SIGNS[curr_s - 1]}",
                "is_exchange": True
            })
            p_num += 1
            curr_s = normalize_sign(curr_s + 1)
            t_curr += 12.0
    else:
        # Standard Jupiter (Direct or Retrograde)
        p_num = 2
        t_curr = t_end
        
        if is_retro:
            # 2nd progression: from previous sign (sign - 1)
            sign2 = normalize_sign(natal_sign - 1)
            timeline.append({
                "progression_number": 2,
                "sign_index": sign2,
                "sign_name": SIGNS[sign2 - 1],
                "age_start": round(t_curr, 2),
                "age_end": round(t_curr + 12.0, 2),
                "duration": 12.0,
                "rule_detail": f"Retro: 12 yrs from Previous Sign ({SIGNS[sign2 - 1]})",
                "is_exchange": False
            })
            t_curr += 12.0
            
            # 3rd progression: next sign to natal position (natal + 1)
            sign3 = normalize_sign(natal_sign + 1)
            timeline.append({
                "progression_number": 3,
                "sign_index": sign3,
                "sign_name": SIGNS[sign3 - 1],
                "age_start": round(t_curr, 2),
                "age_end": round(t_curr + 12.0, 2),
                "duration": 12.0,
                "rule_detail": f"Retro: 12 yrs from Next Sign to Natal ({SIGNS[sign3 - 1]})",
                "is_exchange": False
            })
            t_curr += 12.0
            
            # 4th+: forward thereafter (natal + 2, natal + 3...)
            step = 2
            p_num = 4
            while t_curr < 120.0:
                s = normalize_sign(natal_sign + step)
                timeline.append({
                    "progression_number": p_num,
                    "sign_index": s,
                    "sign_name": SIGNS[s - 1],
                    "age_start": round(t_curr, 2),
                    "age_end": round(t_curr + 12.0, 2),
                    "duration": 12.0,
                    "rule_detail": f"Forward: 12 yrs in {SIGNS[s - 1]}",
                    "is_exchange": False
                })
                t_curr += 12.0
                p_num += 1
                step += 1
        else:
            # Direct: Next 12 yrs from next sign and so on
            step = 1
            while t_curr < 120.0:
                s = normalize_sign(natal_sign + step)
                timeline.append({
                    "progression_number": p_num,
                    "sign_index": s,
                    "sign_name": SIGNS[s - 1],
                    "age_start": round(t_curr, 2),
                    "age_end": round(t_curr + 12.0, 2),
                    "duration": 12.0,
                    "rule_detail": f"Direct: 12 yrs in {SIGNS[s - 1]}",
                    "is_exchange": False
                })
                t_curr += 12.0
                p_num += 1
                step += 1

    # Populate complete 3-level progression hierarchy (Major -> 12 Minor -> 12 Micro)
    hierarchy = populate_progression_hierarchy(
        timeline, current_age, dob_str,
        rate_name="1.0 Year / Sign",
        micro_rate_name="1.0 Month / Sign",
        is_reverse=False
    )
    active_major = hierarchy["active_major"]
    active_minor = hierarchy["active_minor"]
    active_micro = hierarchy["active_micro"]

    elapsed_in_major = max(0.0, current_age - active_major["age_start"])
    minor_elapsed = max(0.0, current_age - active_minor["age_start"])
    minor_remaining = max(0.0, active_minor["age_end"] - current_age)

    return {
        "natal_sign": jupiter.get("sign", ""),
        "natal_sign_index": natal_sign,
        "natal_degree": jupiter.get("degree", ""),
        "degree_in_sign": round(deg, 2),
        "is_retrograde": is_retro,
        "has_exchange": has_exchange,
        "exchange_partner": exchange_partner,
        "exchange_sign": SIGNS[exchange_own_sign - 1] if has_exchange else None,
        "current_age": round(current_age, 2),
        "current_cycle": active_major["progression_number"],
        "current_progressed_sign_index": active_major["sign_index"],
        "current_progressed_sign_name": active_major["sign_name"],
        "elapsed_progression_years": round(elapsed_in_major, 2),
        "remaining_progression_years": round(max(0.0, active_major["age_end"] - current_age), 2),
        "major_progression": {
            "level": "major",
            "progression_number": active_major["progression_number"],
            "sign": active_major["sign_name"],
            "sign_index": active_major["sign_index"],
            "age_start": active_major["age_start"],
            "age_end": active_major["age_end"],
            "start_date": active_major.get("start_date"),
            "end_date": active_major.get("end_date"),
            "duration": active_major["duration"],
            "rule_detail": active_major.get("rule_detail", "")
        },
        "minor_progression": {
            "level": "minor",
            "step": active_minor["step"],
            "sign": active_minor["sign_name"],
            "sign_index": active_minor["sign_index"],
            "age_start": active_minor["age_start"],
            "age_end": active_minor["age_end"],
            "start_date": active_minor.get("start_date"),
            "end_date": active_minor.get("end_date"),
            "duration": active_minor["duration"],
            "elapsed_years": round(minor_elapsed, 2),
            "remaining_years": round(minor_remaining, 2),
            "rate_per_sign": "1.0 Year / Sign",
            "active_periods": active_major.get("minor_periods", [])
        },
        "micro_progression": {
            "level": "micro",
            "step": active_micro["step"],
            "sign": active_micro["sign_name"],
            "sign_index": active_micro["sign_index"],
            "age_start": active_micro["age_start"],
            "age_end": active_micro["age_end"],
            "start_date": active_micro.get("start_date"),
            "end_date": active_micro.get("end_date"),
            "duration": active_micro["duration"],
            "elapsed_days": int(round(max(0.0, current_age - active_micro["age_start"]) * 365.25)),
            "remaining_days": int(round(max(0.0, active_micro["age_end"] - current_age) * 365.25)),
            "rate_per_sign": "1.0 Month / Sign",
            "active_periods": active_minor.get("micro_periods", [])
        },
        "timeline": timeline[:8]
    }

def calculate_saturn_progression(saturn: Dict, planets: List[Dict], jupiter: Optional[Dict], current_age: float, dob_str: str = "1990-01-01") -> Dict[str, Any]:
    """
    Calculates BNN Saturn Progression based strictly on PROGRESSION RULES.pdf:
    - Direct: 1st = (30 - degree) yrs in natal sign. Then 30 yrs each from next sign in zodiacal order.
    - Retrograde:
      - Rule A (If Jupiter is connected in 1, 2, 3, 5, 7, 9, 11, 12 from Saturn):
        1st = (30 - degree) yrs in natal sign. 2nd = 30 yrs from previous sign (sign - 1).
        3rd = 30 yrs from next sign to natal position (sign + 1), and forward thereafter.
      - Rule B (If Jupiter is NOT connected, i.e., in 4, 6, 8, 10 from Saturn):
        Shift Saturn to previous sign and use Rule of Direct Saturn:
        1st = (30 - degree) yrs from previous sign (sign - 1). 2nd = 30 yrs from natal sign.
        3rd = 30 yrs from next sign (sign + 1), and forward thereafter.
    - Exchange (Parivartana): Normal rules up to 36 yrs. After 36 yrs, shift Saturn to own sign,
      progressing 30 yrs each (36-66, 66-96).
    - Minor Progression: Each sign takes 2.5 years, starting from the active major progression sign.
    """
    deg = float(saturn.get("degree_decimal", 0.0)) % 30.0
    natal_sign = int(saturn.get("sign_index", 1))
    is_retro = bool(saturn.get("retrograde", False))
    
    has_exchange, exchange_partner, exchange_own_sign = check_parivartana("Saturn", planets)
    if not exchange_own_sign:
        exchange_own_sign = 10  # Default Capricorn
        
    dur1 = (30.0 - deg) * 1.0  # 30 yrs / 30 deg = 1.0 yr/deg
    
    jup_connected = False
    dist_from_sat = None
    if jupiter:
        jup_sign = int(jupiter.get("sign_index", 1))
        dist_from_sat = ((jup_sign - natal_sign) % 12) + 1
        if dist_from_sat in [1, 2, 3, 5, 7, 9, 11, 12]:
            jup_connected = True
            
    timeline = []
    
    if has_exchange:
        # Page 4: Upto 36 years use normal rules. After 36 yrs shift to own sign, 30 yrs each.
        if dur1 >= 36.0:
            s1 = natal_sign if (not is_retro or jup_connected) else normalize_sign(natal_sign - 1)
            timeline.append({
                "progression_number": 1,
                "sign_index": s1,
                "sign_name": SIGNS[s1 - 1],
                "age_start": 0.0,
                "age_end": 36.0,
                "duration": 36.0,
                "rule_detail": f"Exchange capped at 36 yrs in {SIGNS[s1 - 1]}",
                "is_exchange": False
            })
        else:
            s1 = natal_sign if (not is_retro or jup_connected) else normalize_sign(natal_sign - 1)
            timeline.append({
                "progression_number": 1,
                "sign_index": s1,
                "sign_name": SIGNS[s1 - 1],
                "age_start": 0.0,
                "age_end": round(dur1, 2),
                "duration": round(dur1, 2),
                "rule_detail": f"(30 - {deg:.2f}°) × 1.0 = {dur1:.2f} yrs in {SIGNS[s1 - 1]}",
                "is_exchange": False
            })
            
            if is_retro and not jup_connected:
                s2 = natal_sign
            elif is_retro and jup_connected:
                s2 = normalize_sign(natal_sign - 1)
            else:
                s2 = normalize_sign(natal_sign + 1)
                
            timeline.append({
                "progression_number": 2,
                "sign_index": s2,
                "sign_name": SIGNS[s2 - 1],
                "age_start": round(dur1, 2),
                "age_end": 36.0,
                "duration": round(36.0 - dur1, 2),
                "rule_detail": f"Capped at 36 yrs for Parivartana shift to own sign {SIGNS[exchange_own_sign - 1]}",
                "is_exchange": False
            })
            
        curr_s = exchange_own_sign
        t_curr = 36.0
        p_num = len(timeline) + 1
        while t_curr < 120.0:
            timeline.append({
                "progression_number": p_num,
                "sign_index": curr_s,
                "sign_name": SIGNS[curr_s - 1],
                "age_start": round(t_curr, 2),
                "age_end": round(t_curr + 30.0, 2),
                "duration": 30.0,
                "rule_detail": f"Exchange Shift: 30 yrs in {SIGNS[curr_s - 1]} (Own Sign)" if p_num == 3 else f"30 yrs forward in {SIGNS[curr_s - 1]}",
                "is_exchange": True
            })
            curr_s = normalize_sign(curr_s + 1)
            t_curr += 30.0
            p_num += 1
    else:
        # Standard Saturn (Direct or Retro Rule A / B)
        if not is_retro:
            # Direct Saturn
            timeline.append({
                "progression_number": 1,
                "sign_index": natal_sign,
                "sign_name": SIGNS[natal_sign - 1],
                "age_start": 0.0,
                "age_end": round(dur1, 2),
                "duration": round(dur1, 2),
                "rule_detail": f"Direct: (30 - {deg:.2f}°) = {dur1:.2f} yrs in Natal {SIGNS[natal_sign - 1]}",
                "is_exchange": False
            })
            t_curr = dur1
            step = 1
            p_num = 2
            while t_curr < 120.0:
                s = normalize_sign(natal_sign + step)
                timeline.append({
                    "progression_number": p_num,
                    "sign_index": s,
                    "sign_name": SIGNS[s - 1],
                    "age_start": round(t_curr, 2),
                    "age_end": round(t_curr + 30.0, 2),
                    "duration": 30.0,
                    "rule_detail": f"Direct: 30 yrs forward in {SIGNS[s - 1]}",
                    "is_exchange": False
                })
                t_curr += 30.0
                step += 1
                p_num += 1
        else:
            # Retrograde Saturn
            if jup_connected:
                # Rule A: Jupiter connected
                timeline.append({
                    "progression_number": 1,
                    "sign_index": natal_sign,
                    "sign_name": SIGNS[natal_sign - 1],
                    "age_start": 0.0,
                    "age_end": round(dur1, 2),
                    "duration": round(dur1, 2),
                    "rule_detail": f"Retro Rule A (Jup in house {dist_from_sat}): {dur1:.2f} yrs in Natal {SIGNS[natal_sign - 1]}",
                    "is_exchange": False
                })
                t_curr = dur1
                s2 = normalize_sign(natal_sign - 1)
                timeline.append({
                    "progression_number": 2,
                    "sign_index": s2,
                    "sign_name": SIGNS[s2 - 1],
                    "age_start": round(t_curr, 2),
                    "age_end": round(t_curr + 30.0, 2),
                    "duration": 30.0,
                    "rule_detail": f"Retro Rule A: 30 yrs from Previous Sign ({SIGNS[s2 - 1]})",
                    "is_exchange": False
                })
                t_curr += 30.0
                step = 1
                p_num = 3
                while t_curr < 120.0:
                    s = normalize_sign(natal_sign + step)
                    timeline.append({
                        "progression_number": p_num,
                        "sign_index": s,
                        "sign_name": SIGNS[s - 1],
                        "age_start": round(t_curr, 2),
                        "age_end": round(t_curr + 30.0, 2),
                        "duration": 30.0,
                        "rule_detail": f"Retro Rule A: 30 yrs forward in {SIGNS[s - 1]}",
                        "is_exchange": False
                    })
                    t_curr += 30.0
                    step += 1
                    p_num += 1
            else:
                # Rule B: Jupiter not connected (house 4, 6, 8, 10)
                # Shift Saturn to previous sign and use Rule of Direct Saturn
                s1 = normalize_sign(natal_sign - 1)
                timeline.append({
                    "progression_number": 1,
                    "sign_index": s1,
                    "sign_name": SIGNS[s1 - 1],
                    "age_start": 0.0,
                    "age_end": round(dur1, 2),
                    "duration": round(dur1, 2),
                    "rule_detail": f"Retro Rule B (Jup in house {dist_from_sat}): Shifted to Prev Sign {SIGNS[s1 - 1]} for {dur1:.2f} yrs",
                    "is_exchange": False
                })
                t_curr = dur1
                timeline.append({
                    "progression_number": 2,
                    "sign_index": natal_sign,
                    "sign_name": SIGNS[natal_sign - 1],
                    "age_start": round(t_curr, 2),
                    "age_end": round(t_curr + 30.0, 2),
                    "duration": 30.0,
                    "rule_detail": f"Retro Rule B: 30 yrs in Natal Sign ({SIGNS[natal_sign - 1]})",
                    "is_exchange": False
                })
                t_curr += 30.0
                step = 1
                p_num = 3
                while t_curr < 120.0:
                    s = normalize_sign(natal_sign + step)
                    timeline.append({
                        "progression_number": p_num,
                        "sign_index": s,
                        "sign_name": SIGNS[s - 1],
                        "age_start": round(t_curr, 2),
                        "age_end": round(t_curr + 30.0, 2),
                        "duration": 30.0,
                        "rule_detail": f"Retro Rule B: 30 yrs forward in {SIGNS[s - 1]}",
                        "is_exchange": False
                    })
                    t_curr += 30.0
                    step += 1
                    p_num += 1

    # Populate complete 3-level progression hierarchy (Major -> 12 Minor -> 12 Micro)
    hierarchy = populate_progression_hierarchy(
        timeline, current_age, dob_str,
        rate_name="2.5 Years / Sign",
        micro_rate_name="2.5 Months / Sign",
        is_reverse=False
    )
    active_major = hierarchy["active_major"]
    active_minor = hierarchy["active_minor"]
    active_micro = hierarchy["active_micro"]

    elapsed_in_major = max(0.0, current_age - active_major["age_start"])
    minor_elapsed = max(0.0, current_age - active_minor["age_start"])
    minor_remaining = max(0.0, active_minor["age_end"] - current_age)

    return {
        "natal_sign": saturn.get("sign", ""),
        "natal_sign_index": natal_sign,
        "natal_degree": saturn.get("degree", ""),
        "degree_in_sign": round(deg, 2),
        "is_retrograde": is_retro,
        "jupiter_connected": jup_connected,
        "jupiter_house_from_saturn": dist_from_sat,
        "retrograde_rule": "Rule A (Jup Connected)" if (is_retro and jup_connected) else ("Rule B (Jup Not Connected)" if is_retro else "N/A (Direct)"),
        "has_exchange": has_exchange,
        "exchange_partner": exchange_partner,
        "exchange_sign": SIGNS[exchange_own_sign - 1] if has_exchange else None,
        "current_age": round(current_age, 2),
        "cycle": active_major["progression_number"],
        "current_progressed_sign_index": active_major["sign_index"],
        "current_progressed_sign_name": active_major["sign_name"],
        "elapsed_progression_years": round(elapsed_in_major, 2),
        "remaining_progression_years": round(max(0.0, active_major["age_end"] - current_age), 2),
        "major_progression": {
            "level": "major",
            "progression_number": active_major["progression_number"],
            "sign": active_major["sign_name"],
            "sign_index": active_major["sign_index"],
            "age_start": active_major["age_start"],
            "age_end": active_major["age_end"],
            "start_date": active_major.get("start_date"),
            "end_date": active_major.get("end_date"),
            "duration": active_major["duration"],
            "rule_detail": active_major.get("rule_detail", "")
        },
        "minor_progression": {
            "level": "minor",
            "step": active_minor["step"],
            "sign": active_minor["sign_name"],
            "sign_index": active_minor["sign_index"],
            "age_start": active_minor["age_start"],
            "age_end": active_minor["age_end"],
            "start_date": active_minor.get("start_date"),
            "end_date": active_minor.get("end_date"),
            "duration": active_minor["duration"],
            "elapsed_years": round(minor_elapsed, 2),
            "remaining_years": round(minor_remaining, 2),
            "rate_per_sign": "2.5 Years / Sign",
            "active_periods": active_major.get("minor_periods", [])
        },
        "micro_progression": {
            "level": "micro",
            "step": active_micro["step"],
            "sign": active_micro["sign_name"],
            "sign_index": active_micro["sign_index"],
            "age_start": active_micro["age_start"],
            "age_end": active_micro["age_end"],
            "start_date": active_micro.get("start_date"),
            "end_date": active_micro.get("end_date"),
            "duration": active_micro["duration"],
            "elapsed_days": int(round(max(0.0, current_age - active_micro["age_start"]) * 365.25)),
            "remaining_days": int(round(max(0.0, active_micro["age_end"] - current_age) * 365.25)),
            "rate_per_sign": "2.5 Months / Sign",
            "active_periods": active_minor.get("micro_periods", [])
        },
        "timeline": timeline[:6]
    }

def calculate_node_progression(planet_name: str, node: Dict, current_age: float, dob_str: str = "1990-01-01") -> Dict[str, Any]:
    """
    Calculates BNN Rahu / Ketu Major & Minor Progression based on PROGRESSION RULES.pdf:
    - Progresses in REVERSE direction.
    - 1st Major Progression = degree of Node × 0.6 yrs from natal position.
    - Subsequent Major Progressions = 18 yrs each from previous signs in reverse (sign - 1, sign - 2...).
    - Minor Progression = 1.5 yrs each sign in REVERSE direction starting from the active major sign.
    """
    deg = float(node.get("degree_decimal", 0.0)) % 30.0
    natal_sign = int(node.get("sign_index", 1))
    
    dur1 = deg * 0.6
    timeline = []
    
    timeline.append({
        "progression_number": 1,
        "sign_index": natal_sign,
        "sign_name": SIGNS[natal_sign - 1],
        "age_start": 0.0,
        "age_end": round(dur1, 2),
        "duration": round(dur1, 2),
        "rule_detail": f"{deg:.2f}° × 0.6 = {dur1:.2f} yrs in Natal {SIGNS[natal_sign - 1]} (Reverse)"
    })
    
    t_curr = dur1
    step = 1
    p_num = 2
    while t_curr < 120.0:
        s = normalize_sign(natal_sign - step)
        timeline.append({
            "progression_number": p_num,
            "sign_index": s,
            "sign_name": SIGNS[s - 1],
            "age_start": round(t_curr, 2),
            "age_end": round(t_curr + 18.0, 2),
            "duration": 18.0,
            "rule_detail": f"18 yrs reverse in {SIGNS[s - 1]}"
        })
        t_curr += 18.0
        step += 1
        p_num += 1

    # Populate complete 3-level progression hierarchy (Major -> 12 Minor -> 12 Micro)
    hierarchy = populate_progression_hierarchy(
        timeline, current_age, dob_str,
        rate_name="1.5 Years / Sign (Reverse)",
        micro_rate_name="1.5 Months / Sign (Reverse)",
        is_reverse=True
    )
    active_major = hierarchy["active_major"]
    active_minor = hierarchy["active_minor"]
    active_micro = hierarchy["active_micro"]

    elapsed_in_major = max(0.0, current_age - active_major["age_start"])
    minor_elapsed = max(0.0, current_age - active_minor["age_start"])
    minor_remaining = max(0.0, active_minor["age_end"] - current_age)

    return {
        "planet": planet_name,
        "natal_sign": node.get("sign", ""),
        "natal_sign_index": natal_sign,
        "natal_degree": node.get("degree", ""),
        "degree_in_sign": round(deg, 2),
        "direction": "Reverse",
        "current_age": round(current_age, 2),
        "cycle": active_major["progression_number"],
        "current_progressed_sign_index": active_major["sign_index"],
        "current_progressed_sign_name": active_major["sign_name"],
        "elapsed_progression_years": round(elapsed_in_major, 2),
        "remaining_progression_years": round(max(0.0, active_major["age_end"] - current_age), 2),
        "major_progression": {
            "level": "major",
            "progression_number": active_major["progression_number"],
            "sign": active_major["sign_name"],
            "sign_index": active_major["sign_index"],
            "age_start": active_major["age_start"],
            "age_end": active_major["age_end"],
            "start_date": active_major.get("start_date"),
            "end_date": active_major.get("end_date"),
            "duration": active_major["duration"],
            "direction": "Reverse",
            "rule_detail": active_major.get("rule_detail", "")
        },
        "minor_progression": {
            "level": "minor",
            "step": active_minor["step"],
            "sign": active_minor["sign_name"],
            "sign_index": active_minor["sign_index"],
            "age_start": active_minor["age_start"],
            "age_end": active_minor["age_end"],
            "start_date": active_minor.get("start_date"),
            "end_date": active_minor.get("end_date"),
            "duration": active_minor["duration"],
            "elapsed_years": round(minor_elapsed, 2),
            "remaining_years": round(minor_remaining, 2),
            "rate_per_sign": "1.5 Years / Sign (Reverse)",
            "active_periods": active_major.get("minor_periods", [])
        },
        "micro_progression": {
            "level": "micro",
            "step": active_micro["step"],
            "sign": active_micro["sign_name"],
            "sign_index": active_micro["sign_index"],
            "age_start": active_micro["age_start"],
            "age_end": active_micro["age_end"],
            "start_date": active_micro.get("start_date"),
            "end_date": active_micro.get("end_date"),
            "duration": active_micro["duration"],
            "elapsed_days": int(round(max(0.0, current_age - active_micro["age_start"]) * 365.25)),
            "remaining_days": int(round(max(0.0, active_micro["age_end"] - current_age) * 365.25)),
            "rate_per_sign": "1.5 Months / Sign (Reverse)",
            "active_periods": active_minor.get("micro_periods", [])
        },
        "timeline": timeline[:6]
    }

def generate_bnn_chart(
    name: str, dob_str: str, tob_str: str, pob_str: str,
    latitude: float, longitude: float, timezone: float,
    target_date_str: str = None,
    ayanamsa: str = "LAHIRI",
    custom_ayanamsa: float = None
) -> Dict[str, Any]:
    """Generates the complete, deeply calculated BNN Chart strictly based on BNN Progression rules."""
    
    # 1. Fetch exact natal planetary data using Swiss Ephemeris
    kundli = generate_full_kundli(
        name, dob_str, tob_str, pob_str, latitude, longitude, timezone,
        ayanamsa=ayanamsa, custom_ayanamsa=custom_ayanamsa
    )
    
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    natal_planets = [p for p in kundli.get("planets", []) if p.get("planet_name_simple", p["name"].split(" ")[0]) in valid_planets]
    
    now = datetime.strptime(target_date_str, "%Y-%m-%d") if target_date_str else datetime.utcnow() + __import__('datetime').timedelta(hours=timezone)
    transit_kundli = generate_full_kundli(
        "Transit", now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), pob_str, latitude, longitude, timezone,
        ayanamsa=ayanamsa, custom_ayanamsa=custom_ayanamsa
    )
    transit_planets = [p for p in transit_kundli.get("planets", []) if p.get("planet_name_simple", p["name"].split(" ")[0]) in valid_planets]
    
    current_age = calculate_current_age(dob_str, target_date_str)
    
    # Build core BNN planetary list
    bnn_planets = []
    for p in natal_planets:
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        bnn_planets.append({
            "planet": p_name,
            "karaka": BNN_KARAKAS.get(p_name, "").split(",")[0],
            "sign": p.get("sign", ""),
            "sign_index": p.get("sign_index", 1),
            "degree": p.get("degree_dms", ""),
            "degree_decimal": p.get("degree_decimal", 0.0),
            "nakshatra": p.get("nakshatra", ""),
            "pada": p.get("pada", 1),
            "retrograde": p.get("is_retrograde", False),
            "speed": p.get("speed_deg_per_day", 0.0)
        })

    # Exact BNN Progressions from PDF
    jupiter = next((p for p in bnn_planets if p["planet"] == "Jupiter"), None)
    saturn = next((p for p in bnn_planets if p["planet"] == "Saturn"), None)
    rahu = next((p for p in bnn_planets if p["planet"] == "Rahu"), None)
    ketu = next((p for p in bnn_planets if p["planet"] == "Ketu"), None)
    
    jupiter_progression = calculate_jupiter_progression(jupiter, bnn_planets, current_age, dob_str) if jupiter else {}
    saturn_progression = calculate_saturn_progression(saturn, bnn_planets, jupiter, current_age, dob_str) if saturn else {}
    rahu_progression = calculate_node_progression("Rahu", rahu, current_age, dob_str) if rahu else {}
    ketu_progression = calculate_node_progression("Ketu", ketu, current_age, dob_str) if ketu else {}
    
    # Backward compatible nodes object
    nodes_progression = {
        "rahu_natal": rahu.get("sign", "") if rahu else "",
        "ketu_natal": ketu.get("sign", "") if ketu else "",
        "current_age": round(current_age, 2),
        "cycle": rahu_progression.get("cycle", 1),
        "rahu_progressed_sign_index": rahu_progression.get("current_progressed_sign_index", 1),
        "ketu_progressed_sign_index": ketu_progression.get("current_progressed_sign_index", 7)
    }

    # Dynamic Progressed Planets for BNN Chart at Major, Minor, and Micro levels
    progressed_bnn_planets_major = copy.deepcopy(bnn_planets)
    progressed_bnn_planets_minor = copy.deepcopy(bnn_planets)
    progressed_bnn_planets_micro = copy.deepcopy(bnn_planets)

    for p in progressed_bnn_planets_major:
        if p["planet"] == "Jupiter" and jupiter_progression.get("current_progressed_sign_index"):
            idx = jupiter_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "major"
        elif p["planet"] == "Saturn" and saturn_progression.get("current_progressed_sign_index"):
            idx = saturn_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "major"
        elif p["planet"] == "Rahu" and rahu_progression.get("current_progressed_sign_index"):
            idx = rahu_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "major"
        elif p["planet"] == "Ketu" and ketu_progression.get("current_progressed_sign_index"):
            idx = ketu_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "major"

    for p in progressed_bnn_planets_minor:
        if p["planet"] == "Jupiter" and jupiter_progression.get("minor_progression", {}).get("sign_index"):
            idx = jupiter_progression["minor_progression"]["sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "minor"
        elif p["planet"] == "Saturn" and saturn_progression.get("minor_progression", {}).get("sign_index"):
            idx = saturn_progression["minor_progression"]["sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "minor"
        elif p["planet"] == "Rahu" and rahu_progression.get("minor_progression", {}).get("sign_index"):
            idx = rahu_progression["minor_progression"]["sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "minor"
        elif p["planet"] == "Ketu" and ketu_progression.get("minor_progression", {}).get("sign_index"):
            idx = ketu_progression["minor_progression"]["sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "minor"

    for p in progressed_bnn_planets_micro:
        if p["planet"] == "Jupiter" and jupiter_progression.get("micro_progression", {}).get("sign_index"):
            idx = jupiter_progression["micro_progression"]["sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "micro"
        elif p["planet"] == "Saturn" and saturn_progression.get("micro_progression", {}).get("sign_index"):
            idx = saturn_progression["micro_progression"]["sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "micro"
        elif p["planet"] == "Rahu" and rahu_progression.get("micro_progression", {}).get("sign_index"):
            idx = rahu_progression["micro_progression"]["sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "micro"
        elif p["planet"] == "Ketu" and ketu_progression.get("micro_progression", {}).get("sign_index"):
            idx = ketu_progression["micro_progression"]["sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["progression_level"] = "micro"

    # Default progressive chart planets (Major)
    progressed_bnn_planets = progressed_bnn_planets_major

    def _calc_relationships_for_list(planets_list):
        s_pairs = set()
        rels = []
        for p1 in planets_list:
            for p2 in planets_list:
                if p1["planet"] == p2["planet"]: continue
                pair_sig = tuple(sorted([p1["planet"], p2["planet"]]))
                if pair_sig in s_pairs: continue
                rel = get_bnn_relationship(p1["sign_index"], p2["sign_index"])
                if rel["strength"] > 0:
                    s_pairs.add(pair_sig)
                    dist = ((p2["sign_index"] - p1["sign_index"]) % 12) + 1
                    dist_str = "1" if dist == 1 else f"1-{dist}"
                    rels.append({
                        "planet_a": p1["planet"],
                        "planet_b": p2["planet"],
                        "sign_a": p1["sign"],
                        "sign_b": p2["sign"],
                        "sign_distance": dist_str,
                        "relationship_type": rel["relationship"],
                        "strength_percentage": rel["strength"],
                        "meaning": analyze_bnn_combination(p1["planet"], p2["planet"])
                    })
        rels.sort(key=lambda x: x["strength_percentage"], reverse=True)
        return rels

    def _calc_trines_for_list(planets_list):
        t_groups = []
        for group_name, signs in BNN_TRINE_GROUPS.items():
            planets_in_group = [p["planet"] for p in planets_list if p["sign"] in signs]
            if planets_in_group:
                strength = 100 if len(planets_in_group) > 1 else 0
                t_groups.append({
                    "group": group_name,
                    "signs": ", ".join(signs),
                    "planets": planets_in_group,
                    "strength": strength
                })
        return t_groups

    # 2. Dynamic Relationships across all 3 levels (Major, Minor, Micro)
    relationships_by_level = {
        "major": _calc_relationships_for_list(progressed_bnn_planets_major),
        "minor": _calc_relationships_for_list(progressed_bnn_planets_minor),
        "micro": _calc_relationships_for_list(progressed_bnn_planets_micro),
    }
    relationships = relationships_by_level["major"]

    # 3. Dynamic Trine Groups across all 3 levels (Major, Minor, Micro)
    trine_groups_by_level = {
        "major": _calc_trines_for_list(progressed_bnn_planets_major),
        "minor": _calc_trines_for_list(progressed_bnn_planets_minor),
        "micro": _calc_trines_for_list(progressed_bnn_planets_micro),
    }
    trine_groups = trine_groups_by_level["major"]

    # 4. Planetary Chain (Dispositor linkage)
    chains = []
    for p in progressed_bnn_planets:
        chain_links = [{"planet": p["planet"], "reason": "Base Planet"}]
        trines = [p2["planet"] for p2 in progressed_bnn_planets if p2["planet"] != p["planet"] and get_bnn_relationship(p["sign_index"], p2["sign_index"])["relationship"].startswith("Trine")]
        if trines:
            chain_links.append({"planet": ", ".join(trines), "reason": "Trine Connection"})
        disp = get_dispositor(p["sign_index"], natal_planets)
        if disp and disp.get("planet_name_simple") != p["planet"]:
            chain_links.append({"planet": disp.get("planet_name_simple"), "reason": "Dispositor"})
            
        chains.append({
            "base_planet": p["planet"],
            "chain": chain_links
        })

    # 5. Transit Activation
    transit_activations = []
    for tp in transit_planets:
        tp_name = tp.get("planet_name_simple", tp["name"].split(" ")[0])
        tp_sign_idx = tp.get("sign_index", 1)
        for np in bnn_planets:
            rel = get_bnn_relationship(tp_sign_idx, np["sign_index"])
            if rel["strength"] >= 50:
                transit_activations.append({
                    "transit_planet": tp_name,
                    "transit_sign": tp.get("sign", ""),
                    "transit_degree": tp.get("degree_dms", ""),
                    "natal_planet": np["planet"],
                    "natal_sign": np["sign"],
                    "relationship": rel["relationship"],
                    "strength": rel["strength"],
                    "activation_status": "Highly Active" if rel["strength"] >= 75 else "Active"
                })

    # 6. Event Activation (BNN Minor Annual Progression + Transit Dynamic Activation)
    event_activations = []
    
    # Extract Minor (Annual) Progressed Sign Indices that advance dynamically with each year
    j_minor = jupiter_progression.get("minor_progression", {})
    s_minor = saturn_progression.get("minor_progression", {})
    j_idx = j_minor.get("sign_index") or jupiter_progression.get("current_progressed_sign_index", 1)
    s_idx = s_minor.get("sign_index") or saturn_progression.get("current_progressed_sign_index", 1)
    
    for event, karakas in BNN_EVENTS.items():
        if len(karakas) >= 2:
            p1_natal = next((p for p in bnn_planets if p["planet"] == karakas[0]), None)
            p2_natal = next((p for p in bnn_planets if p["planet"] == karakas[1]), None)
            
            if p1_natal and p2_natal:
                # 1. Natal Base Connection (Birth Promise)
                natal_rel = get_bnn_relationship(p1_natal["sign_index"], p2_natal["sign_index"])
                natal_strength = natal_rel["strength"]
                
                # 2. Progression Activation (Target Year Minor Jupiter & Saturn)
                pj_p1 = get_bnn_relationship(j_idx, p1_natal["sign_index"])
                pj_p2 = get_bnn_relationship(j_idx, p2_natal["sign_index"])
                ps_p1 = get_bnn_relationship(s_idx, p1_natal["sign_index"])
                ps_p2 = get_bnn_relationship(s_idx, p2_natal["sign_index"])
                
                prog_p1 = max(pj_p1["strength"] if pj_p1["strength"] >= 50 else 0, ps_p1["strength"] if ps_p1["strength"] >= 50 else 0)
                prog_p2 = max(pj_p2["strength"] if pj_p2["strength"] >= 50 else 0, ps_p2["strength"] if ps_p2["strength"] >= 50 else 0)
                
                prog_strength = max(prog_p1, prog_p2)
                if prog_p1 >= 50 and prog_p2 >= 50:
                    prog_strength = min(100, prog_strength + 20)
                    
                prog_triggers = []
                if pj_p1["strength"] >= 50: prog_triggers.append(f"Prog. Jup {pj_p1['relationship']} {p1_natal['planet']}")
                if pj_p2["strength"] >= 50: prog_triggers.append(f"Prog. Jup {pj_p2['relationship']} {p2_natal['planet']}")
                if ps_p1["strength"] >= 50: prog_triggers.append(f"Prog. Sat {ps_p1['relationship']} {p1_natal['planet']}")
                if ps_p2["strength"] >= 50: prog_triggers.append(f"Prog. Sat {ps_p2['relationship']} {p2_natal['planet']}")
                
                # 3. Transit Activation (Target Year Transit Jupiter & Saturn)
                tj_hits = [ta for ta in transit_activations if ta.get("transit_planet") == "Jupiter" and ta.get("natal_planet") in [p1_natal["planet"], p2_natal["planet"]] and ta.get("strength", 0) >= 50]
                ts_hits = [ta for ta in transit_activations if ta.get("transit_planet") == "Saturn" and ta.get("natal_planet") in [p1_natal["planet"], p2_natal["planet"]] and ta.get("strength", 0) >= 50]
                
                tj_strength = max([h.get("strength", 0) for h in tj_hits], default=0)
                ts_strength = max([h.get("strength", 0) for h in ts_hits], default=0)
                
                transit_strength = max(tj_strength, ts_strength)
                if tj_strength >= 50 and ts_strength >= 50:
                    transit_strength = min(100, transit_strength + 15)
                    
                transit_triggers = [f"Trst {h['transit_planet']} {h['relationship']} {h['natal_planet']}" for h in (tj_hits + ts_hits)]
                
                # 4. Composite Dynamic Year Potential Score
                # 30% Natal Promise, 40% Progression Alignment, 30% Transit Alignment
                dynamic_score = round(0.30 * natal_strength + 0.40 * prog_strength + 0.30 * transit_strength)
                
                has_prog = len(prog_triggers) > 0
                has_transit = len(transit_triggers) > 0
                
                if dynamic_score >= 65:
                    status = "Active Trigger"
                elif dynamic_score >= 45:
                    status = "Strong Potential"
                elif dynamic_score >= 25:
                    status = "Moderate"
                else:
                    status = "Dormant"

                event_activations.append({
                    "event": event,
                    "karakas": f"{p1_natal['planet']}, {p2_natal['planet']}",
                    "natal_connection": natal_rel["relationship"],
                    "strength": dynamic_score,
                    "dynamic_score": dynamic_score,
                    "natal_strength": natal_strength,
                    "prog_strength": prog_strength,
                    "transit_strength": transit_strength,
                    "transit_trigger": "Yes" if has_transit else "No",
                    "transit_detail": transit_triggers[0] if transit_triggers else "No major transit",
                    "progression_trigger": "Yes" if has_prog else "No",
                    "progression_detail": prog_triggers[0] if prog_triggers else "Dormant",
                    "status": status
                })

    return {
        "overview": {
            "person_name": name,
            "date_of_birth": dob_str,
            "time_of_birth": tob_str,
            "place_of_birth": pob_str,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "ayanamsa": kundli.get("ayanamsa_formatted", "Lahiri"),
            "ephemeris": "Swiss Ephemeris (pyswisseph)",
            "current_age": round(current_age, 2),
            "age": round(current_age, 1),
            "target_year": now.year,
            "target_date": now.strftime("%Y-%m-%d"),
            "bnn_reference_planet": "Jupiter (Male) / Venus (Female)"
        },
        "planets": progressed_bnn_planets,
        "natal_planets": bnn_planets,
        "charts": {
            "major": progressed_bnn_planets_major,
            "minor": progressed_bnn_planets_minor,
            "micro": progressed_bnn_planets_micro
        },
        "progression_hierarchy": {
            "current_age": round(current_age, 2),
            "target_date": now.strftime("%Y-%m-%d"),
            "levels": ["major", "minor", "micro"],
            "active_level": "major",
            "jupiter": {
                "active_major": jupiter_progression.get("major_progression"),
                "active_minor": jupiter_progression.get("minor_progression"),
                "active_micro": jupiter_progression.get("micro_progression"),
                "timeline": jupiter_progression.get("timeline")
            },
            "saturn": {
                "active_major": saturn_progression.get("major_progression"),
                "active_minor": saturn_progression.get("minor_progression"),
                "active_micro": saturn_progression.get("micro_progression"),
                "timeline": saturn_progression.get("timeline")
            },
            "rahu": {
                "active_major": rahu_progression.get("major_progression"),
                "active_minor": rahu_progression.get("minor_progression"),
                "active_micro": rahu_progression.get("micro_progression"),
                "timeline": rahu_progression.get("timeline")
            },
            "ketu": {
                "active_major": ketu_progression.get("major_progression"),
                "active_minor": ketu_progression.get("minor_progression"),
                "active_micro": ketu_progression.get("micro_progression"),
                "timeline": ketu_progression.get("timeline")
            }
        },
        "karakatwas": [{"planet": k, "significations": v} for k, v in BNN_KARAKAS.items()],
        "relationships": relationships,
        "trine_groups": trine_groups,
        "relationships_by_level": relationships_by_level,
        "trine_groups_by_level": trine_groups_by_level,
        "progressions": {
            "jupiter": jupiter_progression,
            "saturn": saturn_progression,
            "rahu": rahu_progression,
            "ketu": ketu_progression,
            "nodes": nodes_progression
        },
        "chains": chains,
        "transit_activations": transit_activations,
        "events": event_activations,
        "debug": {
            "julian_day": kundli.get("julian_day", "N/A"),
            "transit_date": now.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
