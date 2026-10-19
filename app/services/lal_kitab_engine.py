"""Lal Kitab Astrological Engine with authentic Varshphal and 35-Year Dasha Cycle."""
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from app.services.vedic_engine import generate_full_kundli
from app.services.lal_kitab_rules import get_lal_kitab_interpretation

# Lal Kitab Exaltation/Debilitation by House (Kala Purusha: 1=Aries .. 12=Pisces)
LK_EXALTATION_HOUSES = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6, 
    "Jupiter": 4, "Venus": 12, "Saturn": 7, "Rahu": 3, "Ketu": 9
}

LK_DEBILITATION_HOUSES = {
    "Sun": 7, "Moon": 8, "Mars": 4, "Mercury": 12, 
    "Jupiter": 10, "Venus": 6, "Saturn": 1, "Rahu": 9, "Ketu": 3
}

LK_PAKKA_GHAR = {
    "Sun": [1],
    "Moon": [2],
    "Mars": [3, 8],
    "Mercury": [6, 7],
    "Jupiter": [2, 5, 9, 11],
    "Venus": [7, 2],
    "Saturn": [10, 11],
    "Rahu": [12],
    "Ketu": [6]
}

LK_HOUSE_MEANINGS = {
    1: "Self, personality, body and vitality",
    2: "Family, accumulated wealth and speech",
    3: "Siblings, courage, efforts and short travels",
    4: "Mother, peace of mind, domestic life and property",
    5: "Children, intellect, higher learning and luck",
    6: "Enemies, health, debts, disputes and daily duties",
    7: "Spouse, marriage, partnerships and public relations",
    8: "Longevity, sudden transformations and occult",
    9: "Fortune, father, religion and destiny",
    10: "Career, profession, reputation and karma",
    11: "Income, gains, aspirations and social circle",
    12: "Expenses, foreign travels, solitude and spirituality"
}

LK_SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Classical Lal Kitab 35-Year Dasha Cycle (35 Saala Chakkar)
# Format: (Mahadasha Planet, Years, [(Antardasha Planet, Months), ...])
LK_DASHA_PERIODS = [
    ("Jupiter", 6, [("Ketu", 24), ("Jupiter", 24), ("Sun", 24)]),
    ("Sun", 2, [("Sun", 8), ("Moon", 8), ("Mars", 8)]),
    ("Moon", 1, [("Jupiter", 4), ("Sun", 4), ("Moon", 4)]),
    ("Venus", 3, [("Mars", 12), ("Venus", 12), ("Mercury", 12)]),
    ("Mars", 6, [("Mars", 24), ("Saturn", 24), ("Venus", 24)]),
    ("Mercury", 2, [("Moon", 8), ("Mars", 8), ("Jupiter", 8)]),
    ("Saturn", 6, [("Rahu", 24), ("Mercury", 24), ("Saturn", 24)]),
    ("Rahu", 6, [("Mars", 24), ("Ketu", 24), ("Rahu", 24)]),
    ("Ketu", 3, [("Saturn", 12), ("Rahu", 12), ("Ketu", 12)])
]

def determine_lk_dignity(planet: str, house: int) -> str:
    """Determine Lal Kitab specific dignity based strictly on House placement."""
    if LK_EXALTATION_HOUSES.get(planet) == house:
        return "Exalted"
    elif LK_DEBILITATION_HOUSES.get(planet) == house:
        return "Debilitated"
    return "Neutral"

