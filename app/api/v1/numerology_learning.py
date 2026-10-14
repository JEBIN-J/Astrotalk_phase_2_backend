"""
Flask API Blueprint for Numerology Learning Centre.
Handles educational content delivery, quizzes, grading, progress, and interactive calculations.
"""
from flask import Blueprint, jsonify, request
from app.services.learning_content_service import LearningContentService
from app.services.learning_numerology_calculator import LearningNumerologyCalculator

numerology_learning_bp = Blueprint("numerology_learning", __name__)

@numerology_learning_bp.route("/modules", methods=["GET"])
def get_modules():
    """Returns published learning modules with optional difficulty and search filters."""
    difficulty = request.args.get("difficulty")
    search = request.args.get("search")
    modules = LearningContentService.get_modules(difficulty=difficulty, search=search)
    return jsonify({
        "status": "success",
        "data": modules,
        "count": len(modules)
    }), 200

@numerology_learning_bp.route("/modules/<module_identifier>", methods=["GET"])
def get_module_detail(module_identifier):
    """Returns detailed information and lessons for a specific module."""
    mod = LearningContentService.get_module_detail(module_identifier)
    if not mod:
        return jsonify({"status": "error", "message": f"Module '{module_identifier}' not found or unpublished."}), 404
    return jsonify({
        "status": "success",
        "data": mod
    }), 200

@numerology_learning_bp.route("/lessons/<lesson_identifier>", methods=["GET"])
def get_lesson_detail(lesson_identifier):
    """Returns rich lesson content, worked examples, formulas, common mistakes, and references."""
    lesson = LearningContentService.get_lesson_detail(lesson_identifier)
    if not lesson:
        return jsonify({"status": "error", "message": f"Lesson '{lesson_identifier}' not found or unpublished."}), 404
    return jsonify({
        "status": "success",
        "data": lesson
    }), 200

@numerology_learning_bp.route("/quizzes/<int:quiz_id>", methods=["GET"])
def get_quiz(quiz_id):
    """Returns quiz questions and answer choices with server answer keys strictly stripped."""
    quiz = LearningContentService.get_quiz_safe(quiz_id)
    if not quiz:
        return jsonify({"status": "error", "message": f"Quiz {quiz_id} not found."}), 404
    return jsonify({
        "status": "success",
        "data": quiz
    }), 200

