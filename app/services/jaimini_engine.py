"""Jaimini Astrological Engine.
A deterministic calculation-based Jaimini engine powered by Swiss Ephemeris.
"""
import copy
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.services.vedic_engine import generate_full_kundli, get_planet_longitudes_precise, calculate_ascendant_and_mc, calculate_lahiri_ayanamsa
from app.utils.constants import ZODIAC_SIGNS
from app.services.jaimini_rules import JAIMINI_KARAKAS, get_karaka_interpretation

# ==========================================
# CONFIGURATION
# ==========================================
JAIMINI_CONFIG = {
    "karaka_scheme": "7K",             # "7K" or "8K"
    "rahu_reverse_degree": True,       # If True, Rahu's degree is measured backwards (30 - degree)
    "chara_dasha_method": "STANDARD",  # STANDARD Padmanath/Rao
    "arudha_exception": "CLASSICAL",   # 1st/7th apply 10th-from-pada exception
}

# ==========================================
# CORE UTILITIES
# ==========================================

def get_sign_name(index: int) -> str:
    """1-12 index to sign name."""
    return ZODIAC_SIGNS[(index - 1) % 12]["name"]

def format_degree(deg: float) -> str:
    """Decimal degree to formatted string MM° SS'."""
    deg_in_sign = deg % 30.0
    d = int(deg_in_sign)
    m = int((deg_in_sign - d) * 60)
    s = int((((deg_in_sign - d) * 60) - m) * 60)
    return f"{d:02d}° {m:02d}'"

def get_lord_of_sign(sign_idx: int) -> str:
    """Get planetary lord for a sign (1=Aries ... 12=Pisces)."""
    lords = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
        5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
        9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
    }
    return lords[sign_idx]

def resolve_dual_lordship(sign_idx: int, l1: str, l2: str, planets: List[Dict]) -> str:
    """Resolve dual lordship for Scorpio (Mars/Ketu) and Aquarius (Saturn/Rahu) in Jaimini."""
    # Jaimini specific rules:
    # 1. If one lord is in the sign itself, the OTHER is considered stronger and acts as lord.
    # 2. Planet with more planets in conjunction is stronger.
    # 3. Planet with higher degree (0-30) is stronger.
    p_map = {p["planet_name_simple"]: p for p in planets}
    if l1 not in p_map: return l2
    if l2 not in p_map: return l1
    
    p1 = p_map[l1]
    p2 = p_map[l2]
    
    # 1. Copresence with sign
    if p1["sign_index"] == sign_idx and p2["sign_index"] != sign_idx: return l2
    if p2["sign_index"] == sign_idx and p1["sign_index"] != sign_idx: return l1
    
    # 2. Conjunctions count
    c1 = sum(1 for p in planets if p["sign_index"] == p1["sign_index"])
    c2 = sum(1 for p in planets if p["sign_index"] == p2["sign_index"])
    if c1 > c2: return l1
    if c2 > c1: return l2
    
    # 3. Higher degree
    deg1 = p1["degree_decimal"] % 30.0
    deg2 = p2["degree_decimal"] % 30.0
    if deg1 > deg2: return l1
    return l2

def get_jaimini_lord(sign_idx: int, planets: List[Dict]) -> str:
    if sign_idx == 8:
        return resolve_dual_lordship(8, "Mars", "Ketu", planets)
    if sign_idx == 11:
        return resolve_dual_lordship(11, "Saturn", "Rahu", planets)
    return get_lord_of_sign(sign_idx)

# ==========================================
# 1. RASHI DRISHTI ENGINE
# ==========================================

def get_rashi_aspects(sign_index: int) -> List[int]:
    """Calculate Jaimini Rashi Drishti (Aspects)."""
    # Movable: 1, 4, 7, 10
    # Fixed: 2, 5, 8, 11
    # Dual: 3, 6, 9, 12
    if sign_index in [1, 4, 7, 10]:
        fixed_signs = {2, 5, 8, 11}
        adjacent = (sign_index % 12) + 1
        return sorted(list(fixed_signs - {adjacent}))
    elif sign_index in [2, 5, 8, 11]:
        cardinal_signs = {1, 4, 7, 10}
        adjacent = ((sign_index - 2) % 12) + 1
        return sorted(list(cardinal_signs - {adjacent}))
    elif sign_index in [3, 6, 9, 12]:
        mutable_signs = {3, 6, 9, 12}
        return sorted(list(mutable_signs - {sign_index}))
    return []

