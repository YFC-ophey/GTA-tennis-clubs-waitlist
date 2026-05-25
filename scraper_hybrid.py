#!/usr/bin/env python3
"""
Hybrid Tennis Club Scraper
Intelligently chooses between BeautifulSoup (fast) and Playwright (JS-capable)
"""

from scraper_simple import TennisClubScraper
from typing import Dict

# Try to import JS scraper
try:
    from scraper_js import JavaScriptScraper, PLAYWRIGHT_AVAILABLE
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class HybridScraper:
    """
    Hybrid scraper that uses BeautifulSoup by default and falls back to
    Playwright for JavaScript-heavy sites
    """

    def __init__(self, data_merger=None, use_js_fallback=False):
        self.simple_scraper = TennisClubScraper(data_merger=data_merger)
        self.js_scraper = None
        self.use_js_fallback = use_js_fallback and PLAYWRIGHT_AVAILABLE

        if self.use_js_fallback:
            try:
                self.js_scraper = JavaScriptScraper()
                print("✓ JavaScript scraper enabled (Playwright available)")
            except Exception as e:
                print(f"⚠️  Could not initialize JS scraper: {e}")
                self.use_js_fallback = False
        elif use_js_fallback and not PLAYWRIGHT_AVAILABLE:
            print("⚠️  JavaScript fallback requested but Playwright not installed")
            print("   Install with: pip install playwright && playwright install chromium")

    def scrape_club(self, url: str, club_name: str) -> Dict:
        """
        Scrape a club using hybrid approach:
        1. Try BeautifulSoup first (fast)
        2. If JS-heavy and fallback enabled, retry with Playwright
        """

        # First attempt with BeautifulSoup
        result = self.simple_scraper.scrape_club(url, club_name)

        # Check if we should retry with JS scraper
        should_retry_with_js = (
            self.use_js_fallback and
            self.js_scraper and
            (
                result['Scrape Status'] == 'JS-heavy (limited data)' or
                (result['Scrape Status'] == 'Success' and self._has_minimal_data(result))
            )
        )

        if should_retry_with_js:
            print(f"[HYBRID] Retrying {club_name} with JavaScript scraper...")

            # Save pre-loaded data before retrying
            pre_loaded_data = {
                k: v for k, v in result.items()
                if v != 'N/A' and k not in ['Club Name', 'Website', 'Scrape Status']
            }

            # Retry with JS scraper
            js_result = self.js_scraper.scrape_club(url, club_name)

            # Merge results (prefer JS scraper data for fields that were N/A)
            for key, value in js_result.items():
                if key in ['Club Name', 'Website']:
                    continue
                # Use JS result if original was N/A or JS found something
                if result.get(key) == 'N/A' and value != 'N/A':
                    result[key] = value

            # Update status to show hybrid approach was used
            if js_result['Scrape Status'].startswith('Success'):
                if pre_loaded_data:
                    result['Scrape Status'] = 'Success (Hybrid+Pre-loaded)'
                else:
                    result['Scrape Status'] = 'Success (Hybrid)'

        return result

    def _has_minimal_data(self, result: Dict) -> bool:
        """Check if result has very little data (excluding pre-loaded)"""
        data_fields = ['Email', 'Location', 'Club Type', 'Membership Status',
                      'Waitlist Length', 'Number of Courts', 'Court Surface']

        # Count how many fields have actual data
        non_na_count = sum(1 for field in data_fields if result.get(field, 'N/A') != 'N/A')

        # If pre-loaded, we already have good data
        if result['Scrape Status'].startswith('Pre-loaded'):
            return False

        # If very few fields were extracted, worth retrying with JS
        return non_na_count < 3


if __name__ == '__main__':
    # Test the hybrid scraper
    print("Testing Hybrid Scraper...")
    print("=" * 60)

    scraper = HybridScraper(use_js_fallback=True)

    test_url = "https://www.example.com"  # Replace with actual test URL
    result = scraper.scrape_club(test_url, "Test Club")

    print("\nResults:")
    print("=" * 60)
    for key, value in result.items():
        print(f"{key}: {value}")
