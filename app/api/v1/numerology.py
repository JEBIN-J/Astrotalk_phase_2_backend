from app.services.numerology_chart_service import NumerologyChartService
from app.services.crystal_match_engine import CrystalMatchEngine
from app.services.remedy_rule_engine import RemedyRuleEngine
"""
Authoritative Numerology Blueprint and Life Path Controller.
Supports deterministic calculation, database-driven interpretations,
caching, strict validation, and authentication awareness.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.services.numerology_service import NumerologyService
from app.services.life_path_calculator import LifePathCalculator
from app.services.birth_day_calculator import BirthDayNumberCalculator
from app.services.personal_year_calculator import PersonalYearCalculator
from app.services.name_analysis_calculator import NameAnalysisCalculator
from app.services.personality_soul_calculator import PersonalitySoulAnalyzer
from app.services.missing_numbers_calculator import MissingNumbersCalculator
from app.services.numerology_repository import NumerologyRepository
from app.api.v1.auth import get_current_user

numerology_bp = Blueprint('numerology', __name__)

@numerology_bp.route("/profile", methods=["POST"])
def calculate_full_profile():
    try:
        data = request.get_json() or {}
        name = data.get("name", "")
        dob = data.get("dob", "")
        system = data.get("system", "pythagorean").lower()
        
        if system == "chaldean":
            result = NumerologyService.calculate_chaldean(name, dob)
        elif system == "vedic":
            result = NumerologyService.calculate_vedic(name, dob)
        else:
            result = NumerologyService.calculate_pythagorean(name, dob)
            
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 400
            
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@numerology_bp.route("/preview", methods=["GET", "POST"])
@numerology_bp.route("/live-preview", methods=["POST"])
def get_live_preview():
    """
    Authoritative live preview calculation endpoint for name numbers,
    date-of-birth derived numbers, alphabet mapping chart, and strict calendar validation.
    """
    try:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            name = data.get("name", "")
            dob = data.get("dob") or data.get("date_of_birth")
            day = data.get("day")
            month = data.get("month")
            year = data.get("year")
            system = data.get("system", "chaldean")
            gender = data.get("gender")
        else:
            name = request.args.get("name", "")
            dob = request.args.get("dob") or request.args.get("date_of_birth")
            day = request.args.get("day")
            month = request.args.get("month")
            year = request.args.get("year")
            system = request.args.get("system", "chaldean")
            gender = request.args.get("gender")

        parsed_day = int(day) if (day is not None and str(day).strip().isdigit()) else None
        parsed_month = int(month) if (month is not None and str(month).strip().isdigit()) else None
        parsed_year = int(year) if (year is not None and str(year).strip().isdigit()) else None

        result = NumerologyService.calculate_preview(
            name=name,
            dob_str=dob,
            day=parsed_day,
            month=parsed_month,
            year=parsed_year,
            system=system,
            gender=gender
        )

        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@numerology_bp.route("/profile/save", methods=["POST"])
def save_user_numerology_profile():
    """
    Saves user profile details and performs authoritative backend recalculation.
    Validates name (non-empty) and DOB strictly.
    """
    try:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        dob = (data.get("dob") or data.get("date_of_birth") or "").strip()
        system = (data.get("system") or "chaldean").lower().strip()
        gender = (data.get("gender") or "other").lower().strip()

        if not name:
            return jsonify({
                "status": "error",
                "error_code": "EMPTY_NAME",
                "message": "Full name cannot be empty."
            }), 400

        parts = dob.split("-")
        if len(parts) != 3:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_DATE_FORMAT",
                "message": "Date of birth must be in YYYY-MM-DD format."
            }), 400

        try:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            is_valid, err_msg, dt = NumerologyService.validate_date(y, m, d)
            if not is_valid:
                return jsonify({
                    "status": "error",
                    "error_code": "INVALID_DATE",
                    "message": err_msg or "Invalid calendar date."
                }), 400
        except ValueError:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_DATE_VALUES",
                "message": "Day, Month, and Year must be valid integers."
            }), 400

        if system == "chaldean":
            calc_result = NumerologyService.calculate_chaldean(name, dob)
        elif system == "vedic":
            calc_result = NumerologyService.calculate_vedic(name, dob)
        else:
            calc_result = NumerologyService.calculate_pythagorean(name, dob)

        current_user, _ = get_current_user()
        if current_user:
            current_user["name"] = name
            current_user["dob"] = dob
            current_user["gender"] = gender
            current_user["numerology_system"] = system

        preview = NumerologyService.calculate_preview(
            name=name,
            dob_str=dob,
            system=system,
            gender=gender
        )

        return jsonify({
            "status": "success",
            "message": "Profile saved and numerology blueprint calculated successfully.",
            "data": {
                "profile": {
                    "name": name,
                    "dob": dob,
                    "gender": gender,
                    "system": system
                },
                "preview": preview,
                "full_calculation": calc_result
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@numerology_bp.route("/life-path", methods=["GET", "POST"])
def get_life_path_report():
    """
    Production-ready Life Path calculation and interpretation endpoint.
    Retrieves DOB from authenticated user profile or validated input parameter.
    Authoritatively calculates Life Path using Pythagorean method.
    Retrieves reviewed, published interpretations from database.
    """
    try:
        # Check authentication optionally
        current_user, _ = get_current_user()
        user_id = current_user.get("id") if current_user else None

        # Extract parameters from query or JSON payload
        dob = None
        system = "pythagorean"
        name = "Seeker"

        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            dob = payload.get("dob") or payload.get("date_of_birth")
            system = payload.get("system", "pythagorean")
            name = payload.get("name") or name
        else:
            dob = request.args.get("dob") or request.args.get("date_of_birth")
            system = request.args.get("system", "pythagorean")
            name = request.args.get("name") or name

        # If DOB not provided directly, try user's profile if authenticated
        if not dob and current_user:
            dob = current_user.get("dob") or current_user.get("date_of_birth")

        if not dob:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_DATE_OF_BIRTH",
                "message": "Date of birth is required to calculate Life Path number. Please provide a valid date or complete your profile."
            }), 400

        dob = str(dob).strip()

        # Check cache
        cache_key = NumerologyRepository.get_cache_key(user_id, dob, system)
        cached = NumerologyRepository.get_cached_result(cache_key)
        if cached:
            return jsonify(cached), 200

        # Calculate authoritative Life Path & trace
        try:
            calc_result = LifePathCalculator.calculate(dob, system=system)
        except ValueError as ve:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_DATE_FORMAT",
                "message": str(ve)
            }), 400

        lp_number = calc_result["life_path_number"]

        # Retrieve published interpretation from database
        interpretation = NumerologyRepository.get_published_interpretation(system, lp_number)
        if not interpretation and system != "pythagorean":
            interpretation = NumerologyRepository.get_published_interpretation("pythagorean", lp_number)

        if not interpretation:
            return jsonify({
                "status": "error",
                "error_code": "CONTENT_UNAVAILABLE",
                "message": f"Published interpretation for Life Path {lp_number} is currently unavailable.",
                "life_path_number": lp_number,
                "calculation_trace": calc_result["calculation_trace"]
            }), 404

        response_data = {
            "status": "success",
            "calculation_status": "completed",
            "user_name": name,
            "life_path_number": lp_number,
            "number_title": interpretation["number_title"],
            "core_theme": interpretation["core_theme"],
            "is_master_number": calc_result["is_master_number"],
            "date_of_birth_used": dob,
            "calculation_system": interpretation["system_code"],
            "method_version": "1.0.0",
            "content_version": interpretation["content_version"],
            "calculation_trace": calc_result["calculation_trace"],
            "interpretation": {
                "overview": interpretation["overview"],
                "strengths": interpretation["strengths"],
                "challenges": interpretation["challenges"],
                "relationships": interpretation["relationship_interpretation"],
                "career": interpretation["career_interpretation"],
                "personal_growth": interpretation["personal_growth_guidance"],
                "sections": interpretation["sections"]
            },
            "timestamp": datetime.now().isoformat()
        }

        # Store in cache
        NumerologyRepository.set_cached_result(cache_key, response_data)

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "SERVER_ERROR",
            "message": "An unexpected error occurred while calculating Life Path number."
        }), 500


@numerology_bp.route("/content-status", methods=["GET"])
def get_content_status():
    """
    Returns content completeness report for administrative verification.
    """
    system = request.args.get("system", "pythagorean")
    report = NumerologyRepository.check_content_completeness(system)
    return jsonify({
        "status": "success",
        "system": system,
        "completeness_report": report
    }), 200

@numerology_bp.route("/birth-day", methods=["GET", "POST"])
def get_birth_day_report():
    """
    Authoritative Birth Day Number calculation and interpretation endpoint.
    Primary convention: Preserves the exact calendar day from 1 to 31.
    Calculates optional secondary reduced root.
    Retrieves reviewed, published interpretation from database.
    """
    try:
        current_user, _ = get_current_user()
        user_id = current_user.get("id") if current_user else None

        dob = None
        system = "pythagorean"
        name = "Seeker"

        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            dob = payload.get("dob") or payload.get("date_of_birth")
            system = payload.get("system", "pythagorean")
            name = payload.get("name") or name
        else:
            dob = request.args.get("dob") or request.args.get("date_of_birth")
            system = request.args.get("system", "pythagorean")
            name = request.args.get("name") or name

        if not dob and current_user:
            dob = current_user.get("dob") or current_user.get("date_of_birth")

        if not dob:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_DATE_OF_BIRTH",
                "message": "Date of birth is required to calculate Birth Day number."
            }), 400

        dob = str(dob).strip()
        cache_key = f"birthday_{user_id or 'guest'}_{dob}_{system}"
        cached = NumerologyRepository.get_cached_result(cache_key)
        if cached:
            return jsonify(cached), 200

        try:
            calc_result = BirthDayNumberCalculator.calculate(dob, system=system)
        except ValueError as ve:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_DATE_FORMAT",
                "message": str(ve)
            }), 400

        day_num = calc_result["birth_day_number"]
        reduced_root = calc_result["reduced_root"]

        interpretation = NumerologyRepository.get_birth_day_interpretation(system, day_num)
        if not interpretation and system != "pythagorean":
            interpretation = NumerologyRepository.get_birth_day_interpretation("pythagorean", day_num)

        if not interpretation:
            return jsonify({
                "status": "error",
                "error_code": "CONTENT_UNAVAILABLE",
                "message": f"Published interpretation for Birth Day {day_num} is currently unavailable.",
                "birth_day_number": day_num,
                "reduced_root": reduced_root,
                "calculation_trace": calc_result["calculation_trace"]
            }), 404

        response_data = {
            "status": "success",
            "calculation_status": "completed",
            "user_name": name,
            "birth_day_number": day_num,
            "reduced_root": reduced_root,
            "number_title": interpretation["number_title"],
            "core_theme": interpretation["core_theme"],
            "is_master_day": calc_result["is_master_day"],
            "date_of_birth_used": dob,
            "calculation_system": interpretation["system_code"],
            "method_version": calc_result["method_version"],
            "content_version": interpretation["content_version"],
            "calculation_trace": calc_result["calculation_trace"],
            "interpretation": {
                "overview": interpretation["overview"],
                "strengths": interpretation["strengths"],
                "challenges": interpretation["challenges"],
                "personality": interpretation["personality_interpretation"],
                "relationships": interpretation["relationship_interpretation"],
                "career": interpretation["career_interpretation"],
                "personal_growth": interpretation["personal_growth_guidance"],
                "quick_summary": interpretation["quick_summary"],
                "sections": interpretation["sections"]
            },
            "timestamp": datetime.now().isoformat()
        }

        NumerologyRepository.set_cached_result(cache_key, response_data)
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "SERVER_ERROR",
            "message": "An unexpected error occurred while calculating Birth Day number."
        }), 500


@numerology_bp.route("/birth-day-status", methods=["GET"])
def get_birth_day_content_status():
    """Returns content completeness for all 31 days."""
    system = request.args.get("system", "pythagorean")
    report = NumerologyRepository.check_birth_day_completeness(system)
    return jsonify({
        "status": "success",
        "system": system,
        "completeness_report": report
    }), 200


@numerology_bp.route("/personal-year", methods=["GET", "POST"])
def get_personal_year():
    """
    Authoritative Personal Year calculation endpoint.
    Formula:
      month_reduced = reduce_to_single_digit(birth_month)
      day_reduced = reduce_to_single_digit(birth_day)
      year_reduced = reduce_to_single_digit(target_year)
      personal_year = reduce_to_single_digit(month_reduced + day_reduced + year_reduced)
    Target year is validated and dynamically defaults to current server calendar year if omitted.
    """
    try:
        current_user, _ = get_current_user()
        user_id = current_user.get("id") if current_user else None

        dob = None
        system = "pythagorean"
        name = "Seeker"
        target_year = None

        now_year = datetime.now().year

        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            dob = payload.get("dob") or payload.get("date_of_birth")
            system = payload.get("system", "pythagorean")
            name = payload.get("name") or name
            target_year = payload.get("year") or payload.get("target_year")
        else:
            dob = request.args.get("dob") or request.args.get("date_of_birth")
            system = request.args.get("system", "pythagorean")
            name = request.args.get("name") or name
            target_year = request.args.get("year") or request.args.get("target_year")

        if not dob and current_user:
            dob = current_user.get("dob") or current_user.get("date_of_birth")

        if not dob:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_DATE_OF_BIRTH",
                "message": "Date of birth is required to calculate Personal Year."
            }), 400

        dob = str(dob).strip()

        # Handle target year
        if target_year is None or str(target_year).strip() == "":
            target_year = now_year
        else:
            try:
                target_year = int(target_year)
            except (ValueError, TypeError):
                return jsonify({
                    "status": "error",
                    "error_code": "INVALID_TARGET_YEAR",
                    "message": "Target year must be a valid 4-digit integer (e.g. 2026)."
                }), 400

        if target_year < PersonalYearCalculator.MIN_SUPPORTED_YEAR or target_year > PersonalYearCalculator.MAX_SUPPORTED_YEAR:
            return jsonify({
                "status": "error",
                "error_code": "YEAR_OUT_OF_RANGE",
                "message": f"Target year must be between {PersonalYearCalculator.MIN_SUPPORTED_YEAR} and {PersonalYearCalculator.MAX_SUPPORTED_YEAR}."
            }), 400

        cache_key = f"personal_year_{user_id or 'guest'}_{dob}_{target_year}_{system}"
        cached = NumerologyRepository.get_cached_result(cache_key)
        if cached:
            return jsonify(cached), 200

        try:
            calc_result = PersonalYearCalculator.calculate(dob, target_year)
        except ValueError as ve:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_DATE_FORMAT",
                "message": str(ve)
            }), 400

        py_number = calc_result["personal_year_number"]

        interpretation = NumerologyRepository.get_personal_year_interpretation(system, py_number)
        if not interpretation and system != "pythagorean":
            interpretation = NumerologyRepository.get_personal_year_interpretation("pythagorean", py_number)

        if not interpretation:
            return jsonify({
                "status": "error",
                "error_code": "CONTENT_UNAVAILABLE",
                "message": f"Published interpretation for Personal Year {py_number} is currently unavailable.",
                "personal_year_number": py_number,
                "target_year": target_year,
                "calculation_trace": calc_result["calculation_trace"]
            }), 404

        response_data = {
            "status": "success",
            "calculation_status": "completed",
            "user_name": name,
            "personal_year_number": py_number,
            "target_year": target_year,
            "current_calendar_year": now_year,
            "number_title": interpretation["title"],
            "core_theme": interpretation["core_theme"],
            "date_of_birth_used": dob,
            "calculation_system": interpretation["system_code"],
            "method_version": calc_result["method_version"],
            "content_version": interpretation["content_version"],
            "calculation_trace": calc_result["calculation_trace"],
            "interpretation": {
                "overview": interpretation["overview"],
                "opportunities": interpretation["opportunities"],
                "challenges": interpretation["challenges"],
                "career_and_work": interpretation["career_and_work"],
                "relationships": interpretation["relationships"],
                "personal_growth": interpretation["personal_growth"],
                "practical_guidance": interpretation["practical_guidance"],
                "reflection_questions": interpretation["reflection_questions"],
                "sections": interpretation["sections"]
            },
            "timestamp": datetime.now().isoformat()
        }

        NumerologyRepository.set_cached_result(cache_key, response_data)
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "SERVER_ERROR",
            "message": "An unexpected error occurred while calculating Personal Year."
        }), 500


@numerology_bp.route("/personal-year-status", methods=["GET"])
def get_personal_year_content_status():
    """Returns content completeness report for all 9 Personal Year numbers."""
    system = request.args.get("system", "pythagorean")
    report = NumerologyRepository.check_personal_year_completeness(system)
    return jsonify({
        "status": "success",
        "system": system,
        "completeness_report": report
    }), 200


@numerology_bp.route("/name-analysis", methods=["POST", "GET"])
def get_name_analysis():
    """
    Authoritative Name Analysis endpoint.
    Supports both Pythagorean and Chaldean systems.
    Accepts:
      - birth_name (required)
      - current_name (optional)
      - system ('pythagorean' or 'chaldean')
      - date_of_birth (optional, for cosmic comparison)
    """
    try:
        current_user, _ = get_current_user()
        user_id = current_user.get("id") if current_user else None

        birth_name = ""
        current_name = None
        system = "pythagorean"
        dob = None

        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            birth_name = payload.get("birth_name") or payload.get("name") or ""
            current_name = payload.get("current_name")
            system = payload.get("system", "pythagorean")
            dob = payload.get("dob") or payload.get("date_of_birth")
        else:
            birth_name = request.args.get("birth_name") or request.args.get("name") or ""
            current_name = request.args.get("current_name")
            system = request.args.get("system", "pythagorean")
            dob = request.args.get("dob") or request.args.get("date_of_birth")

        if not birth_name and current_user:
            birth_name = current_user.get("name") or ""

        birth_name = str(birth_name).strip()
        if not birth_name:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_BIRTH_NAME",
                "message": "Full birth name is required for Name Analysis."
            }), 400

        system_clean = system.lower().strip()
        if system_clean not in ["pythagorean", "chaldean"]:
            system_clean = "pythagorean"

        cache_key = f"name_analysis_{user_id or 'guest'}_{birth_name}_{current_name or 'none'}_{system_clean}_{dob or 'nodob'}"
        cached = NumerologyRepository.get_cached_result(cache_key)
        if cached:
            return jsonify(cached), 200

        try:
            analysis = NameAnalysisCalculator.calculate(
                birth_name=birth_name,
                current_name=current_name,
                system=system_clean
            )
        except ValueError as ve:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_NAME_INPUT",
                "message": str(ve)
            }), 400

        # Attach database interpretations
        birth_analysis = analysis["birth_name_analysis"]
        interpretations = {}

        if system_clean == "pythagorean":
            core = birth_analysis["core_numbers"]
            exp_val = core["expression"]["final_number"]
            soul_val = core["soul_urge"]["final_number"]
            pers_val = core["personality"]["final_number"]

            interpretations["expression"] = NumerologyRepository.get_name_interpretation("pythagorean", "expression", exp_val)
            interpretations["soul_urge"] = NumerologyRepository.get_name_interpretation("pythagorean", "soul_urge", soul_val)
            interpretations["personality"] = NumerologyRepository.get_name_interpretation("pythagorean", "personality", pers_val)

            if analysis.get("current_name_analysis"):
                c_core = analysis["current_name_analysis"]["core_numbers"]
                c_exp = c_core["expression"]["final_number"]
                if c_exp != exp_val:
                    interpretations["current_expression"] = NumerologyRepository.get_name_interpretation("pythagorean", "expression", c_exp)
        else:
            root_val = birth_analysis["chaldean_root_number"]
            comp_val = birth_analysis["chaldean_compound_number"]
            interpretations["chaldean_root"] = NumerologyRepository.get_name_interpretation("chaldean", "chaldean_root", root_val)
            interpretations["chaldean_compound"] = NumerologyRepository.get_name_interpretation("chaldean", "chaldean_compound", comp_val)

            if analysis.get("current_name_analysis"):
                c_root = analysis["current_name_analysis"]["chaldean_root_number"]
                c_comp = analysis["current_name_analysis"]["chaldean_compound_number"]
                if c_root != root_val:
                    interpretations["current_chaldean_root"] = NumerologyRepository.get_name_interpretation("chaldean", "chaldean_root", c_root)
                if c_comp != comp_val:
                    interpretations["current_chaldean_compound"] = NumerologyRepository.get_name_interpretation("chaldean", "chaldean_compound", c_comp)

        # Optional Date of Birth compatibility analysis
        dob_harmony = None
        if dob and str(dob).strip():
            try:
                dob_clean = str(dob).strip()
                digits = [int(ch) for ch in dob_clean if ch.isdigit()]
                if digits:
                    dob_sum = sum(digits)
                    while dob_sum > 9 and dob_sum not in [11, 22, 33]:
                        dob_sum = sum(int(c) for c in str(dob_sum))
                    
                    if system_clean == "pythagorean":
                        exp_num = birth_analysis["core_numbers"]["expression"]["final_number"]
                        is_aligned = exp_num == dob_sum
                        dob_harmony = {
                            "life_path_number": dob_sum,
                            "expression_number": exp_num,
                            "is_aligned": is_aligned,
                            "summary": f"Your Life Path is {dob_sum} and your Name Expression is {exp_num}." + (
                                " Perfect resonance! Your name directly mirrors your life's foundational path." if is_aligned else
                                " Complementary energies: your name supplies distinct skills that assist your Life Path mission."
                            )
                        }
                    else:
                        root_num = birth_analysis["chaldean_root_number"]
                        is_aligned = root_num == (dob_sum if dob_sum <= 9 else sum(int(c) for c in str(dob_sum)))
                        dob_harmony = {
                            "birth_vibration": dob_sum,
                            "chaldean_root": root_num,
                            "is_aligned": is_aligned,
                            "summary": f"Your birth vibration is {dob_sum} and your Chaldean root is {root_num}." + (
                                " Direct harmonic alignment between your birth moment and name vibration!" if is_aligned else
                                " Interplay of planetary archetypes between your birth date and name frequency."
                            )
                        }
            except Exception:
                pass

        response_data = {
            "status": "success",
            "calculation_status": "completed",
            "system": system_clean,
            "birth_name": birth_name,
            "current_name": current_name,
            "analysis": birth_analysis,
            "current_name_analysis": analysis.get("current_name_analysis"),
            "name_comparison": analysis.get("name_comparison"),
            "dob_harmony": dob_harmony,
            "interpretations": interpretations,
            "calculation_version": "1.0.0",
            "disclaimer": "Name Analysis calculations are rooted in traditional Pythagorean and Chaldean numerology traditions. Interpretations are intended for self-reflection and personal inquiry, not deterministic scientific predictions.",
            "timestamp": datetime.now().isoformat()
        }

        NumerologyRepository.set_cached_result(cache_key, response_data)
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "SERVER_ERROR",
            "message": "An unexpected error occurred while analyzing name."
        }), 500



@numerology_bp.route("/personality-soul", methods=["GET", "POST"])
def get_personality_soul_analysis():
    """
    Authoritative Personality Number & Soul Urge Number endpoint.
    - Consonants strictly for Personality Number (The Outer Persona)
    - Vowels strictly for Soul Urge Number (The Inner Heart's Desire)
    - Configurable Y Policy ('always_consonant' or 'always_vowel')
    - Preserves Master Numbers (11, 22, 33)
    - Database-driven interpretations from published records
    - Full auditable calculation trace
    """
    try:
        current_user, _ = get_current_user()
        user_id = current_user.get("id") if current_user else None

        birth_name = ""
        y_policy = "always_consonant"

        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            birth_name = payload.get("birth_name") or payload.get("name") or ""
            y_policy = payload.get("y_policy", "always_consonant")
        else:
            birth_name = request.args.get("birth_name") or request.args.get("name") or ""
            y_policy = request.args.get("y_policy", "always_consonant")

        # Fallback to authenticated user profile if birth_name is not provided
        if not birth_name and current_user:
            birth_name = current_user.get("full_name") or current_user.get("name") or ""

        birth_name = str(birth_name).strip()
        if not birth_name:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_BIRTH_NAME",
                "message": "Full birth name is required for Personality & Soul Urge calculation. Please complete your profile or enter your birth name."
            }), 400

        if len(birth_name) > 100:
            return jsonify({
                "status": "error",
                "error_code": "NAME_TOO_LONG",
                "message": "Name exceeds maximum length of 100 characters. Please provide a standard birth name."
            }), 400

        y_policy = str(y_policy).strip().lower()
        if y_policy not in ("always_consonant", "always_vowel", "manual"):
            y_policy = "always_consonant"

        cache_key = f"personality_soul:{user_id or 'guest'}:{birth_name.upper()}:{y_policy}:v1.0.0"
        cached = NumerologyRepository.get_cached_result(cache_key)
        if cached:
            return jsonify(cached), 200

        try:
            analysis = PersonalitySoulAnalyzer.analyze(birth_name, y_policy=y_policy)
        except ValueError as ve:
            err_msg = str(ve)
            code = "UNSUPPORTED_SCRIPT" if "non-Latin" in err_msg else "INVALID_NAME"
            return jsonify({
                "status": "error",
                "error_code": code,
                "message": err_msg
            }), 400

        pers_num = analysis["personality"]["number"]
        soul_num = analysis["soul_urge"]["number"]

        # Retrieve published interpretations from SQLite database
        pers_interp = NumerologyRepository.get_name_interpretation("pythagorean", "personality", pers_num)
        soul_interp = NumerologyRepository.get_name_interpretation("pythagorean", "soul_urge", soul_num)

        if not pers_interp:
            return jsonify({
                "status": "error",
                "error_code": "INTERPRETATION_UNAVAILABLE",
                "message": f"Personality Number {pers_num} interpretation record is unpublished or unavailable in the database."
            }), 404

        if not soul_interp:
            return jsonify({
                "status": "error",
                "error_code": "INTERPRETATION_UNAVAILABLE",
                "message": f"Soul Urge Number {soul_num} interpretation record is unpublished or unavailable in the database."
            }), 404

        # Dynamic Harmony & Resonance Evaluation
        is_direct_match = (pers_num == soul_num)
        if is_direct_match:
            harmony_summary = (
                f"Complete Inner-Outer Congruence: Both your Personality and Soul Urge resonate with Number {pers_num}. "
                "The face you show the world perfectly reflects your authentic inner heart's desire. What people see is genuinely who you are."
            )
            harmony_tag = "Perfect Resonance"
        else:
            harmony_summary = (
                f"Dynamic Complementary Synergy: Your outer demeanor radiates Personality {pers_num}, while your secret heart's desire vibrates to Soul Urge {soul_num}. "
                f"Your outward social presence provides the exact practical skills and energetic buffer needed to safely manifest your {soul_num} soul calling."
            )
            harmony_tag = "Complementary Synergy"

        harmony_analysis = {
            "personality_number": pers_num,
            "soul_urge_number": soul_num,
            "is_direct_resonance": is_direct_match,
            "harmony_tag": harmony_tag,
            "harmony_summary": harmony_summary
        }

        response_data = {
            "status": "success",
            "calculation_status": "completed",
            "system": "pythagorean",
            "system_name": "Pythagorean Name Numerology",
            "y_policy": y_policy,
            "birth_name": birth_name,
            "normalized_name": analysis["normalized_name"],
            "is_authenticated": current_user is not None,
            "user_id": user_id,
            "personality": {
                "number": pers_num,
                "root_number": analysis["personality"]["root_number"],
                "is_master_number": analysis["personality"]["is_master_number"],
                "unreduced_sum": analysis["personality"]["unreduced_sum"],
                "included_letters_count": analysis["personality"]["included_letters_count"],
                "included_letters": analysis["personality"]["included_letters"],
                "reduction_steps": analysis["personality"]["reduction_steps"],
                "formula_summary": analysis["personality"]["formula_summary"],
                "words_breakdown": analysis["personality"]["words_breakdown"],
                "interpretation": pers_interp
            },
            "soul_urge": {
                "number": soul_num,
                "root_number": analysis["soul_urge"]["root_number"],
                "is_master_number": analysis["soul_urge"]["is_master_number"],
                "unreduced_sum": analysis["soul_urge"]["unreduced_sum"],
                "included_letters_count": analysis["soul_urge"]["included_letters_count"],
                "included_letters": analysis["soul_urge"]["included_letters"],
                "reduction_steps": analysis["soul_urge"]["reduction_steps"],
                "formula_summary": analysis["soul_urge"]["formula_summary"],
                "words_breakdown": analysis["soul_urge"]["words_breakdown"],
                "interpretation": soul_interp
            },
            "harmony_analysis": harmony_analysis,
            "audit_trace": analysis["audit_trace"],
            "calculation_version": "1.0.0",
            "content_version": pers_interp.get("content_version", "1.0.0"),
            "disclaimer": "Personality and Soul Urge calculations are rooted in authoritative Pythagorean name numerology traditions. Interpretations are intended for self-reflection and personal inquiry, not scientifically validated psychological assessment.",
            "timestamp": datetime.now().isoformat()
        }

        NumerologyRepository.set_cached_result(cache_key, response_data)
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "SERVER_ERROR",
            "message": f"An unexpected error occurred during Personality & Soul calculation: {str(e)}"
        }), 500


@numerology_bp.route("/missing-numbers", methods=["GET", "POST"])
def get_missing_numbers_analysis():
    """
    Authoritative Missing Numbers (Karmic Lessons) endpoint.
    - Full birth name frequency analysis under Pythagorean Name Numerology (1-9 Mapping).
    - Counts occurrences of each number 1 to 9.
    - A number is marked missing IF AND ONLY IF its count is strictly zero.
    - Preserves user name, tracks letter-by-letter mappings, word subtotals, and transparent calculation traces.
    - Retrieves database-driven interpretations for all missing numbers.
    - Rate-limiting and caching aware.
    """
    try:
        current_user, _ = get_current_user()
        user_id = current_user.get("id") if current_user else None

        birth_name = ""
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            birth_name = payload.get("birth_name") or payload.get("name") or ""
        else:
            birth_name = request.args.get("birth_name") or request.args.get("name") or ""

        # Fallback to authenticated user profile if birth_name is not provided
        if not birth_name and current_user:
            birth_name = current_user.get("full_name") or current_user.get("name") or ""

        birth_name = str(birth_name).strip()
        if not birth_name:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_BIRTH_NAME",
                "message": "Full birth name is required for Missing Numbers calculation. Please complete your profile or enter your birth name."
            }), 400

        if len(birth_name) > 100:
            return jsonify({
                "status": "error",
                "error_code": "NAME_TOO_LONG",
                "message": "Name exceeds maximum length of 100 characters. Please provide a standard birth name."
            }), 400

        cache_key = f"missing_numbers:{user_id or 'guest'}:{birth_name.upper()}:v1.0.0"
        cached = NumerologyRepository.get_cached_result(cache_key)
        if cached:
            return jsonify(cached), 200

        try:
            analysis = MissingNumbersCalculator.analyze(birth_name)
        except ValueError as ve:
            err_msg = str(ve)
            code = "UNSUPPORTED_SCRIPT" if "unsupported non-Latin" in err_msg else "INVALID_NAME"
            return jsonify({
                "status": "error",
                "error_code": code,
                "message": err_msg
            }), 400

        missing_nums = analysis["missing_numbers"]

        # Retrieve published interpretations from SQLite database for each missing number
        interpretations = {}
        for num in missing_nums:
            interp = NumerologyRepository.get_missing_number_interpretation(num, "pythagorean")
            if interp:
                interpretations[str(num)] = interp

        response_data = {
            "status": "success",
            "calculation_status": "completed",
            "system": "pythagorean",
            "system_name": "Pythagorean Name Numerology",
            "algorithm_version": "1.0.0",
            "birth_name": birth_name,
            "normalized_name": analysis["normalized_name"],
            "is_authenticated": current_user is not None,
            "user_id": user_id,
            "total_letters_evaluated": analysis["total_letters_evaluated"],
            "frequency_table": {str(k): v for k, v in analysis["frequency_table"].items()},
            "missing_numbers": missing_nums,
            "missing_count": len(missing_nums),
            "present_numbers": analysis["present_numbers"],
            "present_count": len(analysis["present_numbers"]),
            "has_no_missing_numbers": analysis["has_no_missing_numbers"],
            "hidden_passion": analysis["hidden_passion"],
            "planes_of_expression": analysis["planes_of_expression"],
            "interpretations": interpretations,
            "audit_trace": analysis["audit_trace"],
            "calculation_version": "1.0.0",
            "content_version": "1.0.0",
            "disclaimer": "Missing Numbers (Karmic Lessons) reflect traditional Pythagorean frequency analysis of full birth names. Interpretations are intended for self-reflection and personal inquiry, not deterministic limitations.",
            "timestamp": datetime.now().isoformat()
        }

        NumerologyRepository.set_cached_result(cache_key, response_data)
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "SERVER_ERROR",
            "message": f"An unexpected error occurred during Missing Numbers calculation: {str(e)}"
        }), 500

@numerology_bp.route("/remedies", methods=["GET", "POST"])
def get_numerology_remedies():
    """
    Production-ready Remedies & Fixes endpoint.
    - Evaluates authenticated user's actual validated numerology profile (Life Path, Birth Day, Missing Numbers, Personal Year).
    - Determines applicable remedies via documented backend rule engine.
    - Retrieves reviewed, published database content with zero random values.
    - Provides explicit explanations for why each remedy matched.
    - Transparent, non-material, accessible daily habits, reflection practices, symbolic alignments, and acts of kindness.
    """
    try:
        current_user, _ = get_current_user()
        user_id = current_user.get("id") if current_user else None

        dob = ""
        birth_name = ""
        system = "pythagorean"
        category = "all"
        focus_area = "all"
        target_year = None

        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
            dob = payload.get("dob") or payload.get("date_of_birth") or ""
            birth_name = payload.get("birth_name") or payload.get("name") or ""
            system = payload.get("system", "pythagorean").lower()
            category = payload.get("category", "all").lower()
            focus_area = payload.get("focus_area", "all").lower()
            target_year = payload.get("year") or payload.get("target_year")
        else:
            dob = request.args.get("dob") or request.args.get("date_of_birth") or ""
            birth_name = request.args.get("birth_name") or request.args.get("name") or ""
            system = request.args.get("system", "pythagorean").lower()
            category = request.args.get("category", "all").lower()
            focus_area = request.args.get("focus_area", "all").lower()
            target_year = request.args.get("year") or request.args.get("target_year")

        # Fallback to authenticated user profile if data is omitted
        if not dob and current_user:
            dob = current_user.get("date_of_birth") or current_user.get("dob") or ""
        if not birth_name and current_user:
            birth_name = current_user.get("full_name") or current_user.get("name") or ""

        dob = str(dob).strip()
        birth_name = str(birth_name).strip()

        if not dob:
            return jsonify({
                "status": "error",
                "error_code": "MISSING_DOB",
                "message": "Date of birth (YYYY-MM-DD) is required to evaluate your personalized numerology remedies."
            }), 400

        # Validate DOB format
        try:
            parsed_dob = datetime.strptime(dob, "%Y-%m-%d")
            if parsed_dob.year < 1900 or parsed_dob > datetime.now():
                return jsonify({
                    "status": "error",
                    "error_code": "INVALID_DOB_RANGE",
                    "message": "Date of birth must be between 1900 and the present year."
                }), 400
        except ValueError:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_DOB_FORMAT",
                "message": "Date of birth must strictly follow the format YYYY-MM-DD (e.g. 1998-12-13)."
            }), 400

        if target_year:
            try:
                target_year = int(target_year)
            except ValueError:
                target_year = datetime.now().year

        cache_key = f"remedies:{user_id or 'guest'}:{dob}:{birth_name.upper()}:{system}:{category}:{focus_area}:{target_year or ''}:v1.0.0"
        cached = NumerologyRepository.get_cached_result(cache_key)
        if cached:
            return jsonify(cached), 200

        engine = RemedyRuleEngine()
        result = engine.evaluate(
            dob=dob,
            birth_name=birth_name if birth_name else None,
            system_code=system,
            category_filter=category,
            focus_area_filter=focus_area,
            target_year=target_year
        )

        result["is_authenticated"] = current_user is not None
        result["user_id"] = user_id
        result["timestamp"] = datetime.now().isoformat()

        NumerologyRepository.set_cached_result(cache_key, result)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error_code": "SERVER_ERROR",
            "message": f"An unexpected error occurred during Remedies & Fixes evaluation: {str(e)}"
        }), 500


@numerology_bp.route("/remedies-status", methods=["GET"])
def get_remedies_status():
    """
    Inspection endpoint reporting publication status and rule engine completeness.
    """
    try:
        system = request.args.get("system", "pythagorean").lower()
        completeness = NumerologyRepository.check_remedies_completeness(system)
        return jsonify({
            "status": "success",
            "system": system,
            "completeness": completeness,
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



# =========================================================================
# CRYSTAL MATCH & MINERALOGY ENDPOINTS
# =========================================================================

@numerology_bp.route("/crystal-match", methods=["POST"])
def evaluate_crystal_match():
    """
    Evaluates personalized crystal match recommendations based on
    authoritative numerology calculations and reviewed database records.
    """
    try:
        data = request.get_json() or {}
        dob = (data.get("dob") or data.get("date_of_birth") or "").strip()
        if not dob:
            return jsonify({
                "status": "error",
                "message": "Date of birth (dob) is required."
            }), 400

        birth_name = data.get("birth_name") or data.get("name")
        system = data.get("system", "pythagorean")
        intention = data.get("intention", "all")
        target_year = data.get("target_year")

        result = CrystalMatchEngine.evaluate(
            dob=dob,
            birth_name=birth_name,
            system=system,
            intention=intention,
            target_year=target_year
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error evaluating crystal match: {str(e)}"
        }), 500


@numerology_bp.route("/crystal-catalog", methods=["GET"])
def get_crystal_catalog():
    """
    Returns all published crystal records directly from the SQLite database.
    """
    try:
        catalog = CrystalMatchEngine.get_catalog()
        return jsonify({
            "status": "success",
            "total": len(catalog),
            "catalog": catalog
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error fetching crystal catalog: {str(e)}"
        }), 500


@numerology_bp.route("/crystal-intentions", methods=["GET"])
def get_crystal_intentions():
    """
    Returns all supported intention filters directly from the SQLite database.
    """
    try:
        intentions = CrystalMatchEngine.get_intentions()
        return jsonify({
            "status": "success",
            "total": len(intentions),
            "intentions": intentions
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error fetching crystal intentions: {str(e)}"
        }), 500


# =========================================================================
# PHONE NUMBER / MOBILE NUMEROLOGY ENDPOINT
# =========================================================================

@numerology_bp.route("/phone-analysis", methods=["POST"])
def analyze_phone_number():
    """
    Authoritative, deterministic mobile number numerology analysis.
    Evaluates 10-digit subscriber digits, compound total, reduction trace,
    digit frequency, missing/repeated digits, database interpretation,
    and optional personal compatibility with user's Life Path & Birth Day.
    """
    import json
    import logging
    logger = logging.getLogger(__name__)
    from app.services.phone_number_calculator import PhoneNumberCalculator
    from app.core.database import get_db_connection

    try:
        data = request.get_json() or {}
        raw_phone = data.get("phone_number") or data.get("mobile_number") or ""
        if not str(raw_phone).strip():
            return jsonify({
                "status": "error",
                "message": "Phone number is required for analysis."
            }), 400

        country_code = data.get("country_code", "IN")
        dob = data.get("dob") or data.get("date_of_birth")
        system = data.get("system", "pythagorean")

        # 1. Authoritative calculation service
        calc_result = PhoneNumberCalculator.calculate_full(
            phone_number=raw_phone,
            country_code=country_code,
            dob=dob,
            system=system
        )

        root_num = calc_result["root_number"]

        # 2. Retrieve reviewed database interpretation
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    root_number, title, core_theme, planetary_ruler, element,
                    overview, traditional_strengths, potential_challenges,
                    communication_themes, work_and_daily_life, practical_guidance,
                    reflection_questions, content_version
                FROM phone_number_interpretations
                WHERE root_number = ? AND publication_status = 'published'
            """, (root_num,))
            row = cursor.fetchone()

            interp = None
            if row:
                interp = {
                    "root_number": row["root_number"],
                    "title": row["title"],
                    "core_theme": row["core_theme"],
                    "planetary_ruler": row["planetary_ruler"],
                    "element": row["element"],
                    "overview": row["overview"],
                    "traditional_strengths": json.loads(row["traditional_strengths"]) if row["traditional_strengths"] else [],
                    "potential_challenges": json.loads(row["potential_challenges"]) if row["potential_challenges"] else [],
                    "communication_themes": row["communication_themes"],
                    "work_and_daily_life": row["work_and_daily_life"],
                    "practical_guidance": row["practical_guidance"],
                    "reflection_questions": row["reflection_questions"],
                    "content_version": row["content_version"],
                }

            # Retrieve pattern interpretations for repeated digits
            cursor.execute("SELECT pattern_type, pattern_value, title, explanation, recommendation FROM phone_digit_pattern_interpretations WHERE publication_status = 'published'")
            pattern_rows = cursor.fetchall()
            patterns_map = {f"{r['pattern_type']}_{r['pattern_value']}": {
                "title": r["title"], "explanation": r["explanation"], "recommendation": r["recommendation"]
            } for r in pattern_rows}
        finally:
            conn.close()

        # Enhance repeated digits with DB insights
        enhanced_repeated = []
        for rep in calc_result["digit_patterns"]["repeated_digits"]:
            d_str = str(rep["digit"])
            info = patterns_map.get(f"repeated_digit_{d_str}")
            enhanced_repeated.append({
                "digit": rep["digit"],
                "count": rep["count"],
                "intensity": rep["intensity"],
                "insight": info["explanation"] if info else f"Amplified frequency of number {rep['digit']}.",
                "recommendation": info["recommendation"] if info else "Cultivate conscious balance with this vibration."
            })

        response_payload = {
            "status": "success",
            "calculation_status": "completed",
            "algorithm_version": calc_result["algorithm_version"],
            "methodology": calc_result["methodology"],
            "masked_number": calc_result["masked_number"],
            "country_code": calc_result["country_code"],
            "subscriber_digits": calc_result["subscriber_digits"],
            "subscriber_digits_str": calc_result["subscriber_digits_str"],
            "total_digits_count": calc_result["total_digits_count"],
            "compound_total": calc_result["compound_total"],
            "reduction_trace": calc_result["reduction_trace"],
            "root_number": calc_result["root_number"],
            "planetary_ruler": calc_result["planetary_ruler"],
            "digit_patterns": {
                "frequency_table": calc_result["digit_patterns"]["frequency_table"],
                "present_digits": calc_result["digit_patterns"]["present_digits"],
                "missing_digits": calc_result["digit_patterns"]["missing_digits"],
                "repeated_digits": enhanced_repeated,
                "first_digit": calc_result["digit_patterns"]["first_digit"],
                "last_digit": calc_result["digit_patterns"]["last_digit"],
                "last_two_digits": calc_result["digit_patterns"]["last_two_digits"],
                "last_two_compound": calc_result["digit_patterns"]["last_two_compound"],
                "zero_count": calc_result["digit_patterns"]["zero_count"],
            },
            "interpretation": interp,
            "personal_compatibility": calc_result["personal_compatibility"],
            "privacy_notice": "Phone numbers are evaluated in temporary memory and are not permanently logged or shared with third parties."
        }

        return jsonify(response_payload), 200

    except ValueError as ve:
        return jsonify({
            "status": "error",
            "message": str(ve)
        }), 400
    except Exception as e:
        logger.error(f"Error evaluating phone numerology: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Error analyzing phone number: {str(e)}"
        }), 500