def calculate_lal_kitab_dasha_35(dob_dt: date, target_date: Optional[date] = None) -> Dict[str, Any]:
    """Calculate authentic Lal Kitab 35-Year Dasha Cycle (35 Saala Chakkar)."""
    if target_date is None:
        target_date = date.today()

    cycles = []
    current_dasha_info = None
    curr_date = dob_dt

    for cycle_num in range(1, 4):
        cycle_start_age = (cycle_num - 1) * 35
        cycle_end_age = cycle_num * 35
        cycle_start_date = curr_date
        cycle_md_list = []
        cumulative_years = 0

        for p_name, md_years, antars in LK_DASHA_PERIODS:
            md_start = curr_date
            md_end = md_start + relativedelta(years=md_years)
            md_is_current = (md_start <= target_date < md_end)

            antar_list = []
            a_curr_date = md_start
            for a_name, a_months in antars:
                a_start = a_curr_date
                a_end = a_start + relativedelta(months=a_months)
                a_is_current = (a_start <= target_date < a_end)

                antar_list.append({
                    "planet": a_name,
                    "duration_months": a_months,
                    "duration_formatted": f"{a_months // 12} Yrs" if a_months >= 12 and a_months % 12 == 0 else f"{a_months} Months",
                    "start_date": a_start.strftime("%d %b %Y"),
                    "end_date": a_end.strftime("%d %b %Y"),
                    "is_current": a_is_current
                })

                if a_is_current:
                    current_dasha_info = {
                        "cycle": cycle_num,
                        "cycle_name": f"Cycle {cycle_num} (Age {cycle_start_age} - {cycle_end_age})",
                        "mahadasha_planet": p_name,
                        "mahadasha_start": md_start.strftime("%d %b %Y"),
                        "mahadasha_end": md_end.strftime("%d %b %Y"),
                        "mahadasha_years": md_years,
                        "antardasha_planet": a_name,
                        "antardasha_start": a_start.strftime("%d %b %Y"),
                        "antardasha_end": a_end.strftime("%d %b %Y"),
                        "antardasha_months": a_months,
                    }
                a_curr_date = a_end

            start_age = cycle_start_age + cumulative_years
            end_age = start_age + md_years
            cumulative_years += md_years

            cycle_md_list.append({
                "planet": p_name,
                "duration_years": md_years,
                "age_span": f"{start_age} - {end_age} Yrs",
                "start_date": md_start.strftime("%d %b %Y"),
                "end_date": md_end.strftime("%d %b %Y"),
                "is_current": md_is_current,
                "antardashas": antar_list
            })
            curr_date = md_end

        cycles.append({
            "cycle": cycle_num,
            "cycle_name": f"Cycle {cycle_num} (Age {cycle_start_age} - {cycle_end_age})",
            "start_date": cycle_start_date.strftime("%d %b %Y"),
            "end_date": curr_date.strftime("%d %b %Y"),
            "mahadashas": cycle_md_list
        })

    return {
        "current_dasha": current_dasha_info,
        "cycles": cycles
    }

def calculate_lal_kitab_varshphal(natal_planets: List[Dict[str, Any]], dob_dt: date, target_year: int) -> Dict[str, Any]:
    """
    Calculate Lal Kitab Varshphal (Annual Progressed Chart) for target_year.
    Classical progression: annual_house = ((natal_house - 1) + completed_age) % 12 + 1
    """
    today = date.today()
    completed_age = target_year - dob_dt.year
    if completed_age < 0:
        completed_age = 0
    running_year = completed_age + 1

    varsh_start = date(target_year, dob_dt.month, dob_dt.day)
    varsh_end = varsh_start + relativedelta(years=1)

    varsh_planets = []
    varsh_houses = {h: [] for h in range(1, 13)}

    for p in natal_planets:
        p_name = p.get("planet") or p.get("planet_name_simple") or p.get("name", "").split(" ")[0]
        if p_name in ["Ascendant", "Uranus", "Neptune", "Pluto"]:
            continue
        natal_h = int(p.get("house", 1))

        # Lal Kitab Annual progression formula
        annual_h = ((natal_h - 1) + completed_age) % 12 + 1
        varsh_sign = LK_SIGN_NAMES[annual_h - 1]
        dignity = determine_lk_dignity(p_name, annual_h)
        is_pakka = annual_h in LK_PAKKA_GHAR.get(p_name, [])
        interp = get_lal_kitab_interpretation(p_name, annual_h)

        varsh_houses[annual_h].append(p_name)
        varsh_planets.append({
            "planet": p_name,
            "house": annual_h,
            "natal_house": natal_h,
            "sign": varsh_sign,
            "sign_index": annual_h,
            "longitude_formatted": p.get("longitude_formatted", p.get("degree_formatted", "")),
            "retrograde": p.get("retrograde", p.get("is_retrograde", False)),
            "dignity": dignity,
            "is_pakka_ghar": is_pakka,
            "interpretation": interp
        })

    # Maasik Kundli (Monthly 12-month timeline)
    monthly_timeline = []
    for m in range(1, 13):
        m_start = varsh_start + relativedelta(months=m-1)
        m_end = varsh_start + relativedelta(months=m)
        m_house = m
        m_planets = varsh_houses[m_house]
        is_m_current = (m_start <= today < m_end)

        monthly_timeline.append({
            "month_number": m,
            "house": m_house,
            "sign": LK_SIGN_NAMES[m_house - 1],
            "start_date": m_start.strftime("%d %b %Y"),
            "end_date": m_end.strftime("%d %b %Y"),
            "planets_active": m_planets,
            "significance": LK_HOUSE_MEANINGS[m_house],
            "is_current": is_m_current
        })

    # Year Lord: House 1 resident or Mars
    house_1_planets = varsh_houses.get(1, [])
    varsh_lagna_lord = house_1_planets[0] if house_1_planets else "Mars"

    return {
        "target_year": target_year,
        "completed_age": completed_age,
        "running_year": running_year,
        "start_date": varsh_start.strftime("%d %b %Y"),
        "end_date": varsh_end.strftime("%d %b %Y"),
        "year_lord": varsh_lagna_lord,
        "planets": varsh_planets,
        "houses": [{"house_number": h, "meaning": LK_HOUSE_MEANINGS[h], "planets_present": varsh_houses[h]} for h in range(1, 13)],
        "monthly_timeline": monthly_timeline
    }

