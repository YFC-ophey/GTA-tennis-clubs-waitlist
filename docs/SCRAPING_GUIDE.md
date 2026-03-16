# Web Scraping Guide

## Overview

This guide explains the methodology for collecting data from 306 GTA tennis clubs using a hybrid automated-manual approach.

## Data Collection Strategy

### Three-Tier Approach

1. **Automated Directory Scraping** (Tennis Ontario)
   - Official directory with structured data
   - Best for: Club names, locations, basic contact info
   - Success rate: ~80% for basic fields

2. **AI-Assisted Web Scraping** (Individual Club Sites)
   - Claude AI extracts data from club websites
   - Best for: Court counts, surfaces, operating seasons
   - Success rate: ~50% (varies by field)

3. **Manual Email Outreach** (Direct Contact)
   - Required for sensitive competitive data
   - Best for: Membership status, waitlist lengths
   - Success rate: Pending campaign results

## 9 Required Data Fields

| Field | Difficulty | Primary Source | Notes |
|-------|------------|----------------|-------|
| Club Name | Easy | Tennis Ontario | Always available |
| Location | Easy | Tennis Ontario | City, postal code |
| Email | Medium | Club website | Often in contact form |
| Club Type | Medium | Website content | Private/Community/Public |
| Number of Courts | Medium | Website/Google | Usually published |
| Court Surface | Medium | Website | Hard/Clay/Grass/Indoor |
| Operating Season | Medium | Website | Year-round/Seasonal |
| Membership Status | **Hard** | Email outreach | Rarely published |
| Waitlist Length | **Very Hard** | Email outreach | Privacy concerns |

## Scraping Workflow

### Step 1: Get Club Batch

In dashboard, click **"Get Next 10 Clubs"**

The system returns:
```json
{
  "clubs": [
    {
      "Club Name": "Example Tennis Club",
      "Website URL": "http://www.example.ca/"
    }
  ]
}
```

### Step 2: Initial Research

For each club:

1. **Click the copy button** next to the URL
2. **Paste in Claude chat**: "Please scrape this club: [URL]"
3. Claude will:
   - Use `web_search` to find the club
   - Use `web_fetch` to retrieve the HTML
   - Extract all available fields using AI

### Step 3: Data Extraction

Claude looks for these patterns:

**Location**:
- Address in footer or contact page
- Postal code patterns (M4E 3W2)
- "Located in [City]"

**Email**:
- href="mailto:..."
- Patterns: info@, admin@, tennis@
- Contact forms (note: "Contact Form Only")

**Club Type**:
- Keywords: "private club", "community centre", "public courts"
- Membership language
- Municipal associations

**Court Information**:
- Numbers: "8 courts", "twelve outdoor courts"
- Surface keywords: "hard court", "clay", "indoor"
- Photos with court markings

**Operating Season**:
- "Year-round tennis"
- "Open May-October"
- Indoor facility indicators

**Membership Status**:
- "Accepting new members"
- "Waitlist currently full"
- "No availability at this time"

**Waitlist Length**:
- Rarely published
- Sometimes mentioned in news/updates
- Usually requires email inquiry

### Step 4: Handling Missing Data

If a field cannot be found:
- Mark as "Not Found" in database
- Add to email outreach list
- Flag for manual phone call if critical

## Common Challenges

### 1. Anti-Bot Protection

**Problem**: Clubs use Cloudflare, reCAPTCHA, or bot detection

**Solution**: 
- Use Claude's `web_fetch` (appears as human traffic)
- Add random delays between requests
- Respect robots.txt

### 2. JavaScript-Heavy Sites

**Problem**: Content loads dynamically via JavaScript

**Solution**:
- Look for API endpoints in network tab
- Check page source for JSON data
- Use Google search cache if needed

### 3. Contact Forms Only

**Problem**: No direct email address published

**Solution**:
- Note "Contact Form Only" in Email field
- Use form for initial outreach
- Request direct email in response

### 4. Inconsistent Data Formats

**Problem**: Each club formats information differently

**Solution**:
- Claude AI normalizes data during extraction
- Standardize values (e.g., "12" not "twelve")
- Use controlled vocabularies when possible

## Data Validation

After extraction, verify:

1. **Location**: Valid city name, postal code format
2. **Email**: Valid email pattern (contains @)
3. **Club Type**: One of: Private, Community, Public
4. **Court Surface**: One of: Hard, Clay, Grass, Indoor, Mixed
5. **Numbers**: Positive integers only

## Email Outreach Template

For missing data, use this template:

```
Subject: Tennis Club Information Request

Hello,

I'm compiling a comprehensive directory of Greater Toronto Area 
tennis clubs to help players find the right club for their needs.

Would you be able to share the following information about 
[Club Name]?

- Current membership status (Open/Waitlist/Full)
- Approximate waitlist length (if applicable)
- Number of courts at your facility
- Court surface types (Hard/Clay/Indoor)
- Operating season (Year-round/Seasonal)

This information will help tennis players in our community make 
informed decisions about club options.

Thank you for your time!

Best regards,
[Your Name]
```

## Progress Tracking

Monitor success rates by field:

```sql
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN location != 'Not Found' THEN 1 ELSE 0 END) as location_found,
  SUM(CASE WHEN email != 'Not Found' THEN 1 ELSE 0 END) as email_found
FROM processed_clubs;
```

## Best Practices

1. **Batch Processing**: Work in groups of 10-20 clubs
2. **Time Management**: ~5 minutes per club average
3. **Quality Over Speed**: Verify data accuracy
4. **Document Blockers**: Note clubs requiring phone calls
5. **Respect Rate Limits**: Pause between batches
6. **Update Status**: Mark clubs as processed immediately

## Automation Opportunities

### Current State: Semi-Automated
- Manual URL copying
- Manual Claude queries
- Manual data verification

### Future Enhancement: Fully Automated
- Claude API integration for autonomous scraping
- Automated email sending and monitoring
- Scheduled daily scraping runs
- Automatic deduplication and conflict resolution

## Legal & Ethical Considerations

- **Respect robots.txt**: Honor site crawling rules
- **Public Data Only**: Don't scrape behind login walls
- **Rate Limiting**: Don't overload club websites
- **Attribution**: Credit data sources appropriately
- **Privacy**: Handle contact information responsibly
- **Terms of Service**: Review and comply with site ToS

## Troubleshooting

**Claude can't access URL**:
- Verify URL is correct and accessible
- Try adding "https://" if missing
- Check if site is temporarily down
- Use Google cache as backup

**Inconsistent Extractions**:
- Review multiple examples with Claude
- Refine extraction prompts
- Add manual verification step

**Low Success Rates**:
- Adjust strategy for difficult fields
- Pivot to email/phone outreach
- Accept that some data won't be available publicly

## Success Metrics

Target completion rates:
- **Basic Info** (Name, Location, URL): 95%
- **Contact** (Email): 70%
- **Facilities** (Courts, Surface): 80%
- **Membership Status**: 40% (requires outreach)
- **Waitlist Length**: 20% (rarely published)

---

**Remember**: The goal is a comprehensive database, not perfection. Even partial data is valuable for helping players find clubs that match their needs.
