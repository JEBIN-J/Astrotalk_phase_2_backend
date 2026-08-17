"""Jaimini Astrological Rules and Interpretations."""

JAIMINI_KARAKAS = {
    "AK": {"name": "Atmakaraka", "meaning": "Soul, Self, Core Desires"},
    "AmK": {"name": "Amatyakaraka", "meaning": "Career, Profession, Mind, Ministers"},
    "BK": {"name": "Bhratrikaraka", "meaning": "Siblings, Father, Gurus, Guides"},
    "MK": {"name": "Matrikaraka", "meaning": "Mother, Property, Education, Home"},
    "PK": {"name": "Putrakaraka", "meaning": "Children, Intelligence, Creativity"},
    "GK": {"name": "Gnatikaraka", "meaning": "Obstacles, Relatives, Enemies, Diseases"},
    "DK": {"name": "Darakaraka", "meaning": "Spouse, Partnerships, Business"}
}

PLANETARY_KARAKA_MEANINGS = {
    "Sun": {
        "AK": "A soul aiming for leadership, truth, and spiritual authority. Must overcome ego.",
        "AmK": "Career in government, administration, or leadership roles.",
        "DK": "A strong-willed, authoritative spouse."
    },
    "Moon": {
        "AK": "A deeply caring soul seeking emotional connection. Must overcome mood swings.",
        "AmK": "Career involving public dealing, caregiving, or liquid assets.",
        "DK": "A compassionate, emotional, and nurturing spouse."
    },
    "Mars": {
        "AK": "A warrior soul driven by courage and action. Must learn patience.",
        "AmK": "Career in military, engineering, logic, or technical fields.",
        "DK": "A dynamic, energetic, and sometimes argumentative spouse."
    },
    "Mercury": {
        "AK": "A communicative soul driven by learning. Must avoid superficiality.",
        "AmK": "Career in business, writing, commerce, or communication.",
        "DK": "A youthful, communicative, and intelligent spouse."
    },
    "Jupiter": {
        "AK": "A wise soul seeking truth and expansion. Must avoid dogmatism.",
        "AmK": "Career in teaching, law, finance, or religious institutions.",
        "DK": "A wise, optimistic, and highly ethical spouse."
    },
    "Venus": {
        "AK": "A soul driven by love, beauty, and harmony. Must overcome lust and material attachment.",
        "AmK": "Career in arts, luxury, entertainment, or finance.",
        "DK": "A beautiful, diplomatic, and loving spouse."
    },
    "Saturn": {
        "AK": "A soul carrying heavy karma, seeking discipline. Must overcome grief and learn acceptance.",
        "AmK": "Career involving hard work, heavy machinery, agriculture, or traditional structures.",
        "DK": "A mature, serious, and hardworking spouse."
    }
}

def get_karaka_interpretation(planet: str, karaka_code: str) -> str:
    """Retrieve specific Jaimini interpretations for a planet acting as a specific Karaka."""
    planet_data = PLANETARY_KARAKA_MEANINGS.get(planet, {})
    return planet_data.get(karaka_code, f"General {karaka_code} influence through {planet}.")

ARUDHA_MEANINGS = {
    "AL": "Arudha Lagna: Your image in society, how the world perceives you.",
    "UL": "Upapada Lagna: The illusion of marriage, the reality of the spouse, and relationship dynamics."
}
