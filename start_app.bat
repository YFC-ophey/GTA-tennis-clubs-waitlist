@echo off
REM Start the GTA Tennis Clubs Scraper Web App (Windows)

echo ==========================================
echo 🎾 GTA Tennis Clubs Scraper - Web App
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed
    pause
    exit /b 1
)

echo 📦 Checking dependencies...

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Dependencies not found. Installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo ✅ Dependencies OK
echo.
echo 🚀 Starting web application...
echo.
echo 📱 Open your browser and go to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Start the Flask app
python app.py
