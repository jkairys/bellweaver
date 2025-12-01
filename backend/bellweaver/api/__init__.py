"""
Flask application factory for Bellweaver API.

Provides REST API endpoints for accessing aggregated school calendar events.
"""

from flask import Flask

from bellweaver.db.database import init_db
from bellweaver.api.routes import register_routes


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Initialize database on startup
    with app.app_context():
        init_db()

    # Register all route blueprints
    register_routes(app)

    return app


if __name__ == "__main__":
    import os

    app = create_app()
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=5000, use_reloader=debug)