# ============================================================================
# CHILD NUMEROLOGY & BABY NAME MODULE
# ============================================================================
from app.services.child_numerology_calculator import ChildNumerologyCalculator

@numerology_bp.route('/child-analysis', methods=['POST'])
def analyze_child_numerology():
    """
    Evaluates complete child numerology profile:
      - Mulank (Birth Number from calendar day 1-31)
      - Bhagyank (Destiny Number from full date YYYY-MM-DD)
      - Name Number (Expression Number via Pythagorean or Chaldean sound chart)
      - Soul Urge (vowels sum) & Personality Number (consonants sum)
      - Name-to-Birth Auspicious Compatibility
      - Optional Parent-Child Planetary Harmony
      - Database-backed parenting and learning guidance
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing request payload."}), 400

        child_name = data.get("child_name") or data.get("name")
        if not child_name or not str(child_name).strip():
            return jsonify({"status": "error", "message": "Child's name is required."}), 400

        dob = data.get("dob") or data.get("date_of_birth")
        if not dob or not str(dob).strip():
            return jsonify({"status": "error", "message": "Child's date of birth (YYYY-MM-DD) is required."}), 400

        system = data.get("system", "pythagorean")
        parent_name = data.get("parent_name")
        parent_dob = data.get("parent_dob")

        report = ChildNumerologyCalculator.analyze_child(
            child_name=str(child_name).strip(),
            dob_str=str(dob).strip(),
            system=str(system).strip(),
            parent_name=str(parent_name).strip() if parent_name else None,
            parent_dob_str=str(parent_dob).strip() if parent_dob else None
        )

        return jsonify({
            "status": "success",
            "calculation_status": "completed",
            "data": report
        }), 200

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error evaluating child numerology: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error evaluating child numerology: {str(e)}"}), 500


@numerology_bp.route('/child-name-comparison', methods=['POST'])
def compare_child_candidate_names():
    """
    Compares multiple candidate baby names against the child's birth date.
    Calculates compound totals, root numbers, planetary harmony with Mulank & Bhagyank,
    and returns deterministic ranking with transparent explanations.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing request payload."}), 400

        candidate_names = data.get("candidate_names") or data.get("names")
        if not candidate_names or not isinstance(candidate_names, list) or len(candidate_names) == 0:
            return jsonify({"status": "error", "message": "At least one candidate name is required in 'candidate_names' list."}), 400

        dob = data.get("dob") or data.get("date_of_birth")
        if not dob or not str(dob).strip():
            return jsonify({"status": "error", "message": "Child's date of birth (YYYY-MM-DD) is required for comparison."}), 400

        system = data.get("system", "pythagorean")

        comparison_report = ChildNumerologyCalculator.compare_candidate_names(
            candidate_names=[str(n).strip() for n in candidate_names if str(n).strip()],
            dob_str=str(dob).strip(),
            system=str(system).strip()
        )

        return jsonify({
            "status": "success",
            "calculation_status": "completed",
            "data": comparison_report
        }), 200

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error comparing candidate names: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error comparing candidate names: {str(e)}"}), 500


