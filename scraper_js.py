#!/usr/bin/env python3
"""
JavaScript-Capable Tennis Club Scraper
Uses Playwright to scrape JavaScript-heavy sites (React, Vue, Angular, etc.)
This is slower but can handle modern websites that BeautifulSoup cannot.
"""

import re
from typing import Dict
import time

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Run: pip install playwright && playwright install chromium")


class JavaScriptScraper:
    """Scraper for JavaScript-heavy websites using Playwright"""

    def __init__(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. "
                "Install it with: pip install playwright && playwright install chromium"
            )
        self.timeout = 20000  # 20 seconds for JS sites
        self.debug = True

    def scrape_club(self, url: str, club_name: str) -> Dict:
        """Scrape using headless browser with JavaScript support"""
        result = {
            'Club Name': club_name,
            'Website': url,
            'Email': 'N/A',
            'Location': 'N/A',
            'Club Type': 'N/A',
            'Membership Status': 'N/A',
            'Waitlist Length': 'N/A',
            'Number of Courts': 'N/A',
            'Court Surface': 'N/A',
            'Operating Season': 'N/A',
            'Scrape Status': 'Failed'
        }

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        if self.debug:
            print(f"[PLAYWRIGHT] Scraping {club_name}: {url}")

        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()

                # Navigate to page and wait for network to be idle
                page.goto(url, wait_until='networkidle', timeout=self.timeout)

                # Wait a bit for any dynamic content
                page.wait_for_timeout(2000)

                if self.debug:
                    print(f"[PLAYWRIGHT] Page loaded: {page.url}")

                # Get page content after JavaScript execution
                page_text = page.inner_text('body')
                html_content = page.content()

                if self.debug:
                    print(f"[PLAYWRIGHT] Content length: {len(page_text)} characters")
                    print(f"[PLAYWRIGHT] First 200 chars: {page_text[:200]}")

                # Extract emails
                result['Email'] = self._extract_email(page, page_text)

                # Extract other data
                result['Location'] = self._extract_city(page_text)
                result['Number of Courts'] = self._extract_courts(page_text)
                result['Court Surface'] = self._extract_surface(page_text)
                result['Membership Status'] = self._extract_membership(page_text)
                result['Club Type'] = self._extract_club_type(page_text)

                result['Scrape Status'] = 'Success (JS-enabled)'

                if self.debug:
                    found = [k for k, v in result.items() if v != 'N/A' and k not in ['Club Name', 'Website', 'Scrape Status']]
                    print(f"[PLAYWRIGHT] Found: {found}")

                browser.close()

        except PlaywrightTimeout:
            result['Scrape Status'] = 'Timeout (JS)'
            print(f"[PLAYWRIGHT ERROR] Timeout for {club_name}")
        except Exception as e:
            result['Scrape Status'] = f'JS Error: {type(e).__name__}'
            print(f"[PLAYWRIGHT ERROR] {club_name}: {str(e)[:100]}")

        return result

    def _extract_email(self, page, page_text: str) -> str:
        """Extract email using Playwright selectors and text search"""
        try:
            # Try to find mailto links
            mailto_links = page.query_selector_all('a[href^="mailto:"]')
            if mailto_links:
                href = mailto_links[0].get_attribute('href')
                email = href.replace('mailto:', '').split('?')[0].strip()
                if '@' in email:
                    return email

            # Search text content
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_text)

            if emails:
                # Filter and prioritize
                blacklist = ['example.com', 'test.com', 'noreply', 'privacy@', 'legal@']
                priority = ['info@', 'contact@', 'tennis@', 'club@', 'admin@']

                priority_emails = []
                other_emails = []

                for e in emails:
                    e_lower = e.lower()
                    if any(x in e_lower for x in blacklist):
                        continue
                    if any(x in e_lower for x in priority):
                        priority_emails.append(e)
                    else:
                        other_emails.append(e)

                if priority_emails:
                    return priority_emails[0]
                if other_emails:
                    return other_emails[0]

        except Exception as e:
            print(f"[PLAYWRIGHT] Email extraction error: {e}")

        return 'N/A'

    def _extract_city(self, text: str) -> str:
        """Extract city from text"""
        gta_cities = [
            'Toronto', 'Mississauga', 'Brampton', 'Hamilton', 'Markham',
            'Vaughan', 'Richmond Hill', 'Oakville', 'Burlington', 'Oshawa',
            'Pickering', 'Ajax', 'Whitby', 'Newmarket', 'Aurora',
            'Milton', 'Caledon', 'Georgina', 'Stouffville', 'King',
            'Etobicoke', 'Scarborough', 'North York', 'East York'
        ]

        text_lower = text.lower()
        for city in gta_cities:
            if city.lower() in text_lower:
                return city

        return 'N/A'

    def _extract_courts(self, text: str) -> str:
        """Extract court count"""
        patterns = [
            r'(\d+)\s+(?:tennis\s+)?courts?',
            r'courts?[:\s]+(\d+)',
            r'(\d+)[-\s]court',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                count = int(match.group(1))
                if 1 <= count <= 50:
                    return str(count)

        return 'N/A'

    def _extract_surface(self, text: str) -> str:
        """Extract court surface"""
        text_lower = text.lower()
        surfaces = []

        if re.search(r'\bhard\s*court|\bhardcourt', text_lower):
            surfaces.append('Hard')
        if re.search(r'\bclay\s*court', text_lower):
            surfaces.append('Clay')
        if re.search(r'\bindoor', text_lower):
            surfaces.append('Indoor')

        return ', '.join(surfaces) if surfaces else 'N/A'

    def _extract_membership(self, text: str) -> str:
        """Extract membership status"""
        text_lower = text.lower()

        if re.search(r'accepting\s+(?:new\s+)?members|open\s+membership', text_lower):
            return 'Open'
        if re.search(r'waitlist|waiting\s+list', text_lower):
            return 'Waitlist'
        if re.search(r'not\s+accepting|closed|full', text_lower):
            return 'Closed'

        return 'N/A'

    def _extract_club_type(self, text: str) -> str:
        """Extract club type"""
        text_lower = text.lower()

        if re.search(r'private\s+club', text_lower):
            return 'Private'
        if re.search(r'public|community|municipal', text_lower):
            return 'Public'

        return 'N/A'


def test_js_scraper():
    """Test the JavaScript scraper"""
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not available. Install with:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return

    print("Testing JavaScript Scraper...")
    scraper = JavaScriptScraper()

    # Test with a known JS-heavy site
    test_url = "https://www.example.com"  # Replace with actual test URL
    result = scraper.scrape_club(test_url, "Test Club")

    print("\nResults:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    test_js_scraper()
