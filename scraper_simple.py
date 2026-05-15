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
    def __init__(self, data_merger=None):
        self.session = requests.Session()
        # Better headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.timeout = 15
        self.debug = True  # Enable debug logging
        self.data_merger = data_merger  # Optional data merger for pre-populated data

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
        """Extract email address from page - Enhanced with multiple strategies"""

        # Strategy 1: Look for mailto links (highest priority)
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        if mailto_links:
            email = mailto_links[0]['href'].replace('mailto:', '').split('?')[0].strip()
            if '@' in email:
                return email

        # Strategy 2: Look in meta tags
        meta_email = soup.find('meta', attrs={'name': re.compile(r'email', re.I)})
        if meta_email and meta_email.get('content'):
            email = meta_email['content'].strip()
            if '@' in email:
                return email

        # Strategy 3: Look in contact section specifically
        contact_section = soup.find(['div', 'section'], class_=re.compile(r'contact', re.I))
        if contact_section:
            contact_text = contact_section.get_text()
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', contact_text)
            if emails:
                for e in emails:
                    if not any(x in e.lower() for x in ['example', 'test', 'noreply']):
                        return e

        # Strategy 4: Look in footer
        footer = soup.find('footer')
        if footer:
            footer_text = footer.get_text()
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', footer_text)
            if emails:
                for e in emails:
                    if not any(x in e.lower() for x in ['example', 'test', 'noreply']):
                        return e

        # Strategy 5: Search entire page text with smart filtering
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)

        if emails:
            # Filter and prioritize
            blacklist = ['example.com', 'test.com', 'placeholder', 'yourdomain', 'email.com',
                        'sample.com', 'domain.com', 'sampleemail', 'noreply', 'no-reply',
                        'privacy@', 'legal@', 'abuse@']

            # Prioritize club-related emails
            priority_keywords = ['info@', 'contact@', 'tennis@', 'club@', 'admin@', 'president@']

            priority_emails = []
            other_emails = []

            for e in emails:
                e_lower = e.lower()
                # Skip blacklisted
                if any(x in e_lower for x in blacklist):
                    continue
                # Check priority
                if any(keyword in e_lower for keyword in priority_keywords):
                    priority_emails.append(e)
                else:
                    other_emails.append(e)

            # Return priority emails first
            if priority_emails:
                return priority_emails[0]
            if other_emails:
                return other_emails[0]

        # Strategy 6: Look for obfuscated emails (e.g., "info AT domain DOT com")
        obfuscated = re.search(r'(\w+)\s*(?:@|AT|at)\s*(\w+)\s*(?:\.|DOT|dot)\s*(\w+)', page_text, re.I)
        if obfuscated:
            email = f"{obfuscated.group(1)}@{obfuscated.group(2)}.{obfuscated.group(3)}"
            return email

        # Strategy 7: Check if there's a contact page link
        contact_links = soup.find_all('a', href=re.compile(r'contact|email', re.I))
        if contact_links:
            return 'Contact form available'

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
        """Extract number of courts - Enhanced with multiple strategies"""

        # Strategy 1: Look in facilities/amenities section
        facilities = soup.find(['div', 'section'], class_=re.compile(r'facilit|amenity|about', re.I))
        if facilities:
            fac_text = facilities.get_text()
            match = re.search(r'(\d+)\s+(?:tennis\s+)?courts?', fac_text, re.I)
            if match:
                count = int(match.group(1))
                if 1 <= count <= 50:
                    return str(count)

        # Strategy 2: Comprehensive pattern matching
        patterns = [
            r'(\d+)\s+(?:tennis\s+)?courts?(?:\s|,|\.|\)|$)',
            r'courts?[:\s]+(\d+)',
            r'total\s+(?:of\s+)?(\d+)\s+courts?',
            r'we\s+have\s+(\d+)\s+courts?',
            r'featuring\s+(\d+)\s+courts?',
            r'(\d+)\s+(?:indoor|outdoor)\s+courts?',
            r'club\s+has\s+(\d+)\s+courts?',
            r'facilities\s+include\s+(\d+)\s+courts?',
            r'(\d+)[-\s]court',  # e.g., "4-court facility"
            r'with\s+(\d+)\s+courts?',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, page_text, re.I)
            for match in matches:
                count = int(match.group(1))
                # Sanity check - tennis clubs typically have 1-50 courts
                if 1 <= count <= 50:
                    return str(count)

        # Strategy 3: Look for spelled-out numbers
        word_to_num = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        for word, num in word_to_num.items():
            if re.search(rf'\b{word}\s+(?:tennis\s+)?courts?', page_text, re.I):
                return str(num)

        return 'N/A'

    def extract_court_surface(self, page_text: str) -> str:
        """Extract court surface type - Enhanced"""
        text_lower = page_text.lower()

        surfaces_found = []

        # Hard courts (most common)
        if re.search(r'\bhard\s*courts?|\bhardcourts?|\bhard[-\s]surface|\basphalt|\bconcrete\s*courts?', text_lower):
            surfaces_found.append('Hard')

        # Clay courts
        if re.search(r'\bclay\s*courts?|\bred\s*clay|\bhar-tru|\bgreen\s*clay', text_lower):
            surfaces_found.append('Clay')

        # Grass courts
        if re.search(r'\bgrass\s*courts?|\blawn\s*courts?', text_lower):
            surfaces_found.append('Grass')

        # Indoor/Outdoor
        if re.search(r'\bindoor\s*courts?|\benclosed|\bbubble|\bdome', text_lower):
            surfaces_found.append('Indoor')
        if re.search(r'\boutdoor\s*courts?|\bopen-air', text_lower):
            if 'Indoor' not in surfaces_found:  # Don't add if already has indoor
                surfaces_found.append('Outdoor')

        # Synthetic/Other
        if re.search(r'\bsynthetic|\bartificial\s*grass|\bturf\s*courts?', text_lower):
            surfaces_found.append('Synthetic')

        if surfaces_found:
            return ', '.join(set(surfaces_found))  # Remove duplicates

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
            'Operating Season': 'N/A',
            'Scrape Status': 'Failed'  # Track success/failure
        }

        # Check data merger first for existing data
        if self.data_merger:
            existing_data = self.data_merger.get_existing_data(club_name, url)
            if existing_data:
                if self.debug:
                    print(f"[DEBUG] Found existing data for {club_name} from {existing_data.get('source', 'database')}")

                # Use existing data where available
                for key in ['Email', 'Location', 'Club Type', 'Membership Status',
                           'Number of Courts', 'Court Surface', 'Operating Season']:
                    if key in existing_data and existing_data[key] != 'N/A':
                        result[key] = existing_data[key]

                # If we have email and some other data, consider it a success without scraping
                if result['Email'] != 'N/A' or result['Number of Courts'] != 'N/A':
                    result['Scrape Status'] = f"Pre-loaded ({existing_data.get('source', 'DB')})"
                    if self.debug:
                        found_fields = [k for k, v in result.items() if v != 'N/A' and k not in ['Club Name', 'Website', 'Scrape Status']]
                        print(f"[DEBUG] Pre-loaded data fields: {found_fields}")
                    # Still try to scrape for missing data, but don't fail if it doesn't work
                    # Fall through to scraping below
                    pass

        try:
            # Make sure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            if self.debug:
                print(f"[DEBUG] Scraping {club_name}: {url}")

            # Try with SSL verification disabled from the start (many tennis club sites have issues)
            response = self.session.get(url, timeout=self.timeout, verify=False, allow_redirects=True)

            if self.debug:
                print(f"[DEBUG] Status Code: {response.status_code}")
                print(f"[DEBUG] Final URL after redirects: {response.url}")

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check if it's a JavaScript-heavy site
            is_js_heavy = False
            scripts = soup.find_all('script')
            if len(scripts) > 10:  # Lots of scripts
                script_text = ' '.join([s.string or '' for s in scripts[:5]])
                if any(framework in script_text.lower() for framework in ['react', 'vue', 'angular', 'next']):
                    is_js_heavy = True
                    if self.debug:
                        print(f"[DEBUG] ⚠️  JavaScript-heavy site detected - data may be limited")

            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()

            page_text = soup.get_text(separator=' ', strip=True)

            if self.debug:
                print(f"[DEBUG] Page text length: {len(page_text)} characters")
                if len(page_text) < 500:
                    print(f"[DEBUG] ⚠️  Very little visible text - likely JS-rendered")
                print(f"[DEBUG] First 200 chars: {page_text[:200]}")

            # Only extract if we have reasonable content
            if len(page_text) < 200:
                result['Scrape Status'] = 'JS-heavy (limited data)'
                if self.debug:
                    print(f"[DEBUG] ⚠️  Insufficient content - skipping detailed extraction")
            else:
                # Extract all data fields (only if pre-loaded data not complete)
                if result['Email'] == 'N/A':
                    result['Email'] = self.extract_email(soup, page_text)
                if result['Location'] == 'N/A':
                    result['Location'] = self.extract_city_from_address(page_text)
                if result['Club Type'] == 'N/A':
                    result['Club Type'] = self.extract_club_type(page_text, soup)
                if result['Membership Status'] == 'N/A':
                    result['Membership Status'] = self.extract_membership_status(page_text)
                if result['Waitlist Length'] == 'N/A':
                    result['Waitlist Length'] = self.extract_waitlist_length(page_text, soup)
                if result['Number of Courts'] == 'N/A':
                    result['Number of Courts'] = self.extract_courts_count(page_text, soup)
                if result['Court Surface'] == 'N/A':
                    result['Court Surface'] = self.extract_court_surface(page_text)
                if result['Operating Season'] == 'N/A':
                    result['Operating Season'] = self.extract_operating_season(page_text)

                # Update status based on what was found
                if result['Scrape Status'].startswith('Pre-loaded'):
                    # Keep pre-loaded status
                    pass
                elif is_js_heavy and len([v for v in result.values() if v == 'N/A']) > 5:
                    result['Scrape Status'] = 'Success (JS-limited)'
                else:
                    result['Scrape Status'] = 'Success'

            if self.debug:
                found_fields = [k for k, v in result.items() if v != 'N/A' and k not in ['Club Name', 'Website', 'Scrape Status']]
                print(f"[DEBUG] Found data for: {found_fields}")
                missing_fields = [k for k, v in result.items() if v == 'N/A' and k not in ['Club Name', 'Website', 'Scrape Status']]
                if missing_fields:
                    print(f"[DEBUG] Missing data for: {missing_fields}")

            # Small delay to be respectful
            time.sleep(0.5)

        except requests.exceptions.Timeout:
            error_msg = f"Timeout after {self.timeout}s"
            print(f"[ERROR] {club_name}: {error_msg}")
            result['Scrape Status'] = error_msg

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {e.response.status_code}"
            print(f"[ERROR] {club_name}: {error_msg}")
            result['Scrape Status'] = error_msg

        except requests.exceptions.ConnectionError:
            error_msg = "Connection failed"
            print(f"[ERROR] {club_name}: {error_msg}")
            result['Scrape Status'] = error_msg

        except requests.exceptions.TooManyRedirects:
            error_msg = "Too many redirects"
            print(f"[ERROR] {club_name}: {error_msg}")
            result['Scrape Status'] = error_msg

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)[:100]}"
            print(f"[ERROR] {club_name}: {error_msg}")
            result['Scrape Status'] = error_msg

        return result


if __name__ == '__main__':
    # Test the scraper
    scraper = TennisClubScraper()
    test_result = scraper.scrape_club('https://www.example-tennis-club.com', 'Test Club')
    print(test_result)
