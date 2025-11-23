#!/usr/bin/env python3
"""
Simple HTTP-based Tennis Club Web Scraper
Uses requests and BeautifulSoup for reliable scraping
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict
from urllib.parse import urljoin, urlparse
import time

class TennisClubScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 10

    def extract_city_from_address(self, text: str) -> str:
        """Extract city name from address text"""
        # GTA cities pattern
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

        # Try postal code pattern (ends with Ontario city)
        postal_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+ON', text)
        if postal_match:
            return postal_match.group(1)

        return 'N/A'

    def extract_email(self, soup: BeautifulSoup, page_text: str) -> str:
        """Extract email address from page"""
        # Look for mailto links first
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        if mailto_links:
            email = mailto_links[0]['href'].replace('mailto:', '').split('?')[0]
            return email.strip()

        # Search page text for email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)

        if emails:
            # Filter out common false positives
            valid_emails = [e for e in emails if not any(x in e.lower() for x in ['example.com', 'test.com', 'placeholder'])]
            if valid_emails:
                return valid_emails[0]

        return 'N/A'

    def extract_waitlist_length(self, page_text: str, soup: BeautifulSoup) -> str:
        """Extract waitlist length information"""
        # Patterns for waitlist length
        patterns = [
            r'waitlist[:\s]+(\d+)\s*(?:people|members|players)?',
            r'(\d+)\s*(?:people|members|players)?\s+on\s+(?:the\s+)?waitlist',
            r'waiting\s+list[:\s]+(\d+)',
            r'(\d+)\s*year\s+waitlist',
            r'(\d{1,3})\s*(?:\+)?\s*on\s+wait',
        ]

        text_lower = page_text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.I)
            if match:
                return match.group(1)

        # Check for qualitative descriptions
        if re.search(r'no\s+waitlist|waitlist\s+is\s+closed|not\s+accepting', text_lower, re.I):
            return '0'
        if re.search(r'long\s+waitlist|extensive\s+waitlist|several\s+years?', text_lower, re.I):
            return 'Long'

        return 'N/A'

    def extract_membership_status(self, page_text: str) -> str:
        """Extract membership status"""
        text_lower = page_text.lower()

        # Check for open membership
        if re.search(r'(?:accepting|open)\s+(?:new\s+)?(?:members|memberships|applications)', text_lower, re.I):
            return 'Open'

        # Check for waitlist
        if re.search(r'waitlist|waiting\s+list|join\s+(?:our\s+)?wait', text_lower, re.I):
            return 'Waitlist'

        # Check for closed
        if re.search(r'not\s+accepting|membership\s+(?:is\s+)?closed|full\s+capacity', text_lower, re.I):
            return 'Closed'

        return 'N/A'

    def extract_courts_count(self, page_text: str, soup: BeautifulSoup) -> str:
        """Extract number of courts"""
        patterns = [
            r'(\d+)\s+(?:tennis\s+)?courts?',
            r'courts?[:\s]+(\d+)',
            r'total\s+of\s+(\d+)\s+courts?',
        ]

        for pattern in patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                return match.group(1)

        return 'N/A'

    def extract_court_surface(self, page_text: str) -> str:
        """Extract court surface type"""
        text_lower = page_text.lower()

        surfaces_found = []
        if 'hard court' in text_lower or 'hardcourt' in text_lower:
            surfaces_found.append('Hard')
        if 'clay court' in text_lower or 'clay' in text_lower and 'court' in text_lower:
            surfaces_found.append('Clay')
        if 'grass court' in text_lower or 'grass' in text_lower and 'court' in text_lower:
            surfaces_found.append('Grass')
        if 'indoor' in text_lower:
            surfaces_found.append('Indoor')

        if surfaces_found:
            return ', '.join(surfaces_found)

        return 'N/A'

    def extract_operating_season(self, page_text: str) -> str:
        """Extract operating season"""
        text_lower = page_text.lower()

        if 'year round' in text_lower or 'year-round' in text_lower or 'all year' in text_lower:
            return 'Year-round'
        if 'seasonal' in text_lower:
            if 'april' in text_lower or 'may' in text_lower:
                return 'Seasonal (Spring-Fall)'
        if 'outdoor only' in text_lower:
            return 'Seasonal'
        if 'indoor' in text_lower and 'outdoor' in text_lower:
            return 'Year-round'

        return 'N/A'

    def extract_club_type(self, page_text: str, soup: BeautifulSoup) -> str:
        """Extract club type (private/public)"""
        text_lower = page_text.lower()

        if re.search(r'private\s+club|members?\s+only|membership\s+required', text_lower, re.I):
            return 'Private'
        if re.search(r'public|community|municipal|city\s+of', text_lower, re.I):
            return 'Public'

        return 'N/A'

    def scrape_club(self, url: str, club_name: str) -> Dict:
        """Scrape a single tennis club website"""
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
            'Operating Season': 'N/A'
        }

        try:
            # Make sure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Fetch the page
            response = self.session.get(url, timeout=self.timeout, verify=False)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text(separator=' ', strip=True)

            # Extract all data fields
            result['Email'] = self.extract_email(soup, page_text)
            result['Location'] = self.extract_city_from_address(page_text)
            result['Club Type'] = self.extract_club_type(page_text, soup)
            result['Membership Status'] = self.extract_membership_status(page_text)
            result['Waitlist Length'] = self.extract_waitlist_length(page_text, soup)
            result['Number of Courts'] = self.extract_courts_count(page_text, soup)
            result['Court Surface'] = self.extract_court_surface(page_text)
            result['Operating Season'] = self.extract_operating_season(page_text)

            # Small delay to be respectful
            time.sleep(0.5)

        except requests.exceptions.SSLError:
            print(f"SSL Error for {club_name}, trying without verification...")
            try:
                response = self.session.get(url, timeout=self.timeout, verify=False)
                soup = BeautifulSoup(response.text, 'html.parser')
                page_text = soup.get_text(separator=' ', strip=True)
                result['Email'] = self.extract_email(soup, page_text)
                result['Location'] = self.extract_city_from_address(page_text)
            except Exception as e:
                print(f"Still failed for {club_name}: {e}")

        except Exception as e:
            print(f"Error scraping {club_name}: {str(e)}")

        return result


if __name__ == '__main__':
    # Test the scraper
    scraper = TennisClubScraper()
    test_result = scraper.scrape_club('https://www.example-tennis-club.com', 'Test Club')
    print(test_result)
