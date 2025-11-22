#!/bin/bash
# Start the GTA Tennis Clubs Scraper Web App

echo "=========================================="
echo "🎾 GTA Tennis Clubs Scraper - Web App"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Dependencies not found. Installing..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
fi

echo "✅ Dependencies OK"
echo ""
echo "🚀 Starting web application..."
echo ""
echo "📱 Open your browser and go to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the Flask app
python3 app.py
