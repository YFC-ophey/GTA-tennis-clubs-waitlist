# GTA Tennis Clubs Data Scraper

A comprehensive system for scraping tennis club information from the Greater Toronto Area, combining automated web scraping with email outreach for missing data.

> **⚠️ Important**: This scraper needs to run on your local machine (not in a restricted environment) to access tennis club websites. See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

## 🎨 Two Ways to Use

### 1. **Web App** (Recommended - Visual & Easy!) 🌟

Beautiful web interface with real-time progress, data viewer, and email management.

```bash
python app.py
# Open http://localhost:5000
```

**Features:**
- 📊 Interactive dashboard with statistics
- 🔍 Real-time scraping progress
- 📋 Searchable data viewer
- 📧 Email preview and management
- 📥 One-click CSV export

See [WEB_APP_GUIDE.md](WEB_APP_GUIDE.md) for full guide.

### 2. **Command Line** (Advanced)

Traditional CLI for automation and scripting.

```bash
python main.py --scrape --max-clubs 50
```

See usage sections below for CLI details.

---

## Features

- **Automated Web Scraping**: Extracts information from 306+ tennis club websites
- **Web Interface**: Beautiful, user-friendly dashboard (NEW!)
- **Email Outreach Agent**: Automatically contacts clubs with missing data
- **Google Sheets Integration**: Export directly to Google Sheets or CSV
- **Data Analysis**: Provides detailed statistics on data completeness
- **Robust Error Handling**: Graceful handling of failed scrapes and timeouts

## Extracted Data Fields

For each tennis club, the scraper attempts to extract:

- **Club Name**: Name of the tennis club
- **Location**: City only (e.g., "Toronto")
- **Email**: Contact email address
- **Club Type**: Private, Public, Community, etc.
- **Membership Status**: Open, Waitlist, or Closed
- **Current Waitlist Length**: Number of people on waitlist
- **Number of Courts**: Total tennis courts
- **Court Surface**: Clay, Hard Court, Grass, etc.
- **Operating Season**: Year-round, Summer, Winter, etc.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist.git
cd GTA-tennis-clubs-waitlist
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The scraper uses `requests` and `BeautifulSoup` (no Playwright required), making it lightweight and easy to set up!

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Email Configuration (for Gmail)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Google Sheets Configuration (optional)
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_NAME=GTA Tennis Clubs Data
```

**Note**: For Gmail, you need to use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

## Usage

### Quick Start - Test with 10 Clubs

```bash
# Scrape first 10 clubs
python main.py --scrape --max-clubs 10

# Analyze the results
python main.py --analyze

# Export to CSV
python main.py --export csv
```

### Full Pipeline

```bash
# 1. Scrape all 306 clubs
python main.py --scrape

# 2. Analyze data completeness
python main.py --analyze

# 3. Generate email outreach (dry run - no emails sent)
python main.py --email --dry-run

# 4. Export to CSV
python main.py --export csv
```

### Send Actual Emails

```bash
# Send emails to clubs with missing data
python main.py --email
```

### Export to Google Sheets

```bash
# First, set up Google Sheets credentials (see below)
python main.py --export sheets
```

## Command Line Arguments

```
usage: main.py [-h] [--scrape] [--email] [--export {csv,sheets}] [--analyze]
               [--input INPUT] [--output OUTPUT] [--max-clubs MAX_CLUBS]
               [--dry-run] [--sheet-name SHEET_NAME]

Actions:
  --scrape              Scrape tennis club websites
  --email               Send outreach emails to clubs with missing data
  --export {csv,sheets} Export data to CSV or Google Sheets
  --analyze             Analyze scraped data and show statistics

Configuration:
  --input INPUT         Input Excel file (default: GTA Tennis clubs data .xlsx)
  --output OUTPUT       Output JSON file (default: results/scraped_data.json)
  --max-clubs MAX_CLUBS Maximum number of clubs to scrape (for testing)
  --dry-run            Generate emails without actually sending them
  --sheet-name NAME     Google Sheets name
