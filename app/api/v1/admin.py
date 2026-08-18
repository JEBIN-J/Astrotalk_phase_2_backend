"""Flask Admin Panel Blueprint."""
from flask import Blueprint, jsonify

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/login", methods=["POST"])
def admin_login():
    """Authenticate admin user."""
    from flask import request
    
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing credentials"}), 400
        
    username = data.get("username")
    password = data.get("password")
    
    if username == "admin" and password == "admin123":
        return jsonify({"status": "success", "message": "Login successful"})
    else:
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

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

@admin_bp.route("/notifications/send", methods=["POST"])
def send_notification():
    """Send a push notification to all users."""
    from flask import request
    
    data = request.get_json()
    if not data or not data.get("title") or not data.get("message"):
        return jsonify({"status": "error", "message": "Title and message are required"}), 400
        
    title = data.get("title")
    message = data.get("message")
    
    # Here you would typically integrate with Firebase Cloud Messaging (FCM) or APNS
    # For now, we mock the success response.
    return jsonify({
        "status": "success", 
        "message": f"Successfully broadcasted '{title}' to all users!"
    })
