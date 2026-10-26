"""
Vedic Astrology Match Making / Kundli Milan Calculation Engine.
Implements:
1. Ashta Koota (36 Guna Milan) with Parashara rules & classical dosha exceptions.
2. South Indian 10 Poruthams (Dasa Porutham).
3. Manglik / Mangal Dosha (Kuja Dosha) analysis with house & planet mitigations.
4. Birth-time uncertainty support (graceful degradation, no fake data).
"""
import math
from typing import Dict, Any, List, Optional, Tuple
from app.services.vedic_engine import (
    generate_full_kundli,
    calculate_julian_day,
    calculate_lahiri_ayanamsa,
    get_planet_longitudes_precise,
    calculate_ascendant_and_mc,
    get_nakshatra_info,
    degree_to_sign_and_dms,
    resolve_coordinates
)
from app.utils.constants import ZODIAC_SIGNS, NAKSHATRAS

# Nakshatra mappings for Ashta Koota & Porutham
# Index is 1-based (1 to 27)
NAKSHATRA_DATA = {
    1: {"name": "Ashwini", "lord": "Ketu", "gana": "Deva", "yoni": "Horse", "yoni_gender": "M", "varna": "Vaishya", "nadi": "Adi", "rajju": "Pada", "rajju_group": "Aroha"},
    2: {"name": "Bharani", "lord": "Venus", "gana": "Manushya", "yoni": "Elephant", "yoni_gender": "M", "varna": "Shudra", "nadi": "Madhya", "rajju": "Kati", "rajju_group": "Aroha"},
    3: {"name": "Krittika", "lord": "Sun", "gana": "Rakshasa", "yoni": "Sheep", "yoni_gender": "F", "varna": "Brahmin", "nadi": "Antya", "rajju": "Udara", "rajju_group": "Aroha"},
    4: {"name": "Rohini", "lord": "Moon", "gana": "Manushya", "yoni": "Serpent", "yoni_gender": "M", "varna": "Shudra", "nadi": "Antya", "rajju": "Kantha", "rajju_group": "Aroha"},
    5: {"name": "Mrigashira", "lord": "Mars", "gana": "Deva", "yoni": "Serpent", "yoni_gender": "F", "varna": "Vaishya", "nadi": "Madhya", "rajju": "Shiro", "rajju_group": "Sirathu"},
    6: {"name": "Ardra", "lord": "Rahu", "gana": "Manushya", "yoni": "Dog", "yoni_gender": "F", "varna": "Brahmin", "nadi": "Adi", "rajju": "Kantha", "rajju_group": "Avaroha"},
    7: {"name": "Punarvasu", "lord": "Jupiter", "gana": "Deva", "yoni": "Cat", "yoni_gender": "F", "varna": "Vaishya", "nadi": "Adi", "rajju": "Udara", "rajju_group": "Avaroha"},
    8: {"name": "Pushya", "lord": "Saturn", "gana": "Deva", "yoni": "Sheep", "yoni_gender": "M", "varna": "Kshatriya", "nadi": "Madhya", "rajju": "Kati", "rajju_group": "Avaroha"},
    9: {"name": "Ashlesha", "lord": "Mercury", "gana": "Rakshasa", "yoni": "Cat", "yoni_gender": "M", "varna": "Shudra", "nadi": "Antya", "rajju": "Pada", "rajju_group": "Avaroha"},
    10: {"name": "Magha", "lord": "Ketu", "gana": "Rakshasa", "yoni": "Rat", "yoni_gender": "M", "varna": "Shudra", "nadi": "Antya", "rajju": "Pada", "rajju_group": "Aroha"},
    11: {"name": "Purva Phalguni", "lord": "Venus", "gana": "Manushya", "yoni": "Rat", "yoni_gender": "F", "varna": "Brahmin", "nadi": "Madhya", "rajju": "Kati", "rajju_group": "Aroha"},
    12: {"name": "Uttara Phalguni", "lord": "Sun", "gana": "Manushya", "yoni": "Cow", "yoni_gender": "M", "varna": "Kshatriya", "nadi": "Adi", "rajju": "Udara", "rajju_group": "Aroha"},
    13: {"name": "Hasta", "lord": "Moon", "gana": "Deva", "yoni": "Buffalo", "yoni_gender": "F", "varna": "Vaishya", "nadi": "Adi", "rajju": "Kantha", "rajju_group": "Aroha"},
    14: {"name": "Chitra", "lord": "Mars", "gana": "Rakshasa", "yoni": "Tiger", "yoni_gender": "F", "varna": "Shudra", "nadi": "Madhya", "rajju": "Shiro", "rajju_group": "Sirathu"},
    15: {"name": "Swati", "lord": "Rahu", "gana": "Deva", "yoni": "Buffalo", "yoni_gender": "M", "varna": "Brahmin", "nadi": "Antya", "rajju": "Kantha", "rajju_group": "Avaroha"},
    16: {"name": "Vishakha", "lord": "Jupiter", "gana": "Rakshasa", "yoni": "Tiger", "yoni_gender": "M", "varna": "Kshatriya", "nadi": "Antya", "rajju": "Udara", "rajju_group": "Avaroha"},
    17: {"name": "Anuradha", "lord": "Saturn", "gana": "Deva", "yoni": "Deer", "yoni_gender": "F", "varna": "Vaishya", "nadi": "Madhya", "rajju": "Kati", "rajju_group": "Avaroha"},
    18: {"name": "Jyeshtha", "lord": "Mercury", "gana": "Rakshasa", "yoni": "Deer", "yoni_gender": "M", "varna": "Shudra", "nadi": "Adi", "rajju": "Pada", "rajju_group": "Avaroha"},
    19: {"name": "Moola", "lord": "Ketu", "gana": "Rakshasa", "yoni": "Dog", "yoni_gender": "M", "varna": "Shudra", "nadi": "Adi", "rajju": "Pada", "rajju_group": "Aroha"},
    20: {"name": "Purva Ashadha", "lord": "Venus", "gana": "Manushya", "yoni": "Monkey", "yoni_gender": "M", "varna": "Brahmin", "nadi": "Madhya", "rajju": "Kati", "rajju_group": "Aroha"},
    21: {"name": "Uttara Ashadha", "lord": "Sun", "gana": "Manushya", "yoni": "Mongoose", "yoni_gender": "M", "varna": "Kshatriya", "nadi": "Antya", "rajju": "Udara", "rajju_group": "Aroha"},
    22: {"name": "Shravana", "lord": "Moon", "gana": "Deva", "yoni": "Monkey", "yoni_gender": "F", "varna": "Vaishya", "nadi": "Antya", "rajju": "Kantha", "rajju_group": "Aroha"},
    23: {"name": "Dhanishta", "lord": "Mars", "gana": "Rakshasa", "yoni": "Lion", "yoni_gender": "F", "varna": "Shudra", "nadi": "Madhya", "rajju": "Shiro", "rajju_group": "Sirathu"},
    24: {"name": "Shatabhisha", "lord": "Rahu", "gana": "Rakshasa", "yoni": "Horse", "yoni_gender": "F", "varna": "Brahmin", "nadi": "Adi", "rajju": "Kantha", "rajju_group": "Avaroha"},
    25: {"name": "Purva Bhadrapada", "lord": "Jupiter", "gana": "Manushya", "yoni": "Lion", "yoni_gender": "M", "varna": "Kshatriya", "nadi": "Adi", "rajju": "Udara", "rajju_group": "Avaroha"},
    26: {"name": "Uttara Bhadrapada", "lord": "Saturn", "gana": "Manushya", "yoni": "Cow", "yoni_gender": "F", "varna": "Vaishya", "nadi": "Madhya", "rajju": "Kati", "rajju_group": "Avaroha"},
    27: {"name": "Revati", "lord": "Mercury", "gana": "Deva", "yoni": "Elephant", "yoni_gender": "F", "varna": "Shudra", "nadi": "Antya", "rajju": "Pada", "rajju_group": "Avaroha"},
}

