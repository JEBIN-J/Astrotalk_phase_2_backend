"""Flask Application Factory."""
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from app.core.config import config
from app.api.v1.auth import auth_bp
from app.api.v1.horoscope import horoscope_bp
from app.api.v1.panchanga import panchang_bp
from app.api.v1.matching import matching_bp
from app.api.v1.gochara import gochara_bp
from app.api.v1.ephemeris import ephemeris_bp
from app.api.v1.ayanamsa import ayanamsa_bp
from app.api.v1.places import places_bp
from app.api.v1.ai_astro import ai_astro_bp
from app.api.v1.reports import reports_bp


def create_app(config_class=config) -> Flask:
    """Create and configure the Flask Application instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for Flutter mobile, web and desktop clients
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Request timer middleware
    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request
    def add_process_time(response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            response.headers["X-Process-Time"] = f"{duration:.4f}s"
        return response

    # Global Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "status": 404}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error", "status": 500}), 500

    # Root and Health Check
    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "app": config.APP_NAME,
            "version": config.APP_VERSION,
            "status": "online",
            "framework": "Flask 3.x",
            "api_v1_prefix": "/api/v1"
        }), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "version": config.APP_VERSION
        }), 200

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(horoscope_bp)
    app.register_blueprint(panchang_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(gochara_bp)
    app.register_blueprint(ephemeris_bp)
    app.register_blueprint(ayanamsa_bp)
    app.register_blueprint(places_bp)
    app.register_blueprint(ai_astro_bp)
    app.register_blueprint(reports_bp)

    return app
