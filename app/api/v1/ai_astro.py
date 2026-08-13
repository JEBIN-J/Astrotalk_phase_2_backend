"""Flask AI Astrologer Consultation Blueprint."""
from flask import Blueprint, jsonify, request
from app.services.ai_astro_engine import generate_ai_astrology_insights

ai_astro_bp = Blueprint('ai_astro', __name__)

@ai_astro_bp.route("/chat", methods=["POST"])
def chat_ai():
    """Interact with the Vedic AI Astrologer."""
    data = request.json or {}
    question = data.get("question", "How is my future career?")
    birth_details = data.get("birth_details")
    category = data.get("category", "general")
    result = generate_ai_astrology_insights(question, birth_details, category)
    return jsonify(result)
