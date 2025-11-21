#!/bin/bash
# Setup script for GTA Tennis Clubs Scraper

echo "=========================================="
echo "GTA Tennis Clubs Scraper - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo ""
echo "Installing Playwright browsers..."
playwright install chromium

if [ $? -ne 0 ]; then
    echo "Warning: Failed to install Playwright browsers"
    echo "You may need to run: playwright install chromium"
fi

echo ""
echo "Creating results directory..."
mkdir -p results

echo ""
echo "Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template"
    echo "Please edit .env and add your credentials:"
    echo "  - EMAIL_ADDRESS"
    echo "  - EMAIL_PASSWORD (use App Password for Gmail)"
    echo ""
else
    echo ".env file already exists"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your email credentials"
echo "2. Test with: python main.py --scrape --max-clubs 10"
echo "3. Analyze: python main.py --analyze"
echo "4. Export: python main.py --export csv"
echo ""
echo "For help: python main.py --help"
echo ""
