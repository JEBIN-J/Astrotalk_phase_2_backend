from flask import Blueprint, request, jsonify
from app.services.numerology_service import NumerologyService

numerology_bp = Blueprint('numerology', __name__)

@numerology_bp.route("/profile", methods=["POST"])
def calculate_full_profile():
    try:
        data = request.get_json()
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
