"""Bhrigu Nandi Nadi (BNN) Astrological Engine."""
from typing import Dict, Any, List
from app.services.vedic_engine import generate_full_kundli
from app.services.bnn_rules import BNN_KARAKAS, BNN_EVENT_MAPPINGS, get_combination_meaning

def check_linkage(p1_idx: int, p2_idx: int) -> str:
    """Determine BNN linkage type between two sign indices (1-12)."""
    if p1_idx == p2_idx:
        return "Conjunction (1st)"
    
    # Trine (1-5-9)
    if (p2_idx - p1_idx) % 12 in [4, 8]:
        return "Trine (1-5-9)"
        
    # Adjacent (2-12)
    if (p2_idx - p1_idx) % 12 == 1:
        return "Ahead (2nd)"
    if (p2_idx - p1_idx) % 12 == 11:
        return "Behind (12th)"
        
    # Opposition (1-7)
    if (p2_idx - p1_idx) % 12 == 6:
        return "Opposition (7th)"
        
    return "None"

def generate_bnn_chart(
    name: str, dob_str: str, tob_str: str, pob_str: str,
    latitude: float, longitude: float, timezone: float
) -> Dict[str, Any]:
    """Generates the complete BNN Chart and Linkages."""
    
    kundli = generate_full_kundli(
        name, dob_str, tob_str, pob_str, latitude, longitude, timezone
    )
    
    bnn_planets = []
    
    # Filter only the 9 traditional planets
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    filtered_planets = [p for p in kundli.get("planets", []) if p.get("planet_name_simple", p["name"].split(" ")[0]) in valid_planets]
    
    for p in filtered_planets:
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        bnn_planets.append({
            "planet": p_name,
            "karaka": BNN_KARAKAS.get(p_name, ""),
            "sign": p.get("sign", ""),
            "sign_index": p.get("sign_index", 1),
            "degree": p.get("degree_dms", ""),
            "retrograde": p.get("is_retrograde", False),
            "linkages": []
        })

    # Evaluate linkages
    for p1 in bnn_planets:
        for p2 in bnn_planets:
            if p1["planet"] == p2["planet"]:
                continue
            
            linkage_type = check_linkage(p1["sign_index"], p2["sign_index"])
            if linkage_type != "None":
                p1["linkages"].append({
                    "planet": p2["planet"],
                    "type": linkage_type,
                    "meaning": get_combination_meaning(p1["planet"], p2["planet"])
                })

    # Generate Event Analysis
    event_analysis = []
    for event, target_karaka in BNN_EVENT_MAPPINGS.items():
        # Find the target planet
        target_p = next((p for p in bnn_planets if p["planet"] == target_karaka), None)
        if not target_p:
            continue
            
        # Get its strongest influencers (Conjunction and Trine)
        influencers = [lk for lk in target_p["linkages"] if lk["type"] in ["Conjunction (1st)", "Trine (1-5-9)"]]
        
        if not influencers:
            event_analysis.append({
                "category": event,
                "karaka_planet": target_karaka,
                "observation": f"{target_karaka} is isolated from major trinal influences. Success comes through self-effort.",
                "details": []
            })
            continue
            
        details = []
        for inf in influencers:
            details.append(f"{target_karaka} + {inf['planet']} ({inf['type']}): {inf['meaning']}")
            
        event_analysis.append({
            "category": event,
            "karaka_planet": target_karaka,
            "observation": f"{target_karaka} is strongly influenced by {', '.join([inf['planet'] for inf in influencers])}.",
            "details": details
        })

    return {
        "person_name": name,
        "date_of_birth": dob_str,
        "time_of_birth": tob_str,
        "ascendant_sign_index": kundli.get("ascendant_sign_index", 1),
        "planets": bnn_planets,
        "event_analysis": event_analysis
    }