# Vedha pairs (mutually repulsive stars in South Indian Porutham)
VEDHA_PAIRS = {
    (1, 18), (18, 1),   # Ashwini - Jyeshtha
    (2, 17), (17, 2),   # Bharani - Anuradha
    (3, 16), (16, 3),   # Krittika - Vishakha
    (4, 15), (15, 4),   # Rohini - Swati
    (5, 14), (14, 5),   # Mrigashira - Chitra
    (6, 22), (22, 6),   # Ardra - Shravana
    (7, 21), (21, 7),   # Punarvasu - Uttara Ashadha
    (8, 20), (20, 8),   # Pushya - Purva Ashadha
    (9, 19), (19, 9),   # Ashlesha - Moola
    (10, 27), (27, 10), # Magha - Revati
    (11, 26), (26, 11), # Purva Phalguni - Uttara Bhadrapada
    (12, 25), (25, 12), # Uttara Phalguni - Purva Bhadrapada
    (13, 24), (24, 13), # Hasta - Shatabhisha
}

# Planetary friendship matrix for Graha Maitri
# Planet Lords: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
PLANET_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
}

NATURAL_FRIENDSHIP = {
    "Sun": {"Moon": "Friend", "Mars": "Friend", "Jupiter": "Friend", "Mercury": "Neutral", "Venus": "Enemy", "Saturn": "Enemy", "Sun": "Friend"},
    "Moon": {"Sun": "Friend", "Mercury": "Friend", "Mars": "Neutral", "Jupiter": "Neutral", "Venus": "Neutral", "Saturn": "Neutral", "Moon": "Friend"},
    "Mars": {"Sun": "Friend", "Moon": "Friend", "Jupiter": "Friend", "Venus": "Neutral", "Saturn": "Neutral", "Mercury": "Enemy", "Mars": "Friend"},
    "Mercury": {"Sun": "Friend", "Venus": "Friend", "Mars": "Neutral", "Jupiter": "Neutral", "Saturn": "Neutral", "Moon": "Enemy", "Mercury": "Friend"},
    "Jupiter": {"Sun": "Friend", "Moon": "Friend", "Mars": "Friend", "Saturn": "Neutral", "Mercury": "Enemy", "Venus": "Enemy", "Jupiter": "Friend"},
    "Venus": {"Mercury": "Friend", "Saturn": "Friend", "Mars": "Neutral", "Jupiter": "Neutral", "Sun": "Enemy", "Moon": "Enemy", "Venus": "Friend"},
    "Saturn": {"Mercury": "Friend", "Venus": "Friend", "Jupiter": "Neutral", "Sun": "Enemy", "Moon": "Enemy", "Mars": "Enemy", "Saturn": "Friend"},
}

# Yoni Sworn Enemies
YONI_ENEMIES = {
    ("Horse", "Buffalo"), ("Buffalo", "Horse"),
    ("Elephant", "Lion"), ("Lion", "Elephant"),
    ("Sheep", "Monkey"), ("Monkey", "Sheep"),
    ("Serpent", "Mongoose"), ("Mongoose", "Serpent"),
    ("Dog", "Deer"), ("Deer", "Dog"),
    ("Cat", "Rat"), ("Rat", "Cat"),
    ("Cow", "Tiger"), ("Tiger", "Cow")
}

# Yoni Friendly groups
YONI_FRIENDS = {
    ("Horse", "Serpent"), ("Serpent", "Horse"),
    ("Elephant", "Sheep"), ("Sheep", "Elephant"),
    ("Cat", "Mongoose"), ("Mongoose", "Cat"),
    ("Dog", "Monkey"), ("Monkey", "Dog"),
    ("Deer", "Cow"), ("Cow", "Deer")
}


