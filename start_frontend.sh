#!/bin/bash

# Exit on error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements need to be installed
if [ -f "requirements.txt" ]; then
    echo "Checking requirements..."
    missing_packages=false
    while IFS= read -r requirement; do
        if ! pip freeze | grep -i "^${requirement%%[><=~]=*}=\|^${requirement%%[><=~]=*}==\|^${requirement%%[><=~]=*}~=" > /dev/null; then
            missing_packages=true
            break
        fi
    done < requirements.txt

    if [ "$missing_packages" = true ]; then
        echo "Installing missing requirements..."
        pip install -r requirements.txt
    else
        echo "All requirements are already installed."
    fi
fi

# Add the project root to PYTHONPATH
export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH

# Start the Streamlit app
echo "Starting LoadApp.AI frontend..."
cd "$SCRIPT_DIR"
streamlit run src/frontend/app.py
