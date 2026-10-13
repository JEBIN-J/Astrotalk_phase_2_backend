"""
Authoritative Remedies and Fixes Rule Engine.
Evaluates validated user profile numbers against database-driven published rules
to recommend personalized, ethical, zero-cost traditional remedies.
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

logger = logging.getLogger(__name__)

class RemedyRuleEngine:
    """
    Deterministic, auditable rule engine for numerology remedies.
    Zero random values. Every recommendation is traceable to a documented rule
    and reviewed database content.
    """

    def __init__(self):
        self.lp_calc = LifePathCalculator()
        self.bd_calc = BirthDayNumberCalculator()
        self.py_calc = PersonalYearCalculator()
        self.missing_calc = MissingNumbersCalculator()
        self.soul_calc = PersonalitySoulAnalyzer()

    def evaluate(
        self,
        dob: str,
        birth_name: Optional[str] = None,
        system_code: str = "pythagorean",
        category_filter: Optional[str] = None,
        focus_area_filter: Optional[str] = None,
        target_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluates the user's validated profile numbers against active remedy rules.
        """
        current_year = target_year or datetime.now().year

        # 1. Calculate profile numbers
        lp_res = self.lp_calc.calculate(dob)
        lp_num = lp_res.get("life_path_number")

        bd_res = self.bd_calc.calculate(dob)
        bd_num = bd_res.get("birth_day_number")
        bd_reduced = bd_res.get("reduced_root") or bd_num

        py_res = self.py_calc.calculate(dob, current_year)
        py_num = py_res.get("personal_year_number")

        missing_numbers = []
        present_numbers = []
        soul_urge_num = None
        personality_num = None

        if birth_name and birth_name.strip():
            try:
                mn_res = self.missing_calc.analyze(birth_name)
                missing_numbers = mn_res.get("missing_numbers", [])
                present_numbers = mn_res.get("present_numbers", [])
            except Exception as e:
                logger.warning(f"Error analyzing missing numbers for remedies: {e}")

            try:
                ps_res = self.soul_calc.analyze(birth_name)
                soul_urge_num = ps_res.get("soul_urge", {}).get("soul_urge_number")
                personality_num = ps_res.get("personality", {}).get("personality_number")
            except Exception as e:
                logger.warning(f"Error analyzing soul urge for remedies: {e}")

        profile_summary = {
            "birth_name": birth_name.strip() if birth_name else None,
            "date_of_birth": dob,
            "evaluated_year": current_year,
            "life_path_number": lp_num,
            "birth_day_number": bd_num,
            "birth_day_reduced": bd_reduced,
            "personal_year_number": py_num,
            "missing_numbers": missing_numbers,
            "present_numbers": present_numbers,
            "soul_urge_number": soul_urge_num,
            "personality_number": personality_num,
        }

        # 2. Fetch published rules and actions for the system
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    r.id as rule_id,
                    r.rule_code,
                    r.rule_description,
                    r.input_number_type,
                    r.condition_type,
                    r.condition_value,
                    r.priority,
                    r.rule_version,
                    a.remedy_id,
                    a.applicability_reason_template,
                    a.display_order,
                    rem.remedy_code,
                    rem.title,
                    rem.category,
                    rem.focus_area,
                    rem.traditional_association,
                    rem.explanation,
                    rem.instructions,
                    rem.precautions,
                    rem.affirmation,
                    rem.symbolic_color,
                    rem.symbolic_day,
                    rem.estimated_cost_category,
                    rem.is_optional,
                    rem.content_version
                FROM numerology_remedy_rules r
                JOIN numerology_remedy_systems s ON r.system_id = s.id
                JOIN numerology_remedy_rule_actions a ON a.rule_id = r.id
                JOIN numerology_remedies rem ON a.remedy_id = rem.id
                WHERE s.system_code = ?
                  AND r.publication_status = 'published'
                  AND rem.publication_status = 'published'
                  AND s.is_active = 1
                ORDER BY r.priority DESC, a.display_order ASC
            """, (system_code,))
            rows = cursor.fetchall()
        finally:
            conn.close()

        # 3. Rule Evaluation & Deduplication
        matched_remedies_map: Dict[str, Dict[str, Any]] = {}
        rule_evaluation_trace = []
        rules_evaluated_set = set()

        for row in rows:
            rule_code = row["rule_code"]
            input_type = row["input_number_type"]
            cond_type = row["condition_type"]
            cond_val = row["condition_value"]
            rem_code = row["remedy_code"]

            # Determine match
            matched = False
            actual_val = None

            if input_type == "life_path":
                actual_val = lp_num
                if cond_type == "equals" and str(lp_num) == str(cond_val):
                    matched = True
            elif input_type == "birth_day":
                actual_val = bd_num
                if cond_type == "equals" and (str(bd_num) == str(cond_val) or str(bd_reduced) == str(cond_val)):
                    matched = True
            elif input_type == "missing_number":
                actual_val = missing_numbers
                try:
                    c_int = int(cond_val)
                    if c_int in missing_numbers:
                        matched = True
                        actual_val = c_int
                except ValueError:
                    pass
            elif input_type == "personal_year":
                actual_val = py_num
                if cond_type == "equals" and str(py_num) == str(cond_val):
                    matched = True
            elif input_type == "soul_urge":
                actual_val = soul_urge_num
                if soul_urge_num and cond_type == "equals" and str(soul_urge_num) == str(cond_val):
                    matched = True

            # Record in audit trace
            if rule_code not in rules_evaluated_set:
                rules_evaluated_set.add(rule_code)
                rule_evaluation_trace.append({
                    "rule_code": rule_code,
                    "description": row["rule_description"],
                    "input_number_type": input_type,
                    "condition": f"{cond_type} {cond_val}",
                    "actual_value": actual_val,
                    "status": "matched" if matched else "not_matched"
                })

            if matched:
                template = row["applicability_reason_template"]
                formatted_reason = template.replace("{value}", str(actual_val)).replace("{number}", str(actual_val))

                instructions = []
                try:
                    instructions = json.loads(row["instructions"])
                except Exception:
                    instructions = [row["instructions"]]

                if rem_code not in matched_remedies_map:
                    matched_remedies_map[rem_code] = {
                        "id": row["remedy_id"],
                        "remedy_code": rem_code,
                        "title": row["title"],
                        "category": row["category"],
                        "focus_area": row["focus_area"],
                        "traditional_association": row["traditional_association"],
                        "explanation": row["explanation"],
                        "instructions": instructions,
                        "precautions": row["precautions"],
                        "affirmation": row["affirmation"],
                        "symbolic_color": row["symbolic_color"],
                        "symbolic_day": row["symbolic_day"],
                        "estimated_cost_category": row["estimated_cost_category"],
                        "is_optional": bool(row["is_optional"]),
                        "content_version": row["content_version"],
                        "matched_by_rules": [{
                            "rule_code": rule_code,
                            "input_type": input_type,
                            "matched_value": actual_val,
                            "applicability_reason": formatted_reason
                        }],
                        "primary_reason": formatted_reason,
                        "priority": row["priority"]
                    }
                else:
                    # Append additional rule reason
                    matched_remedies_map[rem_code]["matched_by_rules"].append({
                        "rule_code": rule_code,
                        "input_type": input_type,
                        "matched_value": actual_val,
                        "applicability_reason": formatted_reason
                    })

        all_matched_remedies = list(matched_remedies_map.values())
        all_matched_remedies.sort(key=lambda x: x["priority"], reverse=True)

        # 4. Filter by category or focus area if requested
        filtered_remedies = all_matched_remedies
        if category_filter and category_filter.lower() != "all":
            c_target = category_filter.lower()
            filtered_remedies = [r for r in filtered_remedies if r["category"].lower() == c_target]

        if focus_area_filter and focus_area_filter.lower() != "all":
            f_target = focus_area_filter.lower()
            filtered_remedies = [r for r in filtered_remedies if r["focus_area"].lower() == f_target]

        # Calculate category counts
        category_counts = {}
        for r in all_matched_remedies:
            c = r["category"]
            category_counts[c] = category_counts.get(c, 0) + 1

        return {
            "status": "success",
            "calculation_status": "completed",
            "system": system_code,
            "system_name": "Pythagorean Numerology" if system_code == "pythagorean" else "Vedic Numerology",
            "algorithm_version": "1.0.0",
            "profile_summary": profile_summary,
            "total_matched_remedies": len(all_matched_remedies),
            "filtered_remedies_count": len(filtered_remedies),
            "active_category_filter": category_filter or "all",
            "active_focus_area_filter": focus_area_filter or "all",
            "category_counts": category_counts,
            "remedies": filtered_remedies,
            "rule_evaluation_trace": rule_evaluation_trace,
            "safety_notice": "All suggested remedies are traditional voluntary practices and reflection exercises. They carry zero financial cost and do not substitute for certified professional medical, legal, or financial counseling."
        }
