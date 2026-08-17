"""Bhrigu Nandi Nadi (BNN) Rules and Interpretations."""

# BNN Karakas (Significators)
BNN_KARAKAS = {
    "Jupiter": "Self (Male), Life Path, Guru, Wisdom",
    "Venus": "Self (Female), Wife, Wealth, Luxury",
    "Saturn": "Career, Karma, Profession, Elder Brother",
    "Mars": "Husband, Action, Courage, Younger Brother",
    "Sun": "Father, Soul, Authority, Government",
    "Moon": "Mother, Mind, Travel, Change, Art",
    "Mercury": "Intelligence, Education, Business, Speech",
    "Rahu": "Paternal Grandfather, Illusion, Foreign, Massive Expansion",
    "Ketu": "Maternal Grandfather, Moksha, Obstructions, Spirituality"
}

# BNN Event Domains mapped to their primary Karakas
BNN_EVENT_MAPPINGS = {
    "Career & Profession": "Saturn",
    "Finance & Wealth": "Venus",
    "Life Path (Male)": "Jupiter",
    "Relationships (Male)": "Venus",
    "Life Path (Female)": "Venus",
    "Relationships (Female)": "Mars",
    "Education & Intellect": "Mercury",
}

# 2-Planet Combination Interpretations
BNN_COMBINATIONS = {
    ("Sun", "Moon"): "Highly intuitive but may face fluctuating authority or emotional unrest.",
    ("Sun", "Mars"): "Strong willpower, authoritative leadership, and technical or administrative prowess.",
    ("Sun", "Mercury"): "Buddhaditya - Sharp intellect, articulate speech, and strong administrative skills.",
    ("Sun", "Jupiter"): "Jiva-Atma - Divine grace, righteous path, respected in society.",
    ("Sun", "Venus"): "Refined tastes, artistic capabilities, but potential ego clashes in relationships.",
    ("Sun", "Saturn"): "Karma-Atma - Delay in career success, friction with authority or father.",
    ("Sun", "Rahu"): "Desire for massive fame, unconventional leadership, eclipse of soul.",
    ("Sun", "Ketu"): "Spiritual inclination, detachment from worldly power, profound insights.",

    ("Moon", "Mars"): "Chandra-Mangala - Wealth accumulation, emotional drive, sometimes impulsive.",
    ("Moon", "Mercury"): "Imaginative intellect, good for writing or trading, restless mind.",
    ("Moon", "Jupiter"): "Gaja Kesari - Wisdom, optimism, popularity, and emotional stability.",
    ("Moon", "Venus"): "Love for luxury, artistic talents, highly romantic nature.",
    ("Moon", "Saturn"): "Punarphoo - Emotional melancholy, delays in peace, profound serious thinking.",
    ("Moon", "Rahu"): "Intense imagination, obsessive thoughts, attraction to foreign or unconventional things.",
    ("Moon", "Ketu"): "High intuition, mystical mind, frequent emotional detachment.",

    ("Mars", "Mercury"): "Sharp and cutting speech, technical intellect, argumentative.",
    ("Mars", "Jupiter"): "Guru-Mangala - Righteous action, immense energy channeled wisely.",
    ("Mars", "Venus"): "High passion, romantic intensity, dynamic drive for luxury.",
    ("Mars", "Saturn"): "Yama - Frustration, structured action, great potential for technical or engineering fields.",
    ("Mars", "Rahu"): "Explosive energy, reckless courage, unconventional methods.",
    ("Mars", "Ketu"): "Hidden anger, precision, good for surgery or deep technical research.",

    ("Mercury", "Jupiter"): "Profound wisdom, excellent communication, academic success.",
    ("Mercury", "Venus"): "Diplomatic speech, business acumen, artistic expression.",
    ("Mercury", "Saturn"): "Deep analytical mind, structured thinking, slow but steady learning.",
    ("Mercury", "Rahu"): "Shrewd intellect, unconventional ideas, tech-savvy.",
    ("Mercury", "Ketu"): "Intuitive intellect, concise speech, investigative skills.",

    ("Jupiter", "Venus"): "Abundance, great wealth, conflict between spirituality and materialism.",
    ("Jupiter", "Saturn"): "Dharma-Karma - Highly righteous career, responsible, respected professional.",
    ("Jupiter", "Rahu"): "Guru Chandal - Unconventional beliefs, massive expansion, breaking traditions.",
    ("Jupiter", "Ketu"): "Paramahamsa - Supreme spiritual wisdom, detachment, intuition.",

    ("Venus", "Saturn"): "Wealth through structured effort, delay in marriage or serious relationship.",
    ("Venus", "Rahu"): "Unconventional relationships, extreme desire for luxury, media or glamor success.",
    ("Venus", "Ketu"): "Detachment from materialism, spiritual love, potential relationship blockages.",

    ("Saturn", "Rahu"): "Shrapit - Massive ambition, breaking boundaries in career, intense struggles.",
    ("Saturn", "Ketu"): "Career in spiritual, occult, or healing fields; dissatisfaction with routine work."
}

def get_combination_meaning(planet1: str, planet2: str) -> str:
    """Retrieve BNN meaning for a pair of planets."""
    pair = (planet1, planet2)
    reverse_pair = (planet2, planet1)
    
    if pair in BNN_COMBINATIONS:
        return BNN_COMBINATIONS[pair]
    if reverse_pair in BNN_COMBINATIONS:
        return BNN_COMBINATIONS[reverse_pair]
        
    return f"Dynamic interaction between {planet1}'s ({BNN_KARAKAS.get(planet1, '')}) and {planet2}'s ({BNN_KARAKAS.get(planet2, '')}) energies."
