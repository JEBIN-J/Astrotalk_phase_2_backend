"""Jaimini Astrological Engine."""
from typing import Dict, Any, List
import re
from app.services.vedic_engine import generate_full_kundli
from app.services.jaimini_rules import JAIMINI_KARAKAS, get_karaka_interpretation

def parse_degree_to_decimal(dms_str: str) -> float:
    """Parse a degree string like '28° 31\' 49"' into a decimal float."""
    match = re.search(r'(\d+)°\s*(\d+)\'\s*(\d+)"', dms_str)
    if not match:
        return 0.0
    deg, min, sec = map(float, match.groups())
    return deg + (min / 60.0) + (sec / 3600.0)

def get_rashi_aspects(sign_index: int) -> List[int]:
    """Calculate Jaimini Rashi Drishti (Aspects)."""
    # 1=Aries, 2=Taurus, 3=Gemini, 4=Cancer, 5=Leo, 6=Virgo
    # 7=Libra, 8=Scorpio, 9=Sagittarius, 10=Capricorn, 11=Aquarius, 12=Pisces
    
    # Cardinal: 1, 4, 7, 10
    # Fixed: 2, 5, 8, 11
    # Mutable: 3, 6, 9, 12
    
    if sign_index in [1, 4, 7, 10]:
        # Cardinal aspects all Fixed EXCEPT adjacent
        fixed_signs = {2, 5, 8, 11}
        adjacent = (sign_index % 12) + 1
        return list(fixed_signs - {adjacent})
        
    elif sign_index in [2, 5, 8, 11]:
        # Fixed aspects all Cardinal EXCEPT adjacent
        cardinal_signs = {1, 4, 7, 10}
        adjacent = ((sign_index - 2) % 12) + 1
        return list(cardinal_signs - {adjacent})
        
    elif sign_index in [3, 6, 9, 12]:
        # Mutable aspects all other Mutable
        mutable_signs = {3, 6, 9, 12}
        return list(mutable_signs - {sign_index})
        
    return []

def calculate_arudha(house_sign_idx: int, lord_sign_idx: int) -> int:
    """Calculate the Arudha Pada by counting distance from house to lord, and projecting same distance."""
    # Distance from House to Lord (inclusive)
    distance = (lord_sign_idx - house_sign_idx) % 12
    if distance < 0:
        distance += 12
    
    # Project that distance forward from Lord
    arudha_idx = (lord_sign_idx + distance) % 12
    if arudha_idx == 0:
        arudha_idx = 12
        
    # Jaimini Exceptions
    if arudha_idx == house_sign_idx:
        arudha_idx = (arudha_idx + 9) % 12
    elif arudha_idx == (house_sign_idx + 6) % 12 or arudha_idx == (house_sign_idx - 6) % 12:
        arudha_idx = (arudha_idx + 9) % 12
        
    if arudha_idx == 0:
        arudha_idx = 12
        
    return arudha_idx

def get_lord_of_house(house_idx: int, lagna_sign_idx: int) -> str:
    """Find the planetary lord of a given house based on Ascendant."""
    sign_idx = (lagna_sign_idx + house_idx - 2) % 12 + 1
    
    lords = {
        1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 
        5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars", 
        9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
    }
    return lords.get(sign_idx, "Sun")

