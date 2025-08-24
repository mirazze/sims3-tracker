#!/bin/bash
echo "Starting Sims 3 Completionist Tracker..."
cd "$(dirname "$0")"
source venv/bin/activate
python3 -m streamlit run app.py
