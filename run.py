#!/usr/bin/env python3
"""AstroTalk Flask Backend Server Runner."""
from app import create_app
from app.core.config import config

app = create_app()

if __name__ == "__main__":
    print(f"🌟 Starting {config.APP_NAME} v{config.APP_VERSION} (Pure Python Flask)")
    print(f"📡 API Endpoint Root: http://{config.HOST}:{config.PORT}/api/v1")
    print(f"❤️  Health Check:      http://{config.HOST}:{config.PORT}/health")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
