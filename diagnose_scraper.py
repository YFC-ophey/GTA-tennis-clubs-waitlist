#!/usr/bin/env python3
"""
Diagnostic script to check what's happening with the scraper
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

# Read Excel file
df = pd.read_excel('GTA_Tennis_clubs_raw_data .xlsx')

print("=" * 80)
print("DIAGNOSTIC REPORT - First 5 Tennis Clubs")
print("=" * 80)

# Check first 5 rows
for idx in range(min(5, len(df))):
    row = df.iloc[idx]
    club_name = row.get('Club Name', 'Unknown')
    website = row.get('Website', '')

    print(f"\n{idx + 1}. {club_name}")
    print(f"   Website: {website}")

    if pd.isna(website) or not website.strip():
        print(f"   ❌ No website URL provided")
        continue

    # Try to fetch the website
    url = website if website.startswith('http') else f'https://{website}'

    try:
        print(f"   Trying to fetch: {url}")
        response = requests.get(url, timeout=10, verify=False, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        print(f"   ✓ Status Code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)

        print(f"   ✓ Page loaded successfully")
        print(f"   ✓ Text length: {len(text)} characters")

        # Check for emails
        import re
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            print(f"   ✓ Found {len(emails)} email(s): {emails[:3]}")
        else:
            print(f"   ⚠ No emails found")

        # Show first 500 chars
        print(f"   Preview: {text[:500]}...")

    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout - website too slow")
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {e}")
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("COLUMN NAMES IN EXCEL FILE:")
print("=" * 80)
print(df.columns.tolist())