# ==========================================
# 2. CHARA KARAKAS ENGINE
# ==========================================

def calculate_chara_karakas(planets: List[Dict], config: Dict) -> List[Dict]:
    scheme = config.get("karaka_scheme", "7K")
    reverse_rahu = config.get("rahu_reverse_degree", True)
    
    valid_names = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    if scheme == "8K":
        valid_names.append("Rahu")
        
    eligible = []
    for p in planets:
        if p["planet_name_simple"] in valid_names:
            deg = p["degree_decimal"] % 30.0
            eff_deg = deg
            if p["planet_name_simple"] == "Rahu" and reverse_rahu:
                eff_deg = 30.0 - deg
                
            eligible.append({
                "planet": p["planet_name_simple"],
                "degree": deg,
                "effective_degree": eff_deg,
                "sign": p["sign"],
                "sign_index": p["sign_index"],
                "retrograde": p.get("is_retrograde", False),
                "navamsa_sign": p.get("navamsha", {}).get("navamsha_sign", "Aries")
            })
            
    eligible.sort(key=lambda x: x["effective_degree"], reverse=True)
    
    if scheme == "7K":
        titles = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
    else:
        titles = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK", "PiK"]
        
    karakas = []
    for i, p in enumerate(eligible):
        if i < len(titles):
            title = titles[i]
            k_name = JAIMINI_KARAKAS.get(title, {}).get("name", "Pitru Karaka" if title=="PiK" else title)
            meaning = JAIMINI_KARAKAS.get(title, {}).get("meaning", "Father/Ancestors" if title=="PiK" else "")
            karakas.append({
                "rank": i + 1,
                "karaka_code": title,
                "karaka_name": k_name,
                "planet": p["planet"],
                "actual_degree": format_degree(p["degree"]),
                "effective_degree": format_degree(p["effective_degree"]),
                "sign": p["sign"],
                "sign_index": p["sign_index"],
                "retrograde": p["retrograde"],
                "meaning": meaning,
                "navamsa_sign": p["navamsa_sign"]
            })
    return karakas

# ==========================================
# 3. ARUDHA PADAS ENGINE
# ==========================================

def calculate_arudhas(asc_sign_idx: int, planets: List[Dict]) -> List[Dict]:
    arudhas = []
    p_map = {p["planet_name_simple"]: p for p in planets}
    
    names = [
        "AL (Arudha Lagna)", "A2 (Dhana)", "A3 (Bhratri)", "A4 (Matri)",
        "A5 (Putra)", "A6 (Shatru)", "A7 (Dara)", "A8 (Mrityu)",
        "A9 (Bhagya)", "A10 (Rajya)", "A11 (Labha)", "UL (Upapada)"
    ]
    
    for h in range(1, 13):
        house_idx = ((asc_sign_idx + h - 2) % 12) + 1
        lord_name = get_jaimini_lord(house_idx, planets)
        lord_p = p_map.get(lord_name)
        if not lord_p:
            continue
            
        lord_sign_idx = lord_p["sign_index"]
        
        # Distance (inclusive count)
        distance = (lord_sign_idx - house_idx) % 12
        raw_arudha = ((lord_sign_idx - 1 + distance) % 12) + 1
        
        # Exceptions
        final_arudha = raw_arudha
        exception_applied = "No"
        
        dist_from_house = (raw_arudha - house_idx) % 12
        if dist_from_house == 0:
            final_arudha = ((raw_arudha - 1 + 9) % 12) + 1 # 10th from it
            exception_applied = "Yes (10th from Pada)"
        elif dist_from_house == 6:
            final_arudha = ((raw_arudha - 1 + 3) % 12) + 1 # 4th from it
            exception_applied = "Yes (4th from Pada)"
            
        planets_in_pada = [p["planet_name_simple"] for p in planets if p.get("sign_index") == final_arudha]
        
        arudhas.append({
            "house": h,
            "name": names[h-1],
            "source_sign": get_sign_name(house_idx),
            "sign_lord": lord_name,
            "lord_sign": get_sign_name(lord_sign_idx),
            "distance": distance + 1,
            "raw_pada": get_sign_name(raw_arudha),
            "exception": exception_applied,
            "final_pada": get_sign_name(final_arudha),
            "final_pada_index": final_arudha,
            "planets": planets_in_pada
        })
    return arudhas

# ==========================================
# 4. ARGALA ENGINE
# ==========================================

