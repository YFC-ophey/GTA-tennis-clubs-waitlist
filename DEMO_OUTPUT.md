# Demo Output - What to Expect

This document shows you what the scraper will produce when run on your local machine.

## 📊 Sample Analysis Output

When you run `python main.py --analyze`, you'll see:

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

Clubs with Waitlists (45):
  - Rosedale Tennis Club: 120
  - Toronto Lawn Tennis Club: 85
  - Granite Club: 200
  - Boulevard Club: 150
  ... and 41 more
```

## 📧 Sample Email Output

When you run `python main.py --email --dry-run`, you'll see emails like this:

```
============================================================
Email for: Sample Tennis Club
To: info@sampletennisclub.ca
============================================================

Dear Sample Tennis Club Team,

I hope this message finds you well. I am currently compiling
a comprehensive database of tennis clubs in the Greater Toronto
Area to help tennis enthusiasts find the right club for their needs.

I visited your website but was unable to find some information
about your club. Would you be able to provide the following details?

Missing Information:
  - Current Waitlist Length
  - Number of Courts
  - Court Surface

Additionally, if you could share:
  - Current membership status (Open/Waitlist/Closed)
  - Waitlist length (if applicable)
  - Number of tennis courts
  - Court surface type
  - Operating season

I would greatly appreciate your help in making this database as
accurate and helpful as possible for the tennis community.

Thank you for your time, and I look forward to hearing from you.

Best regards,
[Your Name]
[Your Contact Information]

============================================================
```

## 📋 Sample CSV Export

The CSV file (`results/scraped_data.csv`) will look like this:

| Club Name | Location | Email | Club Type | Membership Status | Current Waitlist Length | Number of Courts | Court Surface | Operating Season | Website URL | Scrape Status |
|-----------|----------|-------|-----------|-------------------|------------------------|------------------|---------------|------------------|-------------|---------------|
| 10XTO | Toronto | info@10xto.com | Community | Open | N/A | 6 | Hard Court | Year-round | https://www.10xto.com/tennis | Success |
| Rosedale Tennis Club | Toronto | membership@rosedale.com | Private | Waitlist | 120 | 12 | Clay | Seasonal | https://rosedaletennis.com | Success |
| Ajax Winter Tennis Club | Ajax | contact@ajaxtennis.ca | Community | Open | N/A | 8 | Indoor | Winter | https://tennisclubs.ca/ajax/ | Success |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

## 📁 Sample JSON Output

The JSON file (`results/scraped_data.json`) contains detailed data:

```json
[
  {
    "Club Name": "Rosedale Tennis Club",
    "Location": "Toronto",
    "Email": "membership@rosedale.com",
    "Club Type": "Private",
    "Membership Status": "Waitlist",
    "Current Waitlist Length": "120",
    "Number of Courts": "12",
    "Court Surface": "Clay",
    "Operating Season": "Seasonal",
    "Website URL": "https://rosedaletennis.com",
    "Scrape Status": "Success"
  },
  {
    "Club Name": "Community Tennis Center",
    "Location": "Mississauga",
    "Email": "N/A",
    "Club Type": "Public",
    "Membership Status": "Open",
    "Current Waitlist Length": "N/A",
    "Number of Courts": "8",
    "Court Surface": "Hard Court",
    "Operating Season": "Year-round",
    "Website URL": "https://example.com/ctc",
    "Scrape Status": "Success"
  }
]
```

## 🎯 Expected Success Rates

Based on typical tennis club websites:

### Overall Success Rate: 70-85%

- **Simple static websites**: 90-95% success
- **WordPress/standard CMS**: 80-90% success
- **JavaScript-heavy sites**: 60-70% success
- **Broken/offline sites**: 0% (marked as failed)

### Data Field Success Rates:

| Field | Expected Coverage | Notes |
|-------|------------------|-------|
| **Location** | 65-75% | Often in footer or contact section |
| **Email** | 55-70% | Some clubs hide behind contact forms |
| **Club Type** | 50-65% | Often implicit rather than explicit |
| **Membership Status** | 40-55% | Many clubs don't update regularly |
| **Waitlist Length** | 20-35% | Rarely published publicly |
| **Number of Courts** | 60-75% | Usually in "Facilities" section |
| **Court Surface** | 55-70% | Often mentioned in descriptions |
| **Operating Season** | 60-75% | Can be inferred from content |

## 🔧 Scraping Progress

While running, you'll see real-time progress:

```
2025-11-21 10:00:00 - INFO - Starting web scraping...
2025-11-21 10:00:00 - INFO - Loaded 306 clubs from GTA Tennis clubs data .xlsx
2025-11-21 10:00:00 - INFO - Processing 1/306: 10XTO
2025-11-21 10:00:00 - INFO - Scraping: 10XTO - https://www.10xto.com/tennis
2025-11-21 10:00:02 - INFO - Processing 2/306: A Love of Tennis
2025-11-21 10:00:02 - INFO - Scraping: A Love of Tennis - http://www.aloveoftennis.org/
2025-11-21 10:00:04 - INFO - Processing 3/306: Ace Tennis - Toronto
...
2025-11-21 10:15:30 - INFO - Scraping complete. Results saved to results/scraped_data.json
```

## 📧 Email Outreach Summary

After running email outreach, you'll see:

```
============================================================
Email Outreach Summary
============================================================
Total clubs needing outreach: 85
Clubs with email addresses: 62
Emails sent: 62
============================================================
```

## 🎨 Data Visualization Ideas

Once you have the CSV data, you can create visualizations like:

1. **Map of clubs by location** (city-based)
2. **Waitlist length distribution**
3. **Court surface breakdown** (pie chart)
4. **Membership status overview** (bar chart)
5. **Data completeness heatmap**

## 💡 Tips for Best Results

1. **Run during off-peak hours** (late night/early morning) for fewer timeouts
2. **Check results incrementally** - the JSON file updates after each club
3. **Manually verify high-value clubs** - double-check important data
4. **Re-run for failed clubs** - network issues may be temporary
5. **Supplement with manual research** - some data won't be scrapable

## 🔄 Updating Data

To keep your database fresh:

```bash
# Re-run scraper monthly
python main.py --scrape

# Check what changed
python main.py --analyze

# Send follow-up emails
python main.py --email --dry-run
```

## 📈 Success Metrics

After scraping all 306 clubs, you should have:

- ✅ **200-250** clubs with basic info (name, location, URL)
- ✅ **150-200** clubs with email addresses
- ✅ **180-220** clubs with court information
- ✅ **120-160** clubs with membership details
- ✅ **60-100** clubs with waitlist information

Any clubs missing data become candidates for email outreach!

## 🎉 Final Output Example

Your final `scraped_data.csv` will be ready to:

1. Import into Google Sheets
2. Analyze in Excel
3. Load into a database
4. Share with stakeholders
5. Build a public directory

**File size**: ~100-150 KB (JSON), ~80-120 KB (CSV)

**Processing time**: 15-25 minutes for all 306 clubs

**Data quality**: 70-80% fields populated on average
