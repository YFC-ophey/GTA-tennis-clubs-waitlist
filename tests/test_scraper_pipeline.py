import unittest
from bs4 import BeautifulSoup

from unittest.mock import MagicMock

from scraper_simple import CRITICAL_FIELDS, TennisClubScraper, ClubRecord
from data_merger import DataMerger


class TestScraperParserFamilies(unittest.TestCase):
    def setUp(self):
        self.scraper = TennisClubScraper(data_merger=None, debug=False)

    def test_structured_parser_extracts_fields(self):
        html = """
        <html><body>
          <section class='contact'>
            <a href='mailto:info@exampletennis.ca'>Email</a>
          </section>
          <div class='facilities'>Our club has 12 courts with hard courts available.</div>
          <p>We are accepting new memberships and operate year-round.</p>
          <p>Located in Toronto, ON.</p>
        </body></html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text(' ', strip=True)
        extracted = self.scraper._parse_structured(
            soup=soup,
            page_text=page_text,
            source_url='https://exampletennis.ca',
        )

        self.assertEqual(extracted['Email'][0], 'info@exampletennis.ca')
        self.assertEqual(extracted['Location'][0], 'Toronto')
        self.assertEqual(extracted['Number of Courts'][0], '12')
        self.assertEqual(extracted['Membership Status'][0], 'Open')

    def test_legacy_parser_extracts_table_and_text(self):
        html = """
        <html><body>
          <table>
            <tr><th>Facilities</th><td>8 tennis courts</td></tr>
            <tr><th>Surface</th><td>Clay courts</td></tr>
          </table>
          <ul>
            <li>Contact: admin@legacyclub.ca</li>
            <li>Membership: waitlist</li>
          </ul>
          <p>Address: 123 Main St, Mississauga, ON</p>
        </body></html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text(' ', strip=True)
        extracted = self.scraper._parse_legacy_text_table(
            soup=soup,
            page_text=page_text,
            source_url='https://legacyclub.ca',
        )

        self.assertEqual(extracted['Email'][0], 'admin@legacyclub.ca')
        self.assertEqual(extracted['Number of Courts'][0], '8')
        self.assertIn('Clay', extracted['Court Surface'][0])
        self.assertEqual(extracted['Membership Status'][0], 'Waitlist')

    def test_grouped_link_parser_fetches_repeated_hrefs(self):
        base_html = """
        <html><body>
          <a href='/club-info'>Club Info</a>
          <a href='/club-info'>Read More</a>
          <a href='/club-info'>Facilities</a>
        </body></html>
        """
        detail_html = """
        <html><body><p>Club has 6 courts and hard courts.</p></body></html>
        """

        def fake_fetch(url):
            if url.endswith('/club-info'):
                return BeautifulSoup(detail_html, 'html.parser'), detail_html, 200
            return BeautifulSoup(base_html, 'html.parser'), base_html, 200

        self.scraper._fetch_html_soup = fake_fetch
        soup = BeautifulSoup(base_html, 'html.parser')
        extracted = self.scraper._parse_grouped_links(
            soup=soup,
            base_url='https://club.example',
        )
        self.assertEqual(extracted['Number of Courts'][0], '6')

    def test_contact_subpage_parser_fetches_contact_page(self):
        base_html = """
        <html><body>
          <a href='/contact'>Contact</a>
        </body></html>
        """
        contact_html = """
        <html><body>
          <p>Email: contact@subpageclub.ca</p>
          <p>Season: year-round</p>
          <p>Courts: 9</p>
        </body></html>
        """

        def fake_fetch(url):
            if url.endswith('/contact'):
                soup = BeautifulSoup(contact_html, 'html.parser')
                return soup, soup.get_text(' ', strip=True), 200
            soup = BeautifulSoup(base_html, 'html.parser')
            return soup, soup.get_text(' ', strip=True), 200

        self.scraper._fetch_html_soup = fake_fetch
        soup = BeautifulSoup(base_html, 'html.parser')
        extracted = self.scraper._parse_contact_subpages(
            soup=soup,
            base_url='https://subpageclub.ca',
        )

        self.assertEqual(extracted['Email'][0], 'contact@subpageclub.ca')
        self.assertEqual(extracted['Operating Season'][0], 'Year-round')