def generate_lal_kitab_chart(
    name: str, dob_str: str, tob_str: str, pob_str: str,
    latitude: float, longitude: float, timezone: float,
    target_year: Optional[int] = None
) -> Dict[str, Any]:
    """Generates the complete Lal Kitab Chart, 35-Year Dasha, and Varshphal."""
    
    # Base cosmic data from the core Swiss Ephemeris engine
    kundli = generate_full_kundli(
        name, dob_str, tob_str, pob_str, latitude, longitude, timezone
    )
    
    lk_planets = []
    lk_houses = {h: [] for h in range(1, 13)}
    
    # Process each planet for Lal Kitab logic
    for p in kundli.get("planets", []):
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        if p_name in ["Ascendant", "Uranus", "Neptune", "Pluto"]:
            continue
            
        house_num = p["house"]
        lk_sign = LK_SIGN_NAMES[house_num - 1]
        dignity = determine_lk_dignity(p_name, house_num)
        interp = get_lal_kitab_interpretation(p_name, house_num)
        is_pakka = house_num in LK_PAKKA_GHAR.get(p_name, [])
        
        lk_houses[house_num].append(p_name)
        lk_planets.append({
            "planet": p_name,
            "longitude_formatted": p.get("degree_formatted", ""),
            "sign": p.get("sign", ""),
            "lk_sign": lk_sign,
            "degree": p.get("degree_dms", ""),
            "house": house_num,
            "sign_index": house_num,
            "retrograde": p.get("is_retrograde", False),
            "dignity": dignity,
            "is_pakka_ghar": is_pakka,
            "interpretation": interp
        })
        
    houses_list = []
    for h in range(1, 13):
        houses_list.append({
            "house_number": h,
            "meaning": LK_HOUSE_MEANINGS[h],
            "planets_present": lk_houses[h]
        })

    # Parse birth date
    try:
        dob_dt = datetime.strptime(dob_str.strip(), "%Y-%m-%d").date()
    except Exception:
        try:
            dob_dt = datetime.strptime(dob_str.strip(), "%d/%m/%Y").date()
        except Exception:
            dob_dt = date.today()

    today = date.today()
    if target_year is None:
        target_year = today.year

    # 1. Authentic Lal Kitab 35-Year Dasha Cycle
    dasha_35_years = calculate_lal_kitab_dasha_35(dob_dt, today)

    # 2. Authentic Lal Kitab Varshphal (Annual Progressed Chart) for target_year
    current_varshphal = calculate_lal_kitab_varshphal(lk_planets, dob_dt, target_year)

    # 3. Available Varshphal Years list (Ages 0 to 80)
    available_years = []
    varshphals_cache = {}
    for age in range(0, 81):
        y = dob_dt.year + age
        is_curr = (y == target_year)
        available_years.append({
            "year": y,
            "age": age,
            "running_year": age + 1,
            "is_current": is_curr
        })
        # Precompute the chart so user can flip years instantly
        varshphals_cache[str(y)] = calculate_lal_kitab_varshphal(lk_planets, dob_dt, y)

    return {
        "person_name": name,
        "date_of_birth": dob_str,
        "time_of_birth": tob_str,
        "place_of_birth": pob_str,
        "ascendant_degree": kundli.get("ascendant_degree_formatted", ""),
        "planets": lk_planets,
        "houses": houses_list,
        "dasha_35_years": dasha_35_years,
        "varshphal": current_varshphal,
        "varshphals": varshphals_cache,
        "available_varshphal_years": available_years
    }
