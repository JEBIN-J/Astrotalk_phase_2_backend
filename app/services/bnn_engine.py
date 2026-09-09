from typing import Dict, Any, List
from datetime import datetime
from app.services.vedic_engine import generate_full_kundli
from app.services.bnn_rules import BNN_KARAKAS, BNN_TRINE_GROUPS, get_bnn_relationship, BNN_EVENTS, analyze_bnn_combination

def calculate_current_age(dob_str: str, target_date_str: str = None) -> float:
    dob = datetime.strptime(dob_str, "%Y-%m-%d")
    now = datetime.strptime(target_date_str, "%Y-%m-%d") if target_date_str else datetime.now()
    days_alive = (now - dob).days
    return days_alive / 365.25

def get_dispositor(sign_index: int, planets: List[Dict]) -> Dict:
    lords = {1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"}
    lord_name = lords.get(sign_index)
    return next((p for p in planets if p.get("planet_name_simple") == lord_name), None)

def generate_bnn_chart(
    name: str, dob_str: str, tob_str: str, pob_str: str,
    latitude: float, longitude: float, timezone: float,
    target_date_str: str = None
) -> Dict[str, Any]:
    """Generates the complete, deeply calculated BNN Chart."""
    
    # 1. Fetch exact natal planetary data using Swiss Ephemeris
    kundli = generate_full_kundli(
        name, dob_str, tob_str, pob_str, latitude, longitude, timezone
    )
    
    valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    natal_planets = [p for p in kundli.get("planets", []) if p.get("planet_name_simple", p["name"].split(" ")[0]) in valid_planets]
    
    # Also fetch current transit planets
    now = datetime.strptime(target_date_str, "%Y-%m-%d") if target_date_str else datetime.now()
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

    # 4. Progressions
    # Jupiter Progression (1 year per sign = 12 years per cycle)
    jupiter = next((p for p in bnn_planets if p["planet"] == "Jupiter"), None)
    jupiter_progression = {}
    if jupiter:
        jup_deg = jupiter["degree_decimal"]
        jup_sign_idx = jupiter["sign_index"]
        # 30 degrees = 1 year => 1 degree = 1/30 year
        deg_in_sign = jup_deg % 30
        years_elapsed_in_sign = deg_in_sign / 30.0
        years_remaining_in_sign = 1.0 - years_elapsed_in_sign
        
        cycle = int(current_age // 12) + 1
        # It takes 1 year to move 1 sign
        total_years_from_start_of_sign = current_age + years_elapsed_in_sign
        progressed_signs_moved = int(total_years_from_start_of_sign)
        curr_prog_sign_idx = ((jup_sign_idx - 1 + progressed_signs_moved) % 12) + 1
        
        elapsed_in_current_prog_sign = total_years_from_start_of_sign - progressed_signs_moved
        remaining_in_current_prog_sign = 1.0 - elapsed_in_current_prog_sign
        
        SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        curr_prog_sign_name = SIGNS[curr_prog_sign_idx - 1]
        
        rounds = []
        for i in range(1, 7): # up to 72 years
            r_start = (i-1)*12
            r_end = i*12
            rounds.append({
                "round": i,
                "age_start": r_start,
                "age_end": r_end,
                "natal_sign": jupiter["sign"],
                "natal_degree": jupiter["degree"],
                "progressed_sign": "Moves dynamically",
                "active_connections": "Calculated via engine"
            })
            
        jupiter_progression = {
            "natal_sign": jupiter["sign"],
            "natal_degree": jupiter["degree"],
            "current_age": round(current_age, 2),
            "current_cycle": cycle,
            "elapsed_progression_years": round(elapsed_in_current_prog_sign, 2),
            "remaining_progression_years": round(remaining_in_current_prog_sign, 2),
            "current_progressed_sign_index": curr_prog_sign_idx,
            "current_progressed_sign_name": curr_prog_sign_name,
            "rounds": rounds
        }

    # Saturn Progression (29.4568 years per cycle)
    saturn = next((p for p in bnn_planets if p["planet"] == "Saturn"), None)
    saturn_progression = {}
    if saturn:
        years_per_sign = 29.4568 / 12.0
        deg_in_sign = saturn["degree_decimal"] % 30
        years_elapsed_in_sign = (deg_in_sign / 30.0) * years_per_sign

        cycle = int(current_age // 29.4568) + 1
        total_years_from_start_of_sign = current_age + years_elapsed_in_sign
        prog_signs_moved = int(total_years_from_start_of_sign / years_per_sign)
        curr_prog_sign_idx = ((saturn["sign_index"] - 1 + prog_signs_moved) % 12) + 1
        
        elapsed_in_current_prog_sign = (total_years_from_start_of_sign - (prog_signs_moved * years_per_sign))
        remaining_in_current_prog_sign = years_per_sign - elapsed_in_current_prog_sign
        
        SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        curr_prog_sign_name = SIGNS[curr_prog_sign_idx - 1]
        
        saturn_progression = {
            "natal_sign": saturn["sign"],
            "natal_degree": saturn["degree"],
            "current_age": round(current_age, 2),
            "cycle": cycle,
            "elapsed_progression_years": round(elapsed_in_current_prog_sign, 2),
            "remaining_progression_years": round(remaining_in_current_prog_sign, 2),
            "current_progressed_sign_index": curr_prog_sign_idx,
            "current_progressed_sign_name": curr_prog_sign_name
        }

    # Rahu/Ketu Progression (18.55 years, reverse)
    rahu = next((p for p in bnn_planets if p["planet"] == "Rahu"), None)
    ketu = next((p for p in bnn_planets if p["planet"] == "Ketu"), None)
    nodes_progression = {}
    if rahu and ketu:
        years_per_sign = 18.55 / 12.0
        deg_in_sign = rahu["degree_decimal"] % 30
        years_elapsed_in_sign = (deg_in_sign / 30.0) * years_per_sign
        
        cycle = int(current_age // 18.55) + 1
        total_years_from_start_of_sign = current_age + years_elapsed_in_sign
        prog_signs_moved = int(total_years_from_start_of_sign / years_per_sign)
        
        # Reverse movement
        r_prog_sign_idx = ((rahu["sign_index"] - 1 - prog_signs_moved) % 12) + 1
        if r_prog_sign_idx <= 0: r_prog_sign_idx += 12
        k_prog_sign_idx = ((ketu["sign_index"] - 1 - prog_signs_moved) % 12) + 1
        if k_prog_sign_idx <= 0: k_prog_sign_idx += 12
        
        nodes_progression = {
            "rahu_natal": rahu["sign"],
            "ketu_natal": ketu["sign"],
            "current_age": round(current_age, 2),
            "cycle": cycle,
            "rahu_progressed_sign_index": r_prog_sign_idx,
            "ketu_progressed_sign_index": k_prog_sign_idx
        }


    # --- Dynamic Progressed Planets for BNN ---
    import copy
    progressed_bnn_planets = copy.deepcopy(bnn_planets)
    SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    for p in progressed_bnn_planets:
        if p["planet"] == "Jupiter" and jupiter_progression.get("current_progressed_sign_index"):
            idx = jupiter_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
        elif p["planet"] == "Saturn" and saturn_progression.get("current_progressed_sign_index"):
            idx = saturn_progression["current_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
        elif p["planet"] == "Rahu" and nodes_progression.get("rahu_progressed_sign_index"):
            idx = nodes_progression["rahu_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]
        elif p["planet"] == "Ketu" and nodes_progression.get("ketu_progressed_sign_index"):
            idx = nodes_progression["ketu_progressed_sign_index"]
            p["sign_index"] = idx
            p["sign"] = SIGNS[idx - 1]

    # 2. BNN Relationship Matrix
    seen_pairs = set()
    relationships = []
    for p1 in progressed_bnn_planets:
        for p2 in progressed_bnn_planets:
            if p1["planet"] == p2["planet"]: continue
            
            # Avoid duplicate symmetrical pairs (e.g., Jupiter+Sun and Sun+Jupiter)
            pair_sig = tuple(sorted([p1["planet"], p2["planet"]]))
            if pair_sig in seen_pairs: continue
            
            rel = get_bnn_relationship(p1["sign_index"], p2["sign_index"])
            if rel["strength"] > 0:
                seen_pairs.add(pair_sig)
                dist = ((p2["sign_index"] - p1["sign_index"]) % 12) + 1
                if dist == 1: dist_str = "1"
                else: dist_str = f"1-{dist}"
                
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
            # Check internal strength if multiple planets
            strength = 100 if len(planets_in_group) > 1 else 0
            trine_groups.append({
                "group": group_name,
                "signs": ", ".join(signs),
                "planets": planets_in_group,
                "strength": strength
            })

    # 5. Planetary Chain (Dispositor linkage)
    chains = []
    for p in progressed_bnn_planets:
        chain_links = []
        chain_links.append({"planet": p["planet"], "reason": "Base Planet"})
        
        # 1. Trine
        trines = [p2["planet"] for p2 in progressed_bnn_planets if p2["planet"] != p["planet"] and get_bnn_relationship(p["sign_index"], p2["sign_index"])["relationship"].startswith("Trine")]
        if trines: chain_links.append({"planet": ", ".join(trines), "reason": "Trine Connection"})
        
        # 2. Dispositor
        disp = get_dispositor(p["sign_index"], natal_planets)
        if disp and disp.get("planet_name_simple") != p["planet"]:
            chain_links.append({"planet": disp.get("planet_name_simple"), "reason": "Dispositor"})
            
        chains.append({
            "base_planet": p["planet"],
            "chain": chain_links
        })

    # 6. Transit Activation
    transit_activations = []
    for tp in transit_planets:
        tp_name = tp.get("planet_name_simple", tp["name"].split(" ")[0])
        tp_sign_idx = tp.get("sign_index", 1)
        for np in bnn_planets:
            rel = get_bnn_relationship(tp_sign_idx, np["sign_index"])
            if rel["strength"] >= 50: # Only significant activations
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

    # 7. Event Activation
    event_activations = []
    for event, karakas in BNN_EVENTS.items():
        # Check dynamic strength between these karakas (using progressed positions for Jupiter/Saturn)
        if len(karakas) >= 2:
            p1 = next((p for p in progressed_bnn_planets if p["planet"] == karakas[0]), None)
            p2 = next((p for p in progressed_bnn_planets if p["planet"] == karakas[1]), None)
            
            if p1 and p2:
                rel = get_bnn_relationship(p1["sign_index"], p2["sign_index"])
                
                # Check if major transits (Jupiter/Saturn) are currently triggering the primary karaka
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
            "bnn_reference_planet": "Jupiter (Male) / Venus (Female)"
        },
        "planets": progressed_bnn_planets,
        "karakatwas": [{"planet": k, "significations": v} for k, v in BNN_KARAKAS.items()],
        "relationships": relationships,
        "trine_groups": trine_groups,
        "progressions": {
            "jupiter": jupiter_progression,
            "saturn": saturn_progression,
            "nodes": nodes_progression
        },
        "chains": chains,
        "transit_activations": transit_activations,
        "events": event_activations,
        "debug": {
            "julian_day": kundli.get("julian_day", "N/A"), # Assuming we can add this or it's implicitly there
            "transit_date": now.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
