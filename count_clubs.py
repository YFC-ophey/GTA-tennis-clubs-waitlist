#!/usr/bin/env python3
import pandas as pd

# Load the CSVs
toronto_df = pd.read_csv('Tennis clubs data - CityofToronto.csv')
ota_df = pd.read_csv('Tennis clubs data - OTA.csv')

print("CSV File Counts:")
print(f"City of Toronto: {len(toronto_df)} clubs")
print(f"OTA: {len(ota_df)} clubs")
print(f"Total (without deduplication): {len(toronto_df) + len(ota_df)} clubs")

# Check for duplicates by normalizing names
def normalize_name(name):
    if pd.isna(name):
        return ""
    import re
    name = str(name).lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\s*tennis\s*club\s*', ' ', name)
    return name.strip()

toronto_names = set([normalize_name(name) for name in toronto_df['name'] if pd.notna(name)])
ota_names = set([normalize_name(name) for name in ota_df['name'] if pd.notna(name)])

duplicates = toronto_names & ota_names
unique_total = len(toronto_names | ota_names)

print(f"\nDeduplication Analysis:")
print(f"Unique Toronto clubs: {len(toronto_names)}")
print(f"Unique OTA clubs: {len(ota_names)}")
print(f"Clubs in both datasets: {len(duplicates)}")
print(f"Total unique clubs: {unique_total}")

# Also check the main Excel file
try:
    excel_df = pd.read_excel('GTA_Tennis_clubs_raw_data .xlsx')
    print(f"\nMain Excel file: {len(excel_df)} clubs")
except:
    print("\nCould not load Excel file")
