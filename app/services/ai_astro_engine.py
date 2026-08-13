"""AI-driven Astrological Intelligence and Consultation Engine."""
from typing import Dict, Any, List
from app.services.vedic_engine import generate_full_kundli



def generate_ai_astrology_insights(
    question: str,
    birth_details: Dict[str, Any] = None,
    category: str = "general"
) -> Dict[str, Any]:
    """Generate comprehensive Vedic AI prediction and consultation response based on precise cosmic data."""
    import datetime
    
    # Extract zodiac sign from question if present (as a fallback or thematic hint)
    signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    extracted_sign = "Aries"
    q_lower = question.lower()
    for s in signs:
        if s in q_lower:
            extracted_sign = s.capitalize()
            break

    # If no birth details, create a Prashna/Transit chart for the current time
    if birth_details:
        kundli = generate_full_kundli(
            birth_details.get("name", "User"),
            birth_details.get("date_of_birth", "1995-08-15"),
            birth_details.get("time_of_birth", "06:30"),
            birth_details.get("place_of_birth", "New Delhi, India"),
            birth_details.get("latitude", 28.6139),
            birth_details.get("longitude", 77.2090),
            birth_details.get("timezone", 5.5)
        )
    else:
        now = datetime.datetime.now()
        kundli = generate_full_kundli(
            "Current Transit",
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            "New Delhi, India",
            28.6139,
            77.2090,
            5.5
        )

    # Extract dynamic planetary and astrological factors from the Kundli
    if birth_details:
        moon_rashi = kundli.get("moon_sign_rashi", extracted_sign)
        lagna = kundli.get("ascendant_sign", extracted_sign)
        nakshatra = kundli.get("nakshatra", "Rohini")
        
        current_dasha = kundli.get("current_running_dasha", {})
        active_dasha = current_dasha.get("active_mahadasha", "Jupiter")
        active_antardasha = current_dasha.get("active_antardasha", "Saturn")
    
        houses = kundli.get("houses", [])
    else:
        lagna = extracted_sign
        moon_rashi = kundli.get("moon_sign_rashi", extracted_sign) # Transit Moon
        nakshatra = kundli.get("nakshatra", "Rohini")
        
        sign_lords = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
            "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
            "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
        }
        active_dasha = sign_lords.get(extracted_sign, "Jupiter")
        active_antardasha = kundli.get("moon_sign_lord", "Moon")
        
        # Calculate houses relative to extracted_sign
        sign_names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        try:
            lagna_idx = sign_names.index(extracted_sign) + 1
        except ValueError:
            lagna_idx = 1
            
        houses = []
        planets_list = kundli.get("planets", [])
        for h in range(1, 13):
            h_sign_idx = ((lagna_idx + h - 2) % 12) + 1
            present_planets = [p["name"].split(" ")[0] for p in planets_list if p.get("sign_index") == h_sign_idx and "Ascendant" not in p["name"]]
            houses.append({
                "house_number": h,
                "planets_present": present_planets
            })
            
    def get_house_planets(h_num):
        for h in houses:
            if h["house_number"] == h_num:
                return h.get("planets_present", [])
        return []

    q_lower = question.lower()
    
    if any(w in q_lower for w in ["career", "job", "business", "work", "promotion", "finance", "money"]):
        category = "career_finance"
        tenth_planets = get_house_planets(10)
        eleventh_planets = get_house_planets(11)
        
        planets_str = ""
        if tenth_planets:
            planets_str += f"with {', '.join(tenth_planets)} in the 10th House (Karma Bhava) "
        if eleventh_planets:
            if tenth_planets:
                planets_str += "and "
            else:
                planets_str += "with "
            planets_str += f"{', '.join(eleventh_planets)} in the 11th House (Labha Bhava) "
            
        if not planets_str:
            planets_str = "the 10th House (Karma Bhava) and 11th House (Labha Bhava) energies "
            
        analysis = (
            f"Based on your {lagna} Ascendant with Moon in {moon_rashi} ({nakshatra} Nakshatra) "
            f"and currently navigating {active_dasha} Mahadasha / {active_antardasha} Antardasha, "
            f"{planets_str}indicate strong upward momentum. Strategic initiatives taken "
            f"now will yield high compounding financial dividends."
        )
        astrological_factors = [
            f"Current influence of {active_dasha} on career and professional prestige.",
            f"Moon in {moon_rashi} grants sharp negotiation intellect and business acumen.",
            f"Lagna in {lagna} establishes durable revenue channels and authority."
        ]
        if tenth_planets:
            astrological_factors.append(f"Presence of {', '.join(tenth_planets)} in the 10th House amplifies career growth.")
            
        predictions = [
            "Next 6-9 months bring lucrative career expansion, leadership recognition, or salary hike.",
            "New ventures or investments initiated during Shukla Paksha will show accelerated returns.",
            "A collaborative alliance or mentorship will unlock an unexpected financial gateway."
        ]
        remedies = [
            "Chant 'Om Namo Bhagavate Vasudevaya' 108 times on Thursdays.",
            "Offer water to the rising Sun (Surya Arghya) daily in a copper vessel.",
            "Wear a natural Yellow Sapphire (Pukhraj) or Yellow Topaz on the index finger."
        ]
        lucky_gem = "Yellow Sapphire (Pukhraj)"
        lucky_col = "#F59E0B (Golden Yellow)"
        lucky_day = "Thursday"
        auspicious_time = "11:30 AM - 01:00 PM (Abhijit / Guru Hora)"
        
    elif any(w in q_lower for w in ["love", "marriage", "partner", "relationship", "spouse"]):
        category = "love_marriage"
        seventh_planets = get_house_planets(7)
        
        planets_str = f"with {', '.join(seventh_planets)} in the 7th House" if seventh_planets else "with the 7th House (Kalatra Bhava) energy"
        
        analysis = (
            f"Your 7th House (Kalatra Bhava) {planets_str}, paired with Moon in {moon_rashi}, "
            f"creates high romantic harmony and emotional loyalty. Under {active_dasha} Mahadasha, "
            f"interpersonal trust will deepen significantly."
        )
        astrological_factors = [
            f"Moon in {moon_rashi} creates strong magnetic charm and relationship longevity.",
            f"{active_dasha}'s influence blesses matrimonial alliances with peace.",
            "Nadi and Gana alignments indicate profound soul-level compatibility."
        ]
        if seventh_planets:
            astrological_factors.append(f"Planets {', '.join(seventh_planets)} in the 7th House dynamically shape your relationship trajectory.")
            
        predictions = [
            "A decisive milestone in romance or wedding discussions is indicated in the coming quarters.",
            "Open, heartfelt communication will resolve past emotional hesitations smoothly.",
            "Mutual financial or travel endeavors will bring tremendous shared joy."
        ]
        remedies = [
            "Perform Shiva-Parvati puja on Mondays with white flowers.",
            "Wear an authentic White Opal or Diamond in silver on the ring finger on Fridays.",
            "Chant 'Om Shukraya Namaha' 108 times on Friday mornings."
        ]
        lucky_gem = "White Opal / Diamond"
        lucky_col = "#EC4899 (Rose Pink / Diamond White)"
        lucky_day = "Friday"
        auspicious_time = "06:00 PM - 07:30 PM (Shukra Hora)"
        
    else:
        # Generate predictions dynamically based on exact Kundli calculation values
        
        # Astrological mapping for dynamic properties
        planet_remedies = {
            "Sun": ["Offer water to the rising Sun (Surya Arghya) daily.", "Chant the Gayatri Mantra 11 times every morning."],
            "Moon": ["Offer milk on Shivling on Mondays.", "Respect your mother and seek her blessings."],
            "Mars": ["Chant Hanuman Chalisa on Tuesdays.", "Feed jaggery and gram to monkeys."],
            "Mercury": ["Feed green grass to cows on Wednesdays.", "Chant 'Om Budhaya Namaha' 108 times."],
            "Jupiter": ["Chant 'Om Brihaspataye Namaha' on Thursdays.", "Wear yellow clothes on Thursdays."],
            "Venus": ["Light a ghee lamp in your home sanctuary.", "Wear white or pink on Fridays."],
            "Saturn": ["Feed stray dogs or crows on Saturdays.", "Chant 'Om Sham Shanaishcharaye Namaha'."],
            "Rahu": ["Feed stray dogs.", "Donate black sesame seeds."],
            "Ketu": ["Feed stray dogs.", "Donate warm clothes to the needy."]
        }
        
        planet_gems = {
            "Sun": "Ruby (Manik)", "Moon": "Natural Pearl (Moti)", "Mars": "Red Coral (Moonga)",
            "Mercury": "Emerald (Panna)", "Jupiter": "Yellow Sapphire (Pukhraj)", 
            "Venus": "Diamond / White Opal", "Saturn": "Blue Sapphire (Neelam)",
            "Rahu": "Hessonite (Gomed)", "Ketu": "Cat's Eye (Lehsuniya)"
        }
        
        planet_colors = {
            "Sun": "#F59E0B (Orange/Red)", "Moon": "#F9FAFB (Pearl White)", "Mars": "#EF4444 (Ruby Red)",
            "Mercury": "#10B981 (Emerald Green)", "Jupiter": "#FBBF24 (Golden Yellow)", 
            "Venus": "#F472B6 (Soft Pink)", "Saturn": "#4338CA (Deep Blue)",
            "Rahu": "#64748B (Dark Grey)", "Ketu": "#94A3B8 (Smoky Grey)"
        }
        
        planet_days = {
            "Sun": "Sunday", "Moon": "Monday", "Mars": "Tuesday",
            "Mercury": "Wednesday", "Jupiter": "Thursday", 
            "Venus": "Friday", "Saturn": "Saturday",
            "Rahu": "Saturday", "Ketu": "Tuesday"
        }
        
        # Calculate dynamic outputs based on active Mahadasha planet
        active_planet_remedies = planet_remedies.get(active_dasha, planet_remedies["Jupiter"])
        lucky_gem = planet_gems.get(active_dasha, "Yellow Sapphire")
        lucky_col = planet_colors.get(active_dasha, "#FBBF24 (Golden Yellow)")
        lucky_day = planet_days.get(active_dasha, "Thursday")
        auspicious_time = "Auspicious Hora of the Day"
        
        # Analyze Lagna
        lagna_planets = get_house_planets(1)
        if lagna_planets:
            planets_in_lagna_str = f"Planets {', '.join(lagna_planets)} in your Lagna (1st House) amplify your personal charisma and energy."
        else:
            planets_in_lagna_str = f"Your {lagna} Ascendant establishes a strong foundational physical and mental vitality."
            
        analysis = (
            f"Analyzing the current cosmic alignment for your {lagna} Ascendant, the prominent energy "
            f"stems from the {active_dasha} Mahadasha and {active_antardasha} Antardasha. With your Moon situated "
            f"in {moon_rashi} ({nakshatra} Nakshatra), your emotional intuition is deeply intertwined with these transits. "
            f"{planets_in_lagna_str}"
        )
        
        astrological_factors = [
            f"The active {active_dasha} Mahadasha governs the major themes and opportunities of your current cycle.",
            f"Moon's presence in {moon_rashi} influences your daily emotional responses and internal focus.",
            f"The Lagna in {lagna} dictates your outward approach and resilience."
        ]
        
        predictions = [
            f"Under the influence of {active_dasha}, expect pivotal developments in the areas governed by this planet in your chart.",
            f"Because your Moon is in {moon_rashi}, focusing on emotional equilibrium will help you navigate changes smoothly.",
            f"Short-term endeavors should align with the {active_antardasha} Antardasha energy for maximum impact."
        ]
        
        remedies = active_planet_remedies + ["Practice daily meditation to balance cosmic energies."]

    return {
        "question": question,
        "category": category,
        "analysis": analysis,
        "astrological_factors": astrological_factors,
        "predictions": predictions,
        "remedies": remedies,
        "lucky_gemstone": lucky_gem,
        "lucky_color": lucky_col,
        "lucky_day": lucky_day,
        "auspicious_time": auspicious_time
    }
