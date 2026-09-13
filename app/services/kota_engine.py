import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.services.vedic_engine import generate_full_kundli

NAKSHATRAS_28 = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Abhijit", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

KOTA_ZONES = {
    "STAMBHA": [4, 11, 18, 25],
    "MADHYA": [3, 5, 10, 12, 17, 19, 24, 26],
    "PRAKAARA": [2, 6, 9, 13, 16, 20, 23, 27],
    "BAHYA": [1, 7, 8, 14, 15, 21, 22, 28]
}

def get_zone_for_position(relative_pos: int) -> str:
    for zone, positions in KOTA_ZONES.items():
        if relative_pos in positions:
            return zone
    return "UNKNOWN"

def get_28_nakshatra(longitude: float):
    """Map sidereal longitude strictly to the 28-Nakshatra system including Abhijit."""
    longitude = longitude % 360.0
    
    # Precise boundaries
    UTTARA_ASHADHA_START = 266.6666667
    ABHIJIT_START = 276.6666667
    SHRAVANA_START = 280.8888889 # 280°53'20"
    DHANISHTHA_START = 293.3333333
    
    if UTTARA_ASHADHA_START <= longitude < ABHIJIT_START:
        idx = 21
        deg_inside = longitude - UTTARA_ASHADHA_START
    elif ABHIJIT_START <= longitude < SHRAVANA_START:
        idx = 22
        deg_inside = longitude - ABHIJIT_START
    elif SHRAVANA_START <= longitude < DHANISHTHA_START:
        idx = 23
        deg_inside = longitude - SHRAVANA_START
    elif longitude >= DHANISHTHA_START:
        base_idx = int((longitude - DHANISHTHA_START) / 13.3333333)
        idx = 24 + base_idx
        deg_inside = longitude - (DHANISHTHA_START + base_idx * 13.3333333)
    else:
        base_idx = int(longitude / 13.3333333)
        idx = base_idx + 1
        deg_inside = longitude - (base_idx * 13.3333333)
        
    pada = math.floor(deg_inside / 3.3333333) + 1
    if pada > 4: pada = 4 # Cap for Abhijit/Shravana boundaries
        
    return {
        "index": idx,
        "name": NAKSHATRAS_28[idx - 1],
        "degree_inside": deg_inside,
        "pada": pada
    }

def get_planet_nature(planet: str, is_retrograde: bool) -> str:
    benefics = ["Jupiter", "Venus", "Moon", "Mercury"]
    malefics = ["Saturn", "Mars", "Sun", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]
    if planet in benefics: return "Benefic"
    if planet in malefics: return "Malefic"
    return "Neutral"

def format_degree(decimal_deg: float) -> str:
    d = int(decimal_deg)
    m = int((decimal_deg - d) * 60)
    s = int((((decimal_deg - d) * 60) - m) * 60)
    return f"{d:02d}°{m:02d}'{s:02d}\""