def generate_jaimini_chart(
    name: str, dob_str: str, tob_str: str, pob_str: str,
    latitude: float, longitude: float, timezone: float
) -> Dict[str, Any]:
    """Generates the complete Jaimini Chart and Karakas."""
    
    kundli = generate_full_kundli(
        name, dob_str, tob_str, pob_str, latitude, longitude, timezone
    )
    
    # 1. Chara Karakas (7-Karaka Scheme)
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    jaimini_planets = []
    
    for p in kundli.get("planets", []):
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        if p_name in valid_planets:
            dec_deg = parse_degree_to_decimal(p.get("degree_dms", "0° 0' 0\""))
            nav_info = p.get("navamsha", {})
            nav_sign = nav_info.get("navamsha_sign", "Aries")
            
            jaimini_planets.append({
                "planet": p_name,
                "sign": p.get("sign", ""),
                "sign_index": p.get("sign_index", 1),
                "degree": p.get("degree_dms", ""),
                "decimal_degree": dec_deg,
                "navamsa_sign": nav_sign,
                "retrograde": p.get("is_retrograde", False)
            })
            
    # Sort descending by degree
    jaimini_planets.sort(key=lambda x: x["decimal_degree"], reverse=True)
    
    karaka_titles = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
    chara_karakas = []
    
    ak_planet = None
    
    for i, p in enumerate(jaimini_planets):
        if i < len(karaka_titles):
            title = karaka_titles[i]
            
            if title == "AK":
                ak_planet = p
                
            chara_karakas.append({
                "karaka_code": title,
                "karaka_name": JAIMINI_KARAKAS[title]["name"],
                "meaning": JAIMINI_KARAKAS[title]["meaning"],
                "planet": p["planet"],
                "degree": p["degree"],
                "interpretation": get_karaka_interpretation(p["planet"], title)
            })

    # 2. Karakamsha (Navamsa sign of AK)
    karakamsha = ak_planet["navamsa_sign"] if ak_planet else "Unknown"
    
    # 3. Arudha Padas (AL and UL)
    # Get Ascendant sign index
    # Note: In vedic_engine.py, Ascendant might not be in the 'planets' array. It's often at the root as kundli['ascendant'] or we calculate it.
    asc_deg = kundli.get("ascendant", {}).get("degree_decimal", 0.0) if isinstance(kundli.get("ascendant"), dict) else 0.0
    lagna_sign_idx = int(asc_deg // 30) + 1 if asc_deg else 1
    
    # Check if Ascendant is explicitly in the planets array
    asc_planet = next((p for p in kundli.get("planets", []) if p.get("planet_name_simple", p["name"].split(" ")[0]) == "Ascendant"), None)
    if asc_planet and "sign_index" in asc_planet:
        lagna_sign_idx = asc_planet["sign_index"]
    
    # Get Lagna Lord (Lord of 1st House)
    lagna_lord_name = get_lord_of_house(1, lagna_sign_idx)
    lagna_lord = next((p for p in jaimini_planets if p["planet"] == lagna_lord_name), None)
    
    al_idx = calculate_arudha(lagna_sign_idx, lagna_lord["sign_index"]) if lagna_lord else lagna_sign_idx
    
    # Get 12th House Lord
    h12_sign_idx = (lagna_sign_idx + 10) % 12 + 1
    h12_lord_name = get_lord_of_house(12, lagna_sign_idx)
    h12_lord = next((p for p in jaimini_planets if p["planet"] == h12_lord_name), None)
    
    ul_idx = calculate_arudha(h12_sign_idx, h12_lord["sign_index"]) if h12_lord else h12_sign_idx
    
    sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

    # 4. Jaimini Rashi Aspects
    rashi_aspects = []
    for p in jaimini_planets:
        aspected_indices = get_rashi_aspects(p["sign_index"])
        aspected_signs = [sign_names[i-1] for i in aspected_indices]
        
        # Find planets sitting in those aspected signs
        aspected_planets = [target["planet"] for target in jaimini_planets if target["sign_index"] in aspected_indices]
        
        rashi_aspects.append({
            "planet": p["planet"],
            "sign": p["sign"],
            "aspects_signs": aspected_signs,
            "aspects_planets": aspected_planets
        })

    return {
        "person_name": name,
        "date_of_birth": dob_str,
        "time_of_birth": tob_str,
        "ascendant_sign_index": lagna_sign_idx,
        "planets": jaimini_planets,
        "chara_karakas": chara_karakas,
        "special_points": [
            {
                "name": "Karakamsha",
                "sign": karakamsha,
                "meaning": "The soul's deeper purpose and innate skills (D9 sign of AK)."
            },
            {
                "name": "Arudha Lagna (AL)",
                "sign": sign_names[al_idx - 1],
                "meaning": "How society perceives you; your material image."
            },
            {
                "name": "Upapada Lagna (UL)",
                "sign": sign_names[ul_idx - 1],
                "meaning": "The reality of marriage and the spouse."
            }
        ],
        "rashi_aspects": rashi_aspects
    }
