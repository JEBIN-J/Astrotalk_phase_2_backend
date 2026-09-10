"""Bhrigu Nandi Nadi (BNN) Rules and Interpretations."""

# BNN Karakatwas (Significations)
BNN_KARAKAS = {
    "Jupiter": "Jeeva (Self for Male), Life Path, Wisdom, Expansion, Children",
    "Venus": "Jeeva (Self for Female), Marriage, Wife, Wealth, Luxury, Arts",
    "Saturn": "Karma, Profession, Work, Delay, Discipline, Responsibility",
    "Mars": "Husband, Action, Courage, Property, Siblings",
    "Sun": "Father, Soul, Authority, Government, Leadership",
    "Moon": "Mother, Mind, Emotions, Travel, Nourishment, Public",
    "Mercury": "Intelligence, Education, Business, Communication, Speech",
    "Rahu": "Paternal Grandfather, Illusion, Foreign, Unconventional, Amplification",
    "Ketu": "Maternal Grandfather, Moksha, Obstructions, Spirituality, Detachment"
}

# BNN Trine Groups
BNN_TRINE_GROUPS = {
    "East (1-5-9)": ["Aries", "Leo", "Sagittarius"],
    "South (2-6-10)": ["Taurus", "Virgo", "Capricorn"],
    "West (3-7-11)": ["Gemini", "Libra", "Aquarius"],
    "North (4-8-12)": ["Cancer", "Scorpio", "Pisces"]
}

# BNN Relationship Definitions (Based on Sign Distance)
# 1st (same sign): 100%
# 5th, 9th (trine): 75%
# 7th (opposition): 50%
# 3rd, 11th: 25%
# 2nd, 12th: 15%
def get_bnn_relationship(sign_index_a: int, sign_index_b: int) -> dict:
    if sign_index_a == sign_index_b:
        return {"relationship": "Conjunction (1st)", "strength": 100}
    
    distance = ((sign_index_b - sign_index_a) % 12) + 1
    
    if distance in [5, 9]:
        return {"relationship": f"Trine ({distance}th)", "strength": 75}
    elif distance == 7:
        return {"relationship": "Opposition (7th)", "strength": 50}
    elif distance in [3, 11]:
        return {"relationship": f"Friendly ({distance}th)", "strength": 25}
    elif distance in [2, 12]:
        return {"relationship": f"Adjacent ({distance}th)", "strength": 15}
    
    return {"relationship": "Neutral/Hidden", "strength": 0}

# Event domains and their primary confirming Karakas
BNN_EVENTS = {
    "Career": ["Saturn", "Sun"],
    "Marriage": ["Jupiter", "Venus"],
    "Education": ["Jupiter", "Mercury"],
    "Children": ["Jupiter", "Sun"],
    "Property": ["Saturn", "Mars"],
    "Wealth": ["Saturn", "Venus"],
    "Foreign Travel": ["Rahu", "Moon"],
    "Spirituality": ["Ketu", "Jupiter"],
    "Health": ["Rahu", "Sun"],
    "Relationships": ["Jupiter", "Moon"]
}

def analyze_bnn_combination(planet1: str, planet2: str) -> str:
    """Retrieve BNN meaning for a pair of planets based on their core nature."""
    # Simplified interaction engine for dynamic scaling
    benefics = ["Jupiter", "Venus", "Mercury", "Moon"]
    malefics = ["Saturn", "Mars", "Rahu", "Ketu", "Sun"]
    
    if planet1 in benefics and planet2 in benefics:
        return f"Highly favorable interaction amplifying {planet1}'s {BNN_KARAKAS[planet1].split(',')[0].lower()} and {planet2}'s {BNN_KARAKAS[planet2].split(',')[0].lower()}."
    elif planet1 in malefics and planet2 in malefics:
        return f"Intense and challenging interaction creating friction between {planet1}'s {BNN_KARAKAS[planet1].split(',')[0].lower()} and {planet2}'s {BNN_KARAKAS[planet2].split(',')[0].lower()}."
    else:
        # Mixed
        return f"Dynamic interaction. {planet1}'s {BNN_KARAKAS[planet1].split(',')[0].lower()} is influenced by the structured/intense nature of {planet2}."
