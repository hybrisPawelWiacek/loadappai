"""Run script for the LoadApp.AI Flask application."""
import os
from src.api.app import app

if __name__ == '__main__':
    # Set Flask environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)
