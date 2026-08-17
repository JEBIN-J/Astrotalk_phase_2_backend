from typing import Dict, Any, List
import datetime
from app.services.vedic_engine import generate_full_kundli
from app.utils.constants import ZODIAC_SIGNS

# Map rashi name to its index (1-12)
RASHI_TO_INDEX = {
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4,
    "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8,
    "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12
}

RASHI_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
}

RASHI_ELEMENTS = {
    1: "Fire", 2: "Earth", 3: "Air", 4: "Water",
    5: "Fire", 6: "Earth", 7: "Air", 8: "Water",
    9: "Fire", 10: "Earth", 11: "Air", 12: "Water"
}

LUCKY_NUMBERS = {
    "Sun": 1, "Moon": 2, "Jupiter": 3, "Rahu": 4, 
    "Mercury": 5, "Venus": 6, "Ketu": 7, "Saturn": 8, "Mars": 9
}

LUCKY_COLORS = {
    "Sun": "Orange", "Moon": "White", "Mars": "Red",
    "Mercury": "Green", "Jupiter": "Yellow", "Venus": "Pink",
    "Saturn": "Blue"
}

LUCKY_DIRECTIONS = {
    "Fire": "East", "Earth": "South", "Air": "West", "Water": "North"
}

# Simple gochar (transit) rules mapping [Planet][House_from_Moon] to predictions
# These strings represent classical Vedic Phaladesh. Which string is chosen is DYNAMICALLY
# determined by calculating the real-time planetary longitudes and shifting them into houses.
GOCHAR_RULES = {
    "Jupiter": {
        1: {"finance": "Expenses may rise, plan carefully.", "overall": "A period of self-reflection and inner growth.", "health": "Take care of minor ailments."},
        2: {"finance": "Excellent day for wealth accumulation and family joy.", "overall": "Financial gains and domestic happiness are highlighted.", "family": "Peace and harmony at home."},
        3: {"career": "Short travels may bring new professional connections.", "overall": "Communication and sibling relations come into focus.", "social": "Good day for networking."},
        4: {"family": "Peace at home, though you might feel slightly restricted.", "overall": "Focus on home and emotional well-being today.", "career": "Property matters may need attention."},
        5: {"love": "Romance blossoms, and creativity is at a peak.", "education": "Excellent day for learning and competitive exams.", "overall": "A highly auspicious day for love and intelligence."},
        6: {"health": "Pay attention to your diet and avoid overexertion.", "overall": "Minor obstacles may appear, stay grounded.", "finance": "Avoid taking new loans."},
        7: {"love": "Partnerships thrive. Good for business and marriage.", "overall": "A wonderful transit bringing harmony in relationships.", "career": "Business partnerships show profit."},
        8: {"health": "Unexpected changes possible. Avoid risky investments.", "overall": "A transformative day. Practice patience.", "finance": "Sudden expenses might arise."},
        9: {"travel": "Long distance travel or spiritual journeys are favorable.", "career": "Luck favors your professional endeavors.", "overall": "Divine grace and fortune are with you today."},
        10: {"career": "Increased workload, but leads to long-term success.", "overall": "Focus heavily on your professional responsibilities.", "social": "Public image and reputation grow."},
        11: {"finance": "Tremendous gains, fulfillment of desires, and networking.", "overall": "One of the best transits for overall success and joy.", "social": "Friends bring good news."},
        12: {"finance": "Unplanned expenses or investments in foreign lands.", "overall": "A day for spiritual retreat and letting go.", "travel": "Foreign connections may be beneficial."}
    },
    "Saturn": {
        1: {"health": "Physical fatigue. Maintain a disciplined routine.", "overall": "A time of testing and building endurance. Sade Sati core phase."},
        2: {"finance": "Financial delays. Avoid harsh speech.", "overall": "Sade Sati ending phase. Conserve resources."},
        3: {"career": "Courage and hard work bring great success.", "overall": "An excellent transit. Your efforts yield solid results.", "health": "Vitality is strong."},
        4: {"family": "Domestic responsibilities may feel heavy. Dhaiya phase.", "overall": "Focus on foundational matters and property.", "health": "Mother's health may need care."},
        5: {"love": "Romantic delays or strictness with children.", "education": "Requires deep focus and structured study.", "finance": "Avoid speculative investments."},
        6: {"career": "Triumph over competitors and success in job.", "health": "Chronic issues improve through discipline.", "overall": "Very favorable for overcoming obstacles."},
        7: {"love": "Relationships require maturity and commitment.", "overall": "Partnerships may feel restrictive but are stabilizing.", "travel": "Travel may be delayed or tiresome."},
        8: {"health": "Ashtama Shani. Be cautious with health and avoid risks.", "overall": "A challenging phase requiring immense patience.", "finance": "Avoid lending money."},
        9: {"travel": "Delays in long journeys. Father's health needs care.", "overall": "Dharma and beliefs undergo restructuring."},
        10: {"career": "Intense professional demands. Hard work is mandatory.", "overall": "Career takes center stage. No shortcuts allowed."},
        11: {"finance": "Steady, reliable gains. Wishes are fulfilled slowly.", "overall": "Excellent transit for long-term goal realization.", "career": "Old connections bring profit."},
        12: {"finance": "Expenses on health or foreign travels. Sade Sati begins.", "overall": "Time for isolation and deep spiritual work.", "health": "Sleep may be disturbed."}
    },
    "Mars": {
        1: {"health": "High energy but prone to impatience or minor injuries. Stay calm.", "overall": "You feel driven and assertive today."},
        2: {"finance": "Avoid impulsive spending or harsh speech.", "family": "Maintain peace in family discussions."},
        3: {"career": "High energy and courage. You can conquer anything today.", "overall": "Excellent drive and determination."},
        4: {"family": "Domestic friction is possible. Practice patience.", "health": "Protect your chest and heart area from stress."},
        5: {"education": "Mental restlessness. Focus your energy constructively.", "love": "Passions run high but avoid arguments."},
        6: {"health": "Strong vitality. You defeat your enemies effortlessly.", "career": "You overpower your competitors at work."},
        7: {"love": "Avoid aggression in partnerships.", "career": "Business discussions require diplomacy."},
        8: {"health": "Be cautious of cuts, burns, or accidents.", "finance": "Avoid risky financial decisions today."},
        9: {"travel": "Travel may be hectic. Drive safely.", "education": "Debates on beliefs or philosophy may occur."},
        10: {"career": "Excellent leadership and execution skills at work.", "overall": "You are highly productive and goal-oriented."},
        11: {"finance": "Sudden financial gains and bold networking.", "social": "You take the lead in group activities."},
        12: {"finance": "Sudden expenses may occur.", "health": "Restless sleep or hidden frustrations."}
    },
    "Venus": {
        1: {"overall": "You exude charm and attract positivity today.", "love": "A magnetic and attractive aura surrounds you."},
        2: {"finance": "Good day for accumulating wealth and enjoying good food.", "family": "Sweet speech brings family joy."},
        3: {"travel": "Short trips for pleasure are highlighted.", "social": "Excellent communication with friends."},
        4: {"family": "Home environment is peaceful and luxurious.", "overall": "A great day to relax and enjoy comforts."},
        5: {"love": "A beautiful day for romance and artistic pursuits.", "education": "Creative learning is highly favored."},
        6: {"health": "Minor indulgences may cause health issues.", "finance": "Avoid overspending on luxuries."},
        7: {"love": "Harmony in marriage and favorable business partnerships.", "overall": "Relationships are smooth and joyful."},
        8: {"finance": "Unexpected gains through partners or hidden sources.", "overall": "A deep, intense, yet pleasant emotional day."},
        9: {"travel": "Favorable for pleasant long journeys.", "overall": "Luck and grace are on your side."},
        10: {"career": "Pleasant interactions with colleagues and authority.", "overall": "Professional environment is harmonious."},
        11: {"finance": "Gains through female friends or creative ventures.", "social": "You enjoy socializing and attending events."},
        12: {"overall": "Luxury, comfort, and sensual pleasures are highlighted.", "finance": "Expenses on comforts and luxuries."}
    },
    "Mercury": {
        1: {"overall": "Your mind is sharp and analytical today.", "education": "Excellent day for studying and processing info."},
        2: {"finance": "Excellent communication leads to financial gains.", "family": "Intellectual discussions with family members."},
        3: {"social": "Busy with short trips, emails, and conversations.", "career": "Great day for writing and media work."},
        4: {"family": "Mental focus is on home and domestic matters.", "education": "Good for studying at home."},
        5: {"education": "Sharp intellect helps in exams and learning.", "love": "Playful and intellectual romantic conversations."},
        6: {"career": "Good for detailed analytical work.", "health": "Nervous energy may be high; try to relax."},
        7: {"career": "Excellent day for negotiations and signing contracts.", "love": "Communication with partner is highly logical."},
        8: {"overall": "Deep research and investigative thinking are favored.", "finance": "Good day for analyzing joint finances."},
        9: {"education": "Higher learning and philosophical discussions.", "travel": "Travel for educational or business purposes."},
        10: {"career": "Sharp intellect helps solve complex professional problems.", "overall": "Your ideas are recognized at work."},
        11: {"social": "Great day for networking and socializing with friends.", "finance": "Gains through communication and trade."},
        12: {"overall": "Mind is active but imaginative. Good for meditation.", "health": "Overthinking may cause sleep disturbances."}
    },
    "Sun": {
        1: {"overall": "You feel confident and radiant.", "health": "Vitality is high but watch for ego clashes."},
        2: {"finance": "Ego may clash in family matters. Protect wealth.", "health": "Watch out for eye or throat irritation."},
        3: {"overall": "You feel courageous and ready to take on challenges.", "social": "You take charge in sibling or peer groups."},
        4: {"family": "Ego clashes at home. Try to remain humble.", "career": "Good focus on property and real estate."},
        5: {"education": "Intellect is bright. Good for leadership.", "love": "Romance may require setting ego aside."},
        6: {"career": "Success in competition and recognition at work.", "health": "You easily overcome illnesses."},
        7: {"love": "Avoid dominating your partner.", "career": "Business partnerships may face ego battles."},
        8: {"health": "Protect your vitality. Avoid stressful situations.", "overall": "A day for low profile and inner focus."},
        9: {"travel": "Favorable for spiritual journeys.", "overall": "You feel a strong connection to dharma and ethics."},
        10: {"career": "Authority figures favor you. Great day for leadership.", "overall": "Professional success and recognition are high."},
        11: {"finance": "Status elevation and profitable connections.", "social": "You shine in group settings and networks."},
        12: {"health": "Low energy. Take time to rest.", "overall": "A good day for solitude and spiritual practices."}
    }
}

