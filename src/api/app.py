"""Flask application module."""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/hello')
def hello_world():
    """Simple test endpoint."""
    return jsonify({'message': 'Hello, World!'})
