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
        
        if system == "vedic":
            result = NumerologyService.calculate_vedic(name, dob)
        else:
            result = NumerologyService.calculate_pythagorean(name, dob)
            
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 400
            
        return jsonify({"status": "success", "data": result}), 200
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