def calculate_argala(reference_idx: int, planets: List[Dict]) -> List[Dict]:
    argala_pairs = [
        {"arg": 2, "virodh": 12, "name": "Dhana Argala"},
        {"arg": 4, "virodh": 10, "name": "Sukha Argala"},
        {"arg": 5, "virodh": 9, "name": "Putra Argala"},
        {"arg": 11, "virodh": 3, "name": "Labha Argala"}
    ]
    
    results = []
    for pair in argala_pairs:
        arg_idx = ((reference_idx + pair["arg"] - 2) % 12) + 1
        vir_idx = ((reference_idx + pair["virodh"] - 2) % 12) + 1
        
        arg_planets = [p["planet_name_simple"] for p in planets if p.get("sign_index") == arg_idx]
        vir_planets = [p["planet_name_simple"] for p in planets if p.get("sign_index") == vir_idx]
        
        # Ketu doesn't cause Argala usually, and Nodes might act differently, 
        # but standard check is number of planets.
        if len(arg_planets) > 0:
            if len(arg_planets) > len(vir_planets):
                status = "Effective"
            elif len(arg_planets) < len(vir_planets):
                status = "Blocked"
            else:
                # Same count, check strength (simplified)
                status = "Effective (Needs Strength Check)"
        else:
            status = "No Argala"
            
        results.append({
            "type": pair["name"],
            "argala_house": pair["arg"],
            "argala_sign": get_sign_name(arg_idx),
            "argala_planets": arg_planets,
            "virodh_house": pair["virodh"],
            "virodh_sign": get_sign_name(vir_idx),
            "virodh_planets": vir_planets,
            "status": status
        })
    return results

# ==========================================
# 5. CHARA DASHA ENGINE
# ==========================================

def get_chara_dasha_duration(sign_idx: int, planets: List[Dict]) -> int:
    """Calculate Jaimini Chara Dasha duration for a sign."""
    lord = get_jaimini_lord(sign_idx, planets)
    lord_p = next((p for p in planets if p["planet_name_simple"] == lord), None)
    if not lord_p: return 0
    lord_sign = lord_p["sign_index"]
    
    # 1=Aries (forward), 2=Taurus (backward), 3=Gemini (forward), etc.
    # Exception: Scorpio and Aquarius might have dual lordship.
    # Count distance:
    if sign_idx in [1, 2, 3, 7, 8, 9]:
        # Count Forward
        dist = (lord_sign - sign_idx) % 12
    else:
        # Count Backward
        dist = (sign_idx - lord_sign) % 12
        
    duration = dist
    if duration == 0:
        duration = 12
    
    # Exalted planet gives +1, Debilitated gives -1 (often applied)
    # Keeping it simple based on distance for now.
    return duration

def calculate_chara_dasha(asc_sign_idx: int, planets: List[Dict], birth_dt: datetime) -> List[Dict]:
    """Generate Mahadasha sequence and durations."""
    # Sequence depends on Ascendant (Odd = forward, Even = backward)
    is_odd = asc_sign_idx % 2 != 0
    
    # Certain signs reverse the sequence: Aries forward, Taurus backward...
    # But usually sequence is:
    # Aries, Taurus, Gemini... for Aries Asc
    # Taurus, Aries, Pisces... for Taurus Asc
    # Let's use standard Padmanath sequence:
    if asc_sign_idx in [1, 2, 3, 7, 8, 9]:
        # Actually standard Chara Dasha: 
        # Odd Lagna -> Forward 1..12
        # Even Lagna -> Backward 1..12 (e.g. 2, 1, 12, 11...)
        pass
        
    if is_odd:
        sequence = [(asc_sign_idx - 1 + i) % 12 + 1 for i in range(12)]
    else:
        sequence = [(asc_sign_idx - 1 - i) % 12 + 1 for i in range(12)]
        if 0 in sequence:
            sequence = [s if s != 0 else 12 for s in sequence]
            
    dashas = []
    current_dt = birth_dt
    for s_idx in sequence:
        dur = get_chara_dasha_duration(s_idx, planets)
        end_dt = current_dt + timedelta(days=dur * 365.25)
        
        # Antardashas
        is_ad_odd = s_idx % 2 != 0
        if is_ad_odd:
            ad_seq = [(s_idx - 1 + i) % 12 + 1 for i in range(12)]
        else:
            ad_seq = [(s_idx - 1 - i) % 12 + 1 for i in range(12)]
            ad_seq = [s if s != 0 else 12 for s in ad_seq]
            
        ad_list = []
        ad_dt = current_dt
        for ad_idx in ad_seq:
            ad_end_dt = ad_dt + timedelta(days=dur * 30.4375)
            ad_list.append({
                "sign": get_sign_name(ad_idx),
                "duration": round(dur / 12.0, 2),
                "start_date": ad_dt.strftime("%Y-%m-%d"),
                "end_date": ad_end_dt.strftime("%Y-%m-%d")
            })
            ad_dt = ad_end_dt
        
        dashas.append({
            "sign_index": s_idx,
            "sign": get_sign_name(s_idx),
            "duration": dur,
            "start_date": current_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "lord": get_jaimini_lord(s_idx, planets),
            "antardashas": ad_list
        })
        current_dt = end_dt
        
    return dashas

