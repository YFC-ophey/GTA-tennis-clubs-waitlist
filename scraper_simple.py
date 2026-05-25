#!/usr/bin/env python3
"""
Build-aligned hybrid tennis club scraper.

Pipeline order:
1) preloaded merge
2) structured parser
3) legacy text/table parser
4) grouped-link parser
5) contact subpage parser
6) playwright fallback (optional, last resort)
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import threading
import time
from typing import Dict, Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


SCRAPE_FIELDS = [
    "Email",
    "Location",
    "Club Type",
    "Membership Status",
    "Waitlist Length",
    "Number of Courts",
    "Court Surface",
    "Operating Season",
]

CRITICAL_FIELDS = [
    "Email",
    "Location",
    "Number of Courts",
    "Court Surface",
    "Operating Season",
]

REVIEW_FIELDS = ["Membership Status", "Waitlist Length"]

FIELD_THRESHOLDS = {
    "Email": 0.85,
    "Location": 0.80,
    "Club Type": 0.75,
    "Membership Status": 0.75,
    "Waitlist Length": 0.75,
    "Number of Courts": 0.80,
    "Court Surface": 0.75,
    "Operating Season": 0.75,
}

PLAYWRIGHT_LOCK = threading.Lock()


@dataclass
class ClubRecord:
    club_name: str
    website: str
    values: Dict[str, str] = field(default_factory=lambda: {k: "N/A" for k in SCRAPE_FIELDS})
    confidence_by_field: Dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in SCRAPE_FIELDS})
    field_sources: Dict[str, Dict[str, str | float]] = field(default_factory=dict)
    attempted_urls: list[str] = field(default_factory=list)
    retrieval_history: list[Dict[str, object]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    retrieval_mode: str = "failed"
    status_detail: str = ""
    needs_outreach: bool = False
    site_profile: str = "unknown"

    def set_field(self, key: str, value: str, confidence: float, source: str, stage: str) -> None:
        self.values[key] = value
        self.confidence_by_field[key] = confidence
        self.field_sources[key] = {
            "source": source,
            "stage": stage,
            "confidence": confidence,
        }

    def unresolved(self, fields: Iterable[str]) -> list[str]:
        unresolved = []
        for field in fields:
            value = self.values.get(field, "N/A")
            confidence = self.confidence_by_field.get(field, 0.0)
            threshold = FIELD_THRESHOLDS.get(field, 0.0)
            if value == "N/A" or confidence < threshold:
                unresolved.append(field)
        return unresolved

    def has_usable_data(self) -> bool:
        return any(
            self.values.get(field, "N/A") != "N/A"
            and self.confidence_by_field.get(field, 0.0) >= FIELD_THRESHOLDS.get(field, 0.0)
            for field in SCRAPE_FIELDS
        )

    def status(self) -> str:
        unresolved_critical = self.unresolved(CRITICAL_FIELDS)
        if not unresolved_critical and self.has_usable_data():
            return "Success"
        if self.has_usable_data():
            return "Partial"
        return "Failed"

    def to_result_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "Club Name": self.club_name,
            "Website": self.website,
            "Scrape Status": self.status(),
        }
        payload.update(self.values)
        payload["_meta"] = {
            "retrieval_mode": self.retrieval_mode,
            "field_sources": self.field_sources,
            "attempted_urls": self.attempted_urls,
            "errors": self.errors,
            "site_profile": self.site_profile,
            "needs_outreach": self.needs_outreach,
            "status_detail": self.status_detail,
        }
        return payload


class TennisClubScraper:
    def __init__(self, data_merger=None, debug: bool = True):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        self.timeout = 15
        self.max_retries = 3
        self.retry_backoff_seconds = 1.0
        self.debug = debug
        self.data_merger = data_merger

    def _log(self, message: str) -> None:
        if self.debug:
            print(message)

    def _normalize_url(self, url: str) -> str:
        url = (url or "").strip()
        if not url:
            return ""
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return url

    def _url_candidates(self, url: str) -> list[str]:
        normalized = self._normalize_url(url)
        if not normalized:
            return []

        candidates = [normalized]
        if normalized.startswith("https://"):
            candidates.append("http://" + normalized[len("https://") :])
        elif normalized.startswith("http://"):
            candidates.append("https://" + normalized[len("http://") :])

        expanded: list[str] = []
        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            expanded.append(candidate)
            if "//www." in candidate:
                alt = candidate.replace("//www.", "//", 1)
                if alt not in seen:
                    seen.add(alt)
                    expanded.append(alt)
            else:
                proto, rest = candidate.split("//", 1)
                alt = f"{proto}//www.{rest}"
                if alt not in seen:
                    seen.add(alt)
                    expanded.append(alt)
        return expanded

    def _fetch_html_soup(self, url: str) -> tuple[BeautifulSoup | None, str, int]:
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, verify=False, allow_redirects=True)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = soup.get_text(separator=" ", strip=True)
                return soup, page_text, response.status_code
            except Exception as exc:  # noqa: BLE001
                if attempt < self.max_retries - 1:
                    sleep_s = self.retry_backoff_seconds * (2 ** attempt)
                    self._log(f"[DEBUG] fetch retry {attempt + 1}/{self.max_retries} for {url}: {exc}")
                    time.sleep(sleep_s)
                    continue
                self._log(f"[DEBUG] fetch failed for {url}: {exc}")
        return None, "", 0

    def _profile_site(self, soup: BeautifulSoup, page_text: str) -> str:
        scripts = soup.find_all("script")
        script_text = " ".join((script.get_text() or "") for script in scripts[:10]).lower()
        if len(page_text) < 250:
            return "js_heavy"
        if len(scripts) > 12 and any(framework in script_text for framework in ["react", "vue", "angular", "next"]):
            return "js_heavy"
        has_table = bool(soup.find("table"))
        has_list = bool(soup.find("li"))
        if has_table or has_list:
            return "legacy_html"
        return "structured_html"

    def extract_city_from_address(self, text: str) -> str:
        gta_cities = [
            "Toronto",
            "Mississauga",
            "Brampton",
            "Hamilton",
            "Markham",
            "Vaughan",
            "Richmond Hill",
            "Oakville",
            "Burlington",
            "Oshawa",
            "Pickering",
            "Ajax",
            "Whitby",
            "Newmarket",
            "Aurora",
            "Milton",
            "Caledon",
            "Georgina",
            "Stouffville",
            "King",
            "Etobicoke",
            "Scarborough",
            "North York",
            "East York",
        ]
        text_lower = text.lower()
        for city in gta_cities:
            if city.lower() in text_lower:
                return city

        postal_match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+ON", text)
        if postal_match:
            return postal_match.group(1)

        return "N/A"

    def extract_email(self, soup: BeautifulSoup, page_text: str) -> str:
        mailto_links = soup.find_all("a", href=re.compile(r"^mailto:", re.I))
        for link in mailto_links:
            email = link.get("href", "").replace("mailto:", "").split("?")[0].strip()
            if "@" in email:
                return email

        meta_email = soup.find("meta", attrs={"name": re.compile(r"email", re.I)})
        if meta_email and meta_email.get("content") and "@" in meta_email["content"]:
            return meta_email["content"].strip()

        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, page_text)
        if emails:
            blacklist = ["example", "test", "noreply", "no-reply", "privacy@", "abuse@", "legal@"]
            for email in emails:
                lowered = email.lower()
                if any(token in lowered for token in blacklist):
                    continue
                return email

        obfuscated = re.search(r"(\w+)\s*(?:@|AT|at)\s*(\w+)\s*(?:\.|DOT|dot)\s*(\w+)", page_text, re.I)
        if obfuscated:
            return f"{obfuscated.group(1)}@{obfuscated.group(2)}.{obfuscated.group(3)}"

        contact_links = soup.find_all("a", href=re.compile(r"contact|email", re.I))
        if contact_links:
            return "Contact form available"

        return "N/A"

    def extract_waitlist_length(self, page_text: str) -> str:
        patterns = [
            r"waitlist[:\s]+(\d+)\s*(?:people|members|players)?",
            r"(\d+)\s*(?:people|members|players)?\s+on\s+(?:the\s+)?waitlist",
            r"waiting\s+list[:\s]+(\d+)",
            r"(\d+)\s*year\s+waitlist",
            r"(\d{1,3})\s*(?:\+)?\s*on\s+wait",
        ]
        text_lower = page_text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.I)
            if match:
                return match.group(1)

        if re.search(r"no\s+waitlist|waitlist\s+is\s+closed|not\s+accepting", text_lower, re.I):
            return "0"
        if re.search(r"long\s+waitlist|extensive\s+waitlist|several\s+years?", text_lower, re.I):
            return "Long"

        return "N/A"

    def extract_membership_status(self, page_text: str) -> str:
        text_lower = page_text.lower()
        if re.search(r"(?:accepting|open)\s+(?:new\s+)?(?:members|memberships|applications)", text_lower, re.I):
            return "Open"
        if re.search(r"waitlist|waiting\s+list|join\s+(?:our\s+)?wait", text_lower, re.I):
            return "Waitlist"
        if re.search(r"not\s+accepting|membership\s+(?:is\s+)?closed|full\s+capacity", text_lower, re.I):
            return "Closed"
        return "N/A"

    def extract_courts_count(self, page_text: str) -> str:
        patterns = [
            r"(\d+)\s+(?:tennis\s+)?courts?(?:\s|,|\.|\)|$)",
            r"courts?[:\s]+(\d+)",
            r"total\s+(?:of\s+)?(\d+)\s+courts?",
            r"we\s+have\s+(\d+)\s+courts?",
            r"featuring\s+(\d+)\s+courts?",
            r"(\d+)[-\s]court",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, page_text, re.I):
                count = int(match.group(1))
                if 1 <= count <= 50:
                    return str(count)

        words = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }
        for word, count in words.items():
            if re.search(rf"\b{word}\s+(?:tennis\s+)?courts?", page_text, re.I):
                return str(count)
        return "N/A"

    def extract_court_surface(self, page_text: str) -> str:
        text_lower = page_text.lower()
        surfaces: list[str] = []
        if re.search(r"\bhard\s*courts?|\bhardcourts?|\basphalt|\bconcrete\s*courts?", text_lower):
            surfaces.append("Hard")
        if re.search(r"\bclay\s*courts?|\bred\s*clay|\bhar-tru|\bgreen\s*clay", text_lower):
            surfaces.append("Clay")
        if re.search(r"\bgrass\s*courts?|\blawn\s*courts?", text_lower):
            surfaces.append("Grass")
        if re.search(r"\bindoor\s*courts?|\benclosed|\bbubble|\bdome", text_lower):
            surfaces.append("Indoor")
        if re.search(r"\boutdoor\s*courts?|\bopen-air", text_lower):
            surfaces.append("Outdoor")
        if re.search(r"\bsynthetic|\bartificial\s*grass|\bturf\s*courts?", text_lower):
            surfaces.append("Synthetic")
        if surfaces:
            return ", ".join(sorted(set(surfaces)))
        return "N/A"

    def extract_operating_season(self, page_text: str) -> str:
        text_lower = page_text.lower()
        if "year round" in text_lower or "year-round" in text_lower or "all year" in text_lower:
            return "Year-round"
        if "seasonal" in text_lower and ("april" in text_lower or "may" in text_lower):
            return "Seasonal (Spring-Fall)"
        if "outdoor only" in text_lower:
            return "Seasonal"
        if "indoor" in text_lower and "outdoor" in text_lower:
            return "Year-round"
        return "N/A"

    def extract_club_type(self, page_text: str) -> str:
        text_lower = page_text.lower()
        if re.search(r"private\s+club|members?\s+only|membership\s+required", text_lower, re.I):
            return "Private"
        if re.search(r"public|community|municipal|city\s+of", text_lower, re.I):
            return "Public"
        if re.search(r"commercial", text_lower, re.I):
            return "Commercial"
        return "N/A"

    def _finding(self, value: str, confidence: float, source_url: str) -> tuple[str, float, str] | None:
        value = (value or "").strip()
        if not value or value == "N/A":
            return None
        return value, confidence, source_url

    def _parse_structured(
        self,
        soup: BeautifulSoup,
        page_text: str,
        source_url: str,
    ) -> Dict[str, tuple[str, float, str]]:
        extracted: Dict[str, tuple[str, float, str]] = {}
        candidates = {
            "Email": self._finding(self.extract_email(soup, page_text), 0.90, source_url),
            "Location": self._finding(self.extract_city_from_address(page_text), 0.85, source_url),
            "Club Type": self._finding(self.extract_club_type(page_text), 0.75, source_url),
            "Membership Status": self._finding(self.extract_membership_status(page_text), 0.75, source_url),
            "Waitlist Length": self._finding(self.extract_waitlist_length(page_text), 0.75, source_url),
            "Number of Courts": self._finding(self.extract_courts_count(page_text), 0.85, source_url),
            "Court Surface": self._finding(self.extract_court_surface(page_text), 0.80, source_url),
            "Operating Season": self._finding(self.extract_operating_season(page_text), 0.75, source_url),
        }
        for key, item in candidates.items():
            if item is not None:
                extracted[key] = item
        return extracted

    def _parse_legacy_text_table(
        self,
        soup: BeautifulSoup,
        page_text: str,
        source_url: str,
    ) -> Dict[str, tuple[str, float, str]]:
        extracted = self._parse_structured(soup, page_text, source_url)

        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            key = cells[0].get_text(" ", strip=True).lower()
            value = cells[1].get_text(" ", strip=True)
            if "court" in key:
                finding = self._finding(self.extract_courts_count(value), 0.82, source_url)
                if finding:
                    extracted["Number of Courts"] = finding
            if "surface" in key:
                finding = self._finding(self.extract_court_surface(value), 0.82, source_url)
                if finding:
                    extracted["Court Surface"] = finding
            if "membership" in key:
                finding = self._finding(self.extract_membership_status(value), 0.72, source_url)
                if finding:
                    extracted["Membership Status"] = finding

        for li in soup.find_all("li"):
            text = li.get_text(" ", strip=True)
            if "@" in text:
                email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
                if email_match:
                    extracted["Email"] = (email_match.group(0), 0.80, source_url)

        return extracted

    def _parse_grouped_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, tuple[str, float, str]]:
        links = soup.find_all("a", href=True)
        grouped: Dict[str, int] = {}
        for link in links:
            href = urljoin(base_url, link.get("href", ""))
            if not href.startswith(("http://", "https://")):
                continue
            grouped[href] = grouped.get(href, 0) + 1

        candidates = [href for href, count in grouped.items() if count >= 2][:3]
        combined: Dict[str, tuple[str, float, str]] = {}
        for href in candidates:
            soup_detail, page_text, status = self._fetch_html_soup(href)
            if not soup_detail or status < 200 or status >= 400:
                continue
            details = self._parse_legacy_text_table(soup_detail, page_text, href)
            for key, value in details.items():
                existing = combined.get(key)
                if existing is None or value[1] > existing[1]:
                    combined[key] = value
        return combined

    def _parse_contact_subpages(self, soup: BeautifulSoup, base_url: str) -> Dict[str, tuple[str, float, str]]:
        keywords = ["contact", "about", "membership", "facility", "waitlist"]
        candidates: list[str] = []
        for link in soup.find_all("a", href=True):
            href = urljoin(base_url, link.get("href", ""))
            text = (link.get_text(" ", strip=True) or "").lower()
            if any(keyword in href.lower() or keyword in text for keyword in keywords):
                if href not in candidates:
                    candidates.append(href)
            if len(candidates) >= 4:
                break

        combined: Dict[str, tuple[str, float, str]] = {}
        for href in candidates:
            sub_soup, sub_text, status = self._fetch_html_soup(href)
            if not sub_soup or status < 200 or status >= 400:
                continue
            extracted = self._parse_legacy_text_table(sub_soup, sub_text, href)
            for key, value in extracted.items():
                existing = combined.get(key)
                if existing is None or value[1] > existing[1]:
                    combined[key] = value
        return combined

    def _parse_playwright_fallback(self, url: str, source_url: str) -> Dict[str, tuple[str, float, str]]:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:  # noqa: BLE001
            return {}

        with PLAYWRIGHT_LOCK:
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    html = page.content()
                    browser.close()
            except Exception:  # noqa: BLE001
                return {}

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        extracted = self._parse_legacy_text_table(soup, text, source_url)
        downweighted: Dict[str, tuple[str, float, str]] = {}
        for key, (value, confidence, src) in extracted.items():
            downweighted[key] = (value, min(confidence, 0.70), src)
        return downweighted

    def _apply_extracted_fields(
        self,
        record: ClubRecord,
        extracted: Dict[str, tuple[str, float, str]],
        stage: str,
    ) -> list[str]:
        updated_fields: list[str] = []
        for key, (value, confidence, source_url) in extracted.items():
            current_value = record.values.get(key, "N/A")
            current_confidence = record.confidence_by_field.get(key, 0.0)
            current_source = record.field_sources.get(key, {}).get("source", "")
            threshold = FIELD_THRESHOLDS.get(key, 0.0)

            if current_value != "N/A" and current_confidence >= threshold:
                continue

            should_replace = False
            if current_value == "N/A":
                should_replace = True
            elif confidence > current_confidence:
                if current_source == "preloaded" and confidence <= current_confidence:
                    should_replace = False
                else:
                    should_replace = True

            if should_replace:
                record.set_field(key, value, confidence, source=source_url, stage=stage)
                updated_fields.append(key)

        if updated_fields:
            record.retrieval_history.append({"stage": stage, "updated_fields": updated_fields})
        return updated_fields

    def _populate_preloaded(self, record: ClubRecord, club_name: str, website: str) -> None:
        if not self.data_merger:
            return
        existing_data = self.data_merger.get_existing_data(club_name, website)
        if not existing_data:
            return

        for key in [
            "Email",
            "Location",
            "Club Type",
            "Membership Status",
            "Number of Courts",
            "Court Surface",
            "Operating Season",
        ]:
            value = existing_data.get(key, "N/A")
            if value and value != "N/A":
                record.set_field(key, str(value), confidence=0.93, source="preloaded", stage="preloaded")

        record.retrieval_history.append(
            {
                "stage": "preloaded",
                "updated_fields": [f for f in SCRAPE_FIELDS if record.values.get(f, "N/A") != "N/A"],
                "source": existing_data.get("source", "DB"),
            }
        )

    def _choose_retrieval_mode(self, record: ClubRecord) -> str:
        stage_count: Dict[str, int] = {}
        for details in record.field_sources.values():
            stage = str(details.get("stage", "unknown"))
            stage_count[stage] = stage_count.get(stage, 0) + 1
        if not stage_count:
            return "failed"
        best_stage = sorted(stage_count.items(), key=lambda item: (-item[1], item[0]))[0][0]
        return best_stage

    def scrape_club(self, url: str, club_name: str) -> Dict[str, object]:
        normalized_url = self._normalize_url(url)
        record = ClubRecord(club_name=club_name, website=normalized_url or "N/A")

        self._populate_preloaded(record, club_name, normalized_url)

        soup: BeautifulSoup | None = None
        page_text = ""
        source_url = normalized_url

        for candidate_url in self._url_candidates(normalized_url):
            record.attempted_urls.append(candidate_url)
            candidate_soup, candidate_text, status_code = self._fetch_html_soup(candidate_url)
            if candidate_soup and 200 <= status_code < 400:
                soup = candidate_soup
                page_text = candidate_text
                source_url = candidate_url
                break

        if soup is None:
            record.errors.append("Unable to fetch website via HTTP")
            record.retrieval_mode = self._choose_retrieval_mode(record)
            record.needs_outreach = bool(record.unresolved(REVIEW_FIELDS))
            record.status_detail = "http_fetch_failed"
            return record.to_result_dict()

        record.site_profile = self._profile_site(soup, page_text)

        parsers = [
            ("structured", lambda: self._parse_structured(soup, page_text, source_url)),
            ("legacy_text_table", lambda: self._parse_legacy_text_table(soup, page_text, source_url)),
            ("grouped_link", lambda: self._parse_grouped_links(soup, source_url)),
            ("contact_subpage", lambda: self._parse_contact_subpages(soup, source_url)),
        ]

        for stage_name, parser in parsers:
            extracted = parser()
            self._apply_extracted_fields(record, extracted, stage=stage_name)

        unresolved_after_http = record.unresolved(CRITICAL_FIELDS)
        if unresolved_after_http:
            rendered = self._parse_playwright_fallback(source_url, source_url)
            if rendered:
                self._apply_extracted_fields(record, rendered, stage="playwright")
            else:
                record.errors.append("playwright_fallback_unavailable_or_failed")

        record.retrieval_mode = self._choose_retrieval_mode(record)
        record.needs_outreach = bool(record.unresolved(REVIEW_FIELDS))

        if record.status() == "Success":
            record.status_detail = "critical_fields_resolved"
        elif record.status() == "Partial":
            missing = ",".join(record.unresolved(CRITICAL_FIELDS))
            record.status_detail = f"missing_critical:{missing}"
        else:
            record.status_detail = "no_usable_fields"

        time.sleep(0.3)
        return record.to_result_dict()


if __name__ == "__main__":
    scraper = TennisClubScraper()
    sample = scraper.scrape_club("https://www.example-tennis-club.com", "Test Club")
    print(sample)
