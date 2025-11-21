# GTA Tennis Clubs Scraper - Setup Guide

## 📋 Overview

This system scrapes 306 GTA tennis club websites to collect membership and facility information. Due to network restrictions in the current environment, the scraper needs to be run locally on your machine.

## 🚀 Quick Start (Local Machine)

### Step 1: Clone the Repository

```bash
git clone https://github.com/YFC-ophey/GTA-tennis-clubs-waitlist.git
cd GTA-tennis-clubs-waitlist
```

### Step 2: Install Dependencies

**Option A: Using pip directly**
```bash
pip install -r requirements.txt
```

**Option B: Using a virtual environment (recommended)**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Test the Scraper

Start with a small test to make sure everything works:

```bash
# Test with just 5 clubs
python main.py --scrape --max-clubs 5

# Check the results
python main.py --analyze
```

If the test works, you'll see something like:

```
============================================================
Data Analysis Report
============================================================
Total clubs: 5
Successfully scraped: 4 (80.0%)
...
```

### Step 4: Run Full Scraping

Once the test works, scrape all 306 clubs:

```bash
# This will take about 15-20 minutes
python main.py --scrape

# Analyze the results
python main.py --analyze

# Export to CSV
python main.py --export csv
```

## 📊 Expected Results

### Data Extraction Success Rate

Based on the website types in your list, you can expect:

- **60-80% success rate** for basic data (location, email)
- **40-60% success rate** for membership status
- **20-40% success rate** for waitlist information
- **50-70% success rate** for court information

Many clubs will have missing data fields, which is where the email agent comes in!

### Sample Output

```
======================================================================
Data Analysis Report
======================================================================
Total clubs: 306
Successfully scraped: 245 (80.1%)

Data Completeness:
----------------------------------------------------------------------
Field                          Found      Missing    Coverage
----------------------------------------------------------------------
Location                       210        96         68.6%
Email                          185        121        60.5%
Club Type                      165        141        53.9%
Membership Status              145        161        47.4%
Current Waitlist Length        75         231        24.5%
Number of Courts               190        116        62.1%
Court Surface                  175        131        57.2%
Operating Season               200        106        65.4%
======================================================================
```

## 📧 Email Outreach (Optional)

After scraping, you can send automated emails to clubs with missing data.

### Step 1: Setup Email Credentials

1. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your email:
   ```bash
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ```

3. **For Gmail users**: You need to create an [App Password](https://support.google.com/accounts/answer/185833):
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Use that password in `.env`

### Step 2: Preview Emails (Dry Run)

```bash
# See what emails would be sent (no actual sending)
python main.py --email --dry-run
```

This will show you:
- Which clubs will receive emails
- What the email content looks like
- Summary of clubs needing outreach

### Step 3: Send Emails

When you're ready to send:

```bash
# Send actual emails
python main.py --email
```

## 📈 Export Options

### Option 1: CSV Export (Easiest)

```bash
python main.py --export csv
```

Output: `results/scraped_data.csv`

You can then:
1. Open the CSV in Excel or Google Sheets
2. Import it manually into your spreadsheet
3. Use it for further analysis

### Option 2: Google Sheets Direct Export

This requires more setup but allows automatic upload to Google Sheets.

**Setup Steps:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable APIs:
   - Google Sheets API
   - Google Drive API
4. Create Service Account:
   - IAM & Admin → Service Accounts → Create
   - Create a JSON key and download it
   - Save as `credentials.json` in project folder
5. Update `.env`:
   ```bash
   GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
   GOOGLE_SHEET_NAME=GTA Tennis Clubs Data
   ```
6. Share your Google Sheet with the service account email (from `credentials.json`)

**Run Export:**

```bash
python main.py --export sheets
```

## 🔄 Full Workflow Example

Here's a complete workflow from start to finish:

```bash
# 1. Test with 10 clubs first
python main.py --scrape --max-clubs 10 --analyze

# 2. If that works, scrape all clubs (takes 15-20 mins)
python main.py --scrape

# 3. Analyze the data
python main.py --analyze

# 4. Export to CSV
python main.py --export csv

# 5. Preview email outreach (optional)
python main.py --email --dry-run

# 6. Send emails to clubs with missing data (optional)
python main.py --email
```

## ⚙️ Customization

### Adjust Scraping Speed

Edit `scraper_simple.py`, line ~290:

```python
# Change from 0.5 to higher value to slow down
time.sleep(0.5)  # seconds between requests
```

### Customize Email Template

Edit `email_agent.py`, function `generate_email_template()` (line ~29)

### Change Data Fields

Edit `scraper_simple.py` and add new extraction methods:

```python
def extract_new_field(self, soup, page_text):
    # Your extraction logic
    return extracted_value
```

## 🐛 Troubleshooting

### "ModuleNotFoundError"

```bash
# Make sure you installed requirements
pip install -r requirements.txt
```

### "403 Forbidden" or "Connection Error"

- Check your internet connection
- Some websites may block automated requests
- Try running with fewer concurrent requests
- Some clubs may have gone offline

### "SSL Certificate Error"

The scraper already handles this automatically with `verify=False`

### Slow Scraping

This is normal! With 306 clubs and 0.5 seconds between requests:
- Expected time: ~150 seconds (2.5 minutes) minimum
- With page load time: 15-20 minutes total

### Email Not Sending

1. Check `.env` file has correct credentials
2. For Gmail, use App Password, not regular password
3. Enable "Less secure app access" (for old Gmail accounts)
4. Check spam folder

## 📁 Output Files

After running the scraper, you'll find:

```
results/
├── scraped_data.json          # Raw JSON data
├── scraped_data.csv           # CSV export
└── scraped_data_email_log.json # Email outreach log
```

## 🎯 Next Steps

1. **Review the data**: Check `results/scraped_data.csv`
2. **Fill gaps manually**: For clubs where scraping failed
3. **Email outreach**: Contact clubs with missing data
4. **Update regularly**: Re-run the scraper periodically to keep data fresh

## 💡 Tips

1. **Start small**: Always test with `--max-clubs 10` first
2. **Be patient**: Scraping takes time (15-20 minutes for all clubs)
3. **Save often**: The scraper saves after each club automatically
4. **Check results**: Review `scraped_data.json` as it builds
5. **Email wisely**: Use `--dry-run` first to preview emails

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review error messages in the console
3. Check `scraper_simple.py` for detailed logs
4. Ensure your internet connection is stable

## 🎉 Success Indicators

You'll know it's working when you see:

```
2025-11-21 10:00:00 - INFO - Processing 1/306: 10XTO
2025-11-21 10:00:02 - INFO - Processing 2/306: A Love of Tennis
...
```

And the `results/scraped_data.json` file grows with each club!
