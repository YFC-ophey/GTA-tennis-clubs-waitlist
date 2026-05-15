#!/usr/bin/env python3
"""
GTA Tennis Clubs Web Scraper - Flask Application
Wimbledon Championship Theme
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
import re
from datetime import datetime
from scraper_simple import TennisClubScraper
from email_agent import EmailAgent
from data_merger import initialize_data_merger
import threading
import requests
from urllib.parse import urlparse

app = Flask(__name__)
RAW_DATA_FILE = 'GTA_Tennis_clubs_raw_data .xlsx'

RECORD_FIELDS = [
    'Club Name', 'Website', 'Email', 'Location',
    'Club Type', 'Membership Status', 'Waitlist Length',
    'Number of Courts', 'Court Surface', 'Operating Season', 'Scrape Status'
]

# Initialize data merger with CSV data on startup
print("\n" + "="*80)
print("🎾 Initializing Tennis Club Data Portal")
print("="*80)
global_data_merger = initialize_data_merger()
print("✓ Data merger initialized successfully")
print("="*80 + "\n")

# Global variables for tracking scraping progress
scraping_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current_club': '',
    'results': [],
    'errors': []
}


def _normalize_text(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 'N/A'
    if isinstance(value, str):
        value = value.strip()
        return value if value else 'N/A'
    return str(value).strip() if str(value).strip() else 'N/A'


def _safe_get(mapping, keys):
    if not mapping:
        return 'N/A'
    for key in keys:
        if key in mapping:
            value = _normalize_text(mapping.get(key))
            if value != 'N/A':
                return value
    lowered = {str(k).lower(): v for k, v in mapping.items() if k is not None}
    for key in keys:
        value = _normalize_text(lowered.get(str(key).lower()))
        if value != 'N/A':
            return value
    return 'N/A'


def _extract_coordinates(*values):
    patterns = [
        r'[?&]lat=([-+]?\d{1,2}(?:\.\d+)?)[&,]lng=([-+]?\d{1,3}(?:\.\d+)?)',
        r'@(-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)',
        r'lat[=:](-?\d{1,2}\.\d+).*?lng[=:](-?\d{1,3}\.\d+)',
    ]
    for text in values:
        if not text or text == 'N/A':
            continue
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1)), float(match.group(2))
                except ValueError:
                    continue
    return None, None


def _normalize_name(value):
    if global_data_merger:
        try:
            return global_data_merger.normalize_name(_normalize_text(value))
        except Exception:
            pass
    value = _normalize_text(value).lower().replace(' tennis club', '').replace(' tc', '')
    value = re.sub(r'\s+', ' ', value).strip()
    return value


def _normalize_url(value):
    if global_data_merger:
        try:
            return global_data_merger.normalize_url(_normalize_text(value))
        except Exception:
            pass
    text = _normalize_text(value).lower()
    if text in {'n/a', 'na'}:
        return ''
    parsed = urlparse(text)
    netloc = parsed.netloc.lower().replace('www.', '')
    path = parsed.path.rstrip('/')
    return (netloc + path).strip()


def _build_base_records():
    """Build a deterministic, merged club list from source data."""
    records = []
    seen_names = set()

    try:
        df = pd.read_excel(RAW_DATA_FILE)
    except Exception:
        return records

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        club_name = _normalize_text(row_dict.get('Club Name'))
        if club_name == 'N/A':
            continue

        name_key = _normalize_name(club_name)
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        website = _safe_get(row_dict, ['Website', 'website', 'website_url', 'Website URL'])
        existing_data = global_data_merger.get_existing_data(club_name, website) if global_data_merger else None

        row_email = _safe_get(row_dict, ['Email', 'email'])
        row_location = _safe_get(row_dict, ['Location', 'location'])
        row_club_type = _safe_get(row_dict, ['Club Type', 'Type', 'club_type', 'type'])
        row_membership = _safe_get(row_dict, ['Membership Status', 'membership'])
        row_waitlist = _safe_get(row_dict, ['Waitlist Length', 'waitlist', 'Waitlist'])
        row_courts = _safe_get(row_dict, ['Number of Courts', 'courts'])
        row_surface = _safe_get(row_dict, ['Court Surface', 'Surface', 'surface'])
        row_season = _safe_get(row_dict, ['Operating Season', 'Season', 'operating season'])
        existing_email = _safe_get(existing_data or {}, ['Email', 'email'])
        existing_location = _safe_get(existing_data or {}, ['Location', 'location'])
        existing_club_type = _safe_get(existing_data or {}, ['Club Type', 'club_type', 'Type', 'type'])
        existing_membership = _safe_get(existing_data or {}, ['Membership Status', 'membership_status', 'Membership', 'membership'])
        existing_waitlist = _safe_get(existing_data or {}, ['Waitlist Length', 'Waitlist', 'waitlist'])
        existing_courts = _safe_get(existing_data or {}, ['Number of Courts', 'courts'])
        existing_surface = _safe_get(existing_data or {}, ['Court Surface', 'Surface', 'surface'])
        existing_season = _safe_get(existing_data or {}, ['Operating Season', 'Season', 'operating season'])

        record = {
            'Club Name': club_name,
            'Website': website,
            'Email': row_email if row_email != 'N/A' else existing_email,
            'Location': row_location if row_location != 'N/A' else existing_location,
            'Club Type': row_club_type if row_club_type != 'N/A' else existing_club_type,
            'Membership Status': row_membership if row_membership != 'N/A' else existing_membership,
            'Waitlist Length': row_waitlist if row_waitlist != 'N/A' else existing_waitlist,
            'Number of Courts': row_courts if row_courts != 'N/A' else existing_courts,
            'Court Surface': row_surface if row_surface != 'N/A' else existing_surface,
            'Operating Season': row_season if row_season != 'N/A' else existing_season,
            'Scrape Status': f"Pre-loaded ({existing_data.get('source', 'DB')})" if existing_data else 'No website'
        }

        # Copy known coordinates from merged sources
        source_location = _safe_get(existing_data or {}, ['Location', 'location', 'google map', 'map', 'google_map', 'google map_url', 'google map url'])
        latitude, longitude = _extract_coordinates(
            _safe_get(row_dict, ['Location', 'location']),
            source_location,
            _safe_get(existing_data or {}, ['Website', 'website', 'Website URL']),
            _safe_get(existing_data or {}, ['google map', 'google map url', 'google_map', 'map', 'Location']),
        )
        if latitude is not None and longitude is not None:
            record['lat'] = latitude
            record['lng'] = longitude

        # Fallback status if key fields are present from sources
        if record['Scrape Status'].startswith('Pre-loaded'):
            if (record['Email'] != 'N/A' and record['Membership Status'] != 'N/A' and record['Number of Courts'] != 'N/A'):
                record['Scrape Status'] = 'Success'
            elif record['Email'] != 'N/A':
                record['Scrape Status'] = 'Partial'
            else:
                record['Scrape Status'] = 'No website'

        records.append(record)

    records.sort(key=lambda row: row['Club Name'].lower())
    return records


def _merge_scraped_records(base_records, scraped_results):
    """Overlay the latest scrape results onto base source records."""
    if not base_records:
        return [dict(result) for result in (scraped_results or [])]

    merged = []
    result_index_name = {}
    result_index_website = {}

    for result in scraped_results or []:
        key_name = _normalize_name(result.get('Club Name'))
        key_website = _normalize_url(result.get('Website'))
        if key_name:
            result_index_name[key_name] = result
        if key_website:
            result_index_website[key_website] = result

    used = set()

    for base in base_records:
        normalized_name = _normalize_name(base.get('Club Name'))
        normalized_web = _normalize_url(base.get('Website'))

        candidate = result_index_name.pop(normalized_name, None)
        if candidate is None and normalized_web:
            candidate = result_index_website.pop(normalized_web, None)

        if candidate:
            used.add(id(candidate))
            merged_record = dict(base)
            for field in RECORD_FIELDS:
                candidate_value = _normalize_text(candidate.get(field))
                if candidate_value != 'N/A':
                    merged_record[field] = candidate_value
            if _normalize_text(candidate.get('lat')) != 'N/A' and _normalize_text(candidate.get('lng')) != 'N/A':
                merged_record['lat'] = _normalize_text(candidate.get('lat'))
                merged_record['lng'] = _normalize_text(candidate.get('lng'))
            merged.append(merged_record)
        else:
            merged.append(base)

    # Add truly new scraped entries not in base sources
    for result in scraped_results or []:
        if id(result) in used:
            continue
        name = _normalize_text(result.get('Club Name'))
        if name == 'N/A':
            continue
        merged.append({field: _normalize_text(result.get(field)) for field in RECORD_FIELDS})

    return merged


def _normalize_scrape_status(status_value):
    """Map legacy scrape statuses to compatible status classes."""
    if not status_value or status_value == 'N/A':
        return 'Failed'

    status = _normalize_text(status_value)
    if status == 'N/A':
        return 'Failed'
    if status == 'Success' or status.startswith('Success ('):
        return 'Success'
    if status.startswith('Pre-loaded'):
        return 'Success'
    if status in {'Failed', 'No website'}:
        return 'Failed'
    if status.startswith('JS-heavy'):
        return 'Partial'
    if status.startswith('Error:') or status.startswith('Error'):
        return 'Failed'
    return 'Needs Update'


def _record_needs_update(record):
    return _normalize_scrape_status(record.get('Scrape Status', 'Failed')) != 'Success'


def _known_emails(records):
    emails = []
    for record in records:
        email = _normalize_text(record.get('Email'))
        if email != 'N/A' and '@' in email and not email.lower().startswith('mailto:'):
            emails.append(email)
    unique = sorted(set(emails))
    return unique


def _is_valid_field(value):
    return _normalize_text(value) not in {'N/A', ''}


def _build_payload_records(records):
    payload = []
    for record in records:
        normalized = dict(record)
        if _normalize_scrape_status(normalized.get('Scrape Status')) == 'Needs Update':
            if _is_valid_field(normalized.get('Email')) or _is_valid_field(normalized.get('Membership Status')) or _is_valid_field(normalized.get('Number of Courts')):
                normalized['Scrape Status'] = 'Partial'
            else:
                normalized['Scrape Status'] = 'Failed'
        elif _normalize_scrape_status(normalized.get('Scrape Status')) == 'Success':
            normalized['Scrape Status'] = 'Success'
        payload.append(normalized)
    return payload


def _get_current_records():
    base_records = _build_base_records()
    if scraping_status['running']:
        merged = _merge_scraped_records(base_records, scraping_status['results'])
    else:
        # After a scrape completes, keep latest results visible over source list.
        merged = _merge_scraped_records(base_records, scraping_status['results'])
    return _build_payload_records(merged)


def _get_coverage_stats(records):
    total = len(records)
    success = sum(1 for row in records if _normalize_scrape_status(row.get('Scrape Status')) == 'Success')
    partial_or_failed = total - success
    needs_update = sum(1 for row in records if _record_needs_update(row))
    known_emails = len(_known_emails(records))
    return {
        'total_clubs': total,
        'success_count': success,
        'needs_update_count': needs_update,
        'partial_or_failed_count': partial_or_failed,
        'known_emails_count': known_emails,
        'email_coverage': round((known_emails / total * 100), 2) if total else 0,
    }


def _normalize_club_name_for_output(value):
    return re.sub(r'\s+', ' ', _normalize_text(value)).strip()


def _estimate_court_count_from_query(query, *, source):
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; tennis-club-dashboard/1.0)'
    }
    url = 'https://duckduckgo.com/html/'
    response = requests.get(url, params={'q': query}, headers=headers, timeout=15)
    if response.status_code != 200:
        return None

    snippets = []
    for raw in re.findall(r'(?s)<a rel="nofollow" class="result__snippet".*?>(.*?)</a>', response.text):
        snippets.append(re.sub(r'<[^>]+>', ' ', raw))

    for snippet in snippets:
        match = re.search(r'(\d{1,2})\s+(?:outdoor|indoor)?\s*courts?', snippet, re.I)
        if match:
            count = int(match.group(1))
            if 1 <= count <= 60:
                return {
                    'estimated_courts': str(count),
                    'confidence': 0.43,
                    'evidence': snippet.strip()[:240],
                    'source': source,
                }
    return None


def _estimate_with_firecrawl(query):
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key:
        return None

    try:
        response = requests.post(
            'https://api.firecrawl.dev/v1/search',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={'query': query, 'limit': 5},
            timeout=15
        )
    except Exception:
        return None

    if response.status_code != 200:
        return None

    try:
        payload = response.json()
    except Exception:
        return None

    results = payload.get('data') or payload.get('results') or []
    for result in results[:5]:
        snippet = _normalize_text(result.get('snippet', ''))
        match = re.search(r'(\d{1,2})\s+(?:outdoor|indoor)?\s*courts?', snippet, re.I)
        if match:
            count = int(match.group(1))
            if 1 <= count <= 60:
                return {
                    'estimated_courts': str(count),
                    'confidence': 0.7,
                    'evidence': snippet[:240],
                    'source': result.get('url') or result.get('title', 'Firecrawl'),
                }
    return None

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

        # Initialize scraper with data merger for pre-loaded data
        scraper = TennisClubScraper(data_merger=global_data_merger)

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
                # No website, but check if we have data in our database
                existing_data = global_data_merger.get_existing_data(club_name, '') if global_data_merger else None
                if existing_data:
                    result = {
                        'Club Name': club_name,
                        'Website': 'N/A',
                        'Email': existing_data.get('Email', 'N/A'),
                        'Location': existing_data.get('Location', 'N/A'),
                        'Club Type': existing_data.get('Club Type', 'N/A'),
                        'Membership Status': existing_data.get('Membership Status', 'N/A'),
                        'Waitlist Length': 'N/A',
                        'Number of Courts': existing_data.get('Number of Courts', 'N/A'),
                        'Court Surface': 'N/A',
                        'Operating Season': 'N/A',
                        'Scrape Status': f"Pre-loaded ({existing_data.get('source', 'DB')})"
                    }
                else:
                    result = {
                        'Club Name': club_name,
                        'Website': 'N/A',
                        'Email': 'N/A',
                        'Location': 'N/A',
                        'Club Type': 'N/A',
                        'Membership Status': 'N/A',
                        'Waitlist Length': 'N/A',
                        'Number of Courts': 'N/A',
                        'Court Surface': 'N/A',
                        'Operating Season': 'N/A',
                        'Scrape Status': 'No website'
                    }
                scraping_status['results'].append(result)

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
    dashboard_records = _get_current_records()
    total_clubs = len(dashboard_records)
    return render_template('index.html', total_clubs=total_clubs or 0)

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
    records = _get_current_records()
    return jsonify({
        'results': records,
        'errors': scraping_status['errors'],
        'known_emails': _known_emails(records),
        'result_count': len(records),
        '_meta': _get_coverage_stats(records),
    })


@app.route('/api/dashboard-data')
def get_dashboard_data():
    """Get data consumed by the interactive dashboard."""
    records = _get_current_records()
    coverage = _get_coverage_stats(records)
    return jsonify({
        'records': records,
        'total_clubs': coverage['total_clubs'],
        'known_emails': _known_emails(records),
        'stats': coverage,
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    })


@app.route('/api/court-count-research', methods=['POST'])
def court_count_research():
    """Suggest court counts for unresolved clubs using web snippets."""
    try:
        data = request.get_json() or {}
        clubs = data.get('clubs', [])
        max_records = int(data.get('max_records', 12))
    except Exception:
        return jsonify({'error': 'Invalid request body'}), 400

    if not isinstance(clubs, list):
        return jsonify({'error': 'Expected clubs list'}), 400

    suggestions = []
    for club in clubs[:max_records]:
        club_name = _normalize_club_name_for_output(club.get('Club Name') or club.get('club_name'))
        if not club_name or club_name == 'N/A':
            continue

        location = _normalize_club_name_for_output(club.get('Location', ''))
        query = f"{club_name} {location} tennis courts"

        # Prefer firecrawl when available
        suggestion = _estimate_with_firecrawl(query)
        if not suggestion:
            suggestion = _estimate_court_count_from_query(query, source='duckduckgo')

        if suggestion is None:
            suggestions.append({
                'club_name': club_name,
                'location': location or 'N/A',
                'estimated_courts': 'N/A',
                'confidence': 0.0,
                'evidence': 'No web snippet match yet. Configure FIRECRAWL_API_KEY for improved lookup.',
            })
            continue

        suggestions.append({
            'club_name': club_name,
            'location': location or 'N/A',
            'estimated_courts': suggestion['estimated_courts'],
            'confidence': suggestion['confidence'],
            'evidence': suggestion['evidence'],
        })

    return jsonify({'results': suggestions, 'count': len(suggestions)})

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
