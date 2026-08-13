"""Flask Content Blueprint for Quotes, Notifications, and Muhurat."""
from flask import Blueprint, jsonify, request
from datetime import datetime

content_bp = Blueprint('content', __name__)

@content_bp.route("/quotes", methods=["GET"])
def get_daily_quotes():
    """Retrieve daily astrological quotes."""
    return jsonify([
        {"id": 1, "text": "The stars only impel, they do not compel.", "author": "Vedic Wisdom", "category": "Motivation"},
        {"id": 2, "text": "Saturn delays, but it never denies.", "author": "Astrology Proverb", "category": "Patience"},
        {"id": 3, "text": "A favorable Jupiter brings expansion where you least expect it.", "author": "Cosmic Insight", "category": "Growth"}
    ])

@content_bp.route("/notifications", methods=["GET"])
def get_notifications():
    """Retrieve user notifications and alerts."""
    return jsonify([
        {"id": 1, "title": "Moon enters Taurus", "body": "An emotionally stable and grounding period begins.", "type": "transit", "time": "1 hour ago"},
        {"id": 2, "title": "Abhijit Muhurta Active", "body": "Perfect time to start new ventures (11:58 AM - 12:49 PM).", "type": "muhurta", "time": "Just now"},
        {"id": 3, "title": "Pro Subscription Expiring", "body": "Your Pro plan expires in 3 days. Renew now for uninterrupted access.", "type": "account", "time": "1 day ago"}
    ])

@content_bp.route("/muhurat", methods=["GET"])
def get_muhurat():
    """Retrieve daily Shubh and Ashubh Muhurat timings."""
    latitude = float(request.args.get('latitude', 28.6139))
    longitude = float(request.args.get('longitude', 77.2090))
    return jsonify({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sunrise": "05:48 AM",
        "sunset": "07:08 PM",
        "abhijit_muhurta": "11:58 AM - 12:49 PM (Shubh)",
        "rahu_kaal": "12:28 PM - 02:08 PM (Ashubh)",
        "yamaganda": "07:28 AM - 09:08 AM",
        "gulika_kaal": "09:08 AM - 10:48 AM"
    })
