import app as app_module


def test_extract_website_accepts_workbook_column_name():
    row = {'Club Name': 'Club', 'Website URL': 'https://club.example'}

    assert app_module._extract_website(row) == 'https://club.example'


def test_coverage_denominator_accepts_workbook_column_name(monkeypatch):
    import pandas as pd

    class FakeMerger:
        def get_existing_data(self, club_name, website):
            return {'Email': 'known@example.ca'}

    monkeypatch.setattr(app_module, 'global_data_merger', FakeMerger())
    df = pd.DataFrame([{'Club Name': 'Club', 'Website URL': 'https://club.example'}])

    assert app_module._count_eligible_for_coverage(df, ['Number of Courts']) == 1


def test_marker_supports_common_ontario_locations():
    marker = app_module._build_marker({
        'Club Name': 'Aurora Club',
        'Location': 'Aurora',
        'Email': 'N/A',
        'Website': 'https://aurora.example',
        'Membership Status': 'Open',
        'Number of Courts': '4',
    })

    assert marker is not None
    assert marker['lat'] == app_module.CITY_COORDINATES['Aurora'][0]


def test_preloaded_records_preserve_every_workbook_club(tmp_path, monkeypatch):
    workbook = tmp_path / 'GTA_Tennis_clubs_raw_data .xlsx'
    import pandas as pd

    pd.DataFrame(
        [
            {'Club Name': 'Known Club', 'Website URL': 'https://known.example'},
            {'Club Name': 'Missing Source Club', 'Website URL': 'https://missing.example'},
        ]
    ).to_excel(workbook, index=False)

    class FakeMerger:
        def get_existing_data(self, club_name, website):
            if club_name == 'Known Club':
                return {
                    'source': 'Test',
                    'Club Name': 'Known Club',
                    'Website': website,
                    'Email': 'hello@known.example',
                    'Location': 'Toronto',
                    'Club Type': 'Private',
                }
            return None

    monkeypatch.setattr(app_module, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(app_module, 'global_data_merger', FakeMerger())

    records = app_module._build_records_from_preloaded_data()

    assert [row['Club Name'] for row in records] == ['Known Club', 'Missing Source Club']
    assert records[0]['Email'] == 'hello@known.example'
    assert records[1]['Email'] == 'N/A'
    assert records[1]['Website'] == 'https://missing.example'


def test_scraping_status_has_legacy_and_new_keys():
    app_module.scraping_status = {
        'running': False,
        'progress': 12,
        'total': 50,
        'current_club': 'Example Club',
        'results': [],
        'errors': [],
        'mode_counts': {'structured': 10, 'preloaded': 2},
        'changed_since_last_run': True,
        'review_queue_count': 4,
    }

    client = app_module.app.test_client()
    resp = client.get('/api/scraping-status')
    assert resp.status_code == 200
    payload = resp.get_json()

    # Legacy keys
    assert 'running' in payload
    assert 'progress' in payload
    assert 'total' in payload
    assert 'current_club' in payload
    assert 'errors_count' in payload
    assert 'results_count' in payload

    # Additive keys
    assert payload['mode_counts'] == {'structured': 10, 'preloaded': 2}
    assert payload['changed_since_last_run'] is True
    assert payload['review_queue_count'] == 4


def test_results_endpoint_allows_optional_meta_without_breaking_shape():
    app_module.scraping_status = {
        'running': False,
        'progress': 1,
        'total': 1,
        'current_club': 'Club',
        'errors': [],
        'results': [{
            'Club Name': 'Club',
            'Website': 'https://club.example',
            'Email': 'N/A',
            'Location': 'N/A',
            'Club Type': 'N/A',
            'Membership Status': 'N/A',
            'Waitlist Length': 'N/A',
            'Number of Courts': 'N/A',
            'Court Surface': 'N/A',
            'Operating Season': 'N/A',
            'Scrape Status': 'Partial',
            '_meta': {'retrieval_mode': 'structured'}
        }],
        'mode_counts': {},
        'changed_since_last_run': False,
        'review_queue_count': 0,
    }

    client = app_module.app.test_client()
    resp = client.get('/api/results')
    assert resp.status_code == 200
    payload = resp.get_json()

    assert 'results' in payload
    assert 'errors' in payload
    assert payload['results'][0]['Club Name'] == 'Club'
    assert payload['results'][0]['_meta']['retrieval_mode'] == 'structured'


def test_results_endpoint_normalizes_status_for_frontend_compatibility():
    app_module.scraping_status = {
        'running': False,
        'progress': 1,
        'total': 2,
        'current_club': 'Club 2',
        'errors': [],
        'results': [
            {'Club Name': 'Club', 'Website': 'https://club.example', 'Email': 'a@ex.com',
             'Location': 'Toronto', 'Club Type': 'N/A', 'Membership Status': 'N/A',
             'Waitlist Length': 'N/A', 'Number of Courts': 'N/A', 'Court Surface': 'N/A',
             'Operating Season': 'N/A', 'Scrape Status': 'Partial', '_meta': {'retrieval_mode': 'structured'}},
            {'Club Name': 'Club 2', 'Website': 'https://club2.example', 'Email': 'N/A',
             'Location': 'N/A', 'Club Type': 'N/A', 'Membership Status': 'N/A',
             'Waitlist Length': 'N/A', 'Number of Courts': 'N/A', 'Court Surface': 'N/A',
             'Operating Season': 'N/A', 'Scrape Status': 'Success', '_meta': {'retrieval_mode': 'structured'}},
        ],
        'mode_counts': {},
        'changed_since_last_run': False,
        'review_queue_count': 1,
    }

    client = app_module.app.test_client()
    payload = client.get('/api/results').get_json()
    statuses = [row['Scrape Status'] for row in payload['results']]
    assert 'Needs Update' in statuses
    assert 'Success' in statuses
    assert 'Partial' not in statuses


def test_dashboard_data_exposes_known_email_list():
    app_module.scraping_status = {
        'running': False,
        'progress': 1,
        'total': 1,
        'current_club': 'Club',
        'errors': [],
        'results': [],
        'mode_counts': {},
        'changed_since_last_run': False,
        'review_queue_count': 0,
    }
    app_module.scraping_status['results'] = [
        {
            'Club Name': 'Club',
            'Website': 'https://club.example',
            'Email': 'a@ex.com',
            'Location': 'Toronto',
            'Club Type': 'N/A',
            'Membership Status': 'Open',
            'Waitlist Length': 'N/A',
            'Number of Courts': 'N/A',
            'Court Surface': 'Hard',
            'Operating Season': 'Year-round',
            'Scrape Status': 'Success',
            '_meta': {'retrieval_mode': 'structured'},
        },
    ]
    client = app_module.app.test_client()
    payload = client.get('/api/dashboard-data').get_json()
    assert payload['known_emails_count'] == 1
    assert payload['known_emails'] == ['a@ex.com']


def test_build_review_queue_includes_low_confidence_fields():
    row = {
        'Club Name': 'Confidence Club',
        'Website': 'https://confidence.example',
        'Email': 'contact@confidence.example',
        'Location': 'Toronto',
        'Club Type': 'Private',
        'Membership Status': 'Open',
        'Waitlist Length': 'N/A',
        'Number of Courts': '12',
        'Court Surface': 'Hard',
        'Operating Season': 'Year-round',
        'Scrape Status': 'Partial',
        '_meta': {
            'retrieval_mode': 'structured',
            'needs_outreach': True,
            'field_sources': {
                'Email': {'confidence': 0.96},
                'Location': {'confidence': 0.60},
                'Membership Status': {'confidence': 0.20},
                'Number of Courts': {'confidence': 0.55},
                'Court Surface': {'confidence': 0.70},
            },
        },
    }

    queue = app_module._build_review_queue([row])
    assert len(queue) == 1
    entry = queue[0]
    assert 'Low Confidence Fields' in entry
    assert 'Membership Status' in entry['Missing Fields']
    assert 'Location' in entry['Low Confidence Fields']
    assert 'Number of Courts' in entry['Low Confidence Fields']
