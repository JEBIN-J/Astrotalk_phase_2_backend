"""
Authoritative Child Numerology Calculator Engine.
Supports:
  - Birth Number / Mulank calculation from calendar day of birth.
  - Destiny Number / Bhagyank calculation from complete birth date (YYYY-MM-DD).
  - Name Number / Expression Number calculation under Chaldean and Pythagorean systems.
  - Soul Urge (Heart's Desire) and Personality Number calculations.
  - Candidate Name Analysis & Side-by-Side Comparison against Birth Date.
  - Parent-Child Numerology Compatibility.
  - Database-driven interpretation retrieval from SQLite dataset.db.
"""
from datetime import datetime
import unicodedata
import sqlite3
import json
import os
from typing import Dict, Any, List, Tuple, Optional

class ChildNumerologyCalculator:
    # 1. Pythagorean Letter Mapping (1-9)
    PYTHAGOREAN_MAP = {
        'A': 1, 'J': 1, 'S': 1,
        'B': 2, 'K': 2, 'T': 2,
        'C': 3, 'L': 3, 'U': 3,
        'D': 4, 'M': 4, 'V': 4,
        'E': 5, 'N': 5, 'W': 5,
        'F': 6, 'O': 6, 'X': 6,
        'G': 7, 'P': 7, 'Y': 7,
        'H': 8, 'Q': 8, 'Z': 8,
        'I': 9, 'R': 9
    }

    # 2. Chaldean Letter Mapping (1-8, 9 not assigned to letters)
    CHALDEAN_MAP = {
        'A': 1, 'I': 1, 'J': 1, 'Q': 1, 'Y': 1,
        'B': 2, 'K': 2, 'R': 2,
        'C': 3, 'G': 3, 'L': 3, 'S': 3,
        'D': 4, 'M': 4, 'T': 4,
        'E': 5, 'H': 5, 'N': 5, 'X': 5,
        'U': 6, 'V': 6, 'W': 6,
        'O': 7, 'Z': 7,
        'P': 8, 'F': 8
    }

    VOWELS = {'A', 'E', 'I', 'O', 'U'}

    @classmethod
    def _get_db_connection(cls):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def normalize_name(cls, name: str) -> str:
        if not name:
            return ""
        normalized = unicodedata.normalize('NFKD', name)
        ascii_text = normalized.encode('ASCII', 'ignore').decode('ASCII')
        return ascii_text.upper().strip()

    @classmethod
    def validate_dob(cls, dob_str: str) -> Tuple[datetime, str]:
        if not dob_str or not isinstance(dob_str, str):
            raise ValueError("Date of birth is required.")
        clean = dob_str.strip()
        try:
            dt = datetime.strptime(clean, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{clean}'. Date of birth must be in YYYY-MM-DD format.")
        if dt.year < 1850 or dt.year > 2100:
            raise ValueError("Birth year must be between 1850 and 2100.")
        return dt, clean

    # =========================================================================
    # A. BIRTH NUMBER / MULANK (Calendar day 1-31 -> reduced to 1-9)
    # =========================================================================
    @classmethod
    def calculate_birth_number(cls, dob_str: str) -> Dict[str, Any]:
        dt, clean_dob = cls.validate_dob(dob_str)
        day = dt.day

        steps = []
        reduction_trace = [day]
        val = day
        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            formula_str = " + ".join(str(c) for c in digits) + f" = {summed}"
            steps.append(formula_str)
            val = summed
            reduction_trace.append(val)

        return {
            "day": day,
            "birth_number": val,
            "reduction_trace": reduction_trace,
            "calculation_steps": steps,
            "methodology": "Day of Month integer reduction (Mulank)"
        }

    # =========================================================================
    # B. DESTINY NUMBER / BHAGYANK (Complete date YYYY-MM-DD -> 1-9)
    # =========================================================================
    @classmethod
    def calculate_destiny_number(cls, dob_str: str) -> Dict[str, Any]:
        dt, clean_dob = cls.validate_dob(dob_str)
        # Digits from Day, Month, Year
        # Example 2024-08-14: 1+4 + 0+8 + 2+0+2+4 = 21 -> 2+1 = 3
        day_digits = [int(c) for c in f"{dt.day:02d}"]
        month_digits = [int(c) for c in f"{dt.month:02d}"]
        year_digits = [int(c) for c in f"{dt.year:04d}"]

        all_digits = day_digits + month_digits + year_digits
        first_sum = sum(all_digits)

        steps = []
        digit_formula = " + ".join(str(d) for d in all_digits) + f" = {first_sum}"
        steps.append(digit_formula)

        reduction_trace = [first_sum]
        val = first_sum
        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            steps.append(" + ".join(str(c) for c in digits) + f" = {summed}")
            val = summed
            reduction_trace.append(val)

        return {
            "destiny_number": val,
            "compound_total": first_sum,
            "reduction_trace": reduction_trace,
            "calculation_steps": steps,
            "methodology": "Full Date Integer Summation (Bhagyank)"
        }

    # =========================================================================
    # C. NAME NUMBER / EXPRESSION NUMBER (Pythagorean & Chaldean)
    # =========================================================================
    @classmethod
    def calculate_name_number(cls, name: str, system: str = "pythagorean") -> Dict[str, Any]:
        clean_name = cls.normalize_name(name)
        if not clean_name:
            raise ValueError("Child name cannot be empty.")

        sys_code = "chaldean" if system.lower() == "chaldean" else "pythagorean"
        mapping = cls.CHALDEAN_MAP if sys_code == "chaldean" else cls.PYTHAGOREAN_MAP

        letter_breakdown = []
        vowel_values = []
        consonant_values = []
        all_values = []

        words = clean_name.split()
        word_breakdowns = []

        for w in words:
            word_chars = []
            word_sum = 0
            for ch in w:
                if ch in mapping:
                    val = mapping[ch]
                    is_v = ch in cls.VOWELS
                    char_info = {"letter": ch, "value": val, "is_vowel": is_v}
                    letter_breakdown.append(char_info)
                    word_chars.append(char_info)
                    word_sum += val
                    all_values.append(val)
                    if is_v:
                        vowel_values.append(val)
                    else:
                        consonant_values.append(val)

            word_breakdowns.append({
                "word": w,
                "letters": word_chars,
                "compound_total": word_sum
            })

        if not all_values:
            raise ValueError(f"No valid letters found in name '{name}' for numerology calculation.")

        compound_total = sum(all_values)

        # Reduce compound_total to root (1-9)
        reduction_trace = [compound_total]
        steps = []
        val = compound_total
        while val > 9:
            digits = [int(c) for c in str(val)]
            summed = sum(digits)
            steps.append(" + ".join(str(c) for c in digits) + f" = {summed}")
            val = summed
            reduction_trace.append(val)

        # Soul Urge (vowels)
        soul_urge_compound = sum(vowel_values) if vowel_values else 0
        s_val = soul_urge_compound
        s_trace = [s_val] if s_val > 0 else [0]
        while s_val > 9:
            s_val = sum(int(c) for c in str(s_val))
            s_trace.append(s_val)

        # Personality (consonants)
        personality_compound = sum(consonant_values) if consonant_values else 0
        p_val = personality_compound
        p_trace = [p_val] if p_val > 0 else [0]
        while p_val > 9:
            p_val = sum(int(c) for c in str(p_val))
            p_trace.append(p_val)

        return {
            "name": clean_name,
            "system": sys_code,
            "system_name": "Chaldean Sound System" if sys_code == "chaldean" else "Pythagorean System",
            "name_root": val,
            "compound_total": compound_total,
            "reduction_trace": reduction_trace,
            "calculation_steps": steps,
            "letter_breakdown": letter_breakdown,
            "word_breakdowns": word_breakdowns,
            "soul_urge": {
                "compound": soul_urge_compound,
                "root": s_val,
                "reduction_trace": s_trace
            },
            "personality": {
                "compound": personality_compound,
                "root": p_val,
                "reduction_trace": p_trace
            }
        }

    # =========================================================================
    # D. DATABASE INTERPRETATION RETRIEVAL
    # =========================================================================
    @classmethod
    def get_interpretation(cls, system: str, calc_type: str, number: int) -> Optional[Dict[str, Any]]:
        conn = cls._get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM child_numerology_interpretations
            WHERE system_code = ? AND calculation_type = ? AND number = ? AND is_active = 1
        """, (system, calc_type, number))
        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row["id"],
            "system_code": row["system_code"],
            "calculation_type": row["calculation_type"],
            "number": row["number"],
            "archetype": row["archetype"],
            "short_description": row["short_description"],
            "detailed_explanation": row["detailed_explanation"],
            "strengths": json.loads(row["strengths"]),
            "potential_challenges": json.loads(row["potential_challenges"]),
            "supportive_parenting_guidance": json.loads(row["supportive_parenting_guidance"]),
            "practical_learning_suggestions": json.loads(row["practical_learning_suggestions"]),
            "favourable_elements": json.loads(row["favourable_elements"]),
            "review_status": row["review_status"]
        }

    @classmethod
    def get_name_compatibility_rule(cls, name_root: int, ref_num: int) -> Dict[str, Any]:
        conn = cls._get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM child_name_compatibility_rules
            WHERE name_root = ? AND reference_number = ? AND is_active = 1
        """, (name_root, ref_num))
        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "name_root": row["name_root"],
                "reference_number": row["reference_number"],
                "compatibility_category": row["compatibility_category"],
                "resonance_score": row["resonance_score"],
                "explanation": row["explanation"]
            }

        return {
            "name_root": name_root,
            "reference_number": ref_num,
            "compatibility_category": "Supportive & Neutral",
            "resonance_score": 75,
            "explanation": f"Name Root {name_root} and Number {ref_num} form a steady, supportive vibrational foundation."
        }

    @classmethod
    def get_parent_child_rule(cls, parent_root: int, child_root: int) -> Dict[str, Any]:
        conn = cls._get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM parent_child_compatibility_rules
            WHERE parent_root = ? AND child_root = ? AND is_active = 1
        """, (parent_root, child_root))
        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "parent_root": row["parent_root"],
                "child_root": row["child_root"],
                "compatibility_category": row["compatibility_category"],
                "resonance_score": row["resonance_score"],
                "explanation": row["explanation"],
                "parenting_tip": row["parenting_tip"]
            }

        return {
            "parent_root": parent_root,
            "child_root": child_root,
            "compatibility_category": "Supportive Growth Bond",
            "resonance_score": 75,
            "explanation": f"Parent Root {parent_root} and Child Root {child_root} maintain a calm, adaptable relationship.",
            "parenting_tip": "Foster open, curious dialogue to celebrate each other's individual perspective."
        }

    # =========================================================================
    # E. FULL COMPREHENSIVE CHILD ANALYSIS REPORT
    # =========================================================================
    @classmethod
    def analyze_child(
        cls,
        child_name: str,
        dob_str: str,
        system: str = "pythagorean",
        parent_name: Optional[str] = None,
        parent_dob_str: Optional[str] = None
    ) -> Dict[str, Any]:
        sys_code = "chaldean" if system.lower() == "chaldean" else "pythagorean"

        # 1. Calculations
        birth_calc = cls.calculate_birth_number(dob_str)
        destiny_calc = cls.calculate_destiny_number(dob_str)
        name_calc = cls.calculate_name_number(child_name, system=sys_code)

        mulank = birth_calc["birth_number"]
        bhagyank = destiny_calc["destiny_number"]
        name_root = name_calc["name_root"]
        soul_urge_root = name_calc["soul_urge"]["root"]
        personality_root = name_calc["personality"]["root"]

        # 2. Database Interpretations
        birth_interp = cls.get_interpretation(sys_code, "birth_number", mulank)
        destiny_interp = cls.get_interpretation(sys_code, "destiny_number", bhagyank)
        name_interp = cls.get_interpretation(sys_code, "name_number", name_root)
        soul_urge_interp = cls.get_interpretation(sys_code, "soul_urge", soul_urge_root) if soul_urge_root > 0 else None
        personality_interp = cls.get_interpretation(sys_code, "personality_number", personality_root) if personality_root > 0 else None

        # 3. Name-to-Birth Compatibility
        name_vs_mulank = cls.get_name_compatibility_rule(name_root, mulank)
        name_vs_bhagyank = cls.get_name_compatibility_rule(name_root, bhagyank)

        combined_score = round((name_vs_mulank["resonance_score"] + name_vs_bhagyank["resonance_score"]) / 2)
        if combined_score >= 85:
            overall_name_harmony = "Highly Auspicious & Harmonious"
        elif combined_score >= 70:
            overall_name_harmony = "Balanced & Supportive"
        else:
            overall_name_harmony = "Dynamic & Energetically Challenging"

        # 4. Optional Parent-Child Compatibility
        parent_compatibility = None
        if parent_dob_str and parent_dob_str.strip():
            try:
                p_birth = cls.calculate_birth_number(parent_dob_str)
                p_destiny = cls.calculate_destiny_number(parent_dob_str)
                p_mulank = p_birth["birth_number"]
                p_bhagyank = p_destiny["destiny_number"]

                mulank_match = cls.get_parent_child_rule(p_mulank, mulank)
                bhagyank_match = cls.get_parent_child_rule(p_bhagyank, bhagyank)
                p_combined = round((mulank_match["resonance_score"] + bhagyank_match["resonance_score"]) / 2)

                parent_compatibility = {
                    "parent_name": parent_name.strip() if parent_name else "Parent",
                    "parent_dob": parent_dob_str.strip(),
                    "parent_birth_number": p_mulank,
                    "parent_destiny_number": p_bhagyank,
                    "mulank_harmony": mulank_match,
                    "bhagyank_harmony": bhagyank_match,
                    "overall_score": p_combined,
                    "overall_category": mulank_match["compatibility_category"]
                }
            except Exception:
                pass

        return {
            "success": True,
            "system": sys_code,
            "child_name": name_calc["name"],
            "dob": dob_str.strip(),
            "birth_number": birth_calc,
            "destiny_number": destiny_calc,
            "name_number": name_calc,
            "name_compatibility": {
                "overall_score": combined_score,
                "overall_category": overall_name_harmony,
                "vs_birth_number": name_vs_mulank,
                "vs_destiny_number": name_vs_bhagyank
            },
            "interpretations": {
                "birth_number": birth_interp,
                "destiny_number": destiny_interp,
                "name_number": name_interp,
                "soul_urge": soul_urge_interp,
                "personality_number": personality_interp
            },
            "parent_compatibility": parent_compatibility
        }

    # =========================================================================
    # F. CANDIDATE NAME COMPARISON ENGINE
    # =========================================================================
    @classmethod
    def compare_candidate_names(
        cls,
        candidate_names: List[str],
        dob_str: str,
        system: str = "pythagorean"
    ) -> Dict[str, Any]:
        if not candidate_names:
            raise ValueError("At least one candidate name is required for comparison.")

        birth_calc = cls.calculate_birth_number(dob_str)
        destiny_calc = cls.calculate_destiny_number(dob_str)
        mulank = birth_calc["birth_number"]
        bhagyank = destiny_calc["destiny_number"]

        sys_code = "chaldean" if system.lower() == "chaldean" else "pythagorean"
        results = []

        for name in candidate_names:
            clean = name.strip()
            if not clean:
                continue

            name_calc = cls.calculate_name_number(clean, system=sys_code)
            name_root = name_calc["name_root"]
            compound = name_calc["compound_total"]

            # Query rules
            vs_mulank = cls.get_name_compatibility_rule(name_root, mulank)
            vs_bhagyank = cls.get_name_compatibility_rule(name_root, bhagyank)
            score = round((vs_mulank["resonance_score"] + vs_bhagyank["resonance_score"]) / 2)

            # Get name archetype
            interp = cls.get_interpretation(sys_code, "name_number", name_root)
            archetype = interp["archetype"] if interp else f"Vibration {name_root}"
            short_desc = interp["short_description"] if interp else ""
            favourable = interp["favourable_elements"] if interp else {}

            results.append({
                "candidate_name": clean.upper(),
                "compound_total": compound,
                "name_root": name_root,
                "reduction_trace": name_calc["reduction_trace"],
                "calculation_steps": name_calc["calculation_steps"],
                "letter_breakdown": name_calc["letter_breakdown"],
                "archetype": archetype,
                "short_description": short_desc,
                "favourable_elements": favourable,
                "suitability_score": score,
                "harmony_category": vs_mulank["compatibility_category"],
                "mulank_harmony": vs_mulank,
                "bhagyank_harmony": vs_bhagyank
            })

        # Sort candidates deterministically by suitability score descending
        results.sort(key=lambda x: x["suitability_score"], reverse=True)

        return {
            "success": True,
            "dob": dob_str.strip(),
            "system": sys_code,
            "birth_number": birth_calc,
            "destiny_number": destiny_calc,
            "candidates_count": len(results),
            "candidates": results
        }
