#!/bin/bash
echo "Setting up Sims 3 Completionist Tracker..."
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install requirements
echo "Installing Python packages..."
source venv/bin/activate
pip install -r requirements.txt

# Create database
echo "Creating database..."
python3 db/scripts/db_create_.py

# Load lifetime wishes
echo "Loading lifetime wishes..."
python3 db/scripts/load_lifetime_wishes.py

echo "Setup complete! Run './run.sh' to start the app."
