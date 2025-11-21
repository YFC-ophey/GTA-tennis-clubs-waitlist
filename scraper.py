"""
Tennis Club Web Scraper
Extracts tennis club information from websites using Playwright
"""

import json
import re
import time
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TennisClubScraper:
    def __init__(self, timeout: int = 30000):
        self.timeout = timeout
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def extract_city_from_address(self, text: str) -> str:
        """Extract city name from address text"""
        if not text:
            return "N/A"

        # Common patterns for Canadian cities
        # Example: "3601 Eglinton Avenue West Toronto, Ontario, Canada" -> "Toronto"
        # Pattern: Look for city before province names
        provinces = ['Ontario', 'ON', 'Quebec', 'QC', 'British Columbia', 'BC',
                     'Alberta', 'AB', 'Manitoba', 'MB', 'Saskatchewan', 'SK']

        for province in provinces:
            pattern = rf'([A-Za-z\s]+),?\s*{province}'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                city = match.group(1).strip().rstrip(',')
                # Remove common address parts
                city = re.sub(r'^.*\s+(Avenue|Street|Road|Drive|Boulevard|Lane|Court|Way)\s+', '', city)
                return city

        # Fallback: Try to find postal code and extract city before it
        postal_pattern = r'([A-Za-z\s]+)\s+[A-Z]\d[A-Z]\s*\d[A-Z]\d'
        match = re.search(postal_pattern, text)
        if match:
            return match.group(1).strip().rstrip(',')

        return "N/A"

    def extract_email(self, soup: BeautifulSoup, page_text: str) -> str:
        """Extract email address from page"""
        # Look for mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        if mailto_links:
            email = mailto_links[0]['href'].replace('mailto:', '').split('?')[0]
            return email.strip()

        # Look for email pattern in text
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)
        if emails:
            # Filter out common non-contact emails
            filtered = [e for e in emails if not any(x in e.lower() for x in ['example.com', 'domain.com', 'email.com'])]
            if filtered:
                return filtered[0]

        return "N/A"

    def extract_location(self, soup: BeautifulSoup, page_text: str) -> str:
        """Extract location (city only) from page"""
        # Look in common sections
        contact_sections = soup.find_all(['div', 'section', 'footer'],
                                        class_=re.compile(r'contact|address|location|footer', re.I))

        for section in contact_sections:
            text = section.get_text()
            city = self.extract_city_from_address(text)
            if city != "N/A":
                return city

        # Look for address schema
        address_schema = soup.find('address')
        if address_schema:
            city = self.extract_city_from_address(address_schema.get_text())
            if city != "N/A":
                return city

        # Search entire page text
        city = self.extract_city_from_address(page_text)
        return city

    def extract_club_type(self, page_text: str, soup: BeautifulSoup) -> str:
        """Determine club type (Private, Public, Semi-Private, etc.)"""
        text_lower = page_text.lower()

        if 'private club' in text_lower or 'members only' in text_lower:
            return "Private"
        elif 'public' in text_lower and 'tennis' in text_lower:
            return "Public"
        elif 'semi-private' in text_lower:
            return "Semi-Private"
        elif 'community' in text_lower:
            return "Community"

        return "N/A"

    def extract_membership_status(self, page_text: str, soup: BeautifulSoup) -> str:
        """Extract membership status (Open, Closed, Waitlist)"""
        text_lower = page_text.lower()

        if 'waitlist' in text_lower or 'wait list' in text_lower or 'waiting list' in text_lower:
            return "Waitlist"
        elif 'accepting members' in text_lower or 'membership available' in text_lower:
            return "Open"
        elif 'membership closed' in text_lower or 'not accepting' in text_lower:
            return "Closed"

        return "N/A"

    def extract_waitlist_length(self, page_text: str, soup: BeautifulSoup) -> str:
        """Extract current waitlist length"""
        text_lower = page_text.lower()

        # Look for patterns like "50 people on waitlist" or "waitlist: 30"
        patterns = [
            r'waitlist.*?(\d+)',
            r'(\d+).*?waitlist',
            r'wait list.*?(\d+)',
            r'(\d+).*?wait list',
            r'waiting list.*?(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1)

        # Check if waitlist is mentioned but no number
        if 'waitlist' in text_lower or 'wait list' in text_lower:
            return "Yes (number not specified)"

        return "N/A"

    def extract_court_info(self, page_text: str, soup: BeautifulSoup) -> tuple:
        """Extract number of courts and surface type"""
        text_lower = page_text.lower()

        # Number of courts
        num_courts = "N/A"
        court_patterns = [
            r'(\d+)\s*(?:indoor|outdoor)?\s*courts?',
            r'courts?:\s*(\d+)',
            r'(\d+)\s*tennis\s*courts?'
        ]

        for pattern in court_patterns:
            match = re.search(pattern, text_lower)
            if match:
                num_courts = match.group(1)
                break

        # Court surface
        surface = "N/A"
        surfaces = ['clay', 'hard court', 'grass', 'carpet', 'artificial', 'har-tru',
                   'hardcourt', 'hard-court', 'indoor', 'outdoor']

        for surf in surfaces:
            if surf in text_lower:
                surface = surf.title()
                break

        return num_courts, surface

    def extract_operating_season(self, page_text: str, soup: BeautifulSoup) -> str:
        """Extract operating season"""
        text_lower = page_text.lower()

        if 'year-round' in text_lower or 'year round' in text_lower:
            return "Year-round"
        elif 'seasonal' in text_lower:
            if 'summer' in text_lower:
                return "Summer"
            elif 'winter' in text_lower:
                return "Winter"
            return "Seasonal"
        elif 'indoor' in text_lower and 'outdoor' in text_lower:
            return "Year-round"

        return "N/A"

    def scrape_club(self, url: str, club_name: str) -> Dict:
        """Scrape a single tennis club website"""
        logger.info(f"Scraping: {club_name} - {url}")

        result = {
            "Club Name": club_name,
            "Location": "N/A",
            "Email": "N/A",
            "Club Type": "N/A",
            "Membership Status": "N/A",
            "Current Waitlist Length": "N/A",
            "Number of Courts": "N/A",
            "Court Surface": "N/A",
            "Operating Season": "N/A",
            "Website URL": url,
            "Scrape Status": "Success"
        }

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent=self.user_agent)
                page = context.new_page()

                # Navigate to page
                try:
                    response = page.goto(url, timeout=self.timeout, wait_until='networkidle')

                    if response is None or response.status >= 400:
                        result["Scrape Status"] = f"Failed - HTTP {response.status if response else 'No response'}"
                        browser.close()
                        return result

                except PlaywrightTimeout:
                    result["Scrape Status"] = "Failed - Timeout"
                    browser.close()
                    return result
                except Exception as e:
                    result["Scrape Status"] = f"Failed - {str(e)[:50]}"
                    browser.close()
                    return result

                # Wait a bit for dynamic content
                time.sleep(2)

                # Get page content
                content = page.content()
                page_text = page.inner_text('body')

                # Parse with BeautifulSoup
                soup = BeautifulSoup(content, 'lxml')

                # Extract information
                result["Location"] = self.extract_location(soup, page_text)
                result["Email"] = self.extract_email(soup, page_text)
                result["Club Type"] = self.extract_club_type(page_text, soup)
                result["Membership Status"] = self.extract_membership_status(page_text, soup)
                result["Current Waitlist Length"] = self.extract_waitlist_length(page_text, soup)

                num_courts, surface = self.extract_court_info(page_text, soup)
                result["Number of Courts"] = num_courts
                result["Court Surface"] = surface
                result["Operating Season"] = self.extract_operating_season(page_text, soup)

                browser.close()

        except Exception as e:
            logger.error(f"Error scraping {club_name}: {str(e)}")
            result["Scrape Status"] = f"Failed - {str(e)[:50]}"

        return result

    def scrape_clubs_from_excel(self, excel_file: str, output_json: str = "results/scraped_data.json",
                                max_clubs: Optional[int] = None) -> list:
        """
        Scrape all clubs from Excel file

        Args:
            excel_file: Path to Excel file with club data
            output_json: Output JSON file path
            max_clubs: Maximum number of clubs to scrape (for testing)
        """
        import pandas as pd

        # Read Excel file
        df = pd.read_excel(excel_file)
        logger.info(f"Loaded {len(df)} clubs from {excel_file}")

        # Limit if specified
        if max_clubs:
            df = df.head(max_clubs)
            logger.info(f"Limiting to first {max_clubs} clubs for testing")

        results = []

        for idx, row in df.iterrows():
            club_name = row['Club Name']
            url = row['Website URL']

            logger.info(f"Processing {idx + 1}/{len(df)}: {club_name}")

            # Scrape the club
            result = self.scrape_club(url, club_name)
            results.append(result)

            # Save after each scrape (incremental save)
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            # Be polite - wait between requests
            time.sleep(1)

        logger.info(f"Scraping complete. Results saved to {output_json}")
        return results


if __name__ == "__main__":
    # Test with first 5 clubs
    scraper = TennisClubScraper()
    results = scraper.scrape_clubs_from_excel(
        "GTA Tennis clubs data .xlsx",
        "results/scraped_data.json",
        max_clubs=5  # Test with 5 clubs first
    )

    print(f"\n{'='*60}")
    print(f"Scraped {len(results)} clubs")
    print(f"{'='*60}")

    # Show summary
    successful = sum(1 for r in results if r['Scrape Status'] == 'Success')
    print(f"Successful: {successful}/{len(results)}")
