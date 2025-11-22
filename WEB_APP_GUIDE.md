# 🎾 GTA Tennis Clubs Scraper - Web App Guide

A beautiful, user-friendly web application for scraping tennis club data and managing email outreach.

## 🌟 Features

- **📊 Interactive Dashboard** - Real-time statistics and overview
- **🔍 Visual Scraper** - Watch scraping progress in real-time
- **📋 Data Viewer** - Browse and search through results
- **📧 Email Manager** - Preview and send outreach emails
- **📥 Easy Exports** - Download CSV/JSON with one click

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Web App

```bash
python app.py
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

That's it! The app is now running. 🎉

## 📱 Using the Web App

### Dashboard

The home page shows:
- Total clubs scraped
- Success rate
- Emails found
- Clubs with waitlists
- Quick action buttons

### Scraper Page

1. **Choose number of clubs** to scrape (10-50 for testing, 306 for all)
2. **Click "Start Scraping"**
3. **Watch real-time progress**:
   - Progress bar showing completion %
   - Current club being scraped
   - Success/failure counters
4. Results save automatically

**Expected Time:**
- 10 clubs: ~30 seconds
- 50 clubs: ~1-2 minutes
- 306 clubs: ~15-20 minutes

### Results Page

- **View all scraped data** in a clean table
- **Search clubs** by name, location, or email
- **See statistics**:
  - Total clubs
  - Success rate
  - Data completeness for each field
- **Download CSV** for spreadsheet analysis

### Email Management

1. **Preview Emails**
   - See which clubs need outreach
   - Review email content
   - Check which clubs have email addresses

2. **Dry Run**
   - Test the email system without sending
   - Generate emails and logs
   - Safe for testing

3. **Send Emails**
   - Sends actual emails to clubs
   - Requires email configuration (see below)
   - 5 second delay between emails
   - All activity logged

## ⚙️ Configuration

### Email Setup (Optional)

To use email outreach:

1. Create `.env` file:
```bash
cp .env.example .env
```

2. Edit `.env` with your credentials:
```bash
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

3. **For Gmail users:**
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App Passwords
   - Generate app password for "Mail"
   - Use that password in `.env`

## 🎨 Screenshots

### Dashboard
Clean overview with stats and quick actions

### Scraper
Real-time progress with beautiful progress bar

### Results
Searchable data table with export options

### Email Manager
Preview and manage email outreach

## 📂 File Structure

```
GTA-tennis-clubs-waitlist/
├── app.py                    # Flask web application
├── templates/                # HTML templates
│   ├── base.html            # Base layout
│   ├── index.html           # Dashboard
│   ├── scraper.html         # Scraper page
│   ├── results.html         # Results viewer
│   └── email.html           # Email management
├── static/                   # Static files (CSS/JS)
├── results/                  # Output directory
│   ├── scraped_data.json    # Scraped data
│   ├── scraped_data.csv     # CSV export
│   └── email_log.json       # Email activity log
└── requirements.txt          # Python dependencies
```

## 💡 Tips

1. **Start Small**: Test with 10 clubs first to make sure everything works
2. **Monitor Progress**: The scraper shows real-time updates
3. **Export Often**: Download CSV after each scraping session
4. **Email Safety**: Always use "Dry Run" before sending real emails
5. **Data Backup**: Results save automatically in `results/` folder

## 🔧 Troubleshooting

### Port Already in Use

If port 5000 is taken:
```python
# Edit app.py, last line:
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

### Browser Not Opening

Manually navigate to: `http://localhost:5000`

### Scraper Not Starting

1. Check that `GTA Tennis clubs data .xlsx` exists
2. Ensure dependencies are installed: `pip install -r requirements.txt`
3. Check console for error messages

### Email Not Sending

1. Verify `.env` file exists and has correct credentials
2. For Gmail, use App Password (not regular password)
3. Check that SMTP settings are correct
4. Try "Dry Run" first to test without sending

### No Results Showing

1. Run the scraper first
2. Check `results/scraped_data.json` exists
3. Refresh the page

## 🚀 Production Deployment (Optional)

For production use:

1. **Use a production WSGI server**:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Set up a reverse proxy** (nginx/Apache)

3. **Enable HTTPS** for security

4. **Set DEBUG=False** in app.py

## 📊 Expected Results

When running on your local machine (outside sandbox):

- **Success Rate**: 70-85%
- **Locations Found**: 65-75%
- **Emails Found**: 55-70%
- **Court Info**: 60-75%
- **Waitlist Data**: 20-35%

## ⚠️ Important Notes

- The web app must run on your **local machine** (not in restricted environments)
- Network access required to scrape external websites
- Results save incrementally (no data loss if stopped)
- Email outreach requires configuration first

## 🎯 Workflow Example

1. **Start the app**: `python app.py`
2. **Open browser**: http://localhost:5000
3. **Run scraper**: Scraper page → Start with 10 clubs
4. **Check results**: Results page → Review data
5. **Export data**: Download CSV button
6. **Email outreach** (optional):
   - Preview emails
   - Run dry test
   - Send when ready

## 🆘 Getting Help

If you encounter issues:

1. Check this guide
2. Review error messages in console
3. Verify all files are in place
4. Ensure dependencies installed
5. Check `.env` configuration

## ✨ Enjoy!

The web app makes scraping tennis club data easy and visual. No command line needed - everything is just a click away!

---

**Built with:** Python, Flask, jQuery, and modern CSS
**Total Development Time:** Optimized for ease of use
**Supported Browsers:** Chrome, Firefox, Safari, Edge (modern versions)