class TestMergePolicy(unittest.TestCase):
    def setUp(self):
        self.scraper = TennisClubScraper(data_merger=None, debug=False)

    def test_preloaded_non_na_not_overwritten_by_lower_confidence(self):
        record = ClubRecord(club_name='Test Club', website='https://test.ca')
        record.set_field('Email', 'trusted@club.ca', confidence=0.95, source='preloaded', stage='preloaded')

        self.scraper._apply_extracted_fields(
            record,
            {'Email': ('guess@club.ca', 0.60, 'https://test.ca')},
            stage='structured',
        )

        self.assertEqual(record.values['Email'], 'trusted@club.ca')
        self.assertEqual(record.confidence_by_field['Email'], 0.95)

    def test_threshold_prevents_overwrite_after_confidence(self):
        record = ClubRecord(club_name='Test Club', website='https://test.ca')
        record.set_field('Number of Courts', '10', confidence=0.82, source='structured', stage='structured')

        self.scraper._apply_extracted_fields(
            record,
            {'Number of Courts': ('20', 0.95, 'https://test.ca')},
            stage='legacy_text_table',
        )

        self.assertEqual(record.values['Number of Courts'], '10')
        self.assertEqual(record.confidence_by_field['Number of Courts'], 0.82)

    def test_low_confidence_counts_as_unresolved(self):
        record = ClubRecord(club_name='Test Club', website='https://test.ca')
        record.set_field('Number of Courts', '10', confidence=0.60, source='structured', stage='structured')

        self.assertIn('Number of Courts', record.unresolved(CRITICAL_FIELDS))


class TestDataMergerBackfill(unittest.TestCase):
    def test_run_sheet_enriches_missing_fields_without_overwriting_ota(self):
        import pandas as pd

        merger = DataMerger()
        merger.ota_data = pd.DataFrame(
            [
                {
                    'name': 'Example Tennis Club',
                    'email': 'info@example.ca',
                    'website_url': 'https://example.ca',
                    'type': 'Private',
                    'location': 'Toronto',
                }
            ]
        )
        merger.toronto_data = pd.DataFrame()
        merger.excel_run_data = pd.DataFrame(
            [
                {
                    'Club Name': 'Example Tennis Club',
                    'Website URL': 'https://example.ca',
                    'Location': 'Home About Programs Contact A very noisy scraped menu',
                    'Email': 'scraped@example.ca',
                    'Club Type': 'Community Club',
                    'Membership Status': 'Open',
                    'Court Surface': 'Hard Court',
                    'Operating Season': 'Summer',
                }
            ]
        )

        merger.build_lookup_dict()

        data = merger.get_existing_data('Example Tennis Club', 'https://example.ca')
        self.assertEqual(data['Email'], 'info@example.ca')
        self.assertEqual(data['Location'], 'Toronto')
        self.assertEqual(data['Club Type'], 'Private')
        self.assertEqual(data['Membership Status'], 'Open')
        self.assertEqual(data['Court Surface'], 'Hard Court')
        self.assertEqual(data['Operating Season'], 'Summer')


class TestPlaywrightFallbackOrder(unittest.TestCase):
    def setUp(self):
        self.scraper = TennisClubScraper(data_merger=None, debug=False)

    def _html_with_scripts(self) -> str:
        scripts = "".join("<script>console.log('x')</script>" for _ in range(13))
        return f"<html><body>{scripts}</body></html>"

    def test_playwright_called_only_after_http_unresolved_critical_fields(self):
        def fake_fetch(url):
            soup = BeautifulSoup(self._html_with_scripts(), "html.parser")
            return soup, soup.get_text(" ", strip=True), 200

        self.scraper._fetch_html_soup = fake_fetch
        self.scraper._parse_structured = MagicMock(return_value={})
        self.scraper._parse_legacy_text_table = MagicMock(return_value={})
        self.scraper._parse_grouped_links = MagicMock(return_value={})
        self.scraper._parse_contact_subpages = MagicMock(return_value={})
        self.scraper._parse_playwright_fallback = MagicMock(return_value={})

        self.scraper.scrape_club("https://playwright-check.example", "Playwright Test")

        self.assertGreater(self.scraper._parse_structured.call_count, 0)
        self.assertEqual(self.scraper._parse_playwright_fallback.call_count, 1)

    def test_no_playwright_when_critical_fields_resolved(self):
        def fake_fetch(url):
            html = "<html><body><p>Open to new members with 12 courts. Location: Toronto, ON. Year-round operations.</p></body></html>"
            soup = BeautifulSoup(html, "html.parser")
            return soup, soup.get_text(" ", strip=True), 200

        self.scraper._fetch_html_soup = fake_fetch

        def parse_structured(*_args, **_kwargs):
            return {
                "Email": ("membership@playwright-check.example", 0.95, "https://playwright-check.example"),
                "Number of Courts": ("12", 0.85, "https://playwright-check.example"),
                "Location": ("Toronto", 0.85, "https://playwright-check.example"),
                "Court Surface": ("Hard", 0.75, "https://playwright-check.example"),
                "Operating Season": ("Year-round", 0.75, "https://playwright-check.example"),
            }

        self.scraper._parse_structured = MagicMock(side_effect=parse_structured)
        self.scraper._parse_legacy_text_table = MagicMock(return_value={})
        self.scraper._parse_grouped_links = MagicMock(return_value={})
        self.scraper._parse_contact_subpages = MagicMock(return_value={})
        self.scraper._parse_playwright_fallback = MagicMock(return_value={})

        self.scraper.scrape_club("https://playwright-check.example", "Playwright Test")

        self.assertEqual(self.scraper._parse_playwright_fallback.call_count, 0)


if __name__ == '__main__':
    unittest.main()