# ==========================================
# 6. MISSING JAIMINI SUB-ENGINES (YOGAS, LAGNAS, TRANSITS)
# ==========================================

def calculate_jaimini_yogas(planets: List[Dict], chara_karakas: List[Dict]) -> List[Dict]:
    yogas = []
    ak = next((k for k in chara_karakas if k["karaka_code"] == "AK"), None)
    amk = next((k for k in chara_karakas if k["karaka_code"] == "AmK"), None)
    dk = next((k for k in chara_karakas if k["karaka_code"] == "DK"), None)
    pik = next((k for k in chara_karakas if k["karaka_code"] == "PiK"), None)
    
    if not ak: return yogas
    ak_aspects = get_rashi_aspects(ak["sign_index"])

    # 1. AK + AmK
    if amk:
        if ak["sign_index"] == amk["sign_index"]:
            yogas.append({"yoga": "Jaimini Raja Yoga", "planets": f"{ak['planet']} (AK) + {amk['planet']} (AmK)", "rule": "AK and AmK are conjunct", "evidence": f"Both in {get_sign_name(ak['sign_index'])}", "status": "Formed"})
        elif amk["sign_index"] in ak_aspects:
            yogas.append({"yoga": "Jaimini Raja Yoga", "planets": f"{ak['planet']} (AK) aspecting {amk['planet']} (AmK)", "rule": "AK and AmK aspect each other via Rashi Drishti", "evidence": f"{get_sign_name(ak['sign_index'])} aspects {get_sign_name(amk['sign_index'])}", "status": "Formed"})

    # 2. AK + DK
    if dk:
        if ak["sign_index"] == dk["sign_index"]:
            yogas.append({"yoga": "Jaimini Maha Yoga", "planets": f"{ak['planet']} (AK) + {dk['planet']} (DK)", "rule": "AK and DK are conjunct", "evidence": f"Both in {get_sign_name(ak['sign_index'])}", "status": "Formed"})
        elif dk["sign_index"] in ak_aspects:
            yogas.append({"yoga": "Jaimini Maha Yoga", "planets": f"{ak['planet']} (AK) aspecting {dk['planet']} (DK)", "rule": "AK and DK aspect each other via Rashi Drishti", "evidence": f"{get_sign_name(ak['sign_index'])} aspects {get_sign_name(dk['sign_index'])}", "status": "Formed"})

    # 3. AmK + DK
    if amk and dk:
        if amk["sign_index"] == dk["sign_index"]:
            yogas.append({"yoga": "Wealth Yoga", "planets": f"{amk['planet']} (AmK) + {dk['planet']} (DK)", "rule": "AmK and DK are conjunct", "evidence": f"Both in {get_sign_name(amk['sign_index'])}", "status": "Formed"})
        elif dk["sign_index"] in get_rashi_aspects(amk["sign_index"]):
            yogas.append({"yoga": "Wealth Yoga", "planets": f"{amk['planet']} (AmK) aspecting {dk['planet']} (DK)", "rule": "AmK and DK aspect each other", "evidence": f"{get_sign_name(amk['sign_index'])} aspects {get_sign_name(dk['sign_index'])}", "status": "Formed"})

    return yogas