def generate_daily_horoscope(rashi_name: str) -> Dict[str, Any]:
    """Generates the daily horoscope based on actual current transits from the Moon Sign (Rashi)."""
    
    # Use current datetime (UTC)
    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    # We use a default location for generic transit calculation (e.g., Ujjain, India - classical center)
    kundli = generate_full_kundli("Daily Transit", date_str, time_str, "Ujjain", 23.1765, 75.7885, 5.5)
    
    rashi_idx = RASHI_TO_INDEX.get(rashi_name, 1)
    
    # Extract current planet positions
    transit_planets = []
    planets_dict = {}
    
    for p in kundli.get("planets", []):
        p_name = p.get("planet_name_simple", p["name"].split(" ")[0])
        if p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            
            s_idx = p.get("sign_index", 1)
            # Calculate House from Moon (Rashi)
            house_from_moon = ((s_idx - rashi_idx) % 12) + 1
            
            planet_data = {
                "planet": p_name,
                "sign": p.get("sign", ""),
                "sign_index": s_idx,
                "degree": p.get("degree_dms", ""),
                "decimal_degree": p.get("degree_decimal", 0.0),
                "nakshatra": p.get("nakshatra", ""),
                "pada": p.get("pada", 1),
                "house_from_moon": house_from_moon
            }
            transit_planets.append(planet_data)
            planets_dict[p_name] = planet_data
            
    # Generate Predictions based on transits
    predictions = {
        "overall": "A standard day with mixed results.",
        "career": "Focus on routine tasks. Steady effort is required.",
        "finance": "Maintain a balanced budget.",
        "love": "Patience and understanding will foster harmony.",
        "health": "Maintain regular diet and exercise.",
        "family": "Spend quality time with loved ones.",
        "education": "Consistency in studies will pay off.",
        "travel": "Normal commute. No major disruptions.",
        "social": "A good day to connect with close friends."
    }
    
    # Layer transit rules (outer planets first for deeper impact, then inner planets)
    for planet in ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury"]:
        p_data = planets_dict.get(planet)
        if p_data:
            h = p_data["house_from_moon"]
            if planet in GOCHAR_RULES and h in GOCHAR_RULES[planet]:
                rules = GOCHAR_RULES[planet][h]
                for category, text in rules.items():
                    predictions[category] = text

    # Calculate Lucky Values
    rashi_lord = RASHI_LORDS.get(rashi_idx, "Mars")
    element = RASHI_ELEMENTS.get(rashi_idx, "Fire")
    
    lucky_num = LUCKY_NUMBERS.get(rashi_lord, 1)
    
    # Calculate a dynamic day-based color
    weekday = now.weekday() # 0=Mon, 6=Sun
    weekday_lords = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
    day_lord = weekday_lords[weekday]
    
    # If the day lord is friendly to rashi lord, use day lord's color, else use rashi lord's color
    lucky_color = LUCKY_COLORS.get(rashi_lord, "Red")
    
    lucky_direction = LUCKY_DIRECTIONS.get(element, "East")
    
    # Generate best time based on Hora logic
    # Simplified: Morning Hora of the Rashi Lord
    hora_hours = {"Sun": "06:00 AM - 07:00 AM", "Moon": "07:00 AM - 08:00 AM", 
                  "Mars": "08:00 AM - 09:00 AM", "Mercury": "09:00 AM - 10:00 AM", 
                  "Jupiter": "10:00 AM - 11:00 AM", "Venus": "11:00 AM - 12:00 PM", 
                  "Saturn": "12:00 PM - 01:00 PM"}
    best_time = hora_hours.get(rashi_lord, "10:00 AM - 11:30 AM")

    # Format result matching user requested data structure
    return {
        "basic": {
            "rashi": rashi_name,
            "rashi_name": rashi_name,
            "rashi_sanskrit_name": ZODIAC_SIGNS[rashi_idx - 1]["sanskrit"],
            "rashi_lord": rashi_lord,
            "element": element,
            "modality": ZODIAC_SIGNS[rashi_idx - 1]["quality"]
        },
        "astronomical_values": {
            "date": date_str,
            "sun_sign": planets_dict.get("Sun", {}).get("sign", ""),
            "moon_sign": planets_dict.get("Moon", {}).get("sign", ""),
            "moon_degree": planets_dict.get("Moon", {}).get("degree", ""),
            "moon_nakshatra": planets_dict.get("Moon", {}).get("nakshatra", ""),
            "moon_pada": planets_dict.get("Moon", {}).get("pada", 1),
            "transit_planets": transit_planets
        },
        "predictions": predictions,
        "lucky_values": {
            "lucky_number": lucky_num,
            "lucky_color": lucky_color,
            "lucky_direction": lucky_direction,
            "best_time": best_time
        }
    }
