"""Classical Lal Kitab Rules, Remedies and Interpretations."""

def get_lal_kitab_interpretation(planet: str, house: int) -> dict:
    """
    Returns standard Lal Kitab positive effects, negative effects,
    career/family/finance predictions, and remedies for a given planet and house.
    """
    # Base dictionary for general planet natures in Lal Kitab
    planet_nature = {
        "Sun": {"nature": "Royal, authoritative, soul, government", "friends": ["Moon", "Jupiter", "Mars"]},
        "Moon": {"nature": "Mind, mother, emotions, liquid", "friends": ["Sun", "Mercury"]},
        "Mars": {"nature": "Energy, courage, brothers, land", "friends": ["Sun", "Moon", "Jupiter"]},
        "Mercury": {"nature": "Intellect, business, speech, sister", "friends": ["Sun", "Venus"]},
        "Jupiter": {"nature": "Wisdom, expansion, fate, gurus", "friends": ["Sun", "Moon", "Mars"]},
        "Venus": {"nature": "Luxury, romance, spouse, wealth", "friends": ["Mercury", "Saturn"]},
        "Saturn": {"nature": "Karma, delay, profession, structures", "friends": ["Mercury", "Venus"]},
        "Rahu": {"nature": "Illusion, foreign, sudden events, head", "friends": ["Mercury", "Venus", "Saturn"]},
        "Ketu": {"nature": "Detachment, spirituality, tail, dogs", "friends": ["Venus", "Rahu"]},
    }
    
    # Specific major Lal Kitab rules (simplified for the 108 combinations)
    rules = {
        "Sun": {
            1: {"pos": ["Self-made, royal nature, highly ambitious.", "Blessed with leadership and authority."], "neg": ["Prone to ego clashes and temper.", "Health issues related to heat or stomach."], "rem": ["Marry before 24th year of age.", "Construct a small dark room at the end of your house."], "career": "Excellent for government or authoritative roles.", "family": "Strong presence but may clash with father."},
            2: {"pos": ["Wealthy through self-effort.", "Truthful and straightforward speech."], "neg": ["Disputes over family wealth.", "Harsh speech may alienate relatives."], "rem": ["Do not accept donations or free gifts.", "Donate coconut, mustard oil, and almonds."], "career": "Good for self-owned business.", "family": "Family support is variable."},
            # Generic fallbacks
        },
        "Moon": {
            4: {"pos": ["Excellent wealth and emotional peace.", "Strong intuition and maternal blessings."], "neg": ["Water-borne diseases.", "Over-emotional reactions."], "rem": ["Offer milk to guests but do not drink milk at night.", "Keep a pitcher filled with water/milk at home."], "career": "Great for public dealing, liquid businesses.", "family": "Deep connection with mother."},
            6: {"pos": ["Hardworking and service-oriented.", "Can defeat enemies easily."], "neg": ["Mental anxiety and sleep disturbances.", "Issues related to mother's health."], "rem": ["Do not drink milk at night.", "Serve your father and elderly people."], "career": "Service, medical, or administrative jobs.", "family": "Mother may face chronic health issues."},
        },
        "Mars": {
            3: {"pos": ["Immense courage and valor.", "Protective of siblings."], "neg": ["Aggressive and impulsive nature.", "Risk of physical injuries or cuts."], "rem": ["Keep an ivory item at home.", "Wear a silver ring on the left hand."], "career": "Police, military, or adventurous fields.", "family": "Strong bond with brothers."},
            8: {"pos": ["Strong willpower and occult knowledge.", "Sudden financial gains."], "neg": ["Hidden enemies and sudden accidents.", "Blood-related ailments."], "rem": ["Bury honey in an earthen pot in a deserted place.", "Always wear a silver chain."], "career": "Research, surgery, or detective work.", "family": "Sudden family events can disrupt peace."},
        },
        "Saturn": {
            10: {"pos": ["Ambitious and highly disciplined.", "Steady rise in career."], "neg": ["Overworked and highly stressed.", "Delays in achieving top positions."], "rem": ["Do not consume alcohol or non-vegetarian food.", "Serve blind or disabled people."], "career": "Tremendous success in law, real estate, or administration.", "family": "Work often takes priority over family time."},
        },
        "Jupiter": {
            5: {"pos": ["Highly intelligent and spiritually inclined.", "Blessed with good children."], "neg": ["May become overly preachy or egoistic.", "Stomach or liver issues."], "rem": ["Do not accept donations.", "Plant a peepal tree."], "career": "Teaching, consulting, or religious roles.", "family": "Very supportive family structure."},
        },
        "Rahu": {
            12: {"pos": ["Success in foreign lands.", "Deep imagination."], "neg": ["Unnecessary expenses and hospital visits.", "Sleep disorders."], "rem": ["Keep saunf (fennel) under the pillow.", "Eat meals in the kitchen."], "career": "Foreign trade, MNC jobs, or creative arts.", "family": "Isolation from extended family."},
        },
        "Ketu": {
            2: {"pos": ["Unexpected wealth.", "Spiritual speech."], "neg": ["Mismanagement of finances.", "Harsh or detached speech."], "rem": ["Apply saffron tilak on forehead.", "Serve young girls (Kanyas)."], "career": "Astrology, finance, or spiritual healing.", "family": "Detached approach to family wealth."},
        }
    }
    
    # Generic logic for remaining combinations
    planet_data = rules.get(planet, {})
    house_data = planet_data.get(house, None)
    
    if house_data:
        return house_data
        
    # Generate intelligent fallback based on planet and house
    nature = planet_nature.get(planet, {}).get("nature", "Variable energy")
    
    pos_effects = [f"Brings the energy of {nature.lower()} into the {house}th house affairs.", "Potential for steady growth through persistent effort."]
    neg_effects = [f"Challenges may arise regarding {house}th house matters if afflicted.", "Requires careful handling of associated relationships."]
    remedy = [f"Serve elders and maintain good moral conduct to appease {planet}.", "Donate items related to the color of this planet."]
    
    if house in [1, 5, 9]:
        pos_effects.append("Favorable trine placement brings natural luck and intelligence.")
        remedy.append("Maintain religious or spiritual practices.")
    elif house in [6, 8, 12]:
        neg_effects.append("Placement in a Dusthana (difficult house) indicates struggles or delays.")
        remedy.append("Perform selfless service and avoid illegal activities.")
    elif house in [4, 7, 10]:
        pos_effects.append("Kendra placement provides strong foundational pillars for life.")
        career = "Strongly influences your primary path and public image."
    
    return {
        "pos": pos_effects,
        "neg": neg_effects,
        "rem": remedy,
        "career": f"The {house}th house placement of {planet} strongly colors your professional inclinations.",
        "family": f"Relationships related to the {house}th house require patience and understanding.",
        "finance": f"Financial gains are tied to the disciplined expression of {planet}'s traits."
    }
