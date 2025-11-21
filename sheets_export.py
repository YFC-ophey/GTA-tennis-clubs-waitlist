"""
Google Sheets Exporter
Exports scraped tennis club data to Google Sheets
"""

import json
import logging
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GoogleSheetsExporter:
    def __init__(self, credentials_file: Optional[str] = None):
        self.credentials_file = credentials_file or os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')

        if not self.credentials_file or not os.path.exists(self.credentials_file):
            logger.warning("Google Sheets credentials not found. Export to Google Sheets will be disabled.")
            self.client = None
        else:
            try:
                import gspread
                from google.oauth2.service_account import Credentials

                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]

                creds = Credentials.from_service_account_file(self.credentials_file, scopes=scopes)
                self.client = gspread.authorize(creds)
                logger.info("Google Sheets client initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets client: {str(e)}")
                self.client = None

    def export_to_sheets(self, data: List[Dict], sheet_name: str = None) -> bool:
        """
        Export data to Google Sheets

        Args:
            data: List of club dictionaries
            sheet_name: Name of the Google Sheet
        """

        if not self.client:
            logger.error("Google Sheets client not initialized")
            return False

        sheet_name = sheet_name or os.getenv('GOOGLE_SHEET_NAME', 'GTA Tennis Clubs Data')

        try:
            # Try to open existing spreadsheet or create new one
            try:
                spreadsheet = self.client.open(sheet_name)
                worksheet = spreadsheet.sheet1
                logger.info(f"Opened existing spreadsheet: {sheet_name}")
            except:
                spreadsheet = self.client.create(sheet_name)
                worksheet = spreadsheet.sheet1
                logger.info(f"Created new spreadsheet: {sheet_name}")

            # Prepare data for export
            if not data:
                logger.warning("No data to export")
                return False

            # Get headers from first item
            headers = list(data[0].keys())

            # Prepare rows
            rows = [headers]
            for item in data:
                row = [str(item.get(header, '')) for header in headers]
                rows.append(row)

            # Clear existing data and update
            worksheet.clear()
            worksheet.update(rows, 'A1')

            # Format header row
            worksheet.format('A1:K1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8}
            })

            logger.info(f"Successfully exported {len(data)} clubs to Google Sheets")
            logger.info(f"Spreadsheet URL: {spreadsheet.url}")

            return True

        except Exception as e:
            logger.error(f"Failed to export to Google Sheets: {str(e)}")
            return False

    def export_from_json(self, json_file: str, sheet_name: str = None) -> bool:
        """
        Export data from JSON file to Google Sheets

        Args:
            json_file: Path to JSON file with scraped data
            sheet_name: Name of the Google Sheet
        """

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return self.export_to_sheets(data, sheet_name)

        except Exception as e:
            logger.error(f"Failed to read JSON file: {str(e)}")
            return False


def export_to_csv(json_file: str, csv_file: str = "results/tennis_clubs.csv"):
    """
    Export JSON data to CSV (alternative to Google Sheets)

    Args:
        json_file: Path to JSON file with scraped data
        csv_file: Path to output CSV file
    """
    import pandas as pd

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False, encoding='utf-8')

        logger.info(f"Successfully exported to CSV: {csv_file}")
        return True

    except Exception as e:
        logger.error(f"Failed to export to CSV: {str(e)}")
        return False


if __name__ == "__main__":
    # Test CSV export
    print("Testing CSV export...")

    # Create dummy data
    test_data = [
        {
            "Club Name": "Test Tennis Club",
            "Location": "Toronto",
            "Email": "test@example.com",
            "Club Type": "Private",
            "Membership Status": "Open",
            "Current Waitlist Length": "N/A",
            "Number of Courts": "6",
            "Court Surface": "Hard Court",
            "Operating Season": "Year-round",
            "Website URL": "http://example.com",
            "Scrape Status": "Success"
        }
    ]

    # Save test data
    with open("results/test_data.json", 'w') as f:
        json.dump(test_data, f)

    # Export to CSV
    export_to_csv("results/test_data.json", "results/test_export.csv")

    print("\nTo enable Google Sheets export:")
    print("1. Create a Google Cloud project")
    print("2. Enable Google Sheets API and Google Drive API")
    print("3. Create a service account and download credentials.json")
    print("4. Place credentials.json in the project root")
    print("5. Update .env with GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json")
