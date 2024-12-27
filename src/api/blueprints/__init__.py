"""Blueprint registration and initialization."""
from flask import Blueprint

# Import blueprints
from .routes.routes import routes_bp
from .costs.costs import costs_bp
from .offers.offers import offers_bp
from .settings.settings import settings_bp

def register_blueprints(app):
    """Register all blueprints with the Flask application."""
    app.register_blueprint(routes_bp, url_prefix='/api/routes')
    app.register_blueprint(costs_bp, url_prefix='/api/costs')
    app.register_blueprint(offers_bp, url_prefix='/api/offers')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
