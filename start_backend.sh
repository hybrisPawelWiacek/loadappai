#!/bin/bash

# Exit on error
set -e

# Directory containing this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
if [ ! -d "$DIR/venv" ]; then
    echo "Error: Virtual environment not found in $DIR/venv"
    echo "Please create a virtual environment first using:"
    echo "python3 -m venv venv"
    echo "And install dependencies using:"
    echo "source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source "$DIR/venv/bin/activate"

# Export Flask environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Kill any existing Flask processes
pkill -f "python.*run.py" || true

# Start the Flask backend using run.py
echo "Starting Flask backend on port 5001..."
python run.py

# Deactivate virtual environment on exit
deactivate
