"""
Authoritative Phone Number / Mobile Numerology Calculator.
Deterministic digit sum, compound reduction, digit frequency, positional analysis,
and personal compatibility with Life Path and Birth Day numbers.
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.life_path_calculator import LifePathCalculator
from app.services.birth_day_calculator import BirthDayNumberCalculator

class PhoneNumberCalculator:
    """
    Authoritative phone number analysis calculator.
    Default convention for Indian numbers: 10-digit subscriber number (excludes +91 / 0 prefix).
    """
    ALGORITHM_VERSION = "1.0.0"
    METHODOLOGY = "National 10-Digit Subscriber Numerology (Pythagorean/Vedic Planetary System)"

    # Planetary associations for numbers 1 to 9
    PLANETARY_RULERS = {
        1: {"planet": "Sun (Surya)", "element": "Fire", "energy": "Leadership, Independence, Authority"},
        2: {"planet": "Moon (Chandra)", "element": "Water", "energy": "Diplomacy, Sensitivity, Collaboration"},
        3: {"planet": "Jupiter (Guru)", "element": "Fire/Ether", "energy": "Wisdom, Expansion, Creative Expression"},
        4: {"planet": "Rahu (North Node)", "element": "Earth/Air", "energy": "Structure, Strategy, Unconventional Innovation"},
        5: {"planet": "Mercury (Budh)", "element": "Air", "energy": "Communication, Adaptability, Commerce, Networking"},
        6: {"planet": "Venus (Shukra)", "element": "Water/Earth", "energy": "Harmony, Aesthetics, Luxury, Care, Relationships"},
        7: {"planet": "Ketu (South Node)", "element": "Water/Fire", "energy": "Introspection, Research, Mysticism, Analytical Focus"},
        8: {"planet": "Saturn (Shani)", "element": "Earth", "energy": "Discipline, Endurance, Karma, Executive Authority"},
        9: {"planet": "Mars (Mangal)", "element": "Fire", "energy": "Action, Courage, Drive, Humanitarian Dynamism"},
    }

    # Planetary compatibility matrix for root numbers (1-9) vs personal numbers (1-9)
    COMPATIBILITY_MATRIX = {
        1: {
            "friendly": [1, 2, 3, 5, 9],
            "neutral": [4, 7],
            "challenging": [6, 8],
            "reason": "Sun resonates strongly with Mars, Jupiter, Moon, and Mercury; feels tension with Saturn (discipline vs ego) and Venus (duty vs indulgence)."
        },
        2: {
            "friendly": [1, 2, 3, 5],
            "neutral": [7, 8, 9],
            "challenging": [4, 6],
            "reason": "Moon thrives with solar clarity, Jovian wisdom, and Mercurial intellect; Rahu/Uranus (4) can create emotional unpredictability."
        },
        3: {
            "friendly": [1, 2, 3, 5, 9],
            "neutral": [7, 8],
            "challenging": [4, 6],
            "reason": "Jupiter expands harmoniously with Sun, Moon, and Mars; Venus (6) represents an opposing advisory philosophy (Asura Guru vs Deva Guru)."
        },
        4: {
            "friendly": [5, 6, 7, 8],
            "neutral": [1, 3],
            "challenging": [2, 4, 9],
            "reason": "Rahu aligns with practical Mercury, Venusian charm, and Saturnian structure; clashes with fiery impulsive Mars (9) and sensitive Moon (2)."
        },
        5: {
            "friendly": [1, 2, 3, 5, 6],
            "neutral": [7, 8, 9],
            "challenging": [4],
            "reason": "Mercury is the universal communicator, forming productive friendships with Sun, Venus, Moon, and Jupiter."
        },
        6: {
            "friendly": [4, 5, 6, 8],
            "neutral": [2, 7, 9],
            "challenging": [1, 3],
            "reason": "Venus excels with Mercury, Saturn, and Rahu for worldly manifestation; ideological rivalry with Jupiter (3) and ego clashes with Sun (1)."
        },
        7: {
            "friendly": [1, 4, 5, 7],
            "neutral": [2, 3, 6, 8],
            "challenging": [9],
            "reason": "Ketu supports reflective, scholarly, and technical disciplines; intense Mars (9) energy can disrupt quiet introspection."
        },
        8: {
            "friendly": [3, 4, 5, 6],
            "neutral": [7, 8],
            "challenging": [1, 2, 9],
            "reason": "Saturn rewards long-term consistency, Venusian harmony, and Mercurial commerce; direct conflicts with solar ego (1) and martial haste (9)."
        },
        9: {
            "friendly": [1, 2, 3, 7],
            "neutral": [5, 6, 8],
            "challenging": [4],
            "reason": "Mars thrives with solar vitality, lunar intuition, and Jupiterian wisdom; Rahu (4) brings friction and unpredictable disruption."
        },
    }

    @classmethod
    def clean_phone_number(cls, raw_number: str, country_code: str = "IN") -> Dict[str, Any]:
        """
        Extracts valid subscriber digits under the configured national convention.
        For Indian numbers (IN): Strips +91, 91, or leading 0 if 10 subscriber digits remain.
        """
        raw_str = str(raw_number).strip()
        digits_only = re.sub(r"[^\d]", "", raw_str)

        country = (country_code or "IN").upper().strip()
        subscriber_digits_str = digits_only

        if country == "IN":
            if len(digits_only) == 12 and digits_only.startswith("91"):
                subscriber_digits_str = digits_only[2:]
            elif len(digits_only) == 11 and digits_only.startswith("0"):
                subscriber_digits_str = digits_only[1:]
            elif len(digits_only) > 10 and digits_only.startswith("91"):
                subscriber_digits_str = digits_only[-10:]

        if len(subscriber_digits_str) < 7:
            raise ValueError(f"Phone number must contain at least 7 valid subscriber digits. Provided: '{raw_number}'.")

        digits_list = [int(d) for d in subscriber_digits_str]
        masked = "*" * max(0, len(subscriber_digits_str) - 4) + subscriber_digits_str[-4:] if len(subscriber_digits_str) >= 4 else subscriber_digits_str

        return {
            "raw_input": raw_number,
            "country_code": country,
            "subscriber_digits_str": subscriber_digits_str,
            "subscriber_digits": digits_list,
            "total_digits_count": len(digits_list),
            "masked_number": masked,
        }

    @classmethod
    def calculate_root_and_trace(cls, digits: List[int]) -> Dict[str, Any]:
        """
        Computes compound digit sum and step-by-step reduction to root number (1-9).
        Integer arithmetic only.
        """
        compound_total = sum(digits)
        trace_steps = [compound_total]

        current = compound_total
        while current > 9:
            step_sum = sum(int(c) for c in str(current))
            trace_steps.append(step_sum)
            current = step_sum

        root_number = current

        return {
            "compound_total": compound_total,
            "reduction_trace": trace_steps,
            "root_number": root_number,
        }

    @classmethod
    def analyze_digit_patterns(cls, digits: List[int]) -> Dict[str, Any]:
        """
        Computes digit frequencies (0-9), repeated digits, missing digits, and positional digits.
        """
        frequency = {d: 0 for d in range(10)}
        for d in digits:
            frequency[d] += 1

        repeated_digits = []
        for d in range(10):
            if frequency[d] > 1:
                repeated_digits.append({
                    "digit": d,
                    "count": frequency[d],
                    "intensity": "Moderate (2x)" if frequency[d] == 2 else ("High (3x)" if frequency[d] == 3 else f"Dominant ({frequency[d]}x)")
                })

        missing_digits = [d for d in range(10) if frequency[d] == 0]
        present_digits = [d for d in range(10) if frequency[d] > 0]

        first_digit = digits[0] if digits else 0
        last_digit = digits[-1] if digits else 0
        last_two_str = "".join(str(d) for d in digits[-2:]) if len(digits) >= 2 else str(last_digit)
        last_two_compound = sum(int(c) for c in last_two_str)

        zero_count = frequency.get(0, 0)

        return {
            "frequency_table": {str(k): v for k, v in frequency.items()},
            "present_digits": present_digits,
            "missing_digits": missing_digits,
            "repeated_digits": repeated_digits,
            "first_digit": first_digit,
            "last_digit": last_digit,
            "last_two_digits": last_two_str,
            "last_two_compound": last_two_compound,
            "zero_count": zero_count,
        }

    @classmethod
    def evaluate_personal_compatibility(
        cls,
        mobile_root: int,
        dob: Optional[str] = None,
        system: str = "pythagorean"
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates compatibility of mobile root with user's Life Path & Birth Day numbers.
        Returns None if DOB is not provided.
        """
        if not dob or not str(dob).strip():
            return None

        clean_dob = str(dob).strip()

        try:
            lp_res = LifePathCalculator.calculate(clean_dob, system=system)
            life_path_num = lp_res.get("life_path_number", 1)
        except Exception:
            life_path_num = 1

        try:
            bd_res = BirthDayNumberCalculator.calculate(clean_dob, system=system)
            birth_day_num = bd_res.get("reduced_root") or bd_res.get("birth_day_number", 1)
        except Exception:
            birth_day_num = 1

        def reduce_root(n: int) -> int:
            while n > 9:
                n = sum(int(c) for c in str(n))
            return n

        lp_single = reduce_root(life_path_num)
        bd_single = reduce_root(birth_day_num)

        root_rules = cls.COMPATIBILITY_MATRIX.get(mobile_root, {})
        friendly = root_rules.get("friendly", [])
        neutral = root_rules.get("neutral", [])
        challenging = root_rules.get("challenging", [])
        reason = root_rules.get("reason", "")

        def classify(target_num: int) -> str:
            if target_num in friendly:
                return "friendly"
            elif target_num in challenging:
                return "challenging"
            return "neutral"

        lp_status = classify(lp_single)
        bd_status = classify(bd_single)

        if lp_status == "friendly" and bd_status == "friendly":
            overall_category = "Highly Harmonious"
            overall_code = "friendly"
            score_index = 95
        elif lp_status == "challenging" and bd_status == "challenging":
            overall_category = "Tension & Dynamic Growth"
            overall_code = "challenging"
            score_index = 55
        elif "friendly" in (lp_status, bd_status) and "challenging" not in (lp_status, bd_status):
            overall_category = "Harmonious & Supportive"
            overall_code = "friendly"
            score_index = 85
        elif "challenging" in (lp_status, bd_status):
            overall_category = "Mixed Alignment"
            overall_code = "neutral"
            score_index = 68
        else:
            overall_category = "Balanced & Neutral"
            overall_code = "neutral"
            score_index = 75

        return {
            "date_of_birth": clean_dob,
            "life_path_number": life_path_num,
            "birth_day_number": birth_day_num,
            "mobile_root_number": mobile_root,
            "life_path_compatibility": {
                "number": life_path_num,
                "status": lp_status,
                "status_label": "Harmonious Alignment" if lp_status == "friendly" else ("Challenging Aspect" if lp_status == "challenging" else "Neutral Balance"),
            },
            "birth_day_compatibility": {
                "number": birth_day_num,
                "status": bd_status,
                "status_label": "Harmonious Alignment" if bd_status == "friendly" else ("Challenging Aspect" if bd_status == "challenging" else "Neutral Balance"),
            },
            "overall_category": overall_category,
            "overall_code": overall_code,
            "rule_based_resonance_index": score_index,
            "astrological_explanation": reason,
        }

    @classmethod
    def calculate_full(
        cls,
        phone_number: str,
        country_code: str = "IN",
        dob: Optional[str] = None,
        system: str = "pythagorean"
    ) -> Dict[str, Any]:
        """
        Executes full authoritative calculation and pattern breakdown.
        """
        cleaned = cls.clean_phone_number(phone_number, country_code=country_code)
        digits = cleaned["subscriber_digits"]

        root_trace = cls.calculate_root_and_trace(digits)
        patterns = cls.analyze_digit_patterns(digits)
        compatibility = cls.evaluate_personal_compatibility(root_trace["root_number"], dob=dob, system=system)
        planetary = cls.PLANETARY_RULERS.get(root_trace["root_number"], {})

        return {
            "calculation_status": "completed",
            "algorithm_version": cls.ALGORITHM_VERSION,
            "methodology": cls.METHODOLOGY,
            "raw_input": cleaned["raw_input"],
            "country_code": cleaned["country_code"],
            "masked_number": cleaned["masked_number"],
            "subscriber_digits_str": cleaned["subscriber_digits_str"],
            "subscriber_digits": digits,
            "total_digits_count": cleaned["total_digits_count"],
            "compound_total": root_trace["compound_total"],
            "reduction_trace": root_trace["reduction_trace"],
            "root_number": root_trace["root_number"],
            "planetary_ruler": planetary,
            "digit_patterns": patterns,
            "personal_compatibility": compatibility,
        }
