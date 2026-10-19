from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
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

def calculate_jupiter_progression(jupiter: Dict, planets: List[Dict], current_age: float) -> Dict[str, Any]:
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

    # Active Major Progression
    active_major = timeline[0]
    for item in timeline:
        if item["age_start"] <= current_age < item["age_end"]:
            active_major = item
            break
        elif current_age >= item["age_end"]:
            active_major = item

    # Minor Progression: 1.0 yr per sign starting from major sign
    major_start = active_major["age_start"]
    elapsed_in_major = max(0.0, current_age - major_start)
    minor_steps = int(elapsed_in_major // 1.0)
    minor_sign_idx = normalize_sign(active_major["sign_index"] + minor_steps)
    minor_elapsed = elapsed_in_major - minor_steps
    minor_remaining = max(0.0, 1.0 - minor_elapsed)
    
    minor_periods = []
    num_minor_steps = int(active_major["duration"])
    if active_major["duration"] > num_minor_steps:
        num_minor_steps += 1
    for m in range(min(num_minor_steps, 12)):
        m_start = round(major_start + m * 1.0, 2)
        m_end = round(min(active_major["age_end"], major_start + (m + 1) * 1.0), 2)
        m_sign = normalize_sign(active_major["sign_index"] + m)
        is_active = (m_start <= current_age < m_end) or (m == num_minor_steps - 1 and current_age >= m_start)
        minor_periods.append({
            "step": m + 1,
            "sign_index": m_sign,
            "sign_name": SIGNS[m_sign - 1],
            "age_start": m_start,
            "age_end": m_end,
            "duration": round(m_end - m_start, 2),
            "is_current": is_active
        })

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
            "sign": active_major["sign_name"],
            "sign_index": active_major["sign_index"],
            "age_start": active_major["age_start"],
            "age_end": active_major["age_end"],
            "duration": active_major["duration"],
            "rule_detail": active_major["rule_detail"]
        },
        "minor_progression": {
            "sign": SIGNS[minor_sign_idx - 1],
            "sign_index": minor_sign_idx,
            "elapsed_years": round(minor_elapsed, 2),
            "remaining_years": round(minor_remaining, 2),
            "rate_per_sign": "1.0 Year / Sign",
            "active_periods": minor_periods
        },
        "timeline": timeline[:8]
    }

def calculate_saturn_progression(saturn: Dict, planets: List[Dict], jupiter: Optional[Dict], current_age: float) -> Dict[str, Any]:
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

    # Active Major Progression
    active_major = timeline[0]
    for item in timeline:
        if item["age_start"] <= current_age < item["age_end"]:
            active_major = item
            break
        elif current_age >= item["age_end"]:
            active_major = item

    # Minor Progression: 2.5 yr per sign forward starting from major sign
    major_start = active_major["age_start"]
    elapsed_in_major = max(0.0, current_age - major_start)
    minor_steps = int(elapsed_in_major // 2.5)
    minor_sign_idx = normalize_sign(active_major["sign_index"] + minor_steps)
    minor_elapsed = elapsed_in_major - (minor_steps * 2.5)
    minor_remaining = max(0.0, 2.5 - minor_elapsed)
    
    minor_periods = []
    num_minor_steps = int(active_major["duration"] // 2.5)
    if active_major["duration"] % 2.5 > 0:
        num_minor_steps += 1
    for m in range(min(num_minor_steps, 12)):
        m_start = round(major_start + m * 2.5, 2)
        m_end = round(min(active_major["age_end"], major_start + (m + 1) * 2.5), 2)
        m_sign = normalize_sign(active_major["sign_index"] + m)
        is_active = (m_start <= current_age < m_end) or (m == num_minor_steps - 1 and current_age >= m_start)
        minor_periods.append({
            "step": m + 1,
            "sign_index": m_sign,
            "sign_name": SIGNS[m_sign - 1],
            "age_start": m_start,
            "age_end": m_end,
            "duration": round(m_end - m_start, 2),
            "is_current": is_active
        })

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
            "sign": active_major["sign_name"],
            "sign_index": active_major["sign_index"],
            "age_start": active_major["age_start"],
            "age_end": active_major["age_end"],
            "duration": active_major["duration"],
            "rule_detail": active_major["rule_detail"]
        },
        "minor_progression": {
            "sign": SIGNS[minor_sign_idx - 1],
            "sign_index": minor_sign_idx,
            "elapsed_years": round(minor_elapsed, 2),
            "remaining_years": round(minor_remaining, 2),
            "rate_per_sign": "2.5 Years / Sign",
            "active_periods": minor_periods
        },
        "timeline": timeline[:6]
    }

