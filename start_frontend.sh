#!/bin/bash

# Exit on error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Parse command line arguments
check_requirements=false
while getopts "r" opt; do
    case $opt in
        r) check_requirements=true ;;
        \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
    esac
done

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    check_requirements=true
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check requirements only if -r flag is provided or venv was just created
if [ "$check_requirements" = true ] && [ -f "requirements.txt" ]; then
    echo "Installing/updating requirements..."
    pip install -r requirements.txt
fi

# Add the project root to PYTHONPATH
export PYTHONPATH=$SCRIPT_DIR:$PYTHONPATH

# Start the Streamlit app
echo "Starting LoadApp.AI frontend..."
cd "$SCRIPT_DIR"
streamlit run src/frontend/app.py
