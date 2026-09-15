from flask import Blueprint, request, jsonify
from datetime import datetime, timezone as dt_timezone
import pytz
from app.services.tarot.tarot_data import get_all_cards, get_card_by_id
from app.services.tarot.tarot_engine import TarotEngine
from app.services.tarot.astro_tarot_engine import AstroTarotEngine
from app.services.tarot.tarot_history_service import TarotHistoryService

tarot_bp = Blueprint("tarot", __name__)

# Basic user id extraction for demo purposes (assuming query param or basic auth token in a real app)
def get_user_id():
    return request.headers.get("X-User-Id", "anonymous")

@tarot_bp.route("/cards", methods=["GET"])
def get_cards():
    return jsonify({"cards": get_all_cards()})

@tarot_bp.route("/cards/<card_id>", methods=["GET"])
def get_card(card_id):
    card = get_card_by_id(card_id)
    if card:
        return jsonify(card)
    return jsonify({"error": "Card not found"}), 404

@tarot_bp.route("/daily", methods=["GET", "POST"])
def daily_tarot():
    user_id = get_user_id()
    tz_offset = float(request.args.get("timezone", 0.0) if request.method == "GET" else request.json.get("timezone", 0.0))
    
    # Calculate user's local date
    utc_now = datetime.now(dt_timezone.utc)
    local_time = utc_now.timestamp() + (tz_offset * 3600)
    local_date_str = datetime.fromtimestamp(local_time, dt_timezone.utc).strftime("%Y-%m-%d")

    # If GET, only fetch existing
    if request.method == "GET":
        existing = TarotHistoryService.get_daily_reading(user_id, local_date_str)
        if existing:
            card = get_card_by_id(existing["card_id"])
            card["orientation"] = existing["orientation"]
            return jsonify({"reading": TarotEngine.interpret_card(card), "date": local_date_str})
        return jsonify({"error": "No daily reading exists for today. Use POST to generate one."}), 404

    # If POST, fetch existing or create new
    existing = TarotHistoryService.get_daily_reading(user_id, local_date_str)
    if existing:
        card = get_card_by_id(existing["card_id"])
        card["orientation"] = existing["orientation"]
        return jsonify({"reading": TarotEngine.interpret_card(card), "date": local_date_str, "status": "existing"})

    # Create new
    seed = TarotEngine.generate_seed()
    drawn_cards, _ = TarotEngine.draw_cards(1, seed)
    card = drawn_cards[0]
    
    TarotHistoryService.save_daily_reading(
        user_id, card["id"], card["orientation"], seed, local_date_str, tz_offset
    )
    
    return jsonify({"reading": TarotEngine.interpret_card(card), "date": local_date_str, "status": "new"})

def generate_spread_reading(spread_type, context="general"):
    data = request.json or {}
    question = data.get("question", "")
    seed = data.get("seed")
    user_id = get_user_id()
    
    reading = TarotEngine.create_spread(spread_type, seed)
    
    # Save history
    record_id = TarotHistoryService.save_reading(
        user_id, spread_type, question, reading, None, reading["seed"]
    )
    
    reading["id"] = record_id
    reading["question"] = question
    return jsonify(reading)

@tarot_bp.route("/single", methods=["POST"])
def single_card():
    return generate_spread_reading("single")

@tarot_bp.route("/three-card", methods=["POST"])
def three_card():
    return generate_spread_reading("three_card_past_present_future")

@tarot_bp.route("/yes-no", methods=["POST"])
def yes_no():
    return generate_spread_reading("yes_no", "yes_no")

@tarot_bp.route("/love", methods=["POST"])
def love():
    return generate_spread_reading("love_five_card", "love")

@tarot_bp.route("/career", methods=["POST"])
def career():
    return generate_spread_reading("career_five_card", "career")

@tarot_bp.route("/celtic-cross", methods=["POST"])
def celtic_cross():
    return generate_spread_reading("celtic_cross")

@tarot_bp.route("/year-ahead", methods=["POST"])
def year_ahead():
    return generate_spread_reading("year_ahead")

@tarot_bp.route("/astrological-spread", methods=["POST"])
def astrological_spread():
    return generate_spread_reading("astrological_houses")

@tarot_bp.route("/astro", methods=["POST"])
def astro_tarot():
    data = request.json
    if not data or 'birth_date' not in data:
        return jsonify({"error": "birth_date, birth_time, latitude, longitude, timezone required"}), 400
        
    user_id = get_user_id()
    question = data.get("question", "")
    
    try:
        astro_reading = AstroTarotEngine.get_astro_tarot_reading(
            birth_date=data["birth_date"],
            birth_time=data["birth_time"],
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            tz_offset=float(data["timezone"]),
            question=question,
            seed=data.get("seed")
        )
        
        # Save history
        record_id = TarotHistoryService.save_reading(
            user_id, "astro_tarot", question, 
            astro_reading["tarot_spread"], 
            {"natal": astro_reading["natal_snapshot"], "transit": astro_reading["transit_snapshot"]},
            astro_reading["tarot_spread"]["seed"]
        )
        astro_reading["id"] = record_id
        
        return jsonify(astro_reading)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@tarot_bp.route("/history", methods=["GET"])
def history():
    user_id = get_user_id()
    history_records = TarotHistoryService.get_user_history(user_id)
    return jsonify({"history": history_records})
