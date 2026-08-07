"""Flask Auth and User Profile Blueprint."""
import uuid
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

# In-memory storage for development / testing
USERS_DB = {}
SAVED_CHARTS_DB = {}


def token_required(f):
    """Decorator to protect routes with JWT Bearer authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401
            
        payload = decode_access_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired authentication token"}), 401
            
        user_id = payload.get("sub")
        current_user = USERS_DB.get(user_id)
        if not current_user:
            current_user = {
                "id": user_id,
                "name": "AstroTalk User",
                "email": "user@astrotalk.com",
                "created_at": datetime.now().isoformat()
            }
        return f(current_user, *args, **kwargs)
    return decorated


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "User")
    phone = data.get("phone")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    for user in USERS_DB.values():
        if user["email"] == email:
            return jsonify({"error": "User with this email already exists"}), 400
            
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "name": name,
        "email": email,
        "phone": phone,
        "hashed_password": get_password_hash(password),
        "created_at": datetime.now().isoformat()
    }
    USERS_DB[user_id] = user_data
    token = create_access_token(subject=user_id)
    
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "name": name,
        "email": email
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate and obtain access token."""
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
        
    matched_user = None
    for user in USERS_DB.values():
        if user["email"] == email:
            matched_user = user
            break
            
    if not matched_user or not verify_password(password, matched_user["hashed_password"]):
        # Support demo testing credentials
        if email in ["demo@astrotalk.com", "rahul@example.com"] and password in ["password123", "demo123"]:
            demo_id = "demo_user_1"
            return jsonify({
                "access_token": create_access_token(subject=demo_id),
                "token_type": "bearer",
                "user_id": demo_id,
                "name": "Rahul Sharma",
                "email": email
            }), 200
        return jsonify({"error": "Invalid email or password credentials"}), 401
        
    token = create_access_token(subject=matched_user["id"])
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "user_id": matched_user["id"],
        "name": matched_user["name"],
        "email": matched_user["email"]
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_profile(current_user):
    """Retrieve logged in user profile."""
    return jsonify({
        "user_id": current_user["id"],
        "name": current_user.get("name", "User"),
        "email": current_user.get("email", ""),
        "phone": current_user.get("phone"),
        "created_at": current_user.get("created_at", datetime.now().isoformat()),
        "saved_kundlis_count": len(SAVED_CHARTS_DB.get(current_user["id"], []))
    }), 200
