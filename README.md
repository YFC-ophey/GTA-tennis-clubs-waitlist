# 🎾 GTA Tennis Clubs Data Portal

A beautiful, championship-themed web application for scraping and managing data from Greater Toronto Area tennis clubs. Features a Wimbledon-inspired design with purple, green, and cream colors.

## ✨ Features

- **🔍 Web Scraper**: Automatically extract data from 329 GTA tennis clubs
- **📊 Pre-loaded Data**: 325+ clubs with existing data from OTA & City of Toronto (260 OTA + 65 Toronto)
- **📧 Email Automation**: Send professional outreach to clubs with missing information
- **🏆 Championship Design**: Elegant Wimbledon-themed interface
- **⚡ Smart Scraping**: Skips clubs with complete data, only scrapes when needed

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd GTA-tennis-clubs-waitlist
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # or on macOS:
   pip3 install -r requirements.txt
   ```

3. **Configure email settings** (optional, required for email features)
   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and add your Gmail credentials:
   - `SENDER_EMAIL`: Your Gmail address
   - `SENDER_PASSWORD`: Your Gmail App Password (not regular password)

   **How to get a Gmail App Password:**
   1. Go to [Google Account Security](https://myaccount.google.com/security)
   2. Enable 2-Step Verification
   3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
   4. Generate a new App Password for "Mail"
   5. Copy the 16-character password to `.env`

4. **Run the application**
   ```bash
   python3 app.py
   ```

   The app will start on `http://localhost:5001`

   > **Note**: Port 5001 is used to avoid conflicts with macOS AirPlay Receiver

5. **Open in browser**

   Navigate to `http://localhost:5001`

## 📖 Usage

### Dashboard
- View statistics about total clubs, scraped data, and emails found
- Quick access to all features

### Scraper
1. Optionally set the number of clubs to scrape (leave empty for all)
2. Click "Start Scraping"
3. Monitor real-time progress
4. Results are automatically saved

### Results
- Browse all scraped data in a table
- Search by club name, location, or email
- Export data as CSV or JSON

### Email
1. Write or customize your email template
2. Click "Preview Emails" to see what will be sent
3. Use "Dry Run" to test without sending
4. Click "Send All Emails" to send actual emails

## 🎨 Design

The application features a Wimbledon Championship theme:
- **Colors**: Purple (#3E1F47), Green (#006633), Cream (#F5F3EF)
- **Typography**: Playfair Display (serif headings) + Inter (body)
- **Details**: Tennis court grid patterns, championship aesthetic

## 📁 Data Fields

The scraper extracts:
- Club Name
- Location/City
- Email Address
- Club Type (Private/Public)
- Membership Status
- Waitlist Length
- Number of Courts
- Court Surface
- Operating Season

## 🔧 Technical Stack

- **Backend**: Flask (Python web framework)
- **Scraping**: Requests + BeautifulSoup
- **Frontend**: HTML, CSS, JavaScript (jQuery)
- **Data**: Pandas for Excel/CSV handling
- **Email**: SMTP with Gmail

## 📝 Files

- `app.py` - Flask web application
- `scraper_simple.py` - Web scraping engine
- `email_agent.py` - Email automation
- `templates/` - HTML templates
  - `base.html` - Base template with Wimbledon styling
  - `index.html` - Dashboard
  - `scraper.html` - Scraper interface
  - `results.html` - Results viewer
  - `email.html` - Email management
- `GTA_Tennis_clubs_raw_data .xlsx` - Source data

## 🐛 Troubleshooting

**Port 5000 already in use**
- The app uses port 5001 by default to avoid macOS AirPlay conflicts

**"command not found: python"**
- Use `python3` instead of `python` on macOS/Linux

**Scraper button not working**
- Check browser console for errors
- Ensure JavaScript is enabled
- Try refreshing the page

**Email not sending**
- Verify `.env` file is configured correctly
- Ensure you're using a Gmail App Password, not regular password
- Check that 2-Step Verification is enabled on your Google account

## 📄 License

MIT License

## 🙏 Credits

Created with championship excellence for GTA tennis club data collection.
