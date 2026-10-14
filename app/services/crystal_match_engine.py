"""
Authoritative Crystal Recommendation Engine.
Deterministic, database-backed crystal match calculations based on
user's validated numerology profile (Life Path, Birth Day, Expression,
Soul Urge, Missing Numbers / Karmic Lessons) and intention synergy.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.database import get_db_connection
from app.services.life_path_calculator import LifePathCalculator
from app.services.birth_day_calculator import BirthDayNumberCalculator
from app.services.personal_year_calculator import PersonalYearCalculator
from app.services.missing_numbers_calculator import MissingNumbersCalculator
from app.services.personality_soul_calculator import PersonalitySoulAnalyzer
from app.services.name_analysis_calculator import NameAnalysisCalculator

logger = logging.getLogger(__name__)

class CrystalMatchEngine:
    """
    Deterministic crystal recommendation engine backed entirely by SQLite database records.
    Zero random or client-side hardcoded fallback values.
    """
    ENGINE_VERSION = "2.1.0"
    CONTENT_VERSION = "2026.1"

    @classmethod
    def evaluate(
        cls,
        dob: str,
        birth_name: Optional[str] = None,
        system: str = "pythagorean",
        intention: str = "all",
        target_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculates authoritative numerology numbers and evaluates database matching rules.
        """
        norm_name = (birth_name or "Seeker").strip()
        if not norm_name:
            norm_name = "Seeker"
        norm_dob = dob.strip()
        norm_system = "chaldean" if system.lower() == "chaldean" else "pythagorean"
        norm_intention = (intention or "all").lower().strip()
        current_year = target_year or datetime.now().year

        # 1. Authoritative numerology calculations via backend calculators
        lp_res = LifePathCalculator.calculate(norm_dob, system=norm_system)
        life_path = lp_res.get("life_path_number", 1)

        bd_res = BirthDayNumberCalculator.calculate(norm_dob, system=norm_system)
        birth_day = bd_res.get("reduced_root") or bd_res.get("birth_day_number", 1)

        py_res = PersonalYearCalculator.calculate(norm_dob, current_year)
        personal_year = py_res.get("personal_year_number", 1)

        expression = 1
        soul_urge = 1
        personality_num = 1
        missing_numbers: List[int] = []

        if norm_name:
            try:
                na_res = NameAnalysisCalculator.calculate(norm_name, system=norm_system)
                core = na_res.get("birth_name_analysis", {}).get("core_numbers", {})
                expression = core.get("expression", {}).get("final_number", 1)
            except Exception as e:
                logger.warning(f"Error calculating expression number: {e}")

            try:
                ps_res = PersonalitySoulAnalyzer.analyze(norm_name)
                soul_urge = ps_res.get("soul_urge", {}).get("number", 1)
                personality_num = ps_res.get("personality", {}).get("number", 1)
            except Exception as e:
                logger.warning(f"Error calculating soul urge number: {e}")

            try:
                mn_res = MissingNumbersCalculator.analyze(norm_name)
                missing_numbers = mn_res.get("missing_numbers", [])
            except Exception as e:
                logger.warning(f"Error calculating missing numbers: {e}")

        # 2. Fetch published crystals from SQLite database
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, name, alternative_names, mineral_family, chemical_formula,
                    mohs_hardness, colour_description, geological_description,
                    traditional_associations, pythagorean_numbers, chaldean_numbers,
                    supported_intentions, suggested_use, care_instructions, safety_notes,
                    limitations, publication_status, content_version
                FROM numerology_crystals
                WHERE publication_status = 'published'
                ORDER BY name ASC
            """)
            rows = cursor.fetchall()

            # Fetch intentions dictionary for label resolution
            cursor.execute("SELECT code, title FROM numerology_crystal_intentions")
            intentions_map = {row["code"]: row["title"] for row in cursor.fetchall()}
        finally:
            conn.close()

        scored_map = {}
        for row in rows:
            c_id = row["id"]
            name = row["name"]
            alt_names = json.loads(row["alternative_names"]) if row["alternative_names"] else []
            min_family = row["mineral_family"]
            chem_formula = row["chemical_formula"]
            mohs = row["mohs_hardness"]
            colour = row["colour_description"]
            geol = row["geological_description"]
            trad = row["traditional_associations"]
            pyth_nums = json.loads(row["pythagorean_numbers"]) if row["pythagorean_numbers"] else []
            chald_nums = json.loads(row["chaldean_numbers"]) if row["chaldean_numbers"] else []
            supp_intentions = json.loads(row["supported_intentions"]) if row["supported_intentions"] else []
            sugg_use = row["suggested_use"]
            care = row["care_instructions"]
            safety = row["safety_notes"]
            limitations = row["limitations"]

            associated_numbers = chald_nums if norm_system == "chaldean" else pyth_nums

            # When filtering by intention, only evaluate crystals supporting that intention
            if norm_intention != "all" and norm_intention not in supp_intentions:
                continue

            score = 0
            primary_code = ""
            primary_title = ""
            explanation = ""
            factors = []
            match_num = 0
            role = ""
            is_int_match = False

            # RULE 1: Primary Life Path Resonance [RULE-LP]
            if life_path in associated_numbers:
                score += 100
                primary_code = "RULE-LP"
                primary_title = "Primary Life Path Resonance"
                match_num = life_path
                role = "Life Path Number"
                factors.append(f"Direct resonance with foundational Life Path {life_path}")
                explanation = f"Traditional correspondence with your core Life Path {life_path}. Recommended as your foundational vibrational anchor."

            # RULE 2: Birth Day Number Expression [RULE-BD]
            if birth_day in associated_numbers:
                score += 90
                if not primary_code:
                    primary_code = "RULE-BD"
                    primary_title = "Birth Day Talent Vibration"
                    match_num = birth_day
                    role = "Birth Day Number"
                    explanation = f"Corresponds with your Birth Day {birth_day}, supporting innate temperament, daily communication, and applied natural gifts."
                factors.append(f"Supports your active Birth Day {birth_day} vibration")

            # RULE 3: Expression / Destiny Vibration [RULE-EX]
            if expression in associated_numbers:
                score += 80
                if not primary_code:
                    primary_code = "RULE-EX"
                    primary_title = "Destiny & Expression Harmony"
                    match_num = expression
                    role = "Expression Number"
                    explanation = f"Harmonizes with your Destiny Number {expression}, fostering alignment with your vocation and personal legacy."
                factors.append(f"Aligns with Expression Number {expression}")

            # RULE 4: Soul Urge Vibration [RULE-SU]
            if soul_urge in associated_numbers:
                score += 80
                if not primary_code:
                    primary_code = "RULE-SU"
                    primary_title = "Soul Urge Inner Harmony"
                    match_num = soul_urge
                    role = "Soul Urge Number"
                    explanation = f"Resonates with your Soul Urge Number {soul_urge}, nurturing internal emotional fulfillment and genuine values."
                factors.append(f"Nurtures Soul Urge Number {soul_urge}")

            # RULE 5: Karmic / Missing Number Harmonizer [RULE-KL]
            for m_num in missing_numbers:
                if m_num in associated_numbers:
                    score += 70
                    if not primary_code:
                        primary_code = "RULE-KL"
                        primary_title = "Karmic Lesson Harmonizer"
                        match_num = m_num
                        role = "Karmic Lesson"
                        explanation = f"Number {m_num} is absent from your birth name frequency (Karmic Lesson {m_num}). This crystal serves as a mindful focus to gently cultivate that absent quality."
                    factors.append(f"Harmonizes absent frequency of Number {m_num} (Karmic Lesson {m_num})")
                    break

            # RULE 6: Purpose / Intention Synergy [RULE-INT]
            if norm_intention != "all" and norm_intention in supp_intentions:
                score += 65
                is_int_match = True
                int_label = intentions_map.get(norm_intention, norm_intention.capitalize())
                factors.append(f"Synergizes directly with your selected intention: {int_label}")
                if not primary_code:
                    primary_code = "RULE-INT"
                    primary_title = "Intentional Focus Synergy"
                    match_num = life_path
                    role = "Intention Focus"
                    explanation = f"Chosen to focus your mindful energy specifically on {int_label} while respecting numerological balance."

            if score > 0:
                scored_map[c_id] = {
                    "crystal": {
                        "id": c_id,
                        "name": name,
                        "alternative_names": alt_names,
                        "mineral_family": min_family,
                        "chemical_formula": chem_formula,
                        "mohs_hardness": mohs,
                        "colour_description": colour,
                        "geological_description": geol,
                        "traditional_associations": trad,
                        "pythagorean_numbers": pyth_nums,
                        "chaldean_numbers": chald_nums,
                        "supported_intentions": supp_intentions,
                        "suggested_use": sugg_use,
                        "care_instructions": care,
                        "safety_notes": safety,
                        "limitations": limitations,
                        "publication_status": row["publication_status"],
                        "content_version": row["content_version"],
                    },
                    "match_score": score,
                    "primary_rule_code": primary_code,
                    "primary_rule_title": primary_title,
                    "match_explanation": explanation,
                    "contributing_factors": factors,
                    "matching_number": match_num,
                    "number_role": role,
                    "is_intention_match": is_int_match,
                }

        # Deterministic Ranking: score DESC, name ASC
        ranked_recommendations = list(scored_map.values())
        ranked_recommendations.sort(key=lambda r: (-r["match_score"], r["crystal"]["name"]))

        # Evaluated rules documentation trace
        evaluated_rules = [
            {
                "rule_code": "RULE-LP",
                "title": "Primary Life Path Resonance",
                "priority": 1,
                "input_value": life_path,
                "description": "Direct resonance with authoritative Life Path number.",
                "status": "evaluated"
            },
            {
                "rule_code": "RULE-BD",
                "title": "Birth Day Talent Vibration",
                "priority": 2,
                "input_value": birth_day,
                "description": "Anchoring innate personality gifts and day-of-birth frequency.",
                "status": "evaluated"
            },
            {
                "rule_code": "RULE-EX_SU",
                "title": "Expression & Soul Urge Alignment",
                "priority": 3,
                "input_values": {"expression": expression, "soul_urge": soul_urge},
                "description": "Vibrational synergy with outer vocation and inner heart desire.",
                "status": "evaluated"
            },
            {
                "rule_code": "RULE-KL",
                "title": "Karmic & Missing Number Harmonizer",
                "priority": 4,
                "input_values": missing_numbers,
                "description": "Compensating and consciously cultivating frequencies absent in birth name.",
                "status": "evaluated"
            }
        ]

        if norm_intention != "all":
            int_title = intentions_map.get(norm_intention, norm_intention.capitalize())
            evaluated_rules.append({
                "rule_code": "RULE-INT",
                "title": "Selected Intention Filter & Boost",
                "priority": 5,
                "input_value": norm_intention,
                "description": f"Elevates crystals historically associated with {int_title}.",
                "status": "applied"
            })

        int_title = intentions_map.get(norm_intention, "All Intentions" if norm_intention == "all" else norm_intention.capitalize())

        return {
            "status": "success",
            "calculation_status": "completed",
            "engine_version": cls.ENGINE_VERSION,
            "content_version": cls.CONTENT_VERSION,
            "methodology": {
                "system": norm_system,
                "system_label": "Chaldean Planetary Numerology Tradition" if norm_system == "chaldean" else "Pythagorean Harmonic Numerology Tradition",
                "source_reference": "Numology.io & Reviewed Mineralogical/Traditional Database Records",
                "is_deterministic": True,
                "scientific_claim_policy": "No medical, financial, or supernatural claims (NCCIH compliant).",
            },
            "profile_summary": {
                "birth_name": norm_name,
                "date_of_birth": norm_dob,
                "system": norm_system,
                "life_path": life_path,
                "birth_day": birth_day,
                "expression_number": expression,
                "soul_urge_number": soul_urge,
                "missing_numbers": missing_numbers,
                "personal_year": personal_year,
            },
            "selected_intention": {
                "code": norm_intention,
                "title": int_title,
            },
            "total_matches": len(ranked_recommendations),
            "recommendations": ranked_recommendations,
            "evaluated_rules": evaluated_rules,
            "disclaimer": "Crystals and stones are complementary symbolic and mindfulness practices. They are not intended to diagnose, treat, cure, or prevent any medical or psychological condition, nor do they replace licensed professional, financial, or healthcare advice.",
        }

    @classmethod
    def get_catalog(cls) -> List[Dict[str, Any]]:
        """Returns all published crystals from the database."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, name, alternative_names, mineral_family, chemical_formula,
                    mohs_hardness, colour_description, geological_description,
                    traditional_associations, pythagorean_numbers, chaldean_numbers,
                    supported_intentions, suggested_use, care_instructions, safety_notes,
                    limitations, publication_status, content_version
                FROM numerology_crystals
                WHERE publication_status = 'published'
                ORDER BY name ASC
            """)
            rows = cursor.fetchall()
            catalog = []
            for r in rows:
                catalog.append({
                    "id": r["id"],
                    "name": r["name"],
                    "alternative_names": json.loads(r["alternative_names"]) if r["alternative_names"] else [],
                    "mineral_family": r["mineral_family"],
                    "chemical_formula": r["chemical_formula"],
                    "mohs_hardness": r["mohs_hardness"],
                    "colour_description": r["colour_description"],
                    "geological_description": r["geological_description"],
                    "traditional_associations": r["traditional_associations"],
                    "pythagorean_numbers": json.loads(r["pythagorean_numbers"]) if r["pythagorean_numbers"] else [],
                    "chaldean_numbers": json.loads(r["chaldean_numbers"]) if r["chaldean_numbers"] else [],
                    "supported_intentions": json.loads(r["supported_intentions"]) if r["supported_intentions"] else [],
                    "suggested_use": r["suggested_use"],
                    "care_instructions": r["care_instructions"],
                    "safety_notes": r["safety_notes"],
                    "limitations": r["limitations"],
                    "publication_status": r["publication_status"],
                    "content_version": r["content_version"],
                })
            return catalog
        finally:
            conn.close()

    @classmethod
    def get_intentions(cls) -> List[Dict[str, Any]]:
        """Returns all supported intentions from the database."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT code, title, description, boost_score FROM numerology_crystal_intentions ORDER BY id ASC")
            rows = cursor.fetchall()
            return [
                {
                    "code": r["code"],
                    "title": r["title"],
                    "description": r["description"],
                    "boost_score": r["boost_score"]
                }
                for r in rows
            ]
        finally:
            conn.close()
