@echo off
REM Jarvis Banking AI - Startup Script for Windows

echo.
echo ========================================
echo Jarvis Banking AI - Backend Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
pip list | findstr Flask >nul
if errorlevel 1 (
    echo [2/3] Installing dependencies...
    pip install -r requirements.txt
) else (
    echo [2/3] Dependencies already installed
)

echo [3/3] Starting Flask backend on http://localhost:5000
echo.
echo NOTE: Keep this window open. When you see:
echo   "Running on http://0.0.0.0:5000"
echo Then the backend is ready!
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
