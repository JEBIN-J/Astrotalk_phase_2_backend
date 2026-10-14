"""
Authoritative Advanced Numerology Compatibility Engine.
Deterministic, Database-Driven Multi-Factor Compatibility Calculator.

Supported Factors:
  1. Life Path / Destiny Number (from complete Date of Birth)
  2. Birth Number / Mulank (from Day of Month)
  3. Name / Expression Number (under Chaldean & Pythagorean systems)
  4. Soul Urge / Heart's Desire (from vowels)
  5. Personality Number (from consonants)

Relationship Types Supported:
  - romantic
  - marriage
  - friendship
  - business
  - family

Features:
  - Independent individual profile calculation for Person A & Person B.
  - Symmetrical canonical rule matching (min(a,b), max(a,b)).
  - Database-driven interpretations and guidance from SQLite dataset.db.
  - Transparent dynamic weight normalization for omitted optional factors.
  - Strict absence of random numbers, fake percentages, or arbitrary predictions.
"""

from datetime import datetime
import unicodedata
import sqlite3
import json
import os
from typing import Dict, Any, List, Tuple, Optional


class AdvancedCompatibilityCalculator:
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

    # -------------------------------------------------------------------------
    # ARITHMETIC REDUCTIONS
    # -------------------------------------------------------------------------
    @classmethod
    def reduce_to_single_digit(cls, n: int) -> Tuple[int, List[int]]:
        """
        Reduces an integer to a single digit (1-9) by summing its digits repeatedly.
        Returns (reduced_root, reduction_steps_list).
        """
        steps = [n]
        curr = n
        while curr > 9:
            s = sum(int(d) for d in str(curr))
            steps.append(s)
            curr = s
        return curr, steps

    @classmethod
    def clean_name(cls, name: str) -> str:
        """
        Normalizes a name string: decomposes accents (NFKD), strips non-alphabetic chars,
        and converts to uppercase.
        """
        if not name:
            return ""
        norm = unicodedata.normalize('NFKD', name)
        clean = "".join(c.upper() for c in norm if c.isalpha())
        return clean

    # -------------------------------------------------------------------------
    # INDIVIDUAL FACTOR CALCULATIONS
    # -------------------------------------------------------------------------
    @classmethod
    def calculate_birth_number(cls, dob_str: str) -> Dict[str, Any]:
        """
        Calculates Birth Number (Mulank) from the calendar day of birth.
        Example: 14 August 1992 -> day 14 -> 1 + 4 = 5.
        """
        try:
            dt = datetime.strptime(dob_str.strip(), "%Y-%m-%d")
        except Exception:
            raise ValueError(f"Invalid date format for birth date: '{dob_str}'. Expected YYYY-MM-DD.")

        day = dt.day
        root, steps = cls.reduce_to_single_digit(day)
        digits = [int(c) for c in str(day)]
        digits_str = " + ".join(str(d) for d in digits) if len(digits) > 1 else str(day)

        return {
            "day": day,
            "root": root,
            "digits": digits,
            "calculation_formula": f"{digits_str} = {root}" if len(digits) > 1 else f"{day} = {root}",
            "reduction_steps": steps
        }

    @classmethod
    def calculate_life_path(cls, dob_str: str) -> Dict[str, Any]:
        """
        Calculates Life Path / Destiny Number from the full Date of Birth.
        Example: 14 August 1992 (1992-08-14) -> 1+4+0+8+1+9+9+2 = 34 -> 3+4 = 7.
        """
        try:
            dt = datetime.strptime(dob_str.strip(), "%Y-%m-%d")
        except Exception:
            raise ValueError(f"Invalid date format for birth date: '{dob_str}'. Expected YYYY-MM-DD.")

        dob_digits_str = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}"
        digits = [int(c) for c in dob_digits_str]
        compound = sum(digits)
        root, steps = cls.reduce_to_single_digit(compound)

        return {
            "dob": dob_str,
            "digits": digits,
            "digits_sum_formula": " + ".join(str(d) for d in digits) + f" = {compound}",
            "compound_total": compound,
            "root": root,
            "reduction_steps": [compound] + [s for s in steps if s != compound]
        }

    @classmethod
    def calculate_name_numbers(cls, name_str: str, system: str = "pythagorean") -> Dict[str, Any]:
        """
        Calculates Name Number (Expression), Soul Urge (Vowels), and Personality (Consonants).
        """
        sys_clean = system.strip().lower()
        mapping = cls.CHALDEAN_MAP if sys_clean == "chaldean" else cls.PYTHAGOREAN_MAP
        system_name = "Chaldean" if sys_clean == "chaldean" else "Pythagorean"

        clean_letters = cls.clean_name(name_str)
        if not clean_letters:
            raise ValueError(f"Name '{name_str}' contains no valid alphabetic characters for numerological calculation.")

        breakdown = []
        total_sum = 0
        vowel_sum = 0
        consonant_sum = 0
        vowels_list = []
        consonants_list = []

        for ch in clean_letters:
            val = mapping.get(ch, 0)
            is_vowel = ch in cls.VOWELS
            breakdown.append({
                "letter": ch,
                "value": val,
                "is_vowel": is_vowel
            })
            total_sum += val
            if is_vowel:
                vowel_sum += val
                vowels_list.append((ch, val))
            else:
                consonant_sum += val
                consonants_list.append((ch, val))

        name_root, name_steps = cls.reduce_to_single_digit(total_sum)
        soul_root, soul_steps = (cls.reduce_to_single_digit(vowel_sum) if vowel_sum > 0 else (0, []))
        pers_root, pers_steps = (cls.reduce_to_single_digit(consonant_sum) if consonant_sum > 0 else (0, []))

        return {
            "system": system_name,
            "clean_name": clean_letters,
            "letter_breakdown": breakdown,
            "name_number": {
                "compound_total": total_sum,
                "root": name_root,
                "reduction_steps": name_steps,
                "formula": " + ".join(f"{b['letter']}({b['value']})" for b in breakdown) + f" = {total_sum} -> Root {name_root}"
            },
            "soul_urge": {
                "compound_total": vowel_sum,
                "root": soul_root,
                "reduction_steps": soul_steps,
                "vowels_count": len(vowels_list),
                "is_available": vowel_sum > 0,
                "formula": (" + ".join(f"{ch}({v})" for ch, v in vowels_list) + f" = {vowel_sum} -> Root {soul_root}") if vowels_list else "None"
            },
            "personality_number": {
                "compound_total": consonant_sum,
                "root": pers_root,
                "reduction_steps": pers_steps,
                "consonants_count": len(consonants_list),
                "is_available": consonant_sum > 0,
                "formula": (" + ".join(f"{ch}({v})" for ch, v in consonants_list) + f" = {consonant_sum} -> Root {pers_root}") if consonants_list else "None"
            }
        }

    # -------------------------------------------------------------------------
    # INDEPENDENT PROFILE BUILDER
    # -------------------------------------------------------------------------
    @classmethod
    def build_individual_profile(cls, name: str, dob: Optional[str] = None, system: str = "pythagorean") -> Dict[str, Any]:
        """
        Builds the complete numerology profile for a single person.
        Calculates Mulank, Life Path, Name Number, Soul Urge, and Personality.
        """
        profile: Dict[str, Any] = {
            "display_name": name.strip() if name else "Anonymous",
            "system": "Chaldean" if system.lower() == "chaldean" else "Pythagorean",
            "has_dob": bool(dob and str(dob).strip()),
            "numbers": {},
            "calculation_steps": {}
        }

        # 1. Name Numbers
        if name and name.strip():
            try:
                name_res = cls.calculate_name_numbers(name, system=system)
                profile["numbers"]["name_number"] = name_res["name_number"]["root"]
                profile["numbers"]["soul_urge"] = name_res["soul_urge"]["root"]
                profile["numbers"]["personality_number"] = name_res["personality_number"]["root"]
                profile["calculation_steps"]["name"] = name_res
            except Exception as e:
                profile["numbers"]["name_number"] = None
                profile["numbers"]["soul_urge"] = None
                profile["numbers"]["personality_number"] = None
                profile["calculation_steps"]["name_error"] = str(e)
        else:
            profile["numbers"]["name_number"] = None
            profile["numbers"]["soul_urge"] = None
            profile["numbers"]["personality_number"] = None

        # 2. Date of Birth Numbers
        if dob and str(dob).strip():
            try:
                birth_res = cls.calculate_birth_number(dob)
                life_res = cls.calculate_life_path(dob)
                profile["dob"] = dob.strip()
                profile["numbers"]["birth_number"] = birth_res["root"]
                profile["numbers"]["life_path"] = life_res["root"]
                profile["calculation_steps"]["birth_number"] = birth_res
                profile["calculation_steps"]["life_path"] = life_res
            except Exception as e:
                profile["numbers"]["birth_number"] = None
                profile["numbers"]["life_path"] = None
                profile["calculation_steps"]["dob_error"] = str(e)
        else:
            profile["dob"] = None
            profile["numbers"]["birth_number"] = None
            profile["numbers"]["life_path"] = None

        return profile

    # -------------------------------------------------------------------------
    # MULTI-FACTOR COMPARISON & REPORT GENERATOR
    # -------------------------------------------------------------------------
    @classmethod
    def calculate_advanced_compatibility(
        cls,
        person_a_name: str,
        person_b_name: str,
        person_a_dob: Optional[str] = None,
        person_b_dob: Optional[str] = None,
        relationship_type: str = "romantic",
        system: str = "pythagorean"
    ) -> Dict[str, Any]:
        """
        Executes full multi-factor compatibility evaluation between Person A and Person B.
        Enforces canonical ordering (min, max) for symmetric rule matching.
        Retrieves database-backed interpretations and applies transparent weight normalization.
        """
        valid_rel_types = {"romantic", "marriage", "friendship", "business", "family"}
        rel_clean = relationship_type.strip().lower()
        if rel_clean not in valid_rel_types:
            rel_clean = "romantic"

        sys_clean = "chaldean" if system.strip().lower() == "chaldean" else "pythagorean"

        # 1. Calculate Individual Profiles Independently
        profile_a = cls.build_individual_profile(person_a_name, person_a_dob, system=sys_clean)
        profile_b = cls.build_individual_profile(person_b_name, person_b_dob, system=sys_clean)

        conn = cls._get_db_connection()
        cur = conn.cursor()

        # 2. Retrieve Factor Weights for the Selected Relationship Type
        cur.execute("""
            SELECT factor_code, factor_weight, minimum_score, maximum_score, formula_version
            FROM compatibility_scoring_config
            WHERE relationship_type = ? AND is_active = 1
        """, (rel_clean,))
        weight_rows = cur.fetchall()
        weights_map = {row["factor_code"]: float(row["factor_weight"]) for row in weight_rows}
        if not weights_map:
            # Fallback default configuration if database config table query returned empty
            weights_map = {
                "life_path": 35.0,
                "birth_number": 25.0,
                "name_number": 15.0,
                "soul_urge": 15.0,
                "personality_number": 10.0
            }

        factor_definitions = [
            ("life_path", "Life Path / Destiny", "Core spiritual direction and lifelong values"),
            ("birth_number", "Birth Number (Mulank)", "Instinctive temperament and daily behavioral cadence"),
            ("name_number", "Name / Expression", "Outer worldly communication and interactive synergy"),
            ("soul_urge", "Soul Urge (Heart's Desire)", "Private emotional longing and vulnerable inner desires"),
            ("personality_number", "Personality Number", "External social demeanor and conversational impressions")
        ]

        factor_results = []
        included_weights_sum = 0.0
        weighted_score_accum = 0.0
        included_factors_count = 0
        excluded_factors = []

        for factor_code, factor_title, factor_desc in factor_definitions:
            num_a = profile_a["numbers"].get(factor_code)
            num_b = profile_b["numbers"].get(factor_code)

            if num_a is None or num_b is None:
                reason = "Missing Date of Birth" if factor_code in {"life_path", "birth_number"} else "Missing or incomplete Name input"
                excluded_factors.append({
                    "factor_code": factor_code,
                    "factor_title": factor_title,
                    "reason": reason,
                    "configured_weight": weights_map.get(factor_code, 0.0)
                })
                continue

            # Canonical order for symmetric rule lookup
            canon_a = min(num_a, num_b)
            canon_b = max(num_a, num_b)

            # Query database compatibility rule
            cur.execute("""
                SELECT compatibility_category, score_value, rule_explanation, rule_source
                FROM numerology_compatibility_rules
                WHERE factor_code = ? AND number_a = ? AND number_b = ? AND is_active = 1
                LIMIT 1
            """, (factor_code, canon_a, canon_b))
            rule_row = cur.fetchone()

            if not rule_row:
                # Query fallback with method_code = 'all'
                cur.execute("""
                    SELECT compatibility_category, score_value, rule_explanation, rule_source
                    FROM numerology_compatibility_rules
                    WHERE factor_code = ? AND number_a = ? AND number_b = ?
                    LIMIT 1
                """, (factor_code, canon_a, canon_b))
                rule_row = cur.fetchone()

            if rule_row:
                category = rule_row["compatibility_category"]
                score_val = int(rule_row["score_value"])
                rule_expl = rule_row["rule_explanation"]
                rule_src = rule_row["rule_source"]
            else:
                # Transparent unavailable status, never invent random scores
                category = "Indeterminate"
                score_val = 60
                rule_expl = f"No reviewed rule on record for {factor_title} pairing ({canon_a}, {canon_b})."
                rule_src = "Unreviewed"

            # Query database interpretation for this category and relationship type
            cur.execute("""
                SELECT title, short_explanation, detailed_explanation, strengths, potential_challenges, communication_guidance, practical_guidance
                FROM numerology_compatibility_interpretations
                WHERE factor_code = ? AND compatibility_category = ? AND relationship_type = ? AND is_active = 1
                LIMIT 1
            """, (factor_code, category, rel_clean))
            interp_row = cur.fetchone()

            if not interp_row:
                # Fallback to general interpretation
                cur.execute("""
                    SELECT title, short_explanation, detailed_explanation, strengths, potential_challenges, communication_guidance, practical_guidance
                    FROM numerology_compatibility_interpretations
                    WHERE compatibility_category = ? AND relationship_type = ? AND is_active = 1
                    LIMIT 1
                """, (category, rel_clean))
                interp_row = cur.fetchone()

            interp_data = {
                "title": interp_row["title"] if interp_row else f"{category} Resonance",
                "short_explanation": interp_row["short_explanation"] if interp_row else rule_expl,
                "detailed_explanation": interp_row["detailed_explanation"] if interp_row else rule_expl,
                "strengths": interp_row["strengths"] if interp_row else "Mutual understanding and authentic communication.",
                "potential_challenges": interp_row["potential_challenges"] if interp_row else "Occasional differences in personal rhythm.",
                "communication_guidance": interp_row["communication_guidance"] if interp_row else "Practice clear, non-defensive listening.",
                "practical_guidance": interp_row["practical_guidance"] if interp_row else "Maintain regular shared activities and personal boundaries."
            }

            f_weight = weights_map.get(factor_code, 20.0)
            included_weights_sum += f_weight
            weighted_score_accum += (score_val * f_weight)
            included_factors_count += 1

            factor_results.append({
                "factor_code": factor_code,
                "factor_title": factor_title,
                "description": factor_desc,
                "person_a_number": num_a,
                "person_b_number": num_b,
                "canonical_pair": [canon_a, canon_b],
                "compatibility_category": category,
                "score_value": score_val,
                "configured_weight": f_weight,
                "rule_explanation": rule_expl,
                "rule_source": rule_src,
                "interpretation": interp_data
            })

        conn.close()

        # 3. Transparent Dynamic Weight Normalization
        if included_weights_sum > 0:
            overall_score = round(weighted_score_accum / included_weights_sum)
            for f in factor_results:
                f["normalized_weight_percent"] = round((f["configured_weight"] / included_weights_sum) * 100, 1)
        else:
            overall_score = 0

        # Overall Category Mapping
        if overall_score >= 85:
            overall_category = "Natural Harmony"
            headline = "Exceptional vibrational harmony with effortless natural synergy."
        elif overall_score >= 70:
            overall_category = "Complementary Growth"
            headline = "Dynamic complementary balance that fosters mutual learning and maturity."
        elif overall_score >= 55:
            overall_category = "Neutral Balance"
            headline = "Adaptable resonance that thrives through conscious care and shared purpose."
        else:
            overall_category = "Dynamic Challenge"
            headline = "Contrasting vibrational perspectives that serve as catalysts for personal growth."

        # High-level Strengths and Growth Areas summary
        top_factors = sorted(factor_results, key=lambda x: x["score_value"], reverse=True)
        strengths_summary = [
            f"**{f['factor_title']} ({f['person_a_number']} & {f['person_b_number']}):** {f['rule_explanation']}"
            for f in top_factors if f["score_value"] >= 70
        ]
        growth_summary = [
            f"**{f['factor_title']} ({f['person_a_number']} & {f['person_b_number']}):** {f['rule_explanation']}"
            for f in top_factors if f["score_value"] < 70
        ]

        scoring_transparency = {
            "formula_name": "Normalized Weighted Factor Index (Deterministic Traditional Model)",
            "formula_expression": "Overall Index = Sum(Factor Score * Configured Weight) / Sum(Available Factor Weights)",
            "total_configured_factors": len(factor_definitions),
            "included_factors_count": included_factors_count,
            "included_weights_total": included_weights_sum,
            "excluded_factors": excluded_factors,
            "is_dynamically_normalized": len(excluded_factors) > 0,
            "normalization_note": (
                "Excluded factors were cleanly omitted from the calculation, and weights of available factors were re-normalized to 100%."
                if excluded_factors else "All 5 core factors were available and fully weighted."
            )
        }

        limitations_statement = (
            "Numerology is a traditional symbolic discipline and self-reflection system. "
            "It is not an empirical science or deterministic predictor of interpersonal success. "
            "Real relationship flourishing depends fundamentally on mutual respect, healthy boundaries, "
            "empathetic communication, and conscious commitment."
        )

        return {
            "status": "success",
            "relationship_type": rel_clean,
            "system": "Chaldean" if sys_clean == "chaldean" else "Pythagorean",
            "methodology_version": "2.0",
            "person_a": {
                "name": profile_a["display_name"],
                "dob": profile_a["dob"],
                "numbers": profile_a["numbers"],
                "calculation_steps": profile_a["calculation_steps"]
            },
            "person_b": {
                "name": profile_b["display_name"],
                "dob": profile_b["dob"],
                "numbers": profile_b["numbers"],
                "calculation_steps": profile_b["calculation_steps"]
            },
            "overall_harmony": {
                "score_index": overall_score,
                "category": overall_category,
                "headline": headline,
                "display_badge": f"{overall_score}/100 Harmony Index",
                "scale": "0 to 100 Conventional Resonance Index"
            },
            "factor_comparisons": factor_results,
            "strengths_summary": strengths_summary,
            "growth_areas_summary": growth_summary,
            "scoring_transparency": scoring_transparency,
            "limitations_statement": limitations_statement
        }

    # -------------------------------------------------------------------------
    # SAVED REPORTS REPOSITORY
    # -------------------------------------------------------------------------
    @classmethod
    def save_report(
        cls,
        user_id: Optional[str],
        relationship_type: str,
        system: str,
        person_a_label: str,
        person_b_label: str,
        calculated_data: Dict[str, Any]
    ) -> int:
        """
        Saves a generated compatibility report into saved_compatibility_reports table.
        Returns the inserted report id.
        """
        conn = cls._get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO saved_compatibility_reports
            (authorized_owner_user_id, relationship_type, selected_method, person_a_label, person_b_label, calculated_result_data, content_version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id or "guest",
            relationship_type,
            system,
            person_a_label,
            person_b_label,
            json.dumps(calculated_data),
            "2.0"
        ))
        report_id = cur.lastrowid
        conn.commit()
        conn.close()
        return report_id