@numerology_learning_bp.route("/quizzes/<int:quiz_id>/submit", methods=["POST"])
def submit_quiz(quiz_id):
    """Grades submitted quiz answers on the backend and records user attempt."""
    data = request.get_json() or {}
    user_id = data.get("user_id", "guest_learner")
    answers = data.get("answers", {})

    if not isinstance(answers, dict):
        return jsonify({"status": "error", "message": "'answers' must be a key-value mapping of question IDs to answer IDs."}), 400

    try:
        result = LearningContentService.grade_and_submit_quiz(quiz_id, user_id, answers)
        return jsonify({
            "status": "success",
            "data": result
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Quiz grading failed: {str(e)}"}), 500

@numerology_learning_bp.route("/progress", methods=["GET"])
def get_progress():
    """Retrieves verified database progress for the specified user or guest."""
    user_id = request.args.get("user_id", "guest_learner")
    progress = LearningContentService.get_progress(user_id)
    return jsonify({
        "status": "success",
        "data": progress
    }), 200

@numerology_learning_bp.route("/progress", methods=["POST"])
def update_progress():
    """Updates progress for a lesson (e.g. marked completed)."""
    data = request.get_json() or {}
    user_id = data.get("user_id", "guest_learner")
    lesson_id = data.get("lesson_id") or data.get("lesson_code")
    status = data.get("status", "completed")

    if not lesson_id:
        return jsonify({"status": "error", "message": "lesson_id or lesson_code is required."}), 400

    try:
        res = LearningContentService.update_lesson_progress(user_id, lesson_id, status)
        return jsonify({
            "status": "success",
            "data": res
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@numerology_learning_bp.route("/calculate", methods=["POST"])
def calculate():
    """
    Executes actual backend calculation for interactive learning exercises.
    Accepts calc_type and inputs, returning deterministic step-by-step traces.
    """
    data = request.get_json() or {}
    calc_type = data.get("calc_type", "").lower().strip()
    inputs = data.get("inputs", {})
    system = data.get("system", "pythagorean").lower().strip()

    if not calc_type:
        return jsonify({"status": "error", "message": "Field 'calc_type' is required."}), 400

    try:
        calc = LearningNumerologyCalculator
        if calc_type == "birth_number":
            dob = inputs.get("date_of_birth") or inputs.get("dob")
            if not dob:
                return jsonify({"status": "error", "message": "inputs.date_of_birth is required."}), 400
            res = calc.calculate_birth_number(dob)

        elif calc_type == "life_path":
            dob = inputs.get("date_of_birth") or inputs.get("dob")
            if not dob:
                return jsonify({"status": "error", "message": "inputs.date_of_birth is required."}), 400
            preserve_master = inputs.get("preserve_master", False)
            res = calc.calculate_life_path(dob, preserve_master=preserve_master)

        elif calc_type == "name_number" or calc_type == "expression_number":
            name = inputs.get("name") or inputs.get("birth_name")
            if not name:
                return jsonify({"status": "error", "message": "inputs.name is required."}), 400
            res = calc.calculate_name_number(name, system=system)

        elif calc_type == "soul_urge":
            name = inputs.get("name") or inputs.get("birth_name")
            if not name:
                return jsonify({"status": "error", "message": "inputs.name is required."}), 400
            res = calc.calculate_soul_urge(name, system=system)

        elif calc_type == "personality_number":
            name = inputs.get("name") or inputs.get("birth_name")
            if not name:
                return jsonify({"status": "error", "message": "inputs.name is required."}), 400
            res = calc.calculate_personality_number(name, system=system)

        elif calc_type == "personal_year":
            dob = inputs.get("date_of_birth") or inputs.get("dob")
            target_year = int(inputs.get("target_year", 2026))
            if not dob:
                return jsonify({"status": "error", "message": "inputs.date_of_birth is required."}), 400
            res = calc.calculate_personal_year(dob, target_year)

        elif calc_type == "missing_numbers":
            name = inputs.get("name") or inputs.get("birth_name")
            if not name:
                return jsonify({"status": "error", "message": "inputs.name is required."}), 400
            res = calc.calculate_missing_numbers(name)

        elif calc_type == "compatibility":
            dob_a = inputs.get("dob_a") or inputs.get("date_of_birth_a")
            dob_b = inputs.get("dob_b") or inputs.get("date_of_birth_b")
            if not dob_a or not dob_b:
                return jsonify({"status": "error", "message": "inputs.dob_a and inputs.dob_b are required."}), 400
            name_a = inputs.get("name_a", "")
            name_b = inputs.get("name_b", "")
            res = calc.calculate_compatibility(dob_a, dob_b, name_a, name_b)

        elif calc_type == "child_numerology":
            child_name = inputs.get("child_name") or inputs.get("name")
            dob = inputs.get("date_of_birth") or inputs.get("dob")
            if not child_name or not dob:
                return jsonify({"status": "error", "message": "inputs.child_name and inputs.date_of_birth are required."}), 400
            res = calc.calculate_child_numerology(child_name, dob)

        else:
            return jsonify({
                "status": "error",
                "message": f"Unsupported calc_type: '{calc_type}'. Supported types: birth_number, life_path, name_number, soul_urge, personality_number, personal_year, missing_numbers, compatibility, child_numerology."
            }), 400

        return jsonify({
            "status": "success",
            "data": res
        }), 200

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Calculation failed: {str(e)}"}), 500

@numerology_learning_bp.route("/admin/status", methods=["GET"])
def get_admin_status():
    """Returns database content stats and editorial status."""
    audit = LearningContentService.get_admin_audit()
    return jsonify({
        "status": "success",
        "data": audit
    }), 200