```

## Google Sheets Setup (Optional)

To export directly to Google Sheets:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Sheets API** and **Google Drive API**
4. Create a **Service Account**:
   - Go to "IAM & Admin" > "Service Accounts"
   - Create a service account
   - Create a JSON key and download it
5. Save the JSON file as `credentials.json` in the project root
6. Share your Google Sheet with the service account email (found in `credentials.json`)

Update `.env`:
```bash
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_NAME=GTA Tennis Clubs Data
```

## Project Structure

```
GTA-tennis-clubs-waitlist/
├── main.py                          # Main orchestrator script
├── scraper_simple.py                # HTTP-based web scraper (primary)
├── scraper.py                       # Playwright-based scraper (alternative)
├── email_agent.py                   # Email outreach automation
├── sheets_export.py                 # Google Sheets/CSV export
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore file
├── SETUP_GUIDE.md                   # Detailed setup instructions
├── GTA Tennis clubs data .xlsx      # Input: List of 306 clubs
├── results/                         # Output directory
│   ├── scraped_data.json           # Scraped data (JSON)
│   ├── scraped_data.csv            # Exported data (CSV)
│   └── email_log.json              # Email outreach log
└── README.md                        # This file
```

## How It Works

### 1. Web Scraping (`scraper_simple.py`)

- Uses **requests** + **BeautifulSoup** for reliable HTTP scraping
- Extracts data using:
  - BeautifulSoup for HTML parsing
  - Regex patterns for specific data fields
  - Smart location extraction (city only)
- Saves incrementally to prevent data loss
- Respects rate limits (0.5 seconds between requests)
- Handles SSL certificates automatically

### 2. Email Agent (`email_agent.py`)

- Identifies clubs with ≥3 missing fields or no email
- Generates personalized email templates
- Dry-run mode for testing
- Logs all email activity

### 3. Data Export (`sheets_export.py`)

- Export to CSV (always available)
- Export to Google Sheets (requires credentials)
- Formatted headers and clean data

### 4. Main Orchestrator (`main.py`)

- Command-line interface
- Combines all components
- Data analysis and reporting

## Example Output

```
======================================================================
Data Analysis Report
======================================================================
Total clubs: 306
Successfully scraped: 289 (94.4%)

Data Completeness:
----------------------------------------------------------------------
Field                          Found      Missing    Coverage
----------------------------------------------------------------------
Location                       245        61         80.1%
Email                          198        108        64.7%
Club Type                      156        150        51.0%
Membership Status              134        172        43.8%
Current Waitlist Length        45         261        14.7%
Number of Courts               178        128        58.2%
Court Surface                  167        139        54.6%
Operating Season               189        117        61.8%
======================================================================
```

## Troubleshooting

### Scraping Issues

- **Timeout errors**: Increase timeout in `scraper.py` (default: 30 seconds)
- **Failed scrapes**: Check website accessibility manually
- **Rate limiting**: Increase delay in `scraper.py` (currently 1 second)

### Email Issues

- **Gmail authentication failed**: Use an [App Password](https://support.google.com/accounts/answer/185833)
- **SMTP errors**: Check SMTP settings in `.env`

### Google Sheets Issues

- **Authentication failed**: Verify `credentials.json` is correct
- **Permission denied**: Share the sheet with your service account email

## Development

### Run Individual Components

```bash
# Test scraper with 5 clubs
python scraper.py

# Test email generation (dry run)
python email_agent.py

# Test CSV export
python sheets_export.py
```

### Add Custom Data Fields

Edit `scraper.py` and add new extraction methods:

```python
def extract_new_field(self, soup, page_text):
    # Your extraction logic here
    return extracted_value
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file for details

## Author

Created for GTA tennis club data collection and community building.

## Acknowledgments

- Tennis Ontario
- All GTA tennis clubs for making their information available