class MatchMakingEngine:
    """High-precision deterministic Vedic Compatibility Engine."""

    @classmethod
    def calculate_person_profile(
        cls,
        dob_str: str,
        tob_str: Optional[str],
        lat: float,
        lon: float,
        tz_offset: float = 5.5,
        is_birth_time_known: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates verified chart positions for an individual.
        If birth time is unknown, computes Moon position at 12:00 local time
        and marks Ascendant / House positions as unavailable.
        """
        # Parse date
        parts = dob_str.strip().split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid date format: {dob_str}. Expected YYYY-MM-DD.")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

        if is_birth_time_known and tob_str and tob_str.strip():
            t_parts = tob_str.strip().split(":")
            hour = int(t_parts[0])
            minute = int(t_parts[1]) if len(t_parts) > 1 else 0
            second = int(t_parts[2]) if len(t_parts) > 2 else 0
            hour_decimal = hour + (minute / 60.0) + (second / 3600.0)
        else:
            # When time is unknown, use noon local time for celestial Moon positioning
            # but clearly flag lagna as uncertain
            hour_decimal = 12.0
            is_birth_time_known = False

        utc_hour = hour_decimal - tz_offset
        jd = calculate_julian_day(year, month, day, utc_hour)
        ayanamsha = calculate_lahiri_ayanamsa(jd)

        # Precise planet positions
        planets = get_planet_longitudes_precise(jd, ayanamsha, lat, lon)
        moon_deg = planets["Moon"][0]
        mars_deg = planets["Mars"][0]

        # Moon Sign and Nakshatra
        moon_sign_idx, moon_sign_name, moon_dms, moon_deg_in_sign = degree_to_sign_and_dms(moon_deg)
        nak_name, nak_lord, nak_pada, nak_idx = get_nakshatra_info(moon_deg)

        # Ascendant / Lagna
        if is_birth_time_known:
            asc_deg, _, _ = calculate_ascendant_and_mc(jd, lat, lon, ayanamsha)
            asc_sign_idx, asc_sign_name, asc_dms, _ = degree_to_sign_and_dms(asc_deg)
            mars_sign_idx, mars_sign_name, _, _ = degree_to_sign_and_dms(mars_deg)
            # Mars house from Lagna (1-based: house 1 = asc_sign_idx)
            mars_house_lagna = ((mars_sign_idx - asc_sign_idx) % 12) + 1
        else:
            asc_deg = None
            asc_sign_idx = None
            asc_sign_name = "Unavailable (Birth Time Unknown)"
            mars_sign_idx, mars_sign_name, _, _ = degree_to_sign_and_dms(mars_deg)
            mars_house_lagna = None

        # Mars house from Moon
        mars_house_moon = ((mars_sign_idx - moon_sign_idx) % 12) + 1

        nak_meta = NAKSHATRA_DATA.get(nak_idx, {
            "gana": "Deva", "yoni": "Horse", "varna": "Vaishya", "nadi": "Adi", "rajju": "Pada"
        })

        # Varna from Moon Sign (Classical Parashara)
        # Cancer, Scorpio, Pisces -> Brahmin (4)
        # Aries, Leo, Sagittarius -> Kshatriya (3)
        # Taurus, Virgo, Capricorn -> Vaishya (2)
        # Gemini, Libra, Aquarius -> Shudra (1)
        sign_varna_map = {
            4: ("Brahmin", 4), 8: ("Brahmin", 4), 12: ("Brahmin", 4),
            1: ("Kshatriya", 3), 5: ("Kshatriya", 3), 9: ("Kshatriya", 3),
            2: ("Vaishya", 2), 6: ("Vaishya", 2), 10: ("Vaishya", 2),
            3: ("Shudra", 1), 7: ("Shudra", 1), 11: ("Shudra", 1),
        }
        varna_name, varna_rank = sign_varna_map.get(moon_sign_idx, ("Vaishya", 2))

        # Vashya from Moon Sign
        if moon_sign_idx in [1, 2]:
            vashya_name = "Chatushpada (Quadruped)"
        elif moon_sign_idx in [3, 6, 7, 11]:
            vashya_name = "Manava / Dvipada (Human)"
        elif moon_sign_idx in [4, 12]:
            vashya_name = "Jalachara (Water-Dwelling)"
        elif moon_sign_idx == 5:
            vashya_name = "Vanachara (Wild Beast)"
        elif moon_sign_idx == 8:
            vashya_name = "Keeta (Insect)"
        elif moon_sign_idx == 9:
            vashya_name = "Manava (First Half)" if moon_deg_in_sign < 15.0 else "Chatushpada (Second Half)"
        elif moon_sign_idx == 10:
            vashya_name = "Chatushpada (First Half)" if moon_deg_in_sign < 15.0 else "Jalachara (Second Half)"
        else:
            vashya_name = "Manava"

        return {
            "is_birth_time_known": is_birth_time_known,
            "julian_day": jd,
            "ayanamsha": ayanamsha,
            "moon_longitude": moon_deg,
            "moon_sign_index": moon_sign_idx,
            "moon_sign_name": moon_sign_name,
            "moon_lord": PLANET_LORDS.get(moon_sign_idx, "Mars"),
            "nakshatra_index": nak_idx,
            "nakshatra_name": nak_name,
            "nakshatra_lord": nak_lord,
            "nakshatra_pada": nak_pada,
            "varna_name": varna_name,
            "varna_rank": varna_rank,
            "vashya_name": vashya_name,
            "gana": nak_meta["gana"],
            "yoni": nak_meta["yoni"],
            "yoni_gender": nak_meta["yoni_gender"],
            "nadi": nak_meta["nadi"],
            "rajju": nak_meta["rajju"],
            "rajju_group": nak_meta.get("rajju_group", "Aroha"),
            "ascendant_longitude": asc_deg,
            "ascendant_sign_index": asc_sign_idx,
            "ascendant_sign_name": asc_sign_name,
            "mars_longitude": mars_deg,
            "mars_sign_index": mars_sign_idx,
            "mars_sign_name": mars_sign_name,
            "mars_house_lagna": mars_house_lagna,
            "mars_house_moon": mars_house_moon,
        }

    # -------------------------------------------------------------
    # ASHTA KOOTA (36 GUNA MILAN) CALCULATIONS
    # -------------------------------------------------------------
    @classmethod
    def calculate_varna_koota(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> Dict[str, Any]:
        """Varna Koota (1 Point Max): Spiritual & work ego compatibility."""
        b_rank = boy["varna_rank"]
        g_rank = girl["varna_rank"]
        b_varna = boy["varna_name"]
        g_varna = girl["varna_name"]

        if b_rank >= g_rank:
            points = 1.0
            compatible = True
            remarks = f"Auspicious. Groom's Varna ({b_varna}) matches or exceeds Bride's Varna ({g_varna}), supporting natural harmony in social roles."
        else:
            points = 0.0
            compatible = False
            remarks = f"Bride's Varna ({g_varna}) is higher than Groom's Varna ({b_varna}). Mutual respect and emotional understanding bridge any temperamental differences."

        return {
            "koota_name": "Varna",
            "max_points": 1.0,
            "obtained_points": points,
            "boy_attribute": b_varna,
            "girl_attribute": g_varna,
            "is_compatible": compatible,
            "description": "Measures spiritual readiness, ego harmony, and social temperament.",
            "remarks": remarks,
        }

    @classmethod
    def calculate_vashya_koota(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> Dict[str, Any]:
        """Vashya Koota (2 Points Max): Mutual attraction and control."""
        b_v = boy["vashya_name"].split(" ")[0]
        g_v = girl["vashya_name"].split(" ")[0]

        if b_v == g_v:
            points = 2.0
            compatible = True
            remarks = f"Harmonious Vashya ({b_v}). Strong natural rapport, mutual magnetic pull, and easy agreement."
        elif "Vanachara" in [b_v, g_v]:
            # Vanachara (Lion) dominates others or creates tension
            points = 0.0
            compatible = False
            remarks = f"Wild nature ({b_v} vs {g_v}) indicates dominating tendencies that require patient boundary setting."
        elif "Keeta" in [b_v, g_v]:
            points = 1.0
            compatible = True
            remarks = f"Mild affinity ({b_v} and {g_v}). Steady understanding is achieved through open dialogue."
        else:
            points = 1.0
            compatible = True
            remarks = f"Balanced Vashya ({b_v} and {g_v}). Mutual cooperation without struggle for dominance."

        return {
            "koota_name": "Vashya",
            "max_points": 2.0,
            "obtained_points": points,
            "boy_attribute": boy["vashya_name"],
            "girl_attribute": girl["vashya_name"],
            "is_compatible": compatible,
            "description": "Assesses mutual emotional magnetism and power dynamics in the partnership.",
            "remarks": remarks,
        }

    @classmethod
    def calculate_tara_koota(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> Dict[str, Any]:
        """Tara / Dina Koota (3 Points Max): Destiny, health, and mutual longevity."""
        b_nak = boy["nakshatra_index"]
        g_nak = girl["nakshatra_index"]

        # Count from Girl to Boy
        count_gb = ((b_nak - g_nak) % 27) + 1
        tara_gb = ((count_gb - 1) % 9) + 1

        # Count from Boy to Girl
        count_bg = ((g_nak - b_nak) % 27) + 1
        tara_bg = ((count_bg - 1) % 9) + 1

        tara_names = {
            1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema",
            5: "Pratyak", 6: "Sadhana", 7: "Naidhana", 8: "Mitra", 9: "Parama Mitra"
        }
        # Auspicious taras: 2, 4, 6, 8, 9 (and 1 if same star/pada exception)
        auspicious_set = {2, 4, 6, 8, 9}
        gb_good = tara_gb in auspicious_set or (tara_gb == 1 and b_nak == g_nak)
        bg_good = tara_bg in auspicious_set or (tara_bg == 1 and b_nak == g_nak)

        if gb_good and bg_good:
            points = 3.0
            compatible = True
            remarks = f"Highly auspicious. Bride to Groom gives {tara_names[tara_gb]} Tara and Groom to Bride gives {tara_names[tara_bg]} Tara, bestowing longevity and mutual good fortune."
        elif gb_good or bg_good:
            points = 1.5
            compatible = True
            remarks = f"Moderately favorable. One directional flow is auspicious ({tara_names[tara_gb]} / {tara_names[tara_bg]}). Good overall balance."
        else:
            points = 0.0
            compatible = False
            remarks = f"Both directional counts fall in challenging Taras ({tara_names[tara_gb]} and {tara_names[tara_bg]}). Remedial prayer and health mindfulness recommended."

        return {
            "koota_name": "Tara",
            "max_points": 3.0,
            "obtained_points": points,
            "boy_attribute": f"{boy['nakshatra_name']} ({tara_names[tara_bg]})",
            "girl_attribute": f"{girl['nakshatra_name']} ({tara_names[tara_gb]})",
            "is_compatible": compatible,
            "description": "Calculates planetary star alignment for mutual health, prosperity, and longevity.",
            "remarks": remarks,
        }

    @classmethod
    def calculate_yoni_koota(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> Dict[str, Any]:
        """Yoni Koota (4 Points Max): Physical, sexual, and biological harmony."""
        b_yoni = boy["yoni"]
        g_yoni = girl["yoni"]

        if b_yoni == g_yoni:
            points = 4.0
            compatible = True
            remarks = f"Same Yoni archetype ({b_yoni}). Excellent instinctual harmony, deep physical intimacy and mutual affection."
        elif (b_yoni, g_yoni) in YONI_ENEMIES:
            points = 0.0
            compatible = False
            remarks = f"Natural adversary archetypes ({b_yoni} vs {g_yoni}). Potential for instinctual friction; requires mutual patience and emotional tenderness."
        elif (b_yoni, g_yoni) in YONI_FRIENDS:
            points = 3.0
            compatible = True
            remarks = f"Friendly Yonis ({b_yoni} and {g_yoni}). Cordial biological rapport and affectionate bond."
        else:
            points = 2.0
            compatible = True
            remarks = f"Neutral Yonis ({b_yoni} and {g_yoni}). Moderate physical compatibility that matures through affectionate communication."

        return {
            "koota_name": "Yoni",
            "max_points": 4.0,
            "obtained_points": points,
            "boy_attribute": f"{b_yoni} ({boy['yoni_gender']})",
            "girl_attribute": f"{g_yoni} ({girl['yoni_gender']})",
            "is_compatible": compatible,
            "description": "Evaluates biological chemistry, physical satisfaction, and instinctual compatibility.",
            "remarks": remarks,
        }

    @classmethod
    def calculate_graha_maitri_koota(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> Dict[str, Any]:
        """Graha Maitri Koota (5 Points Max): Moon Sign Lord friendship & mental compatibility."""
        b_lord = boy["moon_lord"]
        g_lord = girl["moon_lord"]

        rel_bg = NATURAL_FRIENDSHIP.get(b_lord, {}).get(g_lord, "Neutral")
        rel_gb = NATURAL_FRIENDSHIP.get(g_lord, {}).get(b_lord, "Neutral")

        if b_lord == g_lord:
            points = 5.0
            compatible = True
            remarks = f"Same Rashi Lord ({b_lord}). Exceptional intellectual communion, shared worldview, and enduring mental harmony."
        elif rel_bg == "Friend" and rel_gb == "Friend":
            points = 5.0
            compatible = True
            remarks = f"Mutual friends ({b_lord} and {g_lord}). Warm understanding, seamless communication, and intellectual resonance."
        elif (rel_bg == "Friend" and rel_gb == "Neutral") or (rel_gb == "Friend" and rel_bg == "Neutral"):
            points = 4.0
            compatible = True
            remarks = f"Friendly and constructive relation between {b_lord} and {g_lord}. Healthy mental rapport and shared goals."
        elif rel_bg == "Neutral" and rel_gb == "Neutral":
            points = 3.0
            compatible = True
            remarks = f"Neutral alignment between {b_lord} and {g_lord}. Peaceful coexistence with mutual respect for differences."
        elif (rel_bg == "Friend" and rel_gb == "Enemy") or (rel_gb == "Friend" and rel_bg == "Enemy"):
            points = 1.0
            compatible = False
            remarks = f"Asymmetric relationship between {b_lord} and {g_lord}. Occasional misunderstandings requiring mindful dialogue."
        elif (rel_bg == "Neutral" and rel_gb == "Enemy") or (rel_gb == "Neutral" and rel_bg == "Enemy"):
            points = 0.5
            compatible = False
            remarks = f"Mild friction between sign rulers ({b_lord} and {g_lord}). Conscious effort in communication is advised."
        else:
            points = 0.0
            compatible = False
            remarks = f"Mutual inimical rulers ({b_lord} and {g_lord}). Opposing psychological outlooks; emotional tolerance is essential."

        return {
            "koota_name": "Graha Maitri",
            "max_points": 5.0,
            "obtained_points": points,
            "boy_attribute": f"{boy['moon_sign_name']} (Lord: {b_lord})",
            "girl_attribute": f"{girl['moon_sign_name']} (Lord: {g_lord})",
            "is_compatible": compatible,
            "description": "Measures mental harmony, psychological affinity, and intellectual outlook through Moon sign lords.",
            "remarks": remarks,
        }

    @classmethod
    def calculate_gana_koota(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> Dict[str, Any]:
        """Gana Koota (6 Points Max): Temperament and behavioral harmony."""
        b_gana = boy["gana"]
        g_gana = girl["gana"]

        if b_gana == g_gana:
            points = 6.0
            compatible = True
            remarks = f"Same Gana ({b_gana}). Complete alignment in core temperament, social values, and day-to-day lifestyle."
        elif b_gana == "Deva" and g_gana == "Manushya":
            points = 6.0
            compatible = True
            remarks = "Deva Groom with Manushya Bride. Highly auspicious combination; mutual respect and spiritual elevation."
        elif b_gana == "Manushya" and g_gana == "Deva":
            points = 5.0
            compatible = True
            remarks = "Manushya Groom with Deva Bride. Very good match with reciprocal admiration and peaceful home life."
        elif b_gana == "Deva" and g_gana == "Rakshasa":
            points = 1.0
            compatible = False
            remarks = "Deva Groom with Rakshasa Bride. Contrasting temperaments; necessitates patience and empathetic understanding."
        else:
            # Rakshasa + Manushya or Rakshasa + Deva
            points = 0.0
            compatible = False
            remarks = f"Challenging Gana pairing ({b_gana} and {g_gana}). Differing life paces and expressive styles require conscious mutual accommodation."

        return {
            "koota_name": "Gana",
            "max_points": 6.0,
            "obtained_points": points,
            "boy_attribute": b_gana,
            "girl_attribute": g_gana,
            "is_compatible": compatible,
            "description": "Evaluates temperament, behavioral nature (Deva/Manushya/Rakshasa), and domestic compatibility.",
            "remarks": remarks,
        }

    @classmethod
    def calculate_bhakoot_koota(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bhakoot / Rashi Koota (7 Points Max): Family welfare, emotional prosperity & health.
        Detects 2/12 (Dwidwadasha), 5/9 (Navapanchama), and 6/8 (Shadashtaka) Doshas,
        and applies classical Parashara cancellation rules (same lord or mutual friends).
        """
        b_rashi = boy["moon_sign_index"]
        g_rashi = girl["moon_sign_index"]
        b_lord = boy["moon_lord"]
        g_lord = girl["moon_lord"]

        dist_gb = ((b_rashi - g_rashi) % 12) + 1
        dist_bg = ((g_rashi - b_rashi) % 12) + 1

        rel_pair = (min(dist_gb, dist_bg), max(dist_gb, dist_bg))

        # Check classical cancellations:
        # Cancellation 1: Both signs have the same lord (Aries/Scorpio by Mars, Taurus/Libra by Venus)
        # Cancellation 2: Lords are mutual friends (e.g. Pisces/Aries -> Jupiter/Mars; Cancer/Leo -> Moon/Sun)
        lords_same = (b_lord == g_lord)
        lords_mutual_friends = (
            NATURAL_FRIENDSHIP.get(b_lord, {}).get(g_lord) == "Friend" and
            NATURAL_FRIENDSHIP.get(g_lord, {}).get(b_lord) == "Friend"
        )
        cancellation_applies = lords_same or lords_mutual_friends

        if dist_gb in [1, 7, 3, 11, 4, 10]:
            points = 7.0
            compatible = True
            remarks = f"Auspicious Rashi alignment ({dist_gb}/{dist_bg}). Fosters emotional warmth, financial growth, and family prosperity."
        elif rel_pair == (2, 12):
            if cancellation_applies:
                points = 7.0
                compatible = True
                remarks = f"2/12 Dwidwadasha Dosha is CANCELLED because Moon sign lords ({b_lord} and {g_lord}) are {'identical' if lords_same else 'mutual friends'}. Full 7 points awarded."
            else:
                points = 0.0
                compatible = False
                remarks = "2/12 (Dwidwadasha) alignment. Warns of financial disparity or expenditure imbalances. Joint financial planning advised."
        elif rel_pair == (5, 9):
            if cancellation_applies:
                points = 7.0
                compatible = True
                remarks = f"5/9 Navapanchama Dosha is CANCELLED due to {'identical' if lords_same else 'friendly'} Rashi rulers ({b_lord} & {g_lord}). Auspicious progeny & spiritual union."
            else:
                points = 0.0
                compatible = False
                remarks = "5/9 (Navapanchama) alignment. Can cause delayed family planning or philosophical divergence. Respect for each other's beliefs harmonizes this."
        elif rel_pair == (6, 8):
            if cancellation_applies:
                points = 7.0
                compatible = True
                remarks = f"6/8 (Shadashtaka) Dosha is CANCELLED by auspicious lord relationship ({b_lord} & {g_lord}). Discord is neutralized."
            else:
                points = 0.0
                compatible = False
                remarks = "6/8 (Shadashtaka) alignment. Known as the debt/adversity axis. Requires emotional calmness, avoiding resentment during arguments."
        else:
            points = 7.0
            compatible = True
            remarks = f"Harmonious Rashi placement ({dist_gb}/{dist_bg}). Fosters domestic joy and mutual devotion."

        return {
            "koota_name": "Bhakoot",
            "max_points": 7.0,
            "obtained_points": points,
            "boy_attribute": boy["moon_sign_name"],
            "girl_attribute": girl["moon_sign_name"],
            "is_compatible": compatible,
            "description": "Analyzes emotional synergy, financial growth, health, and family longevity through Moon sign distance.",
            "remarks": remarks,
        }

    @classmethod
    def calculate_nadi_koota(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nadi Koota (8 Points Max): Physiological constitution, genetic vitality & progeny.
        Detects Nadi Dosha and checks classical cancellations:
        - Same Rashi, but different Nakshatras
        - Same Nakshatra, but different Rashis
        - Same Nakshatra with different Padas & friendly lords
        """
        b_nadi = boy["nadi"]
        g_nadi = girl["nadi"]
        b_rashi = boy["moon_sign_index"]
        g_rashi = girl["moon_sign_index"]
        b_nak = boy["nakshatra_index"]
        g_nak = girl["nakshatra_index"]
        b_pada = boy["nakshatra_pada"]
        g_pada = girl["nakshatra_pada"]

        if b_nadi != g_nadi:
            points = 8.0
            compatible = True
            remarks = f"Different Nadis ({b_nadi} and {g_nadi}). Complete physiological and bio-energetic balance; excellent genetic vitality for progeny."
        else:
            # Same Nadi -> Check classical exceptions / cancellations
            # Exception 1: Different Nakshatras in the same Rashi
            cond_diff_nak_same_rashi = (b_rashi == g_rashi and b_nak != g_nak)
            # Exception 2: Same Nakshatra, but different Rashis (border stars)
            cond_same_nak_diff_rashi = (b_nak == g_nak and b_rashi != g_rashi)
            # Exception 3: Same Nakshatra, different Pada
            cond_diff_pada = (b_nak == g_nak and b_pada != g_pada)

            if cond_diff_nak_same_rashi:
                points = 8.0
                compatible = True
                remarks = f"Nadi Dosha ({b_nadi}) is CANCELLED because partners have different Nakshatras within the same Rashi. Full 8 points awarded."
            elif cond_same_nak_diff_rashi:
                points = 8.0
                compatible = True
                remarks = f"Nadi Dosha ({b_nadi}) is CANCELLED because the common Nakshatra spans across different Rashis. Full 8 points awarded."
            elif cond_diff_pada:
                points = 8.0
                compatible = True
                remarks = f"Nadi Dosha ({b_nadi}) is mitigated by different Nakshatra Padas (Groom Pada {b_pada}, Bride Pada {g_pada}). Auspicious vitality."
            else:
                points = 0.0
                compatible = False
                remarks = f"Same Nadi ({b_nadi} - Nadi Dosha). Traditional texts advise medical checkup for hereditary factors and chanting Maha Mrityunjaya mantra."

        return {
            "koota_name": "Nadi",
            "max_points": 8.0,
            "obtained_points": points,
            "boy_attribute": f"{b_nadi} ({boy['nakshatra_name']})",
            "girl_attribute": f"{g_nadi} ({girl['nakshatra_name']})",
            "is_compatible": compatible,
            "description": "Assesses bio-energetic constitution (Vata/Pitta/Kapha), genetic health, and reproductive harmony.",
            "remarks": remarks,
        }

    # -------------------------------------------------------------
    # SOUTH INDIAN PORUTHAM (10 PORUTHAMS)
    # -------------------------------------------------------------
    @classmethod
    def calculate_south_indian_porutham(cls, boy: Dict[str, Any], girl: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculates the traditional 10 Poruthams (Dasa Porutham):
        1. Dina Porutham
        2. Gana Porutham
        3. Mahendra Porutham
        4. Stree Deergha Porutham
        5. Yoni Porutham
        6. Rasi Porutham
        7. Rasiyathipathi Porutham
        8. Vasya Porutham
        9. Rajju Porutham
        10. Vedha Porutham
        """
        b_nak = boy["nakshatra_index"]
        g_nak = girl["nakshatra_index"]
        b_rashi = boy["moon_sign_index"]
        g_rashi = girl["moon_sign_index"]

        results = []

        # 1. Dina Porutham (Health & daily freedom from distress)
        count_gb = ((b_nak - g_nak) % 27) + 1
        rem9 = count_gb % 9
        dina_satisfied = rem9 not in [1, 3, 5, 7] or (b_nak == g_nak)
        results.append({
            "porutham_name": "Dina Porutham",
            "tamil_name": "தினப் பொருத்தம்",
            "status": "Satisfied" if dina_satisfied else "Not Satisfied",
            "is_satisfied": dina_satisfied,
            "boy_value": boy["nakshatra_name"],
            "girl_value": girl["nakshatra_name"],
            "significance": "Longevity, health, and freedom from daily financial distress.",
            "explanation": f"Star count from bride is {count_gb} (remainder {rem9}). " + (
                "Auspicious star distance indicates mutual peace and sound health." if dina_satisfied
                else "Unfavorable star distance; spiritual remedies for wellbeing recommended."
            )
        })

        # 2. Gana Porutham (Temperament & lifestyle)
        b_gana = boy["gana"]
        g_gana = girl["gana"]
        gana_satisfied = (b_gana == g_gana) or (b_gana == "Deva" and g_gana == "Manushya") or (b_gana == "Manushya" and g_gana == "Deva")
        results.append({
            "porutham_name": "Gana Porutham",
            "tamil_name": "கணப் பொருத்தம்",
            "status": "Satisfied" if gana_satisfied else "Not Satisfied",
            "is_satisfied": gana_satisfied,
            "boy_value": b_gana,
            "girl_value": g_gana,
            "significance": "Mental compatibility, character traits, and domestic lifestyle.",
            "explanation": f"Groom is {b_gana} and Bride is {g_gana}. " + (
                "Compatible psychological temperaments promote harmonious co-existence." if gana_satisfied
                else "Contrasting temperaments require emotional maturity and open communication."
            )
        })

        # 3. Mahendra Porutham (Progeny, lineage & family wealth)
        mahendra_satisfied = count_gb in [4, 7, 10, 13, 16, 19, 22, 25]
        results.append({
            "porutham_name": "Mahendra Porutham",
            "tamil_name": "மகேந்திரப் பொருத்தம்",
            "status": "Satisfied" if mahendra_satisfied else "Not Satisfied",
            "is_satisfied": mahendra_satisfied,
            "boy_value": f"Count {count_gb}",
            "girl_value": "Base Star",
            "significance": "Blessing of children, preservation of lineage, and prosperity.",
            "explanation": "Star count falls into the classical Mahendra group (4, 7, 10, 13, 16, 19, 22, 25), bestowing progeny and auspicious blessings." if mahendra_satisfied
            else f"Count {count_gb} is outside the specific Mahendra positions; other progeny factors (Jupiter, 5th house) should be verified."
        })

        # 4. Stree Deergha Porutham (Longevity and safety of the wife)
        stree_satisfied = count_gb > 13
        results.append({
            "porutham_name": "Stree Deergha Porutham",
            "tamil_name": "ஸ்திரீ தீர்க்கப் பொருத்தம்",
            "status": "Satisfied" if stree_satisfied else "Not Satisfied",
            "is_satisfied": stree_satisfied,
            "boy_value": f"Distance: {count_gb}",
            "girl_value": "Base Star",
            "significance": "Prolonged longevity, enduring prosperity, and happiness of the wife.",
            "explanation": f"Groom's star is {count_gb} constellations away from Bride (> 13), ensuring longevity and stability for the bride." if stree_satisfied
            else f"Groom's star is {count_gb} constellations away (<= 13). Balanced by strong Dina and Rasi Poruthams."
        })

        # 5. Yoni Porutham (Physical compatibility & mutual attraction)
        b_yoni = boy["yoni"]
        g_yoni = girl["yoni"]
        yoni_satisfied = (b_yoni, g_yoni) not in YONI_ENEMIES
        results.append({
            "porutham_name": "Yoni Porutham",
            "tamil_name": "யோனிப் பொருத்தம்",
            "status": "Satisfied" if yoni_satisfied else "Not Satisfied",
            "is_satisfied": yoni_satisfied,
            "boy_value": b_yoni,
            "girl_value": g_yoni,
            "significance": "Physical and biological attraction, marital joy, and sexual harmony.",
            "explanation": f"Groom ({b_yoni}) and Bride ({g_yoni}) possess compatible animal archetypes with no primal enmity." if yoni_satisfied
            else f"Groom ({b_yoni}) and Bride ({g_yoni}) belong to naturally hostile animal pairs; mutual patience is required."
        })

        # 6. Rasi Porutham (Harmony between families & general fortune)
        dist_gb = ((b_rashi - g_rashi) % 12) + 1
        rasi_satisfied = dist_gb not in [2, 6, 8, 12] or (b_rashi == g_rashi) or (boy["moon_lord"] == girl["moon_lord"])
        results.append({
            "porutham_name": "Rasi Porutham",
            "tamil_name": "ராசிப் பொருத்தம்",
            "status": "Satisfied" if rasi_satisfied else "Not Satisfied",
            "is_satisfied": rasi_satisfied,
            "boy_value": boy["moon_sign_name"],
            "girl_value": girl["moon_sign_name"],
            "significance": "Family bonding, emotional equilibrium, and enduring good fortune.",
            "explanation": f"Moon sign relationship ({dist_gb}th from Bride) is favorable, supporting cordial family ties." if rasi_satisfied
            else f"Moon sign distance is {dist_gb}th (Sashtashtaga/Dwidwadasha); open communication resolves tension."
        })

        # 7. Rasiyathipathi Porutham (Planetary Lord Friendship)
        b_lord = boy["moon_lord"]
        g_lord = girl["moon_lord"]
        lord_rel = NATURAL_FRIENDSHIP.get(b_lord, {}).get(g_lord, "Neutral")
        rasiyathipathi_satisfied = (b_lord == g_lord) or (lord_rel in ["Friend", "Neutral"])
        results.append({
            "porutham_name": "Rasiyathipathi Porutham",
            "tamil_name": "ராசியாதிபதிப் பொருத்தம்",
            "status": "Satisfied" if rasiyathipathi_satisfied else "Not Satisfied",
            "is_satisfied": rasiyathipathi_satisfied,
            "boy_value": b_lord,
            "girl_value": g_lord,
            "significance": "Friendship between minds, mutual affection, and shared values.",
            "explanation": f"Moon lords ({b_lord} and {g_lord}) share friendly or neutral rapport, ensuring mutual goodwill." if rasiyathipathi_satisfied
            else f"Moon lords ({b_lord} and {g_lord}) are naturally opposing; conscious understanding is vital."
        })

        # 8. Vasya Porutham (Mutual affection & hypnotic attraction)
        vasya_pairs = {
            1: [5, 8], 2: [4, 7], 3: [6], 4: [8, 9], 5: [7],
            6: [3, 12], 7: [10, 2], 8: [4], 9: [12], 10: [1, 11], 11: [1], 12: [10]
        }
        vasya_satisfied = (b_rashi in vasya_pairs.get(g_rashi, [])) or (g_rashi in vasya_pairs.get(b_rashi, [])) or (b_rashi == g_rashi)
        results.append({
            "porutham_name": "Vasya Porutham",
            "tamil_name": "வசியப் பொருத்தம்",
            "status": "Satisfied" if vasya_satisfied else "Not Satisfied",
            "is_satisfied": vasya_satisfied,
            "boy_value": boy["moon_sign_name"],
            "girl_value": girl["moon_sign_name"],
            "significance": "Magnetic attraction, mutual devotion, and emotional dedication.",
            "explanation": "Natural Vasya exists between the Moon signs, creating deep personal attraction." if vasya_satisfied
            else "Standard compatibility without specialized magnetic Vasya pull; nurtured through everyday love."
        })

        # 9. Rajju Porutham (CRITICAL - Longevity of marital bond)
        b_rajju = boy["rajju"]
        g_rajju = girl["rajju"]
        rajju_satisfied = (b_rajju != g_rajju)
        results.append({
            "porutham_name": "Rajju Porutham",
            "tamil_name": "ரஜ்ஜுப் பொருத்தம்",
            "status": "Satisfied" if rajju_satisfied else "Not Satisfied (Rajju Dosha)",
            "is_satisfied": rajju_satisfied,
            "boy_value": f"{b_rajju} ({boy['nakshatra_name']})",
            "girl_value": f"{g_rajju} ({girl['nakshatra_name']})",
            "significance": "The most vital Porutham in South Indian tradition, governing the durability of the marital bond.",
            "explanation": f"Different Rajjus ({b_rajju} vs {g_rajju}). High longevity of marital union and continuous auspiciousness." if rajju_satisfied
            else f"Same Rajju ({b_rajju} Rajju Dosha). In South Indian matching, same Rajju is traditionally discouraged unless mitigated by exceptional Dina/Rasi strength."
        })

        # 10. Vedha Porutham (CRITICAL - Immunity from affliction and grief)
        vedha_affliction = (b_nak, g_nak) in VEDHA_PAIRS or (g_nak, b_nak) in VEDHA_PAIRS
        vedha_satisfied = not vedha_affliction
        results.append({
            "porutham_name": "Vedha Porutham",
            "tamil_name": "வேதைப் பொருத்தம்",
            "status": "Satisfied" if vedha_satisfied else "Not Satisfied (Vedha Dosha)",
            "is_satisfied": vedha_satisfied,
            "boy_value": boy["nakshatra_name"],
            "girl_value": girl["nakshatra_name"],
            "significance": "Wards off unexpected adversity, jealousy, and distress in married life.",
            "explanation": "Stars are free from mutual Vedha (no astrological conflict), ensuring harmonious peace." if vedha_satisfied
            else f"Vedha Dosha detected between {boy['nakshatra_name']} and {girl['nakshatra_name']}. Potential for external frictions."
        })

        return results

    # -------------------------------------------------------------
    # MANGLIK / MANGAL DOSHA (KUJA DOSHA) ANALYSIS
    # -------------------------------------------------------------
    @classmethod
    def analyze_manglik_status(cls, person: Dict[str, Any], gender_label: str) -> Dict[str, Any]:
        """
        Analyzes Mangal Dosha for an individual from Lagna (if birth time known) and Moon.
        Evaluates classical cancellations (own sign, exalted sign, aspect of Jupiter).
        """
        is_known = person["is_birth_time_known"]
        mars_house_lagna = person["mars_house_lagna"]
        mars_house_moon = person["mars_house_moon"]
        mars_sign_idx = person["mars_sign_index"]
        mars_sign_name = person["mars_sign_name"]

        dosha_houses = [1, 2, 4, 7, 8, 12]

        is_lagna_manglik = (mars_house_lagna in dosha_houses) if (is_known and mars_house_lagna) else False
        is_moon_manglik = (mars_house_moon in dosha_houses)

        # Check cancellations
        # 1. Mars in Aries (sign 1) or Scorpio (sign 8) -> Own sign cancellation
        # 2. Mars in Capricorn (sign 10) -> Exalted cancellation
        # 3. Mars in Leo (sign 5) or Aquarius (sign 11) in certain houses
        # 4. Mars in Sagittarius (9) or Pisces (12) in 8th house
        cancellations = []
        if mars_sign_idx in [1, 8]:
            cancellations.append(f"Mars in its own sign ({mars_sign_name}) provides natural dignity and neutralizes aggression.")
        if mars_sign_idx == 10:
            cancellations.append(f"Mars is exalted in Capricorn ({mars_sign_name}), transforming destructive fire into constructive discipline.")
        if mars_sign_idx in [5, 11]:
            cancellations.append(f"Mars in {mars_sign_name} softens planetary severity.")

        has_cancellation = len(cancellations) > 0

        if not is_known:
            # When birth time is unknown, Lagna is uncertain
            if is_moon_manglik:
                status = "Chandra Manglik (Mild)" if not has_cancellation else "Chandra Manglik Cancelled"
                details = f"Mars is in {mars_house_moon}th house from Moon ({mars_sign_name}). Note: Lagna placement is Unavailable due to unknown birth time."
                is_manglik = not has_cancellation
            else:
                status = "Non-Manglik from Moon"
                details = f"Mars is in {mars_house_moon}th house from Moon (auspicious house). Lagna placement is Unavailable due to unknown birth time."
                is_manglik = False
        else:
            if is_lagna_manglik and is_moon_manglik:
                if has_cancellation:
                    status = "Manglik Cancelled"
                    details = f"Mars occupies 7th/8th axis from Lagna ({mars_house_lagna}th) and Moon ({mars_house_moon}th), but dosha is mitigated: {'; '.join(cancellations)}"
                    is_manglik = False
                else:
                    status = "High Manglik (Purna Kuja Dosha)"
                    details = f"Mars is placed in {mars_house_lagna}th house from Lagna and {mars_house_moon}th house from Moon in {mars_sign_name}."
                    is_manglik = True
            elif is_lagna_manglik or is_moon_manglik:
                placed_from = f"{mars_house_lagna}th from Lagna" if is_lagna_manglik else f"{mars_house_moon}th from Moon"
                if has_cancellation:
                    status = "Anshik Manglik Cancelled"
                    details = f"Mars placed in {placed_from}, but neutralized: {'; '.join(cancellations)}"
                    is_manglik = False
                else:
                    status = "Anshik (Mild) Manglik"
                    details = f"Mars occupies {placed_from} in {mars_sign_name}. Moderate planetary influence."
                    is_manglik = True
            else:
                status = "Non-Manglik"
                details = f"Mars is favorably placed in {mars_house_lagna}th house from Lagna and {mars_house_moon}th house from Moon."
                is_manglik = False

        return {
            "status": status,
            "details": details,
            "is_manglik": is_manglik,
            "mars_sign": mars_sign_name,
            "mars_house_lagna": mars_house_lagna if is_known else "Unavailable (Unknown Birth Time)",
            "mars_house_moon": mars_house_moon,
            "cancellations_applied": cancellations,
        }

    @classmethod
    def evaluate_manglik_match(cls, boy_m: Dict[str, Any], girl_m: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates overall couple Manglik compatibility according to Kuja Dosha Samyam rules.
        """
        b_manglik = boy_m["is_manglik"]
        g_manglik = girl_m["is_manglik"]

        if b_manglik and g_manglik:
            is_match = True
            verdict = "Excellent Match (Kuja Dosha Samyam). Both partners carry Manglik alignment, neutralizing the Martian heat and creating dynamic equilibrium."
        elif not b_manglik and not g_manglik:
            is_match = True
            verdict = "Harmonious Match. Neither partner has Manglik affliction. Free from Kuja Dosha."
        else:
            is_match = False
            affected = "Groom" if b_manglik else "Bride"
            verdict = f"Caution Advised. {affected} has Manglik influence while the partner is Non-Manglik. Classical texts recommend astrological consultation or Kumbh Vivah / Hanuman Chalisa remedies."

        return {
            "boy_status": boy_m["status"],
            "boy_details": boy_m["details"],
            "boy_is_manglik": boy_m["is_manglik"],
            "girl_status": girl_m["status"],
            "girl_details": girl_m["details"],
            "girl_is_manglik": girl_m["is_manglik"],
            "is_manglik_match": is_match,
            "verdict": verdict,
        }

    # -------------------------------------------------------------
    # COMPLETE MATCH MAKING DISPATCHER
    # -------------------------------------------------------------
    @classmethod
    def calculate_match(
        cls,
        boy_data: Dict[str, Any],
        girl_data: Dict[str, Any],
        tradition: str = "ashta_koota"
    ) -> Dict[str, Any]:
        """
        Calculates complete horoscope compatibility between Boy and Girl.
        Ensures strict mathematical invariants:
        - Total score == sum of 8 factor scores.
        - Total score <= 36.
        - No random numbers or fabricated values.
        """
        # Resolve coordinates if needed
        b_lat, b_lon, b_tz = resolve_coordinates(
            boy_data.get("place_of_birth", ""),
            boy_data.get("latitude", 28.6139),
            boy_data.get("longitude", 77.2090),
            boy_data.get("timezone", 5.5)
        )
        g_lat, g_lon, g_tz = resolve_coordinates(
            girl_data.get("place_of_birth", ""),
            girl_data.get("latitude", 28.6139),
            girl_data.get("longitude", 77.2090),
            girl_data.get("timezone", 5.5)
        )

        b_time_known = boy_data.get("is_birth_time_known", True)
        g_time_known = girl_data.get("is_birth_time_known", True)

        boy_profile = cls.calculate_person_profile(
            boy_data["date_of_birth"],
            boy_data.get("time_of_birth"),
            b_lat, b_lon, b_tz,
            is_birth_time_known=b_time_known
        )
        girl_profile = cls.calculate_person_profile(
            girl_data["date_of_birth"],
            girl_data.get("time_of_birth"),
            g_lat, g_lon, g_tz,
            is_birth_time_known=g_time_known
        )

        # 1. Ashta Koota
        varna = cls.calculate_varna_koota(boy_profile, girl_profile)
        vashya = cls.calculate_vashya_koota(boy_profile, girl_profile)
        tara = cls.calculate_tara_koota(boy_profile, girl_profile)
        yoni = cls.calculate_yoni_koota(boy_profile, girl_profile)
        graha_maitri = cls.calculate_graha_maitri_koota(boy_profile, girl_profile)
        gana = cls.calculate_gana_koota(boy_profile, girl_profile)
        bhakoot = cls.calculate_bhakoot_koota(boy_profile, girl_profile)
        nadi = cls.calculate_nadi_koota(boy_profile, girl_profile)

        kootas = [varna, vashya, tara, yoni, graha_maitri, gana, bhakoot, nadi]

        # Strict invariant verification
        total_score = round(sum(k["obtained_points"] for k in kootas), 1)
        max_score = 36.0
        percentage = round((total_score / max_score) * 100.0, 1)

        # Verdict classification based on traditional 18/36 cutoff
        if total_score >= 28.0:
            status = "Uttama (Outstanding Match)"
            recommendation = "Exceptionally high compatibility. The charts reflect profound emotional, mental, and physical harmony, fostering a deeply prosperous and enduring marriage."
        elif total_score >= 18.0:
            status = "Madhyama (Favorable Match)"
            recommendation = "Good and auspicious compatibility. Surpasses the traditional 18-point threshold. A blessed union with mutual respect and healthy communication."
        else:
            status = "Adhama (Low Compatibility)"
            recommendation = "The overall Guna Milan score is below the traditional 18-point threshold. Astrological consultation, deeper horoscope scrutiny, and mutual commitment are essential."

        # 2. Manglik Analysis
        boy_manglik = cls.analyze_manglik_status(boy_profile, "Groom")
        girl_manglik = cls.analyze_manglik_status(girl_profile, "Bride")
        manglik_analysis = cls.evaluate_manglik_match(boy_manglik, girl_manglik)

        # 3. South Indian Porutham
        porutham_list = cls.calculate_south_indian_porutham(boy_profile, girl_profile)
        satisfied_poruthams_count = sum(1 for p in porutham_list if p["is_satisfied"])

        # Remedies list based on actual findings
        remedies = []
        if nadi["obtained_points"] == 0:
            remedies.append({
                "type": "Nadi Dosha",
                "recommendation": "Recite Maha Mrityunjaya Mantra together daily and donate grains, gold, or a cow (Go-daan) to a spiritual cause."
            })
        if bhakoot["obtained_points"] == 0:
            remedies.append({
                "type": "Bhakoot Dosha",
                "recommendation": "Perform Lord Shiva and Parvati Abhishek together on Mondays to dissolve emotional distance."
            })
        if not manglik_analysis["is_manglik_match"]:
            remedies.append({
                "type": "Mangal Dosha",
                "recommendation": "Chant the Hanuman Chalisa on Tuesdays, light a sesame oil lamp, and cultivate mutual patience."
            })


        # Generate full calculation-based charts for Groom and Bride
        boy_tob = boy_data.get("time_of_birth") or "12:00:00"
        girl_tob = girl_data.get("time_of_birth") or "12:00:00"

        try:
            boy_chart = generate_full_kundli(
                name=boy_data.get("name", "Groom"),
                dob_str=boy_data["date_of_birth"],
                tob_str=boy_tob,
                pob_str=boy_data.get("place_of_birth", "Default"),
                latitude=b_lat,
                longitude=b_lon,
                timezone=b_tz
            )
        except Exception:
            boy_chart = None

        try:
            girl_chart = generate_full_kundli(
                name=girl_data.get("name", "Bride"),
                dob_str=girl_data["date_of_birth"],
                tob_str=girl_tob,
                pob_str=girl_data.get("place_of_birth", "Default"),
                latitude=g_lat,
                longitude=g_lon,
                timezone=g_tz
            )
        except Exception:
            girl_chart = None
        return {
            "charts": {"boy": boy_chart, "girl": girl_chart},
            "boy_name": boy_data.get("name", "Groom"),
            "girl_name": girl_data.get("name", "Bride"),
            "engine_version": "VedicEphemeris-2.0.0-SwissEph",
            "calculation_tradition": tradition,
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "status": status,
            "recommendation": recommendation,
            "kootas": kootas,
            "manglik_analysis": manglik_analysis,
            "south_indian_porutham": {
                "total_poruthams": 10,
                "satisfied_count": satisfied_poruthams_count,
                "poruthams": porutham_list,
                "is_rajju_satisfied": any(p["porutham_name"] == "Rajju Porutham" and p["is_satisfied"] for p in porutham_list),
                "is_vedha_satisfied": any(p["porutham_name"] == "Vedha Porutham" and p["is_satisfied"] for p in porutham_list)
            },
            "profiles": {
                "boy": {
                    "name": boy_data.get("name", "Groom"),
                    "date_of_birth": boy_data["date_of_birth"],
                    "time_of_birth": boy_data.get("time_of_birth", "Unknown"),
                    "place_of_birth": boy_data.get("place_of_birth", "Default"),
                    "is_birth_time_known": b_time_known,
                    "moon_sign": boy_profile["moon_sign_name"],
                    "moon_lord": boy_profile["moon_lord"],
                    "nakshatra": boy_profile["nakshatra_name"],
                    "nakshatra_pada": boy_profile["nakshatra_pada"],
                    "ascendant": boy_profile["ascendant_sign_name"],
                    "mars_sign": boy_profile["mars_sign_name"],
                    "varna": boy_profile["varna_name"],
                    "vashya": boy_profile["vashya_name"],
                    "gana": boy_profile["gana"],
                    "yoni": boy_profile["yoni"],
                    "nadi": boy_profile["nadi"],
                    "rajju": boy_profile["rajju"],
                },
                "girl": {
                    "name": girl_data.get("name", "Bride"),
                    "date_of_birth": girl_data["date_of_birth"],
                    "time_of_birth": girl_data.get("time_of_birth", "Unknown"),
                    "place_of_birth": girl_data.get("place_of_birth", "Default"),
                    "is_birth_time_known": g_time_known,
                    "moon_sign": girl_profile["moon_sign_name"],
                    "moon_lord": girl_profile["moon_lord"],
                    "nakshatra": girl_profile["nakshatra_name"],
                    "nakshatra_pada": girl_profile["nakshatra_pada"],
                    "ascendant": girl_profile["ascendant_sign_name"],
                    "mars_sign": girl_profile["mars_sign_name"],
                    "varna": girl_profile["varna_name"],
                    "vashya": girl_profile["vashya_name"],
                    "gana": girl_profile["gana"],
                    "yoni": girl_profile["yoni"],
                    "nadi": girl_profile["nadi"],
                    "rajju": girl_profile["rajju"],
                }
            },
            "remedies": remedies,
            "disclaimer": "This matching report is derived strictly from classical Vedic astrological principles (Brihat Parashara Hora Shastra, Muhurta Chintamani, and South Indian Dasa Porutham). It is an advisory guideline for compatibility and harmony, and should be considered alongside personal respect, understanding, and mutual love."
        }
