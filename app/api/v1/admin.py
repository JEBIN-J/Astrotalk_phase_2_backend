"""Flask Admin Panel Blueprint."""
from flask import Blueprint, jsonify

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/stats", methods=["GET"])
def get_admin_stats():
    """Retrieve high-level dashboard statistics."""
    return jsonify({
        "total_users": 15420,
        "active_subscribers": 3205,
        "daily_active_users": 1850,
        "total_revenue": "$45,200",
        "recent_signups": 125,
        "ai_calls_made": 8940,
        "kundli_generated": 24500
    })

@admin_bp.route("/users", methods=["GET"])
def get_recent_users():
    """Retrieve list of recent users."""
    return jsonify([
        {"id": "u_1", "name": "Rahul Sharma", "email": "rahul@example.com", "status": "Pro", "joined": "2026-08-01"},
        {"id": "u_2", "name": "Priya Singh", "email": "priya@example.com", "status": "Free", "joined": "2026-08-10"},
        {"id": "u_3", "name": "Amit Kumar", "email": "amit@example.com", "status": "Pro", "joined": "2026-07-15"}
    ])
