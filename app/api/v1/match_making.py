"""
match_making.py
REST API Blueprint for Vedic Match Making / Kundli Milan Module.
"""
from flask import Blueprint, request, jsonify
import sqlite3
import json
from datetime import datetime
from app.services.match_making_engine import MatchMakingEngine
from app.core.database import get_db_connection
from app.api.v1.auth import get_current_user

match_making_bp = Blueprint("match_making", __name__)

def _resolve_user_id(data: dict = None):
    """Resolves authenticated user ID from JWT or payload."""
    current_user, _ = get_current_user()
    if current_user and current_user.get("id"):
        return str(current_user.get("id"))
    if data and data.get("user_id"):
        return str(data.get("user_id"))
    uid = request.args.get("user_id") or request.headers.get("X-User-ID")
    if uid:
        return str(uid)
    return "guest_user"

@match_making_bp.route("", methods=["POST"])
@match_making_bp.route("/", methods=["POST"])
@match_making_bp.route("/calculate", methods=["POST"])
def calculate_match():
    """
    Main Match Making calculation endpoint.
    Calculates Ashta Koota (36 Gunas), South Indian Poruthams (10 Poruthams),
    and Manglik Analysis using Swiss Ephemeris.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        boy_data = data.get("boy")
        girl_data = data.get("girl")

        if not boy_data or not girl_data:
            return jsonify({
                "status": "error",
                "message": "Both 'boy' and 'girl' birth profiles are required."
            }), 400

        # Validate required date of birth
        if not boy_data.get("date_of_birth") or not girl_data.get("date_of_birth"):
            return jsonify({
                "status": "error",
                "message": "Valid 'date_of_birth' (YYYY-MM-DD) is required for both individuals."
            }), 400

        tradition = data.get("tradition", "both")
        result = MatchMakingEngine.calculate_match(boy_data, girl_data, tradition=tradition)

        return jsonify({
            "status": "success",
            "data": result
        }), 200

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Astrological calculation error: {str(e)}"}), 500

@match_making_bp.route("/ashta-koota", methods=["POST"])
def calculate_ashta_koota():
    """Calculates traditional 8 Kootas (36 Gunas) exclusively."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        boy_data = data.get("boy")
        girl_data = data.get("girl")

        if not boy_data or not girl_data:
            return jsonify({"status": "error", "message": "Both 'boy' and 'girl' profiles required."}), 400

        result = MatchMakingEngine.calculate_match(boy_data, girl_data, tradition="ashta_koota")
        return jsonify({
            "status": "success",
            "data": {
                "total_score": result["total_score"],
                "max_score": result["max_score"],
                "percentage": result["percentage"],
                "status": result["status"],
                "recommendation": result["recommendation"],
                "kootas": result["kootas"],
                "profiles": result["profiles"]
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@match_making_bp.route("/porutham", methods=["POST"])
def calculate_porutham():
    """Calculates South Indian 10 Poruthams exclusively."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        boy_data = data.get("boy")
        girl_data = data.get("girl")

        if not boy_data or not girl_data:
            return jsonify({"status": "error", "message": "Both 'boy' and 'girl' profiles required."}), 400

        result = MatchMakingEngine.calculate_match(boy_data, girl_data, tradition="porutham")
        return jsonify({
            "status": "success",
            "data": {
                "south_indian_porutham": result["south_indian_porutham"],
                "profiles": result["profiles"],
                "disclaimer": result["disclaimer"]
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@match_making_bp.route("/dosha-analysis", methods=["POST"])
def calculate_dosha():
    """Calculates Mangal (Kuja), Nadi, and Bhakoot Dosha analysis."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        boy_data = data.get("boy")
        girl_data = data.get("girl")

        if not boy_data or not girl_data:
            return jsonify({"status": "error", "message": "Both 'boy' and 'girl' profiles required."}), 400

        result = MatchMakingEngine.calculate_match(boy_data, girl_data, tradition="both")
        return jsonify({
            "status": "success",
            "data": {
                "manglik_analysis": result["manglik_analysis"],
                "nadi_koota": next((k for k in result["kootas"] if k["koota_name"] == "Nadi"), None),
                "bhakoot_koota": next((k for k in result["kootas"] if k["koota_name"] == "Bhakoot"), None),
                "remedies": result["remedies"]
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@match_making_bp.route("/methods", methods=["GET"])
def get_matching_methods():
    """Returns available matching traditions and calculation metadata."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT method_code, method_name, engine_version, ayanamsha_code, zodiac_convention FROM astrology_calculation_methods WHERE is_active = 1")
        methods = [
            {
                "method_code": row[0],
                "method_name": row[1],
                "engine_version": row[2],
                "ayanamsha_code": row[3],
                "zodiac_convention": row[4]
            }
            for row in cursor.fetchall()
        ]
        conn.close()
        return jsonify({
            "status": "success",
            "methods": methods,
            "traditions": [
                {"code": "ashta_koota", "name": "Ashta Koota / 36 Guna Milan (North Indian & Universal)", "max_points": 36},
                {"code": "porutham", "name": "South Indian 10 Poruthams (Tamil / Kerala / Dasa Porutham)", "max_factors": 10},
                {"code": "both", "name": "Comprehensive Vedic Milan (Ashta Koota + Porutham + Kuja Dosha)", "recommended": True}
            ]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@match_making_bp.route("/save-report", methods=["POST"])
def save_matching_report():
    """Saves a calculated match report for future reference."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        user_id = _resolve_user_id(data)
        report_data = data.get("report_data")

        if not report_data:
            return jsonify({"status": "error", "message": "report_data is required"}), 400

        boy_name = report_data.get("boy_name", "Groom")
        girl_name = report_data.get("girl_name", "Bride")
        method_code = report_data.get("calculation_tradition", "both")
        rule_set_version = "1.0.0"
        engine_version = report_data.get("engine_version", "2.0.0-SwissEph")
        total_score = float(report_data.get("total_score", 0.0))
        max_score = float(report_data.get("max_score", 36.0))
        status = report_data.get("status", "Calculated")
        now = datetime.utcnow().isoformat()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO saved_matching_reports
            (authorized_owner_user_id, boy_name, girl_name, method_code, rule_set_version, engine_version, total_score, max_score, status, report_result_data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, boy_name, girl_name, method_code, rule_set_version, engine_version, total_score, max_score, status, json.dumps(report_data), now, now))
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Report saved successfully",
            "report_id": report_id
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@match_making_bp.route("/saved-reports", methods=["GET"])
def get_saved_reports():
    """Retrieves list of saved reports for current user."""
    try:
        user_id = _resolve_user_id()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, boy_name, girl_name, method_code, total_score, max_score, status, created_at
            FROM saved_matching_reports
            WHERE authorized_owner_user_id = ?
            ORDER BY id DESC
            LIMIT 50
        """, (user_id,))
        rows = cursor.fetchall()
        reports = [
            {
                "id": r[0],
                "boy_name": r[1],
                "girl_name": r[2],
                "method_code": r[3],
                "total_score": r[4],
                "max_score": r[5],
                "status": r[6],
                "created_at": r[7]
            }
            for r in rows
        ]
        conn.close()
        return jsonify({"status": "success", "reports": reports}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
