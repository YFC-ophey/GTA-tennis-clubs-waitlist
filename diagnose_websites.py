#!/usr/bin/env python3
"""
Website Diagnostic Tool
Tests actual club websites to see what content is available
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import warnings
warnings.filterwarnings('ignore')

def test_website(url, club_name):
    """Test a single website and show what content we can access"""
    print("\n" + "="*80)
    print(f"Testing: {club_name}")
    print(f"URL: {url}")
    print("="*80)

    if not url.startswith('http'):
        url = 'https://' + url

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        response = requests.get(url, headers=headers, timeout=15, verify=False, allow_redirects=True)

        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ Final URL: {response.url}")
        print(f"✓ Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"✓ Content Length: {len(response.text)} characters")

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove scripts and styles
        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        page_text = soup.get_text(separator=' ', strip=True)

        print(f"✓ Visible Text Length: {len(page_text)} characters")

        # Check for emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
        if emails:
            print(f"\n📧 Emails Found: {len(emails)}")
            for email in emails[:5]:
                print(f"   - {email}")
        else:
            print("\n❌ No emails found in visible text")

        # Check for court mentions
        court_matches = re.findall(r'(\d+)\s*(?:tennis\s+)?courts?', page_text, re.I)
        if court_matches:
            print(f"\n🎾 Court Mentions: {court_matches[:3]}")
        else:
            print("\n❌ No court count found")

        # Check for membership/waitlist
        if re.search(r'waitlist|waiting\s+list', page_text, re.I):
            print("\n📋 Mentions: waitlist/waiting list")
        if re.search(r'membership|member', page_text, re.I):
            print("📋 Mentions: membership")

        # Show first 500 chars of visible text
        print(f"\n📄 First 500 chars of visible text:")
        print("-" * 80)
        print(page_text[:500])
        print("-" * 80)

        # Check if it's a JavaScript-heavy site
        scripts = soup.find_all('script')
        print(f"\n🔧 Technical Details:")
        print(f"   - Script tags: {len(scripts)}")
        print(f"   - Has React: {'Yes' if 'react' in response.text.lower() else 'No'}")
        print(f"   - Has Vue: {'Yes' if 'vue' in response.text.lower() else 'No'}")
        print(f"   - Has Angular: {'Yes' if 'angular' in response.text.lower() else 'No'}")

        return True

    except requests.exceptions.Timeout:
        print("❌ Timeout - website too slow")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)[:100]}")
        return False

# Test a sample of clubs
print("\n" + "="*80)
print("🎾 TENNIS CLUB WEBSITE DIAGNOSTIC TOOL")
print("="*80)

# Load Excel file
try:
    df = pd.read_excel('GTA_Tennis_clubs_raw_data .xlsx')
    print(f"\nLoaded {len(df)} clubs from Excel file")

    # Test first 5 clubs with websites
    tested = 0
    successful = 0

    for idx, row in df.iterrows():
        if tested >= 5:
            break

        club_name = row.get('Club Name', 'Unknown')
        website = row.get('Website', '')

        if pd.notna(website) and website.strip():
            tested += 1
            if test_website(website, club_name):
                successful += 1

    print("\n" + "="*80)
    print(f"SUMMARY: {successful}/{tested} websites successfully accessed")
    print("="*80)

except Exception as e:
    print(f"Error loading Excel file: {e}")
