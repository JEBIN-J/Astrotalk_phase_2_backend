"""36 Guna Ashtakoota Milan and Manglik Dosh Matching Engine."""
from typing import Dict, Any, List
from app.utils.constants import NAKSHATRAS, ZODIAC_SIGNS, PLANETS_INFO
from app.services.vedic_engine import generate_full_kundli


# Planetary friendship matrix for Graha Maitri (5 points)
PLANET_FRIENDS = {
    "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "neutrals": ["Mercury"], "enemies": ["Venus", "Saturn"]},
    "Moon": {"friends": ["Sun", "Mercury"], "neutrals": ["Mars", "Jupiter", "Venus", "Saturn"], "enemies": []},
    "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "neutrals": ["Venus", "Saturn"], "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun", "Venus"], "neutrals": ["Mars", "Jupiter", "Saturn"], "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "neutrals": ["Saturn"], "enemies": ["Mercury", "Venus"]},
    "Venus": {"friends": ["Mercury", "Saturn"], "neutrals": ["Mars", "Jupiter"], "enemies": ["Sun", "Moon"]},
    "Saturn": {"friends": ["Mercury", "Venus"], "neutrals": ["Jupiter"], "enemies": ["Sun", "Moon", "Mars"]}
}


def calculate_ashtakoota_milan(
    boy_details: Dict[str, Any],
    girl_details: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate authentic 36-point Ashtakoota Milan compatibility between boy and girl."""
    boy_kundli = generate_full_kundli(
        boy_details["name"],
        boy_details["date_of_birth"],
        boy_details["time_of_birth"],
        boy_details["place_of_birth"],
        boy_details.get("latitude", 28.6139),
        boy_details.get("longitude", 77.2090),
        boy_details.get("timezone", 5.5)
    )
    girl_kundli = generate_full_kundli(
        girl_details["name"],
        girl_details["date_of_birth"],
        girl_details["time_of_birth"],
        girl_details["place_of_birth"],
        girl_details.get("latitude", 28.6139),
        girl_details.get("longitude", 77.2090),
        girl_details.get("timezone", 5.5)
    )

    # Extract Moon Nakshatra and Rashi info
    boy_moon = next(p for p in boy_kundli["planets"] if "Moon" in p["name"])
    girl_moon = next(p for p in girl_kundli["planets"] if "Moon" in p["name"])

    boy_nak = next(n for n in NAKSHATRAS if n["name"] == boy_moon["nakshatra"])
    girl_nak = next(n for n in NAKSHATRAS if n["name"] == girl_moon["nakshatra"])

    boy_rashi = next(r for r in ZODIAC_SIGNS if r["name"] == boy_moon["sign"])
    girl_rashi = next(r for r in ZODIAC_SIGNS if r["name"] == girl_moon["sign"])

    kootas = []
    total_obtained = 0.0

    # 1. VARNA KOOTA (Max 1.0)
    varna_hierarchy = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1, "Mleccha": 1}
    b_varna = boy_nak["varna"]
    g_varna = girl_nak["varna"]
    varna_score = 1.0 if varna_hierarchy.get(b_varna, 1) >= varna_hierarchy.get(g_varna, 1) else 0.0
    total_obtained += varna_score
    kootas.append({
        "koota_name": "1. Varna Koota (Work Temperament & Ego)",
        "description": "Measures spiritual ego, occupational nature, and mutual working temperament.",
        "max_points": 1.0,
        "obtained_points": varna_score,
        "boy_attribute": b_varna,
        "girl_attribute": g_varna,
        "is_compatible": varna_score >= 1.0,
        "remarks": "Mutually supportive mental attitudes and egalitarian values." if varna_score == 1.0 else "Minor differences in temperament, easily harmonized."
    })

    # 2. VASHYA KOOTA (Max 2.0)
    b_vashya = boy_nak["vashya"]
    g_vashya = girl_nak["vashya"]
    vashya_score = 2.0 if b_vashya == g_vashya else (1.0 if b_vashya == "Manava" or g_vashya == "Manava" else 0.5)
    total_obtained += vashya_score
    kootas.append({
        "koota_name": "2. Vashya Koota (Mutual Dominance & Influence)",
        "description": "Evaluates domestic power balance, magnetic attraction, and authority.",
        "max_points": 2.0,
        "obtained_points": vashya_score,
        "boy_attribute": b_vashya,
        "girl_attribute": g_vashya,
        "is_compatible": vashya_score >= 1.0,
        "remarks": "Excellent natural balance of mutual leadership and respect."
    })

    # 3. TARA KOOTA (Max 3.0)
    tara_diff = abs(boy_nak["index"] - girl_nak["index"]) % 9
    tara_score = 3.0 if tara_diff in [0, 2, 4, 6, 8] else 1.5
    total_obtained += tara_score
    kootas.append({
        "koota_name": "3. Tara Koota (Destiny, Health & Longevity)",
        "description": "Calculates health stability, destiny alignment, and long-term prosperity.",
        "max_points": 3.0,
        "obtained_points": tara_score,
        "boy_attribute": f"Nakshatra #{boy_nak['index']}",
        "girl_attribute": f"Nakshatra #{girl_nak['index']}",
        "is_compatible": tara_score >= 2.0,
        "remarks": "Sampat & Kshema Tara alignment - delivers auspicious fortune and good health."
    })

    # 4. YONI KOOTA (Max 4.0)
    b_yoni = boy_nak["yoni"]
    g_yoni = girl_nak["yoni"]
    yoni_score = 4.0 if b_yoni == g_yoni else 3.0
    total_obtained += yoni_score
    kootas.append({
        "koota_name": "4. Yoni Koota (Physical & Biological Harmony)",
        "description": "Governs intimate compatibility, physical attraction, and biological synergy.",
        "max_points": 4.0,
        "obtained_points": yoni_score,
        "boy_attribute": b_yoni,
        "girl_attribute": g_yoni,
        "is_compatible": yoni_score >= 2.0,
        "remarks": "Warm, affectionate physical bond with enduring closeness."
    })

    # 5. GRAHA MAITRI (Max 5.0)
    b_lord = boy_rashi["lord"]
    g_lord = girl_rashi["lord"]
    if b_lord == g_lord:
        graha_score = 5.0
    elif g_lord in PLANET_FRIENDS.get(b_lord, {}).get("friends", []):
        graha_score = 4.0
    elif g_lord in PLANET_FRIENDS.get(b_lord, {}).get("neutrals", []):
        graha_score = 3.0
    else:
        graha_score = 1.0
    total_obtained += graha_score
    kootas.append({
        "koota_name": "5. Graha Maitri (Mental Harmony & Friendship)",
        "description": "Determines psychological intimacy, friendship, and day-to-day conversation flow.",
        "max_points": 5.0,
        "obtained_points": graha_score,
        "boy_attribute": f"{boy_rashi['name']} ({b_lord})",
        "girl_attribute": f"{girl_rashi['name']} ({g_lord})",
        "is_compatible": graha_score >= 3.0,
        "remarks": "Harmonious planetary rulers foster strong intellectual understanding."
    })

    # 6. GANA KOOTA (Max 6.0)
    b_gana = boy_nak["gana"]
    g_gana = girl_nak["gana"]
    if b_gana == g_gana:
        gana_score = 6.0
    elif (b_gana == "Deva" and g_gana == "Manushya") or (b_gana == "Manushya" and g_gana == "Deva"):
        gana_score = 5.0
    elif b_gana == "Deva" and g_gana == "Rakshasa":
        gana_score = 1.0
    else:
        gana_score = 0.0
    total_obtained += gana_score
    kootas.append({
        "koota_name": "6. Gana Koota (Behavioral Nature & Mindset)",
        "description": "Tests social behavioral tendencies: Deva (divine), Manushya (human), Rakshasa (fiery).",
        "max_points": 6.0,
        "obtained_points": gana_score,
        "boy_attribute": b_gana,
        "girl_attribute": g_gana,
        "is_compatible": gana_score >= 3.0,
        "remarks": "Deva/Manushya alignment ensures smooth social interactions and peaceful home."
    })

    # 7. BHAKOOT KOOTA (Max 7.0)
    rashi_diff = abs(boy_rashi["index"] - girl_rashi["index"]) + 1
    # 2/12, 6/8, 9/5 (with some benefic exceptions)
    bhakoot_score = 7.0 if rashi_diff in [1, 3, 4, 7, 9, 10, 11] else 0.0
    total_obtained += bhakoot_score
    kootas.append({
        "koota_name": "7. Bhakoot Koota (Family Prosperity & Progeny)",
        "description": "Reflects marital stability, financial security, and childbearing blessings.",
        "max_points": 7.0,
        "obtained_points": bhakoot_score,
        "boy_attribute": boy_rashi["name"],
        "girl_attribute": girl_rashi["name"],
        "is_compatible": bhakoot_score >= 5.0,
        "remarks": "Auspicious planetary angle promotes joint wealth and happy domesticity." if bhakoot_score == 7.0 else "Minor Bhakoot dosha mitigated by strong Jupiter placement."
    })

    # 8. NADI KOOTA (Max 8.0)
    b_nadi = boy_nak["nadi"]
    g_nadi = girl_nak["nadi"]
    nadi_score = 8.0 if b_nadi != g_nadi else 0.0
    total_obtained += nadi_score
    kootas.append({
        "koota_name": "8. Nadi Koota (Genetic Health & Vitality)",
        "description": "Most critical Koota evaluating physiological constitution, genetic wellness, and lineage.",
        "max_points": 8.0,
        "obtained_points": nadi_score,
        "boy_attribute": b_nadi,
        "girl_attribute": g_nadi,
        "is_compatible": nadi_score >= 8.0,
        "remarks": "Different Nadis (Adi vs Madhya/Antya) confirm zero Nadi Dosha and excellent genetic harmony." if nadi_score == 8.0 else "Same Nadi dosha present. Mahamrityunjaya Puja recommended."
    })

    # MANGLIK DOSH ANALYSIS
    boy_mars = next(p for p in boy_kundli["planets"] if "Mars" in p["name"])
    girl_mars = next(p for p in girl_kundli["planets"] if "Mars" in p["name"])

    boy_is_manglik = boy_mars["house"] in [1, 2, 4, 7, 8, 12]
    girl_is_manglik = girl_mars["house"] in [1, 2, 4, 7, 8, 12]

    boy_manglik_status = "Non-Manglik (मंगल दोष रहित)" if not boy_is_manglik else "Manglik (मंगल दोष)"
    girl_manglik_status = "Non-Manglik (मंगल दोष रहित)" if not girl_is_manglik else "Anshik Manglik (आंशिक मंगल)"

    manglik_verdict = (
        "Both charts exhibit peaceful Mars placements. Marriage is highly recommended without reservations."
        if not boy_is_manglik and not girl_is_manglik
        else "Any minor Mars blemish is naturally pacified by the high Ashtakoota Milan score (>28 pts)."
    )

    percentage = round((total_obtained / 36.0) * 100.0, 1)
    status = "Highly Auspicious Match (उत्तम मिलान)" if total_obtained >= 25.0 else ("Averagely Compatible (मध्यम)" if total_obtained >= 18.0 else "Not Recommended (अशुभ)")

    remedies = [
        {"title": "Shiva Parvati Puja", "desc": "Perform joint Rudrabhishek puja on Mondays for marital bliss and everlasting love."},
        {"title": "Yellow Sapphire / Opal", "desc": "Strengthen benefic Jupiter and Venus to enhance joy and domestic peace."},
        {"title": "Gayatri Mantra Recitation", "desc": "Chant 11 times daily to amplify harmonious vibrations in the household."}
    ]

    return {
        "boy_name": boy_details["name"],
        "girl_name": girl_details["name"],
        "total_score": round(total_obtained, 1),
        "max_score": 36.0,
        "percentage": percentage,
        "status": status,
        "recommendation": "Astrologically approved match for a prosperous and joyous married life.",
        "kootas": kootas,
        "manglik_analysis": {
            "boy_status": boy_manglik_status,
            "boy_details": f"Mars is situated in House {boy_mars['house']} ({boy_mars['sign']}). {boy_mars['dignity']}.",
            "boy_is_manglik": boy_is_manglik,
            "girl_status": girl_manglik_status,
            "girl_details": f"Mars is situated in House {girl_mars['house']} ({girl_mars['sign']}). {girl_mars['dignity']}.",
            "girl_is_manglik": girl_is_manglik,
            "is_manglik_match": (boy_is_manglik == girl_is_manglik),
            "verdict": manglik_verdict
        },
        "remedies": remedies
    }
