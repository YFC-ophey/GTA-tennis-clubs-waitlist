"""
GTA Tennis Clubs Scraper - Web Application
A user-friendly web interface for scraping tennis clubs and managing email outreach
"""

from flask import Flask, render_template, jsonify, request, send_file, session
from flask_cors import CORS
import json
import os
import threading
from datetime import datetime
from scraper_simple import TennisClubScraper
from email_agent import EmailAgent
from sheets_export import export_to_csv

app = Flask(__name__)
app.secret_key = 'tennis-clubs-scraper-secret-key-2024'
CORS(app)

# Global state
scraping_state = {
    'is_running': False,
    'current_club': 0,
    'total_clubs': 0,
    'current_name': '',
    'successful': 0,
    'failed': 0,
    'progress': 0
}

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

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
    global scraping_state

    if scraping_state['is_running']:
        return jsonify({'error': 'Scraping is already running'}), 400

    data = request.json
    max_clubs = data.get('max_clubs', None)

    # Reset state
    scraping_state = {
        'is_running': True,
        'current_club': 0,
        'total_clubs': max_clubs if max_clubs else 306,
        'current_name': '',
        'successful': 0,
        'failed': 0,
        'progress': 0
    }

    # Start scraping in background thread
    thread = threading.Thread(target=run_scraper, args=(max_clubs,))
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'message': 'Scraping started successfully'})

def run_scraper(max_clubs=None):
    """Run the scraper in background"""
    global scraping_state

    try:
        scraper = TennisClubScraper()
        import pandas as pd

        # Read Excel file
        df = pd.read_excel('GTA Tennis clubs data .xlsx')

        if max_clubs:
            df = df.head(max_clubs)

        scraping_state['total_clubs'] = len(df)
        results = []

        for idx, row in df.iterrows():
            club_name = row['Club Name']
            url = row['Website URL']

            scraping_state['current_club'] = idx + 1
            scraping_state['current_name'] = club_name
            scraping_state['progress'] = int((idx + 1) / len(df) * 100)

            # Scrape the club
            result = scraper.scrape_club(url, club_name)
            results.append(result)

            if result['Scrape Status'] == 'Success':
                scraping_state['successful'] += 1
            else:
                scraping_state['failed'] += 1

            # Save incrementally
            with open('results/scraped_data.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            # Small delay between requests
            import time
            time.sleep(0.5)

        # Export to CSV
        export_to_csv('results/scraped_data.json', 'results/scraped_data.csv')

    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        scraping_state['is_running'] = False

@app.route('/api/scraping-status')
def scraping_status():
    """Get current scraping status"""
    return jsonify(scraping_state)

@app.route('/api/results')
def get_results():
    """Get scraping results"""
    try:
        if os.path.exists('results/scraped_data.json'):
            with open('results/scraped_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Calculate statistics
            total = len(data)
            successful = sum(1 for d in data if d['Scrape Status'] == 'Success')

            # Field completeness
            fields = ['Location', 'Email', 'Club Type', 'Membership Status',
                     'Current Waitlist Length', 'Number of Courts', 'Court Surface', 'Operating Season']

            field_stats = {}
            for field in fields:
                found = sum(1 for d in data if d.get(field) != 'N/A')
                field_stats[field] = {
                    'found': found,
                    'missing': total - found,
                    'percentage': round(found / total * 100, 1) if total > 0 else 0
                }

            return jsonify({
                'data': data,
                'stats': {
                    'total': total,
                    'successful': successful,
                    'failed': total - successful,
                    'field_stats': field_stats
                }
            })
        else:
            return jsonify({'data': [], 'stats': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/email-preview', methods=['POST'])
def email_preview():
    """Preview emails that would be sent"""
    try:
        agent = EmailAgent()
        clubs_needing_outreach = agent.identify_clubs_with_missing_data(
            'results/scraped_data.json',
            threshold=3
        )

        preview_data = []
        for item in clubs_needing_outreach[:10]:  # Limit to first 10 for preview
            club = item['club']
            missing_fields = item['missing_fields']

            email_body = agent.generate_email_template(club['Club Name'], missing_fields)

            preview_data.append({
                'club_name': club['Club Name'],
                'email': club.get('Email', 'N/A'),
                'missing_fields': missing_fields,
                'email_body': email_body
            })

        return jsonify({
            'total_clubs': len(clubs_needing_outreach),
            'with_email': sum(1 for item in clubs_needing_outreach if item['club'].get('Email') != 'N/A'),
            'preview': preview_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-emails', methods=['POST'])
def send_emails():
    """Send outreach emails"""
    try:
        data = request.json
        dry_run = data.get('dry_run', True)

        agent = EmailAgent()
        agent.send_outreach_emails(
            'results/scraped_data.json',
            'results/email_log.json',
            dry_run=dry_run
        )

        # Read the log
        with open('results/email_log.json', 'r', encoding='utf-8') as f:
            log = json.load(f)

        sent = sum(1 for e in log if e['sent'])

        return jsonify({
            'status': 'success',
            'total': len(log),
            'sent': sent,
            'dry_run': dry_run
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a results file"""
    file_path = f'results/{filename}'
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        stats = {
            'total_clubs': 306,
            'scraped': 0,
            'success_rate': 0,
            'emails_found': 0,
            'waitlist_clubs': 0,
            'last_run': None
        }

        if os.path.exists('results/scraped_data.json'):
            with open('results/scraped_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            stats['scraped'] = len(data)
            stats['success_rate'] = round(sum(1 for d in data if d['Scrape Status'] == 'Success') / len(data) * 100, 1) if data else 0
            stats['emails_found'] = sum(1 for d in data if d.get('Email') != 'N/A')
            stats['waitlist_clubs'] = sum(1 for d in data if 'Waitlist' in d.get('Membership Status', ''))

            # Get file modification time
            mtime = os.path.getmtime('results/scraped_data.json')
            stats['last_run'] = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    print("\n" + "="*70)
    print("🎾 GTA Tennis Clubs Scraper - Web Application")
    print("="*70)
    print("\n📱 Open your browser and go to: http://localhost:5000")
    print("\n✨ Features:")
    print("  • Visual scraper with real-time progress")
    print("  • Data viewer with statistics")
    print("  • Email management interface")
    print("  • Easy CSV export\n")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
