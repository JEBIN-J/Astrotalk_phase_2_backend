"""AI-driven Astrological Intelligence and Consultation Engine."""
from typing import Dict, Any, List
from app.services.vedic_engine import generate_full_kundli


def generate_ai_astrology_insights(
    question: str,
    birth_details: Dict[str, Any] = None,
    category: str = "general"
) -> Dict[str, Any]:
    """Generate comprehensive Vedic AI prediction and consultation response."""
    # If birth details provided, calculate actual placements
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
        moon_rashi = kundli["moon_sign_rashi"]
        lagna = kundli["ascendant_lagna"].split(" ")[0]
        nakshatra = kundli["nakshatra"]
        active_dasha = kundli["current_running_dasha"]["active_mahadasha"]
    else:
        moon_rashi = "Vrishabha (Taurus)"
        lagna = "Mesha (Aries)"
        nakshatra = "Rohini"
        active_dasha = "Jupiter"

    q_lower = question.lower()
    
    if any(w in q_lower for w in ["career", "job", "business", "work", "promotion", "finance", "money"]):
        category = "career_finance"
        analysis = (
            f"Based on your {lagna} Ascendant with Moon in {moon_rashi} ({nakshatra} Nakshatra) "
            f"and currently navigating {active_dasha} Mahadasha, the 10th House (Karma Bhava) and "
            f"11th House (Labha Bhava) indicate strong upward momentum. Strategic initiatives taken "
            f"now will yield high compounding financial dividends."
        )
        astrological_factors = [
            f"Benefic aspect of {active_dasha} on the 10th house of career and professional prestige.",
            f"Moon in {moon_rashi} grants sharp negotiation intellect and business acumen.",
            "Saturn transiting your 11th house establishes durable revenue channels and authority."
        ]
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
        analysis = (
            f"Your 7th House (Kalatra Bhava) governed by Venus, paired with Moon in {moon_rashi}, "
            f"creates high romantic harmony and emotional loyalty. Under {active_dasha} Mahadasha, "
            f"interpersonal trust will deepen significantly."
        )
        astrological_factors = [
            "Venus placed favorably creates strong magnetic charm and relationship longevity.",
            "Jupiter's aspect on the 7th house blesses matrimonial alliances with peace.",
            "Nadi and Gana alignments indicate profound soul-level compatibility."
        ]
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
        analysis = (
            f"Analyzing your cosmic birth chart ({lagna} Lagna, Moon in {moon_rashi}), you are "
            f"experiencing a high-vitality transformational phase under {active_dasha} Mahadasha. "
            f"Your intuitive wisdom and perseverance will help you overcome transient hurdles with grace."
        )
        astrological_factors = [
            f"Moon in exalted {moon_rashi} anchors mental poise and emotional equilibrium.",
            f"The running {active_dasha} period catalyzes spiritual clarity and material stability.",
            "Benefic planetary transits over the Kendra houses ensure consistent protection."
        ]
        predictions = [
            "Clarity on pivotal life choices will crystallize within the next 4 to 8 weeks.",
            "Travel, personal learning, and spiritual practices will bring high satisfaction.",
            "Health and physical energy will remain well-fortified with balanced routines."
        ]
        remedies = [
            "Chant the Maha Mrityunjaya Mantra 11 times every morning.",
            "Feed birds or contribute to charitable food distribution on Saturdays.",
            "Maintain a copper pyramid or crystal yantra in your work / prayer sanctuary."
        ]
        lucky_gem = "Natural Pearl / Yellow Sapphire"
        lucky_col = "#6366F1 (Royal Celestial Blue)"
        lucky_day = "Thursday & Monday"
        auspicious_time = "08:00 AM - 10:00 AM"

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