def generate_kota_chakra(
    name: str, dob_str: str, tob_str: str, pob_str: str,
    latitude: float, longitude: float, timezone: float,
    transit_date_str: str = None, transit_time_str: str = None
) -> Dict[str, Any]:
    
    # 1. Calculate Natal Chart via Swiss Ephemeris
    natal = generate_full_kundli(name, dob_str, tob_str, pob_str, latitude, longitude, timezone)
    natal_planets = natal.get("planets", [])
    
    moon = next((p for p in natal_planets if p["planet_name_simple"] == "Moon"), None)
    if not moon:
        raise Exception("Failed to calculate Natal Moon")
        
    moon_lon = moon.get("degree_decimal_full", moon.get("degree_decimal", 0.0))
    janma_nak = get_28_nakshatra(moon_lon)
    
    # 2. Calculate Transit Chart
    if not transit_date_str or not transit_time_str:
        now = datetime.utcnow() + timedelta(hours=timezone)
        transit_date_str = now.strftime("%Y-%m-%d")
        transit_time_str = now.strftime("%H:%M")
        
    # We need "previous" transit chart (24 hours ago) for movement analysis
    try:
        t_dt = datetime.strptime(f"{transit_date_str} {transit_time_str}", "%Y-%m-%d %H:%M")
    except:
        t_dt = datetime.utcnow() + timedelta(hours=timezone)
        
    t_prev = t_dt - timedelta(days=1)
    
    transit_current = generate_full_kundli("Transit", t_dt.strftime("%Y-%m-%d"), t_dt.strftime("%H:%M"), pob_str, latitude, longitude, timezone)
    transit_prev = generate_full_kundli("TransitPrev", t_prev.strftime("%Y-%m-%d"), t_prev.strftime("%H:%M"), pob_str, latitude, longitude, timezone)
    
    # 3. Mapping Transits
    transits = []
    zones_map = {"BAHYA": [], "PRAKAARA": [], "MADHYA": [], "STAMBHA": []}
    alerts = []
    
    t_planets = transit_current.get("planets", [])
    p_planets = {p["planet_name_simple"]: p for p in transit_prev.get("planets", [])}
    
    # Keep standard + modern
    include_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]
    
    for tp in t_planets:
        p_name = tp["planet_name_simple"]
        if p_name not in include_planets: continue
        
        t_lon = tp.get("degree_decimal_full", tp.get("degree_decimal", 0.0))
        t_nak = get_28_nakshatra(t_lon)
        
        rel_pos = ((t_nak["index"] - janma_nak["index"]) % 28) + 1
        zone = get_zone_for_position(rel_pos)
        is_retrograde = tp.get("is_retrograde", False)
        nature = get_planet_nature(p_name, is_retrograde)
        
        # Movement Analysis (Mathematically accurate Pravesha / Nirgamana)
        # Inwards (Entering) paths: 1-4, 8-11, 15-18, 22-25
        # Outwards (Exiting) paths: 5-7, 12-14, 19-21, 26-28
        inward_paths = [1, 2, 3, 4, 8, 9, 10, 11, 15, 16, 17, 18, 22, 23, 24, 25]
        
        if rel_pos in inward_paths:
            movement = "PRAVESHA" if not is_retrograde else "NIRGAMANA"
        else:
            movement = "NIRGAMANA" if not is_retrograde else "PRAVESHA"
                    
        transit_obj = {
            "planet": p_name,
            "longitude": format_degree(t_lon),
            "sign": tp.get("sign", ""),
            "nakshatra": t_nak["name"],
            "pada": t_nak["pada"],
            "relative_position": rel_pos,
            "zone": zone,
            "nature": nature,
            "retrograde": is_retrograde,
            "movement": movement
        }
        transits.append(transit_obj)
        if zone in zones_map:
            zones_map[zone].append(transit_obj)
            
        # Alerts Rule Engine
        if zone == "STAMBHA" and nature == "Malefic":
            alerts.append({"severity": "Critical", "rule": f"{p_name} in Stambha", "details": "Malefic in the core pillar."})
        if movement == "PRAVESHA" and nature == "Malefic" and zone in ["STAMBHA", "MADHYA"]:
            alerts.append({"severity": "Warning", "rule": f"{p_name} entering {zone}", "details": "Malefic approaching inner zones."})
            
    # 4. Kota Swami & Paala
    kota_swami = moon.get("sign_lord", "Unknown")
    
    # Calculate Kota Paala dynamically based on the 27-Nakshatra Lord of the Moon
    # Sequence of lords: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
    nak_lords_seq = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    idx_27 = int(moon_lon / (360.0 / 27.0))
    kota_paala = nak_lords_seq[idx_27 % 9]
    
    # 5. Master Nakshatra Map
    nak_map = []
    for i in range(1, 29):
        rel = ((i - janma_nak["index"]) % 28) + 1
        z = get_zone_for_position(rel)
        nak_map.append({
            "index": i,
            "nakshatra": NAKSHATRAS_28[i-1],
            "relative_position": rel,
            "zone": z
        })

    return {
        "overview": {
            "birth_date": dob_str,
            "birth_time": tob_str,
            "transit_date": transit_date_str,
            "transit_time": transit_time_str,
            "ayanamsa": "Lahiri"
        },
        "natal_reference": {
            "moon_longitude": format_degree(moon_lon),
            "moon_sign": moon.get("sign", ""),
            "janma_nakshatra": janma_nak["name"],
            "janma_index": janma_nak["index"],
            "pada": janma_nak["pada"],
            "kota_swami": kota_swami,
            "kota_paala": kota_paala
        },
        "zones": zones_map,
        "transits": transits,
        "nakshatra_mapping": nak_map,
        "alerts": alerts,
        "calculation_details": {
            "moon_decimal": moon_lon,
            "transit_date_str": transit_date_str
        }
    }