# =========================================================================
# ADVANCED NUMEROLOGY COMPATIBILITY MODULE ENDPOINTS
# =========================================================================

from app.services.advanced_compatibility_calculator import AdvancedCompatibilityCalculator


@numerology_bp.route('/advanced-compatibility', methods=['POST'])
def calculate_advanced_compatibility():
    """
    Calculates comprehensive, multi-factor Advanced Compatibility between two individuals.
    Profiles are calculated independently, matched against reviewed database rules,
    and returned with transparent scoring, strengths, growth areas, and practical guidance.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing request payload."}), 400

        person_a_name = data.get("person_a_name") or data.get("name_a")
        person_b_name = data.get("person_b_name") or data.get("name_b")

        if not person_a_name or not str(person_a_name).strip():
            return jsonify({"status": "error", "message": "Person A name is required."}), 400
        if not person_b_name or not str(person_b_name).strip():
            return jsonify({"status": "error", "message": "Person B name is required."}), 400

        person_a_dob = data.get("person_a_dob") or data.get("dob_a")
        person_b_dob = data.get("person_b_dob") or data.get("dob_b")
        relationship_type = data.get("relationship_type", "romantic")
        system = data.get("system", "pythagorean")

        report = AdvancedCompatibilityCalculator.calculate_advanced_compatibility(
            person_a_name=str(person_a_name).strip(),
            person_b_name=str(person_b_name).strip(),
            person_a_dob=str(person_a_dob).strip() if person_a_dob else None,
            person_b_dob=str(person_b_dob).strip() if person_b_dob else None,
            relationship_type=str(relationship_type).strip().lower(),
            system=str(system).strip().lower()
        )

        return jsonify({
            "status": "success",
            "calculation_status": "completed",
            "data": report
        }), 200

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error calculating advanced compatibility: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Error calculating compatibility: {str(e)}"}), 500


@numerology_bp.route('/compatibility/methods', methods=['GET'])
def get_compatibility_methods():
    """
    Returns supported numerology calculation methods from database.
    """
    try:
        conn = AdvancedCompatibilityCalculator._get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT method_code, method_name, methodology_version, reduction_policy FROM numerology_compatibility_methods WHERE is_active = 1")
        methods = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify({"status": "success", "data": methods}), 200
    except Exception as e:
        logger.error(f"Error fetching compatibility methods: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@numerology_bp.route('/compatibility/factors', methods=['GET'])
def get_compatibility_factors():
    """
    Returns available compatibility factors and their supported relationship types.
    """
    try:
        conn = AdvancedCompatibilityCalculator._get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT factor_code, factor_name, description, supported_relationship_types FROM compatibility_factor_definitions WHERE is_active = 1")
        factors = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify({"status": "success", "data": factors}), 200
    except Exception as e:
        logger.error(f"Error fetching compatibility factors: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@numerology_bp.route('/compatibility/content-status', methods=['GET'])
def get_compatibility_content_status():
    """
    Administrative check reporting active rules and interpretations count in database.
    """
    try:
        conn = AdvancedCompatibilityCalculator._get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM numerology_compatibility_rules WHERE is_active = 1")
        rule_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM numerology_compatibility_interpretations WHERE is_active = 1")
        interp_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM compatibility_scoring_config WHERE is_active = 1")
        scoring_count = cur.fetchone()[0]
        conn.close()
        return jsonify({
            "status": "success",
            "data": {
                "active_rules_count": rule_count,
                "active_interpretations_count": interp_count,
                "active_scoring_configs_count": scoring_count,
                "review_status": "approved",
                "version": "2.0"
            }
        }), 200
    except Exception as e:
        logger.error(f"Error fetching content status: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@numerology_bp.route('/compatibility/save-report', methods=['POST'])
def save_compatibility_report():
    """
    Saves an authorized compatibility report to database.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Missing request payload."}), 400

        user_id = data.get("user_id", "guest")
        rel_type = data.get("relationship_type", "romantic")
        system = data.get("system", "pythagorean")
        person_a_label = data.get("person_a_label", "Person A")
        person_b_label = data.get("person_b_label", "Person B")
        calculated_data = data.get("calculated_data", {})

        report_id = AdvancedCompatibilityCalculator.save_report(
            user_id=user_id,
            relationship_type=rel_type,
            system=system,
            person_a_label=person_a_label,
            person_b_label=person_b_label,
            calculated_data=calculated_data
        )

        return jsonify({
            "status": "success",
            "message": "Report saved successfully.",
            "data": {"report_id": report_id}
        }), 200

    except Exception as e:
        logger.error(f"Error saving compatibility report: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

from app.services.numerology_dasha_service import NumerologyDashaService

# =========================================================================
# ASTROLOGER MODE - NUMEROLOGY DASHA WORKSPACE
# =========================================================================

@numerology_bp.route('/astrologer-workspace', methods=['POST'])
def get_astrologer_workspace():
    """
    Dedicated table-based Numerology Dasha workspace calculation endpoint.
    Deterministic, backend-only calculations for:
    - Basic Info (Mulank, Supportive Number, Destiny Number, Lucky attributes, reduction steps)
    - 100-Year Mahadasha Lifetime Progression Table
    - Annual Antardasha Milestone Schedule
    - Pratantardasha / Paryantardasha 365-day Subdivisions
    - Daily Dasha Planetary Schedule & Explanations
    """
    try:
        data = request.get_json() or {}
        name = str(data.get("name", "")).strip()
        dob = str(data.get("dob") or data.get("date_of_birth", "")).strip()
        system = str(data.get("system", "pythagorean")).strip()
        ref_date = data.get("reference_date")

        if not dob:
            return jsonify({
                "status": "error",
                "message": "Date of birth (dob) is required to calculate Astrologer Dasha workspace."
            }), 400

        if not name:
            name = "Seeker"

        workspace = NumerologyDashaService.get_full_workspace(
            name=name,
            dob_str=dob,
            system=system,
            ref_date_str=ref_date
        )

        return jsonify(workspace), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Calculation failed: {str(e)}"}), 500


@numerology_bp.route('/dasha/paryantardashas', methods=['POST'])
def get_paryantardashas_for_year():
    """
    Retrieves the 9 Pratantardashas for a specific Antardasha cycle year.
    """
    try:
        data = request.get_json() or {}
        dob = str(data.get("dob") or data.get("date_of_birth", "")).strip()
        year = data.get("year")
        ref_date = data.get("reference_date")

        if not dob:
            return jsonify({"status": "error", "message": "Date of birth (dob) is required."}), 400

        pds = NumerologyDashaService.calculate_paryantardashas(
            dob_str=dob,
            antardasha_year=int(year) if year is not None else None,
            ref_date_str=ref_date
        )

        return jsonify({"status": "success", "data": pds}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@numerology_bp.route('/dasha/daily', methods=['POST'])
def get_daily_dashas():
    """
    Retrieves Daily Dasha schedule for a specified center date and span.
    """
    try:
        data = request.get_json() or {}
        dob = str(data.get("dob") or data.get("date_of_birth", "")).strip()
        center_date = data.get("center_date") or data.get("date")
        span_days = int(data.get("span_days", 14))

        if not dob:
            return jsonify({"status": "error", "message": "Date of birth (dob) is required."}), 400

        daily_list = NumerologyDashaService.calculate_daily_dashas(
            dob_str=dob,
            center_date_str=center_date,
            days_span=span_days
        )

        return jsonify({"status": "success", "data": daily_list}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================================================================
# NUMEROLOGY CHART WORKSPACE (BASIC CHART, DASHA TIMELINE & PRATYANTAR)
# =========================================================================

@numerology_bp.route("/chart-workspace", methods=["POST"])
@numerology_bp.route("/chart", methods=["POST"])
def get_chart_workspace():
    """
    Production-ready Chart Workspace calculation endpoint.
    Deterministic, backend-only calculations for:
    - Section A: Basic Chart (Lo Shu 3x3 Grid, 8 Directional Planes, Multiplicity, Core Numbers)
    - Section B: Dasha Chart (Date-based timeline with 1, 5, 10, 15-Year & Custom Range window filtering)
    - Section C: Pratyantar Dasha Chart (Hierarchical subperiods linked to parent Mahadasha & Antardasha)
    """
    try:
        data = request.get_json() or {}
        name = str(data.get("name", "")).strip()
        dob = str(data.get("dob") or data.get("date_of_birth", "")).strip()
        system = str(data.get("system", "pythagorean")).strip()
        start_date = data.get("start_date")
        duration_years = int(data.get("duration_years", 10))
        end_date = data.get("end_date")
        ref_date = data.get("reference_date")
        parent_filter = data.get("parent_dasha_filter")
        if parent_filter is not None:
            parent_filter = int(parent_filter)

        if not dob:
            return jsonify({
                "status": "error",
                "message": "Date of birth (dob) is required to calculate Numerology Chart."
            }), 400

        if not name:
            name = "Seeker"

        workspace = NumerologyChartService.get_full_chart_workspace(
            name=name,
            dob_str=dob,
            system=system,
            start_date_str=start_date,
            duration_years=duration_years,
            end_date_str=end_date,
            ref_date_str=ref_date,
            parent_dasha_filter=parent_filter
        )

        return jsonify(workspace), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Chart calculation failed: {str(e)}"}), 500


@numerology_bp.route("/chart/basic", methods=["POST"])
def get_basic_chart():
    """
    Retrieves Section A ? Basic Chart (Lo Shu Grid & Planes analysis).
    """
    try:
        data = request.get_json() or {}
        name = str(data.get("name", "Seeker")).strip()
        dob = str(data.get("dob") or data.get("date_of_birth", "")).strip()
        system = str(data.get("system", "pythagorean")).strip()

        if not dob:
            return jsonify({"status": "error", "message": "Date of birth (dob) is required."}), 400

        basic_chart = NumerologyChartService.calculate_basic_chart(name=name, dob_str=dob, system=system)
        return jsonify({"status": "success", "data": basic_chart}), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@numerology_bp.route("/chart/dasha-timeline", methods=["POST"])
def get_dasha_timeline():
    """
    Retrieves Section B ? Dasha Chart Timeline filtered by window duration.
    """
    try:
        data = request.get_json() or {}
        dob = str(data.get("dob") or data.get("date_of_birth", "")).strip()
        start_date = data.get("start_date")
        duration_years = int(data.get("duration_years", 10))
        end_date = data.get("end_date")
        ref_date = data.get("reference_date")

        if not dob:
            return jsonify({"status": "error", "message": "Date of birth (dob) is required."}), 400

        timeline = NumerologyChartService.calculate_dasha_chart(
            dob_str=dob,
            start_date_str=start_date,
            duration_years=duration_years,
            end_date_str=end_date,
            ref_date_str=ref_date
        )
        return jsonify({"status": "success", "data": timeline}), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@numerology_bp.route("/chart/pratyantar", methods=["POST"])
def get_pratyantar_chart():
    """
    Retrieves Section C ? Pratyantar Dasha table for a parent period or custom window.
    """
    try:
        data = request.get_json() or {}
        dob = str(data.get("dob") or data.get("date_of_birth", "")).strip()
        start_date = data.get("start_date")
        duration_years = int(data.get("duration_years", 10))
        end_date = data.get("end_date")
        ref_date = data.get("reference_date")
        parent_filter = data.get("parent_dasha_filter")
        if parent_filter is not None:
            parent_filter = int(parent_filter)
        antardasha_year = data.get("antardasha_year_filter")
        if antardasha_year is not None:
            antardasha_year = int(antardasha_year)

        if not dob:
            return jsonify({"status": "error", "message": "Date of birth (dob) is required."}), 400

        pratyantar = NumerologyChartService.calculate_pratyantar_chart(
            dob_str=dob,
            start_date_str=start_date,
            duration_years=duration_years,
            end_date_str=end_date,
            ref_date_str=ref_date,
            parent_dasha_filter=parent_filter,
            antardasha_year_filter=antardasha_year
        )
        return jsonify({"status": "success", "data": pratyantar}), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
