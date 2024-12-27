"""Run script for the LoadApp.AI Flask application."""
import os
from src.api.app import app
from src.settings import get_settings

if __name__ == '__main__':
    settings = get_settings()
    
    # Set Flask environment variables
    os.environ['FLASK_ENV'] = settings.ENV
    os.environ['FLASK_DEBUG'] = '1' if settings.ENV == 'development' else '0'
    
    # Run the Flask app
    app.run(host=settings.BACKEND_HOST, port=settings.PORT, debug=settings.ENV == 'development')
