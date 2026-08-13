"""Flask AI Vision Blueprint for Palm & Face Reading."""
from flask import Blueprint, jsonify, request
from app.services.vision_engine import analyze_face, analyze_palm

ai_vision_bp = Blueprint('ai_vision', __name__)

@ai_vision_bp.route("/palm-reading", methods=["POST"])
def palm_reading():
    """Analyze palm lines dynamically using OpenCV and MediaPipe."""
    if 'file' not in request.files:
        return jsonify({"detail": "File is required"}), 400
    file = request.files['file']
    data = file.read()
    if not data:
        return jsonify({"detail": "Empty file"}), 400
        
    try:
        analysis, summary, conf = analyze_palm(data)
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "overall_summary": summary,
            "confidence": f"{conf}%"
        })
    except Exception as e:
        return jsonify({"detail": f"Vision analysis failed: {str(e)}"}), 500

@ai_vision_bp.route("/face-reading", methods=["POST"])
def face_reading():
    """Analyze facial features dynamically using MediaPipe Face Mesh."""
    if 'file' not in request.files:
        return jsonify({"detail": "File is required"}), 400
    file = request.files['file']
    data = file.read()
    if not data:
        return jsonify({"detail": "Empty file"}), 400
        
    try:
        analysis, summary, conf = analyze_face(data)
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "overall_summary": summary,
            "confidence": f"{conf}%"
        })
    except Exception as e:
        return jsonify({"detail": f"Vision analysis failed: {str(e)}"}), 500
