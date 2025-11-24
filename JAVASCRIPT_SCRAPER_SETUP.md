# 🚀 JavaScript Scraper Setup Guide

The JavaScript scraper allows you to scrape modern websites built with React, Vue, Angular, or other JavaScript frameworks that the regular scraper cannot handle.

## Why Use the JavaScript Scraper?

**Regular Scraper (BeautifulSoup):**
- ✅ Fast (< 1 second per site)
- ✅ Low resource usage
- ❌ Cannot see JavaScript-rendered content
- ❌ Shows "N/A" for React/Vue/Angular sites

**JavaScript Scraper (Playwright):**
- ✅ Handles JavaScript-heavy sites
- ✅ Sees dynamically loaded content
- ✅ Executes React/Vue/Angular apps
- ⚠️  Slower (~3-5 seconds per site)
- ⚠️  Higher resource usage (runs actual browser)

## Installation

### Step 1: Install Playwright

```bash
pip3 install playwright
```

### Step 2: Install Browser

```bash
playwright install chromium
```

This downloads a ~300MB Chromium browser that Playwright will use.

### Step 3: Verify Installation

```bash
python3 -c "from playwright.sync_api import sync_playwright; print('✓ Playwright installed successfully!')"
```

You should see: `✓ Playwright installed successfully!`

## Usage

### Option 1: Enable in Web UI

1. Start the app: `python3 app.py`
2. Go to the Scraper page
3. Check the box: **"🚀 Enable JavaScript Fallback"**
4. Start scraping

The hybrid scraper will:
- Try regular scraper first (fast)
- If JS-heavy site detected, retry with Playwright
- Show status as "Success (Hybrid)" when JS scraper was used

### Option 2: Use Directly in Code

```python
from scraper_hybrid import HybridScraper

scraper = HybridScraper(use_js_fallback=True)
result = scraper.scrape_club('https://example.com', 'Example Club')
```

### Option 3: Use JS Scraper Only

```python
from scraper_js import JavaScriptScraper

scraper = JavaScriptScraper()
result = scraper.scrape_club('https://example.com', 'Example Club')
```

## Performance Comparison

| Scraper Type | Speed | Success Rate | Resource Usage |
|--------------|-------|--------------|----------------|
| Regular | 0.5-1s | 60-70% | Low |
| JavaScript | 3-5s | 85-90% | High |
| **Hybrid (Recommended)** | **1-2s avg** | **80-85%** | **Medium** |

## How Hybrid Mode Works

1. **First Attempt**: Uses regular scraper (fast)
2. **Detection**: If page has < 200 chars visible text → likely JS-heavy
3. **Retry**: Automatically retries with JavaScript scraper
4. **Merge**: Combines results from both attempts
5. **Status**: Shows "Success (Hybrid)" or "Success (Hybrid+Pre-loaded)"

## Tips

**When to Enable JavaScript Fallback:**
- ✅ When scraping 10-50 clubs (acceptable slowdown)
- ✅ When you see many "JS-heavy (limited data)" status messages
- ✅ When you need maximum data extraction
- ❌ When scraping 100+ clubs (too slow - 5-10 minutes vs 1-2 minutes)

**Performance Tips:**
- Start with 10-20 clubs to test
- Enable only when needed
- Pre-loaded CSV data (260+ clubs) makes this less critical
- Most clubs without JS will already have good data

## Troubleshooting

### "Playwright not installed" error

```bash
pip3 install playwright
playwright install chromium
```

### "Browser executable doesn't exist" error

```bash
playwright install chromium
```

### Scraping is too slow

- Disable JavaScript fallback
- Reduce number of clubs
- Remember: most clubs have pre-loaded data from CSV files

### Out of memory errors

JavaScript scraper uses ~200MB RAM per browser instance. If scraping many clubs:
- Reduce concurrent operations
- Scrape in smaller batches
- Disable JS fallback for large batches

## Technical Details

**What Playwright Does:**
1. Launches headless Chromium browser
2. Navigates to page
3. Waits for network to be idle
4. Waits 2 seconds for dynamic content
5. Extracts page text after JavaScript execution
6. Closes browser

**Detection Logic:**
- Counts `<script>` tags
- Checks for React/Vue/Angular keywords
- Measures visible text length
- Flags sites with < 200 chars as JS-heavy

## Uninstalling

If you want to remove Playwright:

```bash
playwright uninstall chromium
pip3 uninstall playwright
```

The regular scraper will continue to work without any issues.
