"""Lal Kitab Astrological Engine."""
from typing import Dict, Any, List
from app.services.vedic_engine import generate_full_kundli
from app.services.lal_kitab_rules import get_lal_kitab_interpretation

# Lal Kitab Exaltation/Debilitation by House (Kala Purusha)
LK_EXALTATION_HOUSES = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6, 
    "Jupiter": 4, "Venus": 12, "Saturn": 7, "Rahu": 3, "Ketu": 9 # Or 6 depending on branch, but using standard 3/9 for nodes
}

LK_DEBILITATION_HOUSES = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12, 
    "Jupiter": 10, "Venus": 6, "Saturn": 1, "Rahu": 9, "Ketu": 3
}

LK_HOUSE_MEANINGS = {
    1: "Self, personality, body",
    2: "Family, wealth, speech",
    3: "Siblings, courage, communication",
    4: "Mother, home, property",
    5: "Children, intelligence, education",
    6: "Enemies, debts, disease, service",
    7: "Marriage, spouse, partnership",
    8: "Longevity, sudden events, inheritance",
    9: "Fortune, father, higher principles",
    10: "Career, profession, status",
    11: "Income, gains, fulfilment",
    12: "Expenses, foreign matters, isolation"
}

def determine_lk_dignity(planet: str, house: int) -> str:
    """Determine Lal Kitab specific dignity based strictly on House placement."""
    if LK_EXALTATION_HOUSES.get(planet) == house:
        return "Exalted"
    elif LK_DEBILITATION_HOUSES.get(planet) == house:
        return "Debilitated"
    return "Neutral"

def generate_lal_kitab_chart(
    name: str, dob_str: str, tob_str: str, pob_str: str,
    latitude: float, longitude: float, timezone: float
) -> Dict[str, Any]:
    """Generates the complete Lal Kitab Chart and Interpretations."""
    
    # Base cosmic data from the core Swiss Ephemeris engine
    kundli = generate_full_kundli(
        name, dob_str, tob_str, pob_str, latitude, longitude, timezone
    )
    
    lk_planets = []
    lk_houses = {h: [] for h in range(1, 13)}
    
    # Process each planet for Lal Kitab logic
    for p in kundli.get("planets", []):
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        if p_name == "Ascendant" or p_name == "Uranus" or p_name == "Neptune" or p_name == "Pluto":
            continue
            
        house_num = p["house"]
        
        # In Lal Kitab, House 1 is always Aries. So sign index = house_num
        lk_sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        lk_sign = lk_sign_names[house_num - 1]
        
        dignity = determine_lk_dignity(p_name, house_num)
        interp = get_lal_kitab_interpretation(p_name, house_num)
        
        # Add to house map
        lk_houses[house_num].append(p_name)
        
        lk_planets.append({
            "planet": p_name,
            "longitude_formatted": p.get("degree_formatted", ""),
            "sign": p.get("sign", ""), # Actual Vedic sign
            "lk_sign": lk_sign,       # Lal Kitab Kala Purusha sign
            "degree": p.get("degree_dms", ""),
            "house": house_num,
            "retrograde": p.get("is_retrograde", False),
            "dignity": dignity,
            "interpretation": interp
        })
        
    # Format houses for the UI
    houses_list = []
    for h in range(1, 13):
        houses_list.append({
            "house_number": h,
            "meaning": LK_HOUSE_MEANINGS[h],
            "planets_present": lk_houses[h]
        })
        
    return {
        "person_name": name,
        "date_of_birth": dob_str,
        "time_of_birth": tob_str,
        "place_of_birth": pob_str,
        "ascendant_degree": kundli.get("ascendant_degree_formatted", ""),
        "planets": lk_planets,
        "houses": houses_list
    }
