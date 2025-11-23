#!/usr/bin/env python3
"""
GTA Tennis Clubs Web Scraper - Flask Application
Wimbledon Championship Theme
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
from datetime import datetime
from scraper_simple import TennisClubScraper
from email_agent import EmailAgent
import threading

app = Flask(__name__)

# Global variables for tracking scraping progress
scraping_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_club': '',
    'results': [],
    'errors': []
}

def background_scraping_task(max_clubs=None):
    """Background task to run the scraper"""
    global scraping_status

    try:
        # Load Excel file
        excel_file = 'GTA_Tennis_clubs_raw_data .xlsx'
        df = pd.read_excel(excel_file)

        # Limit clubs if specified
        if max_clubs:
            df = df.head(max_clubs)

        scraping_status['total'] = len(df)
        scraping_status['results'] = []
        scraping_status['errors'] = []

        # Initialize scraper
        scraper = TennisClubScraper()

        # Scrape each club
        for idx, row in df.iterrows():
            if not scraping_status['running']:
                break

            club_name = row.get('Club Name', 'Unknown')
            website = row.get('Website', '')

            scraping_status['current_club'] = club_name
            scraping_status['progress'] = idx + 1

            if pd.notna(website) and website.strip():
                try:
                    result = scraper.scrape_club(website, club_name)
                    scraping_status['results'].append(result)
                except Exception as e:
                    error_msg = f"Error scraping {club_name}: {str(e)}"
                    scraping_status['errors'].append(error_msg)
                    print(error_msg)
            else:
                scraping_status['results'].append({
                    'Club Name': club_name,
                    'Website': 'N/A',
                    'Email': 'N/A',
                    'Location': 'N/A',
                    'Club Type': 'N/A',
                    'Membership Status': 'N/A',
                    'Waitlist Length': 'N/A',
                    'Number of Courts': 'N/A',
                    'Court Surface': 'N/A',
                    'Operating Season': 'N/A'
                })

        # Save results
        if scraping_status['results']:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'scraped_data_{timestamp}.json'
            with open(output_file, 'w') as f:
                json.dump(scraping_status['results'], f, indent=2)

            # Also save as CSV
            csv_file = f'scraped_data_{timestamp}.csv'
            results_df = pd.DataFrame(scraping_status['results'])
            results_df.to_csv(csv_file, index=False)

        scraping_status['running'] = False

    except Exception as e:
        scraping_status['errors'].append(f"Fatal error: {str(e)}")
        scraping_status['running'] = False

@app.route('/')
def index():
    """Dashboard page"""
    # Count clubs from Excel
    try:
        df = pd.read_excel('GTA_Tennis_clubs_raw_data .xlsx')
        total_clubs = len(df)
    except:
        total_clubs = 306

    return render_template('index.html', total_clubs=total_clubs)

@app.route('/scraper')
def scraper():
    """Scraper page"""
    return render_template('scraper.html')

@app.route('/results')
def results():
    """Results viewer page"""
    return render_template('results.html')

@app.route('/email')
def email():
    """Email management page"""
    return render_template('email.html')

@app.route('/api/start-scraping', methods=['POST'])
def start_scraping():
    """Start the scraping process"""
    global scraping_status

    if scraping_status['running']:
        return jsonify({'error': 'Scraping already in progress'}), 400

    data = request.get_json() or {}
    max_clubs = data.get('max_clubs')

    # Reset status
    scraping_status = {
        'running': True,
        'progress': 0,
        'total': 0,
        'current_club': '',
        'results': [],
        'errors': []
    }

    # Start background thread
    thread = threading.Thread(target=background_scraping_task, args=(max_clubs,))
    thread.daemon = True
    thread.start()

    return jsonify({'message': 'Scraping started'})

@app.route('/api/scraping-status')
def get_scraping_status():
    """Get current scraping status"""
    return jsonify({
        'running': scraping_status['running'],
        'progress': scraping_status['progress'],
        'total': scraping_status['total'],
        'current_club': scraping_status['current_club'],
        'errors_count': len(scraping_status['errors']),
        'results_count': len(scraping_status['results'])
    })

@app.route('/api/results')
def get_results():
    """Get scraping results"""
    return jsonify({
        'results': scraping_status['results'],
        'errors': scraping_status['errors']
    })

@app.route('/api/email-preview', methods=['POST'])
def preview_emails():
    """Preview emails that would be sent"""
    try:
        data = request.get_json()
        template = data.get('template', '')

        # Get clubs with missing data
        clubs_to_contact = []
        for result in scraping_status['results']:
            if (result.get('Email') != 'N/A' and
                result.get('Email') and
                (result.get('Waitlist Length') == 'N/A' or
                 result.get('Membership Status') == 'N/A')):
                clubs_to_contact.append(result)

        # Generate preview
        email_agent = EmailAgent()
        previews = []

        for club in clubs_to_contact[:5]:  # Preview first 5
            subject, body = email_agent.generate_email(club, template)
            previews.append({
                'club_name': club['Club Name'],
                'email': club['Email'],
                'subject': subject,
                'body': body
            })

        return jsonify({
            'total_emails': len(clubs_to_contact),
            'previews': previews
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-emails', methods=['POST'])
def send_emails():
    """Send emails to clubs"""
    try:
        data = request.get_json()
        template = data.get('template', '')
        dry_run = data.get('dry_run', True)

        # Get clubs with missing data
        clubs_to_contact = []
        for result in scraping_status['results']:
            if (result.get('Email') != 'N/A' and
                result.get('Email') and
                (result.get('Waitlist Length') == 'N/A' or
                 result.get('Membership Status') == 'N/A')):
                clubs_to_contact.append(result)

        if dry_run:
            return jsonify({
                'message': 'Dry run completed',
                'total_emails': len(clubs_to_contact),
                'dry_run': True
            })

        # Actually send emails
        email_agent = EmailAgent()
        sent_count = 0
        failed_count = 0

        for club in clubs_to_contact:
            try:
                subject, body = email_agent.generate_email(club, template)
                email_agent.send_email(club['Email'], subject, body)
                sent_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to {club['Club Name']}: {e}")

        return jsonify({
            'message': 'Emails sent',
            'sent': sent_count,
            'failed': failed_count,
            'total': len(clubs_to_contact)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run on port 5001 to avoid macOS AirPlay conflict
    app.run(debug=True, host='0.0.0.0', port=5001)
