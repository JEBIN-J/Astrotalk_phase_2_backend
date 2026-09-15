import json

def generate_tarot_deck():
    cards = []
    
    # Major Arcana definitions
    majors = [
        ("The Fool", "0", "Uranus", "Air", "0"),
        ("The Magician", "1", "Mercury", "Air", "1"),
        ("The High Priestess", "2", "Moon", "Water", "2"),
        ("The Empress", "3", "Venus", "Earth", "3"),
        ("The Emperor", "4", "Aries", "Fire", "4"),
        ("The Hierophant", "5", "Taurus", "Earth", "5"),
        ("The Lovers", "6", "Gemini", "Air", "6"),
        ("The Chariot", "7", "Cancer", "Water", "7"),
        ("Strength", "8", "Leo", "Fire", "8"),
        ("The Hermit", "9", "Virgo", "Earth", "9"),
        ("Wheel of Fortune", "10", "Jupiter", "Fire", "1"),
        ("Justice", "11", "Libra", "Air", "2"),
        ("The Hanged Man", "12", "Neptune", "Water", "3"),
        ("Death", "13", "Scorpio", "Water", "4"),
        ("Temperance", "14", "Sagittarius", "Fire", "5"),
        ("The Devil", "15", "Capricorn", "Earth", "6"),
        ("The Tower", "16", "Mars", "Fire", "7"),
        ("The Star", "17", "Aquarius", "Air", "8"),
        ("The Moon", "18", "Pisces", "Water", "9"),
        ("The Sun", "19", "Sun", "Fire", "1"),
        ("Judgement", "20", "Pluto", "Fire", "2"),
        ("The World", "21", "Saturn", "Earth", "3")
    ]
    
    for name, rank, astro, elem, num in majors:
        cards.append({
            "id": f"major_{rank}",
            "name": name,
            "arcana": "Major",
            "suit": None,
            "rank": rank,
            "keywords_upright": ["Beginnings", "Freedom", "Innocence", "Originality", "Adventure", "Idealism", "Spontaneity"] if rank == "0" else ["Power", "Skill", "Concentration", "Action", "Resourcefulness"],
            "keywords_reversed": ["Recklessness", "Carelessness", "Distraction", "Apathy", "Irrationality", "Folly"] if rank == "0" else ["Manipulation", "Poor planning", "Untapped talents", "Illusion"],
            "meaning_upright": f"The {name} upright brings a message of positive energy related to {elem} and {astro}.",
            "meaning_reversed": f"The {name} reversed warns of blockages in {elem} energy or difficulties associated with {astro}.",
            "love_upright": f"In love, {name} signifies strong {astro} bonds.",
            "love_reversed": f"Reversed, {name} in love means miscommunication or hesitation.",
            "career_upright": f"Career prospects look good, tapping into {elem} resources.",
            "career_reversed": f"Career stagnation or lack of {elem} groundedness.",
            "finance_upright": "Positive financial flow and stability.",
            "finance_reversed": "Financial delays or unexpected expenses.",
            "spiritual_upright": "A time of great spiritual awakening.",
            "spiritual_reversed": "Feeling disconnected from your spiritual path.",
            "astrological_correspondence": astro,
            "element": elem,
            "numerology": num,
            "yes_no": "YES" if int(rank) % 2 == 0 else "NO",
            "description": f"The {name} is a powerful Major Arcana card representing fundamental life lessons."
        })

    # Minor Arcana
    suits = {
        "Wands": {"element": "Fire", "astro_base": "Mars", "nature": "Action and Passion"},
        "Cups": {"element": "Water", "astro_base": "Moon", "nature": "Emotions and Relationships"},
        "Swords": {"element": "Air", "astro_base": "Mercury", "nature": "Thoughts and Conflicts"},
        "Pentacles": {"element": "Earth", "astro_base": "Venus", "nature": "Material and Finances"}
    }
    
    ranks = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Page", "Knight", "Queen", "King"]
    
    for suit, props in suits.items():
        for r_idx, rank in enumerate(ranks):
            card_id = f"{suit.lower()}_{rank.lower()}"
            name = f"{rank} of {suit}"
            num = str((r_idx % 9) + 1)
            
            # Simple algorithmic meaning generation that yields well-structured distinct dictionary
            cards.append({
                "id": card_id,
                "name": name,
                "arcana": "Minor",
                "suit": suit,
                "rank": rank,
                "keywords_upright": [props["nature"], f"{rank} level energy", "Growth", "Movement"],
                "keywords_reversed": ["Blocked " + props["nature"], "Delay", "Frustration"],
                "meaning_upright": f"The {name} represents positive {props['element']} energy manifesting as {props['nature']}.",
                "meaning_reversed": f"The {name} reversed suggests internal struggles regarding {props['nature']}.",
                "love_upright": f"A time of {props['nature']} in your relationships.",
                "love_reversed": "Misunderstandings or lack of alignment in love.",
                "career_upright": f"Advancement through {props['nature']}.",
                "career_reversed": "Workplace tension or unfulfilled goals.",
                "finance_upright": "Steady progress or new opportunities.",
                "finance_reversed": "Be cautious with spending and investments.",
                "spiritual_upright": f"Finding meaning through {props['element']}.",
                "spiritual_reversed": "Need for grounding and realignment.",
                "astrological_correspondence": props["astro_base"],
                "element": props["element"],
                "numerology": num,
                "yes_no": "YES" if (r_idx+1) % 2 == 1 or rank in ["Queen", "King"] else "NO",
                "description": f"The {name} is a Minor Arcana card of the {suit} suit."
            })

    # Wrap in Python module format
    py_code = 'TAROT_DECK = ' + json.dumps(cards, indent=4) + '\n\n'
    py_code += 'def get_all_cards():\n    return TAROT_DECK\n\n'
    py_code += 'def get_card_by_id(card_id):\n    for c in TAROT_DECK:\n        if c["id"] == card_id:\n            return c\n    return None\n'

    with open("/Users/apple/Desktop/Astrotalk_phase_2_with_flutter/Astrotalk_phase_2_backend/app/services/tarot/tarot_data.py", "w") as f:
        f.write(py_code)

if __name__ == "__main__":
    generate_tarot_deck()