def calculate_special_lagnas(kundli: Dict) -> List[Dict]:
    planets = kundli.get("planets", [])
    
    asc = next((p for p in planets if p.get("planet_name_simple") == "Ascendant"), None)
    asc_deg = asc["degree_decimal"] if asc else 0.0
    
    sun = next((p for p in planets if p.get("planet_name_simple") == "Sun"), None)
    sun_deg = sun["degree_decimal"] if sun else 0.0
    
    hl_deg = (sun_deg + asc_deg * 2) % 360.0
    gl_deg = (sun_deg + asc_deg * 5) % 360.0
    bl_deg = (asc_deg + sun_deg) % 360.0
    
    hl_sign = int(hl_deg // 30) + 1
    gl_sign = int(gl_deg // 30) + 1
    bl_sign = int(bl_deg // 30) + 1

    return [
        {"name": "Hora Lagna (HL)", "sign": get_sign_name(hl_sign), "degree": format_degree(hl_deg), "method": "Standard Angular"},
        {"name": "Ghati Lagna (GL)", "sign": get_sign_name(gl_sign), "degree": format_degree(gl_deg), "method": "Standard Angular"},
        {"name": "Bhava Lagna (BL)", "sign": get_sign_name(bl_sign), "degree": format_degree(bl_deg), "method": "Standard Angular"}
    ]

def calculate_karakamsha_analysis(karakamsha_sign: str, planets: List[Dict]) -> List[Dict]:
    if not karakamsha_sign or karakamsha_sign == "Unknown":
        return []
    k_sign_idx = next((i for i, s in enumerate(ZODIAC_SIGNS) if s["name"] == karakamsha_sign), 0) + 1
    
    analysis = []
    for h in range(1, 13):
        house_idx = ((k_sign_idx + h - 2) % 12) + 1
        sign_name = get_sign_name(house_idx)
        p_in_sign = [p["planet_name_simple"] for p in planets if p.get("sign_index") == house_idx]
        lord = get_jaimini_lord(house_idx, planets)
        aspects = [get_sign_name(a) for a in get_rashi_aspects(house_idx)]
        
        analysis.append({
            "house": h,
            "sign": sign_name,
            "planets": p_in_sign,
            "lord": lord,
            "rashi_drishti_received_from": aspects
        })
    return analysis

def calculate_jaimini_transits(transit_planets: List[Dict], natal_arudhas: List[Dict], dasha_sign: str) -> List[Dict]:
    transits = []
    al = next((a for a in natal_arudhas if a["house"] == 1), None)
    al_sign_idx = al["final_pada_index"] if al else -1
    dasha_sign_idx = next((i for i, s in enumerate(ZODIAC_SIGNS) if s["name"] == dasha_sign), 0) + 1

    for tp in transit_planets:
        if tp["planet_name_simple"] in ["Ascendant", "Uranus", "Neptune", "Pluto"]: continue
        
        tp_sign_idx = tp["sign_index"]
        tp_aspects = get_rashi_aspects(tp_sign_idx)
        
        connections = []
        if tp_sign_idx == al_sign_idx: connections.append("Conjunct AL")
        elif al_sign_idx in tp_aspects: connections.append("Aspects AL")
            
        if tp_sign_idx == dasha_sign_idx: connections.append("Conjunct Dasha Sign")
        elif dasha_sign_idx in tp_aspects: connections.append("Aspects Dasha Sign")
            
        if connections:
            transits.append({
                "transit_planet": tp["planet_name_simple"],
                "transit_sign": get_sign_name(tp_sign_idx),
                "connections": connections
            })
    return transits

# ==========================================
# 7. MAIN ENGINE ENTRY POINT
# ==========================================

def generate_jaimini_chart(
    name: str, dob_str: str, tob_str: str, pob_str: str,
    latitude: float, longitude: float, timezone: float
) -> Dict[str, Any]:
    """Generate the complete Jaimini Chart output."""
    
    # 1. Base Swiss Ephemeris data
    kundli = generate_full_kundli(name, dob_str, tob_str, pob_str, latitude, longitude, timezone)
    planets = kundli.get("planets", [])
    
    # Find ASC
    asc_deg = kundli.get("ascendant", {}).get("degree_decimal", 0.0) if isinstance(kundli.get("ascendant"), dict) else 0.0
    asc_p = next((p for p in planets if p["planet_name_simple"] == "Ascendant"), None)
    if asc_p:
        asc_sign_idx = asc_p["sign_index"]
    else:
        asc_sign_idx = int(asc_deg // 30) + 1
        
    # 2. Chara Karakas
    chara_karakas = calculate_chara_karakas(planets, JAIMINI_CONFIG)
    ak = next((k for k in chara_karakas if k["karaka_code"] == "AK"), None)
    amk = next((k for k in chara_karakas if k["karaka_code"] == "AmK"), None)
    dk = next((k for k in chara_karakas if k["karaka_code"] == "DK"), None)
    
    # 3. Karakamsha & Swamsha
    karakamsha = ak["navamsa_sign"] if ak else "Unknown"
    # Identify Navamsa Lagna for Swamsha
    d9_asc = kundli.get("ascendant", {}).get("navamsha", {}).get("navamsha_sign")
    if not d9_asc and asc_p:
        d9_asc = asc_p.get("navamsha", {}).get("navamsha_sign", "Unknown")
    
    # 4. Arudha Padas
    arudhas = calculate_arudhas(asc_sign_idx, planets)
    al = next((a for a in arudhas if a["house"] == 1), None)
    ul = next((a for a in arudhas if a["house"] == 12), None)
    
    # 5. Rashi Drishti Matrix
    rashi_matrix = []
    for i in range(1, 13):
        aspects = get_rashi_aspects(i)
        rashi_matrix.append({
            "sign": get_sign_name(i),
            "sign_index": i,
            "aspects": [get_sign_name(a) for a in aspects],
            "aspects_indices": aspects,
            "planets_in_sign": [p["planet_name_simple"] for p in planets if p.get("sign_index") == i]
        })
        
    # 6. Argala Analysis (Reference = AL for general example)
    argala = calculate_argala(al["final_pada_index"] if al else 1, planets)
    
    # 7. Chara Dasha
    # Parse DOB
    try:
        tob_parts = [int(p) for p in tob_str.split(":")]
        second_part = tob_parts[2] if len(tob_parts) > 2 else 0
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        birth_dt = datetime(dob.year, dob.month, dob.day, tob_parts[0], tob_parts[1], second_part)
    except:
        birth_dt = datetime.now()
        
    dasha_timeline = calculate_chara_dasha(asc_sign_idx, planets, birth_dt)
    
    # 8. Current Period logic
    now_dt = datetime.now()
    current_dasha = None
    for d in dasha_timeline:
        start = datetime.strptime(d["start_date"], "%Y-%m-%d")
        end = datetime.strptime(d["end_date"], "%Y-%m-%d")
        if start <= now_dt < end:
            current_dasha = d
            break
            
    if not current_dasha:
        current_dasha = dasha_timeline[-1] if dasha_timeline else {}

    # 9. Missing Sub-engines
    jaimini_yogas = calculate_jaimini_yogas(planets, chara_karakas)
    special_lagnas = calculate_special_lagnas(kundli)
    karakamsha_analysis = calculate_karakamsha_analysis(karakamsha, planets)
    
    # 10. Jaimini Transits (generate Kundli for today)
    try:
        now_str = now_dt.strftime("%Y-%m-%d")
        time_str = now_dt.strftime("%H:%M")
        transit_kundli = generate_full_kundli("Transit", now_str, time_str, pob_str, latitude, longitude, timezone)
        transit_planets = transit_kundli.get("planets", [])
        current_transits = calculate_jaimini_transits(transit_planets, arudhas, current_dasha.get("sign", ""))
    except Exception as e:
        current_transits = []

    # Pack everything
    return {
        "overview": {
            "name": name,
            "date_of_birth": dob_str,
            "time_of_birth": tob_str,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "ascendant_sign": get_sign_name(asc_sign_idx),
            "atmakaraka": ak["planet"] if ak else "Unknown",
            "amatyakaraka": amk["planet"] if amk else "Unknown",
            "darakaraka": dk["planet"] if dk else "Unknown",
            "karakamsha": karakamsha,
            "navamsa_lagna": d9_asc,
            "arudha_lagna": al["final_pada"] if al else "Unknown",
            "upapada": ul["final_pada"] if ul else "Unknown",
            "current_dasha_sign": current_dasha.get("sign", "Unknown")
        },
        "config": JAIMINI_CONFIG,
        "planets": planets, # Passthrough for UI drawing chart
        "chara_karakas": chara_karakas,
        "arudha_padas": arudhas,
        "rashi_drishti": rashi_matrix,
        "argala_on_al": argala,
        "chara_dasha": dasha_timeline,
        "jaimini_yogas": jaimini_yogas,
        "special_lagnas": special_lagnas,
        "karakamsha_analysis": karakamsha_analysis,
        "current_transits": current_transits,
        "current_period": {
            "current_date": now_dt.strftime("%Y-%m-%d"),
            "mahadasha": current_dasha
        }
    }