def calculate_node_progression(planet_name: str, node: Dict, current_age: float) -> Dict[str, Any]:
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

    active_major = timeline[0]
    for item in timeline:
        if item["age_start"] <= current_age < item["age_end"]:
            active_major = item
            break
        elif current_age >= item["age_end"]:
            active_major = item

    # Minor Progression: 1.5 yr per sign in REVERSE direction starting from major sign
    major_start = active_major["age_start"]
    elapsed_in_major = max(0.0, current_age - major_start)
    minor_steps = int(elapsed_in_major // 1.5)
    minor_sign_idx = normalize_sign(active_major["sign_index"] - minor_steps)
    minor_elapsed = elapsed_in_major - (minor_steps * 1.5)
    minor_remaining = max(0.0, 1.5 - minor_elapsed)
    
    minor_periods = []
    num_minor_steps = int(active_major["duration"] // 1.5)
    if active_major["duration"] % 1.5 > 0:
        num_minor_steps += 1
    for m in range(min(num_minor_steps, 12)):
        m_start = round(major_start + m * 1.5, 2)
        m_end = round(min(active_major["age_end"], major_start + (m + 1) * 1.5), 2)
        m_sign = normalize_sign(active_major["sign_index"] - m)
        is_active = (m_start <= current_age < m_end) or (m == num_minor_steps - 1 and current_age >= m_start)
        minor_periods.append({
            "step": m + 1,
            "sign_index": m_sign,
            "sign_name": SIGNS[m_sign - 1],
            "age_start": m_start,
            "age_end": m_end,
            "duration": round(m_end - m_start, 2),
            "is_current": is_active
        })

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
            "sign": active_major["sign_name"],
            "sign_index": active_major["sign_index"],
            "age_start": active_major["age_start"],
            "age_end": active_major["age_end"],
            "duration": active_major["duration"],
            "direction": "Reverse",
            "rule_detail": active_major["rule_detail"]
        },
        "minor_progression": {
            "sign": SIGNS[minor_sign_idx - 1],
            "sign_index": minor_sign_idx,
            "elapsed_years": round(minor_elapsed, 2),
            "remaining_years": round(minor_remaining, 2),
            "rate_per_sign": "1.5 Years / Sign (Reverse)",
            "active_periods": minor_periods
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
        name, dob_str, tob_str, pob_str, latitude, longitude, timezone
    )
    
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    natal_planets = [p for p in kundli.get("planets", []) if p.get("planet_name_simple", p["name"].split(" ")[0]) in valid_planets]
    
    now = datetime.strptime(target_date_str, "%Y-%m-%d") if target_date_str else datetime.utcnow() + __import__('datetime').timedelta(hours=timezone)
    transit_kundli = generate_full_kundli(
        "Transit", now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), pob_str, latitude, longitude, timezone
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
    
    jupiter_progression = calculate_jupiter_progression(jupiter, bnn_planets, current_age) if jupiter else {}
    saturn_progression = calculate_saturn_progression(saturn, bnn_planets, jupiter, current_age) if saturn else {}
    rahu_progression = calculate_node_progression("Rahu", rahu, current_age) if rahu else {}
    ketu_progression = calculate_node_progression("Ketu", ketu, current_age) if ketu else {}
    
    # Backward compatible nodes object
    nodes_progression = {
        "rahu_natal": rahu.get("sign", "") if rahu else "",
        "ketu_natal": ketu.get("sign", "") if ketu else "",
        "current_age": round(current_age, 2),
        "cycle": rahu_progression.get("cycle", 1),
        "rahu_progressed_sign_index": rahu_progression.get("current_progressed_sign_index", 1),
        "ketu_progressed_sign_index": ketu_progression.get("current_progressed_sign_index", 7)
    }

    # Dynamic Progressed Planets for BNN Chart
    progressed_bnn_planets = copy.deepcopy(bnn_planets)
    for p in progressed_bnn_planets:
        if p["planet"] == "Jupiter" and jupiter_progression.get("current_progressed_sign_index"):
            idx = jupiter_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["minor_sign"] = jupiter_progression.get("minor_progression", {}).get("sign")
        elif p["planet"] == "Saturn" and saturn_progression.get("current_progressed_sign_index"):
            idx = saturn_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["minor_sign"] = saturn_progression.get("minor_progression", {}).get("sign")
        elif p["planet"] == "Rahu" and rahu_progression.get("current_progressed_sign_index"):
            idx = rahu_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["minor_sign"] = rahu_progression.get("minor_progression", {}).get("sign")
        elif p["planet"] == "Ketu" and ketu_progression.get("current_progressed_sign_index"):
            idx = ketu_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
            p["minor_sign"] = ketu_progression.get("minor_progression", {}).get("sign")

    # 2. BNN Relationship Matrix
    seen_pairs = set()
    relationships = []
    for p1 in progressed_bnn_planets:
        for p2 in progressed_bnn_planets:
            if p1["planet"] == p2["planet"]: continue
            pair_sig = tuple(sorted([p1["planet"], p2["planet"]]))
            if pair_sig in seen_pairs: continue
            
            rel = get_bnn_relationship(p1["sign_index"], p2["sign_index"])
            if rel["strength"] > 0:
                seen_pairs.add(pair_sig)
                dist = ((p2["sign_index"] - p1["sign_index"]) % 12) + 1
                dist_str = "1" if dist == 1 else f"1-{dist}"
                
                relationships.append({
                    "planet_a": p1["planet"],
                    "planet_b": p2["planet"],
                    "sign_a": p1["sign"],
                    "sign_b": p2["sign"],
                    "sign_distance": dist_str,
                    "relationship_type": rel["relationship"],
                    "strength_percentage": rel["strength"],
                    "meaning": analyze_bnn_combination(p1["planet"], p2["planet"])
                })
    relationships.sort(key=lambda x: x["strength_percentage"], reverse=True)

    # 3. Trine Groups
    trine_groups = []
    for group_name, signs in BNN_TRINE_GROUPS.items():
        planets_in_group = [p["planet"] for p in progressed_bnn_planets if p["sign"] in signs]
        if planets_in_group:
            strength = 100 if len(planets_in_group) > 1 else 0
            trine_groups.append({
                "group": group_name,
                "signs": ", ".join(signs),
                "planets": planets_in_group,
                "strength": strength
            })

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

    # 6. Event Activation
    event_activations = []
    for event, karakas in BNN_EVENTS.items():
        if len(karakas) >= 2:
            p1 = next((p for p in progressed_bnn_planets if p["planet"] == karakas[0]), None)
            p2 = next((p for p in progressed_bnn_planets if p["planet"] == karakas[1]), None)
            
            if p1 and p2:
                rel = get_bnn_relationship(p1["sign_index"], p2["sign_index"])
                transit_trigger = "No"
                for ta in transit_activations:
                    if ta["natal_planet"] == p1["planet"] and ta["strength"] >= 75 and ta["transit_planet"] in ["Jupiter", "Saturn"]:
                        transit_trigger = "Yes"
                        break
                        
                event_activations.append({
                    "event": event,
                    "karakas": ", ".join(karakas),
                    "natal_connection": rel["relationship"],
                    "strength": rel["strength"],
                    "transit_trigger": transit_trigger,
                    "status": "Strong Potential" if rel["strength"] >= 50 else "Insufficient BNN confirmation"
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
            "target_date": now.strftime("%Y-%m-%d"),
            "bnn_reference_planet": "Jupiter (Male) / Venus (Female)"
        },
        "planets": progressed_bnn_planets,
        "natal_planets": bnn_planets,
        "karakatwas": [{"planet": k, "significations": v} for k, v in BNN_KARAKAS.items()],
        "relationships": relationships,
        "trine_groups": trine_groups,
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
