#!/usr/bin/env python3
"""
GTA Tennis Clubs Data Scraper - Main Orchestrator
Coordinates scraping, email outreach, and data export
"""

import argparse
import json
import logging
import sys
from scraper import TennisClubScraper
from email_agent import EmailAgent
from sheets_export import GoogleSheetsExporter, export_to_csv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def scrape_clubs(excel_file: str, output_json: str, max_clubs: int = None):
    """Step 1: Scrape tennis club websites"""
    logger.info("Starting web scraping...")

    scraper = TennisClubScraper()
    results = scraper.scrape_clubs_from_excel(
        excel_file=excel_file,
        output_json=output_json,
        max_clubs=max_clubs
    )

    # Print summary
    successful = sum(1 for r in results if r['Scrape Status'] == 'Success')
    print(f"\n{'='*60}")
    print(f"Scraping Summary")
    print(f"{'='*60}")
    print(f"Total clubs processed: {len(results)}")
    print(f"Successfully scraped: {successful}")
    print(f"Failed: {len(results) - successful}")
    print(f"Results saved to: {output_json}")
    print(f"{'='*60}\n")

    return results


def send_emails(scraped_data_file: str, email_log_file: str, dry_run: bool = True):
    """Step 2: Send outreach emails to clubs with missing data"""
    logger.info("Starting email outreach...")

    agent = EmailAgent()
    agent.send_outreach_emails(
        scraped_data_file=scraped_data_file,
        output_log=email_log_file,
        dry_run=dry_run
    )


def export_data(json_file: str, format: str = 'csv', sheet_name: str = None):
    """Step 3: Export data to Google Sheets or CSV"""
    logger.info(f"Exporting data to {format.upper()}...")

    if format.lower() == 'csv':
        csv_file = json_file.replace('.json', '.csv')
        export_to_csv(json_file, csv_file)
        print(f"\nData exported to: {csv_file}")
        print("You can import this CSV file into Google Sheets manually.\n")

    elif format.lower() == 'sheets':
        exporter = GoogleSheetsExporter()
        success = exporter.export_from_json(json_file, sheet_name)

        if success:
            print(f"\nData successfully exported to Google Sheets!")
        else:
            print(f"\nFailed to export to Google Sheets. Falling back to CSV...")
            export_data(json_file, format='csv')

    else:
        logger.error(f"Unknown export format: {format}")


def analyze_data(json_file: str):
    """Analyze scraped data and provide statistics"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = len(data)
    successful = sum(1 for d in data if d['Scrape Status'] == 'Success')

    # Count N/A values per field
    fields = ['Location', 'Email', 'Club Type', 'Membership Status',
              'Current Waitlist Length', 'Number of Courts', 'Court Surface', 'Operating Season']

    field_stats = {}
    for field in fields:
        na_count = sum(1 for d in data if d.get(field) == 'N/A')
        field_stats[field] = {
            'found': total - na_count,
            'missing': na_count,
            'percentage': round((total - na_count) / total * 100, 1) if total > 0 else 0
        }

    print(f"\n{'='*70}")
    print(f"Data Analysis Report")
    print(f"{'='*70}")
    print(f"Total clubs: {total}")
    print(f"Successfully scraped: {successful} ({round(successful/total*100, 1)}%)")
    print(f"\nData Completeness:")
    print(f"{'-'*70}")
    print(f"{'Field':<30} {'Found':<10} {'Missing':<10} {'Coverage':<10}")
    print(f"{'-'*70}")

    for field, stats in field_stats.items():
        print(f"{field:<30} {stats['found']:<10} {stats['missing']:<10} {stats['percentage']}%")

    print(f"{'='*70}\n")

    # Clubs with waitlists
    waitlist_clubs = [d for d in data if 'Waitlist' in d.get('Membership Status', '')]
    if waitlist_clubs:
        print(f"\nClubs with Waitlists ({len(waitlist_clubs)}):")
        for club in waitlist_clubs[:10]:  # Show first 10
            print(f"  - {club['Club Name']}: {club.get('Current Waitlist Length', 'N/A')}")
        if len(waitlist_clubs) > 10:
            print(f"  ... and {len(waitlist_clubs) - 10} more")


def main():
    parser = argparse.ArgumentParser(
        description='GTA Tennis Clubs Data Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape first 10 clubs (testing)
  python main.py --scrape --max-clubs 10

  # Scrape all clubs
  python main.py --scrape

  # Analyze scraped data
  python main.py --analyze

  # Send email outreach (dry run)
  python main.py --email --dry-run

  # Send actual emails
  python main.py --email

  # Export to CSV
  python main.py --export csv

  # Export to Google Sheets
  python main.py --export sheets

  # Full pipeline (scrape + analyze + export to CSV)
  python main.py --scrape --analyze --export csv
        """
    )

    # Action arguments
    parser.add_argument('--scrape', action='store_true',
                       help='Scrape tennis club websites')
    parser.add_argument('--email', action='store_true',
                       help='Send outreach emails to clubs with missing data')
    parser.add_argument('--export', type=str, choices=['csv', 'sheets'],
                       help='Export data to CSV or Google Sheets')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze scraped data and show statistics')

    # Configuration arguments
    parser.add_argument('--input', type=str, default='GTA Tennis clubs data .xlsx',
                       help='Input Excel file (default: GTA Tennis clubs data .xlsx)')
    parser.add_argument('--output', type=str, default='results/scraped_data.json',
                       help='Output JSON file (default: results/scraped_data.json)')
    parser.add_argument('--max-clubs', type=int,
                       help='Maximum number of clubs to scrape (for testing)')
    parser.add_argument('--dry-run', action='store_true',
                       help='For email: generate emails without sending')
    parser.add_argument('--sheet-name', type=str,
                       help='Google Sheets name (default: from .env or "GTA Tennis Clubs Data")')

    args = parser.parse_args()

    # If no action specified, show help
    if not any([args.scrape, args.email, args.export, args.analyze]):
        parser.print_help()
        sys.exit(0)

    # Execute actions in order
    if args.scrape:
        scrape_clubs(args.input, args.output, args.max_clubs)

    if args.analyze:
        analyze_data(args.output)

    if args.email:
        email_log = args.output.replace('.json', '_email_log.json')
        send_emails(args.output, email_log, args.dry_run)

    if args.export:
        export_data(args.output, args.export, args.sheet_name)

    print("\n✓ All tasks completed successfully!\n")


if __name__ == "__main__":
    main()
