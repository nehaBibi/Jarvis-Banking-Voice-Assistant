#!/bin/bash
# Jarvis Banking AI - Startup Script for Mac/Linux

echo ""
echo "========================================"
echo "Jarvis Banking AI - Backend Startup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from python.org"
    exit 1
fi

echo "[1/3] Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "[2/3] Installing dependencies..."
    pip3 install -r requirements.txt
else
    echo "[2/3] Dependencies already installed"
fi

echo "[3/3] Starting Flask backend on http://localhost:5000"
echo ""
echo "NOTE: When you see 'Running on http://0.0.0.0:5000'"
echo "Then the backend is ready!"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
