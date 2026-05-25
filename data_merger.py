#!/usr/bin/env python3
"""
Data Merger - Combines existing CSV data with Excel file
Pre-populates known information so scraper doesn't need to re-scrape
"""

import pandas as pd
import re
from typing import Dict, List


class DataMerger:
    def __init__(self):
        self.toronto_data = None
        self.ota_data = None
        self.excel_data = None
        self.excel_run_data = None
        self.merged_data = {}

    def load_data(self):
        """Load all data sources"""
        print("Loading data sources...")

        # Load Toronto CSV
        try:
            self.toronto_data = pd.read_csv('Tennis clubs data - CityofToronto.csv')
            print(f"✓ City of Toronto: {len(self.toronto_data)} clubs")
        except Exception as e:
            print(f"⚠ Could not load Toronto data: {e}")

        # Load OTA CSV
        try:
            self.ota_data = pd.read_csv('Tennis clubs data - OTA.csv')
            print(f"✓ Ontario Tennis Association: {len(self.ota_data)} clubs")
        except Exception as e:
            print(f"⚠ Could not load OTA data: {e}")

        # Load main Excel file
        try:
            self.excel_data = pd.read_excel('GTA_Tennis_clubs_raw_data .xlsx', sheet_name='data')
            self.excel_run_data = pd.read_excel('GTA_Tennis_clubs_raw_data .xlsx', sheet_name='run')
            print(f"✓ Main Excel file: {len(self.excel_data)} clubs")
        except Exception as e:
            print(f"⚠ Could not load Excel data: {e}")

        # Calculate total
        total_raw = 0
        if self.toronto_data is not None:
            total_raw += len(self.toronto_data)
        if self.ota_data is not None:
            total_raw += len(self.ota_data)

        print(f"\n📊 CSV Data: {total_raw} total clubs (before deduplication)")

    def normalize_name(self, name: str) -> str:
        """Normalize club name for matching"""
        if pd.isna(name):
            return ""
        # Convert to lowercase, remove extra spaces, remove common suffixes
        name = str(name).lower().strip()
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'\s*tennis\s*club\s*', ' ', name)
        name = re.sub(r'\s*tc\s*', ' ', name)
        name = name.strip()
        return name

    def normalize_url(self, url: str) -> str:
        """Normalize URL for matching"""
        if pd.isna(url):
            return ""
        url = str(url).lower().strip()
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        url = re.sub(r'/$', '', url)
        return url

    def build_lookup_dict(self):
        """Build lookup dictionary from CSV data"""
        print("\nBuilding lookup dictionary...")

        # Process OTA data (has email addresses!)
        if self.ota_data is not None:
            for _, row in self.ota_data.iterrows():
                club_name = row.get('name', '')
                email = row.get('email', '')
                website = row.get('website_url', '')
                club_type = row.get('type', '')
                location = row.get('location', '')

                if pd.isna(club_name):
                    continue

                # Create normalized keys for matching
                name_key = self.normalize_name(club_name)
                url_key = self.normalize_url(website)

                data = {
                    'source': 'OTA',
                    'Club Name': club_name,
                    'Email': email if pd.notna(email) and email else 'N/A',
                    'Location': location if pd.notna(location) else 'N/A',
                    'Club Type': self.map_club_type(club_type),
                    'Website': website if pd.notna(website) else 'N/A',
                }

                if name_key:
                    self.merged_data[name_key] = data
                if url_key:
                    self.merged_data[url_key] = data

        # Process Toronto data (has court counts, membership status)
        if self.toronto_data is not None:
            for _, row in self.toronto_data.iterrows():
                club_name = row.get('name', '')
                website = row.get('website_url', '')
                courts = row.get('courts', '')
                membership = row.get('membership_status', '')
                phone = row.get('phone', '')
                club_type = row.get('type', '')

                if pd.isna(club_name):
                    continue

                name_key = self.normalize_name(club_name)
                url_key = self.normalize_url(website)

                # Build data dict
                data = {
                    'source': 'Toronto',
                    'Club Name': club_name,
                    'Number of Courts': str(int(courts)) if pd.notna(courts) and str(courts).replace('.', '').isdigit() else 'N/A',
                    'Membership Status': self.map_membership_status(membership),
                    'Phone': phone if pd.notna(phone) else 'N/A',
                    'Club Type': self.map_club_type(club_type),
                    'Website': website if pd.notna(website) else 'N/A',
                }

                # Merge with existing data if present
                if name_key in self.merged_data:
                    # OTA data already exists, add Toronto info
                    self.merged_data[name_key].update({k: v for k, v in data.items() if v != 'N/A'})
                    self.merged_data[name_key]['source'] = 'OTA+Toronto'
                else:
                    if name_key:
                        self.merged_data[name_key] = data

                if url_key and url_key not in self.merged_data:
                    self.merged_data[url_key] = data

        # Process previously scraped workbook rows as enrichment only.
        # These values are noisier than OTA/Toronto, so they fill gaps but do not overwrite.
        if self.excel_run_data is not None:
            for _, row in self.excel_run_data.iterrows():
                club_name = row.get('Club Name', '')
                website = row.get('Website URL', '')

                if pd.isna(club_name):
                    continue

                name_key = self.normalize_name(club_name)
                url_key = self.normalize_url(website)
                existing = self.merged_data.get(name_key) or self.merged_data.get(url_key)

                data = {
                    'source': 'Workbook Run',
                    'Club Name': club_name,
                    'Email': self.clean_email(row.get('Email', '')),
                    'Location': self.clean_location(row.get('Location', '')),
                    'Club Type': self.map_club_type(row.get('Club Type', '')),
                    'Membership Status': self.map_membership_status(row.get('Membership Status', '')),
                    'Court Surface': self.clean_court_surface(row.get('Court Surface', '')),
                    'Operating Season': self.clean_operating_season(row.get('Operating Season', '')),
                    'Website': website if pd.notna(website) else 'N/A',
                }

                if existing is None:
                    existing = data
                else:
                    self.merge_missing_fields(existing, data)

                if name_key:
                    self.merged_data[name_key] = existing
                if url_key:
                    self.merged_data[url_key] = existing

        print(f"✓ Built lookup dictionary with {len(self.merged_data)} entries")

    def is_missing(self, value: object) -> bool:
        if pd.isna(value):
            return True
        text = str(value).strip()
        return not text or text.lower() in {'n/a', 'na', 'not found', 'none', 'nan', 'null'}

    def merge_missing_fields(self, existing: Dict, incoming: Dict) -> None:
        for key, value in incoming.items():
            if key == 'source':
                continue
            if self.is_missing(value):
                continue
            if self.is_missing(existing.get(key, 'N/A')):
                existing[key] = value

        source = existing.get('source', '')
        incoming_source = incoming.get('source', '')
        if incoming_source and incoming_source not in str(source):
            existing['source'] = f"{source}+{incoming_source}" if source else incoming_source

    def clean_email(self, value: object) -> str:
        if self.is_missing(value):
            return 'N/A'
        text = str(value).strip()
        return text if '@' in text else 'N/A'

    def clean_location(self, value: object) -> str:
        if self.is_missing(value):
            return 'N/A'
        text = re.sub(r'\s+', ' ', str(value)).strip()
        if len(text) > 60:
            return 'N/A'
        noisy_terms = ['home', 'programs', 'registration', 'contact us', 'skip to content']
        lowered = text.lower()
        if any(term in lowered for term in noisy_terms):
            return 'N/A'
        return text

    def clean_court_surface(self, value: object) -> str:
        if self.is_missing(value):
            return 'N/A'
        text = str(value).strip()
        lowered = text.lower()
        if any(surface in lowered for surface in ['hard', 'clay', 'grass', 'indoor', 'outdoor']):
            return text
        return 'N/A'

    def clean_operating_season(self, value: object) -> str:
        if self.is_missing(value):
            return 'N/A'
        text = str(value).strip()
        lowered = text.lower()
        if any(season in lowered for season in ['year-round', 'year round', 'summer', 'winter', 'seasonal']):
            return text
        return 'N/A'

    def map_club_type(self, club_type: str) -> str:
        """Map club type to standard format"""
        if pd.isna(club_type):
            return 'N/A'

        club_type = str(club_type).lower()
        if 'private' in club_type:
            return 'Private'
        elif 'public' in club_type or 'community' in club_type:
            return 'Public'
        elif 'commercial' in club_type or 'associate' in club_type:
            return 'Commercial'
        return 'N/A'

    def map_membership_status(self, status: str) -> str:
        """Map membership status to standard format"""
        if pd.isna(status):
            return 'N/A'

        status = str(status).lower()
        if 'open' in status:
            return 'Open'
        elif 'waitlist' in status or 'wait' in status:
            return 'Waitlist'
        elif 'closed' in status or 'full' in status:
            return 'Closed'
        return 'N/A'

    def get_existing_data(self, club_name: str, website: str) -> Dict:
        """Get existing data for a club if available"""
        # Try to match by name first
        name_key = self.normalize_name(club_name)
        if name_key in self.merged_data:
            return self.merged_data[name_key]

        # Try to match by URL
        url_key = self.normalize_url(website)
        if url_key in self.merged_data:
            return self.merged_data[url_key]

        return None

    def print_summary(self):
        """Print summary of available data"""
        if not self.merged_data:
            return

        # Count unique clubs by club name
        unique_clubs = set([v['Club Name'] for v in self.merged_data.values() if 'Club Name' in v])
        total_unique = len(unique_clubs)

        # Count clubs with specific data
        with_email = len(set([v['Club Name'] for v in self.merged_data.values()
                             if v.get('Email', 'N/A') != 'N/A' and 'Club Name' in v]))
        with_courts = len(set([v['Club Name'] for v in self.merged_data.values()
                              if v.get('Number of Courts', 'N/A') != 'N/A' and 'Club Name' in v]))
        with_membership = len(set([v['Club Name'] for v in self.merged_data.values()
                                  if v.get('Membership Status', 'N/A') != 'N/A' and 'Club Name' in v]))

        print("\n" + "="*70)
        print("📊 PRE-LOADED DATA SUMMARY")
        print("="*70)
        print(f"Unique clubs with pre-loaded data: {total_unique}")
        print(f"  ✉️  With email addresses: {with_email}")
        print(f"  🎾 With court counts: {with_courts}")
        print(f"  📋 With membership status: {with_membership}")
        print("="*70)
        print("These clubs will skip scraping and use existing data!")
        print("="*70)


# Global instance
data_merger = DataMerger()


def initialize_data_merger():
    """Initialize the data merger on startup"""
    global data_merger
    data_merger = DataMerger()
    data_merger.load_data()
    data_merger.build_lookup_dict()
    data_merger.print_summary()
    return data_merger


if __name__ == '__main__':
    # Test the data merger
    merger = initialize_data_merger()

    # Test lookup
    print("\n\nTesting lookups:")
    print("-" * 60)

    test_clubs = [
        ('Agincourt Tennis Club', 'http://www.agincourttennisclub.ca'),
        ('Banbury Tennis Club', 'http://www.banburytennisclub.net'),
        ('10XTO', 'https://www.10xto.com/tennis'),
    ]

    for name, url in test_clubs:
        print(f"\nLooking up: {name}")
        data = merger.get_existing_data(name, url)
        if data:
            print(f"  ✓ Found! Source: {data.get('source', 'Unknown')}")
            print(f"    Email: {data.get('Email', 'N/A')}")
            print(f"    Courts: {data.get('Number of Courts', 'N/A')}")
            print(f"    Membership: {data.get('Membership Status', 'N/A')}")
        else:
            print(f"  ✗ Not found in database")
