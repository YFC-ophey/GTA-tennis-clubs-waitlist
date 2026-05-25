#!/usr/bin/env python3
"""
GTA Tennis Clubs Web Scraper - Flask Application
Wimbledon Championship Theme
"""

from __future__ import annotations

from collections import Counter
import csv
import os
from datetime import datetime
import json
from pathlib import Path
import re
import threading
from typing import Iterable

from flask import Flask, jsonify, render_template, request
import requests
import pandas as pd
from bs4 import BeautifulSoup

from data_merger import initialize_data_merger
from email_agent import EmailAgent
from scraper_simple import CRITICAL_FIELDS, FIELD_THRESHOLDS, REVIEW_FIELDS, TennisClubScraper

try:
    from scraper_hybrid import HybridScraper, PLAYWRIGHT_AVAILABLE
except ImportError:
    HybridScraper = None
    PLAYWRIGHT_AVAILABLE = False


BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "data" / "current_club_state.json"
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "").strip()
REQUEST_TIMEOUT = 12

CITY_COORDINATES = {
    "Toronto": (43.653225, -79.383186),
    "Mississauga": (43.5890, -79.6441),
    "Brampton": (43.7315, -79.7624),
    "Markham": (43.8561, -79.3370),
    "Vaughan": (43.8361, -79.5085),
    "Richmond Hill": (43.8828, -79.4403),
    "Oakville": (43.4675, -79.6877),
    "Burlington": (43.3255, -79.7990),
    "Oshawa": (43.8971, -78.8658),
    "Pickering": (43.8508, -79.0870),
    "Ajax": (43.8508, -79.0204),
    "Whitby": (43.8971, -78.9428),
    "Milton": (43.5168, -79.8827),
    "Hamilton": (43.2557, -79.8711),
    "Scarborough": (43.7731, -79.2578),
    "Etobicoke": (43.6542, -79.5659),
    "North York": (43.7542, -79.4207),
    "East York": (43.6997, -79.3324),
    "Aurora": (44.0065, -79.4504),
    "Newmarket": (44.0592, -79.4613),
    "Thornhill": (43.8157, -79.4234),
    "Woodbridge": (43.7762, -79.6093),
    "Caledon": (43.8754, -79.8590),
    "Stouffville": (43.9706, -79.2443),
    "Barrie": (44.3894, -79.6903),
    "Ottawa": (45.4215, -75.6972),
    "Nepean": (45.3349, -75.7241),
    "Gloucester": (45.4501, -75.5891),
    "Guelph": (43.5448, -80.2482),
    "Cambridge": (43.3616, -80.3144),
    "Kingston": (44.2312, -76.4860),
    "London": (42.9849, -81.2453),
    "Niagara-on-the-Lake": (43.2550, -79.0710),
    "Welland": (42.9922, -79.2483),
}


def _normalize_status(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"success", "succeeded", "complete", "done"}:
        return "Success"
    if text in {"failed", "failure", "error"}:
        return "Failed"
    if text == "partial" or text == "needs update":
        return "Needs Update"
    return "Needs Update"


def _format_status_for_display(value: object) -> str:
    return _normalize_status(value)


def _ensure_status_compatibility(rows: Iterable[dict]) -> list[dict]:
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        status = row.get("Scrape Status", "")
        normalized.append(dict(row, **{"Scrape Status": _format_status_for_display(status)}))
    return normalized


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

print("\n" + "=" * 80)
print("🎾 Initializing Tennis Club Data Portal")
print("=" * 80)
global_data_merger = initialize_data_merger()
print("✓ Data merger initialized successfully")
if PLAYWRIGHT_AVAILABLE:
    print("✓ JavaScript scraper available (Playwright installed)")
else:
    print("ℹ️  JavaScript scraper not available (install: pip install playwright)")
print("=" * 80 + "\n")


scraping_status = {
    "running": False,
    "progress": 0,
    "total": 0,
    "current_club": "",
    "results": [],
    "errors": [],
    "mode_counts": {},
    "changed_since_last_run": False,
    "review_queue": [],
    "review_queue_count": 0,
    "coverage_metrics": {},
}


def _normalize_value(value: object) -> str:
    text = str(value or "").strip()
    return text.casefold()


def _canonical_signature(results: list[dict]) -> list[tuple[str, ...]]:
    signatures = []
    for row in results:
        signatures.append(
            (
                _normalize_value(row.get("Club Name", "")),
                _normalize_value(row.get("Website", "")),
                _normalize_value(row.get("Email", "N/A")),
                _normalize_value(row.get("Location", "N/A")),
                _normalize_value(row.get("Club Type", "N/A")),
                _normalize_value(row.get("Membership Status", "N/A")),
                _normalize_value(row.get("Waitlist Length", "N/A")),
                _normalize_value(row.get("Number of Courts", "N/A")),
                _normalize_value(row.get("Court Surface", "N/A")),
                _normalize_value(row.get("Operating Season", "N/A")),
                _normalize_value(row.get("Scrape Status", "Failed")),
            )
        )
    return sorted(signatures)


def _load_previous_signatures() -> list[tuple[str, ...]]:
    if not STATE_FILE.exists():
        return []
    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            return []
        return _canonical_signature(payload)
    except Exception:  # noqa: BLE001
        return []


def _persist_canonical_state(results: list[dict]) -> bool:
    previous = _load_previous_signatures()
    current = _canonical_signature(results)

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    return previous != current


def _result_without_meta(result: dict) -> dict:
    return {k: v for k, v in result.items() if k != "_meta"}


def _compute_mode_counts(results: list[dict]) -> dict[str, int]:
    counter = Counter()
    for row in results:
        mode = row.get("_meta", {}).get("retrieval_mode", "unknown")
        counter[mode] += 1
    return dict(counter)


def _build_review_queue(results: list[dict]) -> list[dict]:
    queue: list[dict] = []
    for row in results:
        meta = row.get("_meta", {})
        field_sources = meta.get("field_sources", {})
        actual_missing_fields, low_confidence_fields = _review_queue_field_gaps(row, field_sources)
        missing_fields = list(dict.fromkeys([*actual_missing_fields, *low_confidence_fields]))
        attempted_urls = _normalized_attempted_urls(meta.get("attempted_urls"), row.get("Website"))
        failure = _classify_review_failure(row, meta, actual_missing_fields, low_confidence_fields)

        if meta.get("needs_outreach") or missing_fields or low_confidence_fields:
            queue.append(
                {
                    "Club Name": row.get("Club Name", "Unknown"),
                    "Website": row.get("Website", "N/A"),
                    "Email": row.get("Email", "N/A"),
                    "Missing Fields": ", ".join(missing_fields) if missing_fields else "",
                    "Low Confidence Fields": ", ".join(low_confidence_fields),
                    "Recommendation": failure["recommended_next_action"],
                    "Retrieval Mode": meta.get("retrieval_mode", "unknown"),
                    "Status": row.get("Scrape Status", "Partial"),
                    "failure_reason": failure["failure_reason"],
                    "failed_stage": failure["failed_stage"],
                    "missing_fields": missing_fields,
                    "attempted_urls": attempted_urls,
                    "recommended_next_action": failure["recommended_next_action"],
                }
            )
    return queue


def _review_queue_field_gaps(row: dict, field_sources: dict) -> tuple[list[str], list[str]]:
    ordered_fields = list(dict.fromkeys([*CRITICAL_FIELDS, *REVIEW_FIELDS]))
    missing_fields: list[str] = []
    low_confidence_fields: list[str] = []

    for field in ordered_fields:
        value = str(row.get(field, "N/A")).strip()
        threshold = FIELD_THRESHOLDS.get(field, 0.0)
        confidence = field_sources.get(field, {}).get("confidence", 0.0)
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0

        is_missing = value in {"", "N/A"}
        is_low_confidence = not is_missing and confidence_value < threshold
        if is_missing:
            missing_fields.append(field)
        if is_low_confidence:
            low_confidence_fields.append(field)

    return missing_fields, low_confidence_fields


def _normalized_attempted_urls(attempted_urls: object, website: object) -> list[str]:
    normalized: list[str] = []

    if isinstance(attempted_urls, list):
        candidates = attempted_urls
    elif attempted_urls:
        candidates = [attempted_urls]
    else:
        candidates = []

    for candidate in candidates:
        text = _safe_text(candidate)
        if text and text not in normalized:
            normalized.append(text)

    website_text = _safe_text(website)
    if website_text and website_text.lower() not in {"n/a", "na", "none", "nan"} and website_text not in normalized:
        normalized.append(website_text)
    return normalized


def _classify_review_failure(row: dict, meta: dict, missing_fields: list[str], low_confidence_fields: list[str]) -> dict[str, object]:
    retrieval_mode = _safe_text(meta.get("retrieval_mode", "unknown")).lower()
    status_detail = _safe_text(meta.get("status_detail", "")).lower()
    site_profile = _safe_text(meta.get("site_profile", "unknown")).lower()
    errors = " ".join(
        _safe_text(error).lower()
        for error in meta.get("errors", [])
        if _safe_text(error)
    )

    if retrieval_mode == "no_website" or site_profile == "no_website" or status_detail == "preloaded_no_website":
        return {
            "failure_reason": "no_website",
            "failed_stage": "source_selection",
            "recommended_next_action": "verify_official_website_or_manual_outreach",
        }

    if (
        retrieval_mode == "failed"
        or "http_fetch_failed" in status_detail
        or "unable to fetch" in errors
        or "fetch_failed" in errors
    ):
        return {
            "failure_reason": "fetch_failed",
            "failed_stage": "fetch",
            "recommended_next_action": "retry_with_browser_automation_or_verify_url",
        }

    if site_profile == "js_heavy" or retrieval_mode == "js_heavy" or "js_heavy" in status_detail:
        return {
            "failure_reason": "js_heavy",
            "failed_stage": "render",
            "recommended_next_action": "use_browser_automation_or_site_adapter",
        }

    if missing_fields:
        return {
            "failure_reason": "partial_unpublished",
            "failed_stage": "post_processing",
            "recommended_next_action": "manual_review_or_contact_club",
        }

    if low_confidence_fields:
        return {
            "failure_reason": "parser_mismatch",
            "failed_stage": "parse",
            "recommended_next_action": "inspect_parser_and_source_html",
        }

    return {
        "failure_reason": "manual_review_needed",
        "failed_stage": "post_processing",
        "recommended_next_action": "manual_review",
    }


def _safe_text(value: object) -> str:
    return str(value or "").strip()


def _extract_website(row: object) -> str:
    for key in ("Website", "Website URL", "website_url", "website"):
        try:
            value = row.get(key, "")  # type: ignore[attr-defined]
        except AttributeError:
            value = ""
        text = _safe_text(value)
        if text and text.lower() not in {"n/a", "na", "nan", "none"}:
            return text
    return ""


def _parse_int(value: object) -> int | None:
    text = _safe_text(value)
    if not text or text in {"N/A", "NA", "n/a"}:
        return None
    match = re.search(r"\b(\d{1,3})\b", text)
    if not match:
        return None
    try:
        number = int(match.group(1))
    except ValueError:
        return None
    if number < 0:
        return None
    return number


def _court_bucket(count: int | None) -> str:
    if count is None:
        return "N/A"
    if count == 1:
        return "1"
    if 2 <= count <= 4:
        return "2-4"
    if 5 <= count <= 9:
        return "5-9"
    if 10 <= count <= 14:
        return "10-14"
    return "15+"


def _normalize_membership(value: object) -> str:
    text = _safe_text(value).lower()
    if not text or text in {"n/a", "na", "unknown"}:
        return "Unknown"
    if ("take" in text and "player" in text) or "accepting" in text:
        return "Taking players now"
    if "wait" in text:
        return "Waitlist"
    if "close" in text or "full" in text:
        return "Closed"
    if "open" in text:
        return "Open"
    return "Other"


def _normalize_membership_for_payload(value: object) -> str:
    return _normalize_membership(value)


def _is_taking_players_now(value: object) -> bool:
    normalized = _normalize_membership_for_payload(value)
    if normalized == "Taking players now":
        return True
    return normalized in {"Open", "Waitlist"}


def _normalize_city(value: object) -> str:
    text = _safe_text(value).lower().replace(",", " ")
    for city in CITY_COORDINATES:
        if city.lower() in text:
            return city
    return ""


def _build_marker(record: dict) -> dict | None:
    city = _normalize_city(record.get("Location", ""))
    if not city:
        return None

    lat, lng = CITY_COORDINATES[city]
    courts = _parse_int(record.get("Number of Courts", "N/A"))
    return {
        "name": record.get("Club Name", "Unknown"),
        "club_name": record.get("Club Name", "Unknown"),
        "location": record.get("Location", ""),
        "email": record.get("Email", "N/A"),
        "website": record.get("Website", "N/A"),
        "membership_status": record.get("Membership Status", "N/A"),
        "membership_status_normalized": record.get(
            "Membership Status Normalized",
            _normalize_membership_for_payload(record.get("Membership Status", "")),
        ),
        "taking_players_now": record.get(
            "Taking Players Now",
            _is_taking_players_now(record.get("Membership Status", "")),
        ),
        "courts": record.get("Number of Courts", "N/A"),
        "court_bucket": _court_bucket(courts if isinstance(courts, int) else _parse_int(courts)),
        "lat": lat,
        "lng": lng,
    }


def _build_records_from_state() -> list[dict]:
    if not STATE_FILE.exists():
        return []
    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
    except Exception:  # noqa: BLE001
        return []
    return []


def _build_records_from_preloaded_data() -> list[dict]:
    excel_file = BASE_DIR / "GTA_Tennis_clubs_raw_data .xlsx"
    if not excel_file.exists():
        return []

    try:
        df = pd.read_excel(excel_file)
    except Exception:  # noqa: BLE001
        return []

    records: list[dict] = []
    seen: set[str] = set()
    preloaded_fields = [
        "Email",
        "Location",
        "Club Type",
        "Membership Status",
        "Number of Courts",
        "Court Surface",
        "Operating Season",
    ]

    for _, row in df.iterrows():
        name = _safe_text(row.get("Club Name"))
        website = _extract_website(row)
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())

        entry = global_data_merger.get_existing_data(name, website) if global_data_merger else None
        if entry is None:
            entry = {}

        field_sources = {
            key: {"source": entry.get("source", "DB"), "stage": "preloaded", "confidence": 0.93}
            for key in preloaded_fields
            if _safe_text(entry.get(key)) not in {"", "N/A"}
        }

        records.append(
            {
                "Club Name": name,
                "Website": _safe_text(entry.get("Website")) or website or "N/A",
                "Email": entry.get("Email", "N/A"),
                "Location": entry.get("Location", "N/A"),
                "Club Type": entry.get("Club Type", "N/A"),
                "Membership Status": entry.get("Membership Status", "N/A"),
                "Waitlist Length": entry.get("Waitlist Length", "N/A"),
                "Number of Courts": entry.get("Number of Courts", "N/A"),
                "Court Surface": entry.get("Court Surface", "N/A"),
                "Operating Season": entry.get("Operating Season", "N/A"),
                "Scrape Status": "Success",
                "_meta": {
                    "retrieval_mode": "preloaded",
                    "field_sources": field_sources,
                    "attempted_urls": [],
                    "errors": [],
                    "site_profile": "preloaded",
                    "needs_outreach": bool(
                        _safe_text(entry.get("Membership Status")) in {"", "N/A"}
                        or _safe_text(entry.get("Waitlist Length")) in {"", "N/A"}
                    ),
                    "status_detail": "preloaded_local_sources",
                },
            }
        )
    return records


def _get_active_records() -> list[dict]:
    if scraping_status.get("results"):
        return _ensure_status_compatibility(scraping_status["results"])
    state_records = _build_records_from_state()
    if state_records:
        return _ensure_status_compatibility(state_records)
    return _ensure_status_compatibility(_build_records_from_preloaded_data())


def _collect_known_emails(records: list[dict]) -> list[str]:
    emails = []
    seen = set()
    for row in records:
        email = _safe_text(row.get("Email"))
        if "@" in email and email not in seen and email.lower() != "contact form available":
            seen.add(email)
            emails.append(email)
    return emails


def _count_eligible_for_coverage(df: pd.DataFrame, target_fields: list[str]) -> int:
    eligible = 0
    for _, row in df.iterrows():
        website = _extract_website(row)
        if not website:
            continue
        existing = global_data_merger.get_existing_data(row.get("Club Name", ""), website) if global_data_merger else None
        if existing is None:
            eligible += 1
            continue
        if any(str(existing.get(field, "N/A") or "N/A") == "N/A" for field in target_fields):
            eligible += 1
    return eligible


def _compute_coverage_metrics(results: list[dict], denominator: int) -> dict:
    tracked_fields = ["Number of Courts", "Court Surface", "Operating Season", "Membership Status", "Email", "Location"]
    metrics: dict[str, dict[str, float | int]] = {"denominator": {"count": denominator, "pct": 100.0}}

    if denominator <= 0:
        for field in tracked_fields:
            metrics[field] = {"count": 0, "pct": 0.0}
        metrics["acceptance_count"] = {"count": 0, "pct": 0.0}
        return metrics

    website_results = [row for row in results if str(row.get("Website", "") or "").strip() not in {"", "N/A"}]
    for field in tracked_fields:
        count = 0
        for row in website_results:
            value = str(row.get(field, "N/A") or "").strip()
            confidence = (
                row.get("_meta", {})
                .get("field_sources", {})
                .get(field, {})
                .get("confidence", 0.0)
            )
            try:
                confidence_value = float(confidence)
            except (TypeError, ValueError):
                confidence_value = 0.0

            threshold = FIELD_THRESHOLDS.get(field, 0.0)
            if value and value != "N/A" and confidence_value >= threshold:
                count += 1
        metrics[field] = {"count": count, "pct": round((count / denominator) * 100, 1)}

    acceptance_count = sum(
        1 for row in website_results if _is_taking_players_now(row.get("Membership Status", ""))
    )
    metrics["acceptance_count"] = {
        "count": acceptance_count,
        "pct": round((acceptance_count / denominator) * 100, 1),
    }
    return metrics


def _build_payload_records(records: list[dict]) -> list[dict]:
    payload_records = []
    for row in records:
        if not isinstance(row, dict):
            continue
        normalized_membership = _normalize_membership_for_payload(row.get("Membership Status", ""))
        payload_records.append(
            {
                **row,
                "Membership Status Normalized": normalized_membership,
                "Taking Players Now": _is_taking_players_now(normalized_membership),
            }
        )
    return payload_records


def _search_web_snippets(query: str, max_results: int = 5) -> list[str]:
    if not query.strip():
        return []

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GTA-Tennis-Scraper/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    }
    results: list[str] = []

    if FIRECRAWL_API_KEY:
        try:
            response = requests.post(
                "https://api.firecrawl.dev/v1/search",
                json={"query": query, "limit": max_results, "sources": ["search"], "autoparse": True},
                headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}", "Content-Type": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("data", [])[:max_results]:
                text = _safe_text(item.get("snippet") or item.get("content") or "")
                if text:
                    results.append(text)
        except Exception:  # noqa: BLE001
            pass
        if results:
            return results

    try:
        response = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except Exception:  # noqa: BLE001
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    for item in soup.select(".result__snippet"):
        snippet = _safe_text(item.get_text(" ", strip=True))
        if snippet:
            results.append(snippet)
        if len(results) >= max_results:
            break

    if not results:
        for item in soup.select("a.result__a + .result__body"):
            snippet = _safe_text(item.get_text(" ", strip=True))
            if snippet:
                results.append(snippet)
            if len(results) >= max_results:
                break

    return results[:max_results]


def _extract_court_count_from_text(text: str) -> int | None:
    if not text:
        return None
    patterns = [
        r"(\d{1,3})\s*(?:tennis\s+)?courts?\b",
        r"courts?\s*(?:\(|:)?\s*(\d{1,3})",
        r"number\s+of\s+(\d{1,3})\s+tennis\s+courts",
        r"(\d{1,3})\s*court[s]?\s*facility",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        try:
            value = int(match.group(1))
        except ValueError:
            continue
        if 1 <= value <= 50:
            return value
    return None


def _estimate_courts_from_search(club_name: str, location: str) -> dict[str, object]:
    location_clause = _safe_text(location) or "GTA"
    queries = [
        f"{club_name} {location_clause} number of courts",
        f"{club_name} {location_clause} tennis courts",
        f"{club_name} {location_clause} \"tennis club\" \"reviews\" \"courts\"",
        f"{club_name} {location_clause} site:google.com reviews courts",
        f"{club_name} {location_clause} site:yelp.com tennis courts",
    ]

    best: dict[str, object] = {"courts": "N/A", "confidence": 0.0, "evidence": ""}
    for query in queries:
        for snippet in _search_web_snippets(query, max_results=4):
            detected = _extract_court_count_from_text(snippet)
            if detected is not None:
                best = {
                    "courts": str(detected),
                    "confidence": 0.62,
                    "evidence": snippet[:250],
                    "query": query,
                }
                return best

    return best


def _write_outputs(results: list[dict], review_queue: list[dict], changed: bool) -> str | None:
    if not results:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_json = BASE_DIR / f"scraped_data_{timestamp}.json"
    output_csv = BASE_DIR / f"scraped_data_{timestamp}.csv"
    evidence_jsonl = BASE_DIR / f"scraped_evidence_{timestamp}.jsonl"
    review_csv = BASE_DIR / f"review_queue_{timestamp}.csv"

    output_json.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    flat_results = [_result_without_meta(row) for row in results]
    pd.DataFrame(flat_results).to_csv(output_csv, index=False)

    with evidence_jsonl.open("w", encoding="utf-8") as handle:
        for row in results:
            evidence_row = {
                "Club Name": row.get("Club Name"),
                "Website": row.get("Website"),
                "Scrape Status": row.get("Scrape Status"),
                "_meta": row.get("_meta", {}),
                "changed_since_last_run": changed,
            }
            handle.write(json.dumps(evidence_row, ensure_ascii=False) + "\n")

    review_headers = [
        "Club Name",
        "Website",
        "Email",
        "Missing Fields",
        "Low Confidence Fields",
        "Recommendation",
        "Retrieval Mode",
        "Status",
        "failure_reason",
        "failed_stage",
        "missing_fields",
        "attempted_urls",
        "recommended_next_action",
    ]
    with review_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=review_headers)
        writer.writeheader()
        for row in review_queue:
            writer.writerow(row)

    return timestamp


def background_scraping_task(max_clubs=None, use_js_fallback=False):
    """Background task to run the scraper"""
    global scraping_status

    try:
        excel_file = BASE_DIR / "GTA_Tennis_clubs_raw_data .xlsx"
        df = pd.read_excel(excel_file)

        if max_clubs:
            df = df.head(max_clubs)

        scraping_status["total"] = len(df)
        scraping_status["results"] = []
        scraping_status["errors"] = []
        scraping_status["mode_counts"] = {}
        scraping_status["changed_since_last_run"] = False
        scraping_status["review_queue"] = []
        scraping_status["review_queue_count"] = 0
        scraping_status["coverage_metrics"] = {}

        target_fields = [
            "Number of Courts",
            "Court Surface",
            "Operating Season",
            "Membership Status",
            "Email",
            "Location",
        ]
        coverage_denominator = _count_eligible_for_coverage(df, target_fields)

        if use_js_fallback and HybridScraper is not None:
            print("[INFO] Using hybrid scraper (JavaScript fallback enabled)")
            scraper = HybridScraper(data_merger=global_data_merger, use_js_fallback=True)
        else:
            if use_js_fallback and HybridScraper is None:
                print("[WARNING] JavaScript fallback requested but hybrid scraper is unavailable")
            scraper = TennisClubScraper(data_merger=global_data_merger, debug=False)

        for idx, row in df.iterrows():
            if not scraping_status["running"]:
                break

            club_name = row.get("Club Name", "Unknown")
            website = _extract_website(row)

            scraping_status["current_club"] = club_name
            scraping_status["progress"] = idx + 1

            if website:
                try:
                    result = scraper.scrape_club(website, club_name)
                except Exception as exc:  # noqa: BLE001
                    error_msg = f"Error scraping {club_name}: {exc}"
                    scraping_status["errors"].append(error_msg)
                    result = {
                        "Club Name": club_name,
                        "Website": website,
                        "Email": "N/A",
                        "Location": "N/A",
                        "Club Type": "N/A",
                        "Membership Status": "N/A",
                        "Waitlist Length": "N/A",
                        "Number of Courts": "N/A",
                        "Court Surface": "N/A",
                        "Operating Season": "N/A",
                        "Scrape Status": "Failed",
                        "_meta": {
                            "retrieval_mode": "failed",
                            "field_sources": {},
                            "attempted_urls": [website],
                            "errors": [str(exc)],
                            "site_profile": "unknown",
                            "needs_outreach": True,
                            "status_detail": "exception",
                        },
                    }
            else:
                existing_data = global_data_merger.get_existing_data(club_name, "") if global_data_merger else None
                if existing_data:
                    preloaded_sources: dict[str, dict[str, object]] = {}
                    preloaded_fields = [
                        "Email",
                        "Location",
                        "Club Type",
                        "Membership Status",
                        "Number of Courts",
                        "Court Surface",
                        "Operating Season",
                    ]
                    for preloaded_field in preloaded_fields:
                        value = existing_data.get(preloaded_field, "N/A")
                        if value and value != "N/A":
                            preloaded_sources[preloaded_field] = {
                                "source": existing_data.get("source", "DB"),
                                "stage": "preloaded",
                                "confidence": 0.93,
                            }
                    result = {
                        "Club Name": club_name,
                        "Website": "N/A",
                        "Email": existing_data.get("Email", "N/A"),
                        "Location": existing_data.get("Location", "N/A"),
                        "Club Type": existing_data.get("Club Type", "N/A"),
                        "Membership Status": existing_data.get("Membership Status", "N/A"),
                        "Waitlist Length": "N/A",
                        "Number of Courts": existing_data.get("Number of Courts", "N/A"),
                        "Court Surface": existing_data.get("Court Surface", "N/A"),
                        "Operating Season": existing_data.get("Operating Season", "N/A"),
                        "Scrape Status": "Success",
                        "_meta": {
                            "retrieval_mode": "preloaded",
                            "field_sources": preloaded_sources,
                            "attempted_urls": [],
                            "errors": [],
                            "site_profile": "no_website",
                            "needs_outreach": True,
                            "status_detail": "preloaded_no_website",
                        },
                    }
                else:
                    result = {
                        "Club Name": club_name,
                        "Website": "N/A",
                        "Email": "N/A",
                        "Location": "N/A",
                        "Club Type": "N/A",
                        "Membership Status": "N/A",
                        "Waitlist Length": "N/A",
                        "Number of Courts": "N/A",
                        "Court Surface": "N/A",
                        "Operating Season": "N/A",
                        "Scrape Status": "Failed",
                        "_meta": {
                            "retrieval_mode": "no_website",
                            "field_sources": {},
                            "attempted_urls": [],
                            "errors": ["no_website"],
                            "site_profile": "no_website",
                            "needs_outreach": True,
                            "status_detail": "no_website",
                        },
                    }

            scraping_status["results"].append(result)

            mode = result.get("_meta", {}).get("retrieval_mode", "unknown")
            mode_counts = Counter(scraping_status.get("mode_counts", {}))
            mode_counts[mode] += 1
            scraping_status["mode_counts"] = dict(mode_counts)

        review_queue = _build_review_queue(scraping_status["results"])
        changed = _persist_canonical_state(scraping_status["results"]) if scraping_status["results"] else False
        scraping_status["changed_since_last_run"] = changed
        scraping_status["review_queue"] = review_queue
        scraping_status["review_queue_count"] = len(review_queue)
        scraping_status["coverage_metrics"] = _compute_coverage_metrics(scraping_status["results"], coverage_denominator)

        _write_outputs(scraping_status["results"], review_queue, changed)

        scraping_status["running"] = False

    except Exception as exc:  # noqa: BLE001
        scraping_status["errors"].append(f"Fatal error: {exc}")
        scraping_status["running"] = False


@app.route("/")
def index():
    """Dashboard page"""
    active_records = _get_active_records()
    total_clubs = len(active_records)
    return render_template("index.html", total_clubs=total_clubs)


@app.route("/scraper")
def scraper():
    return render_template("scraper.html")


@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/players")
def players():
    return render_template("results.html")


@app.route("/email")
def email():
    return render_template("email.html")


@app.route("/api/start-scraping", methods=["POST"])
def start_scraping():
    global scraping_status

    if scraping_status["running"]:
        return jsonify({"error": "Scraping already in progress"}), 400

    data = request.get_json() or {}
    max_clubs = data.get("max_clubs")
    use_js_fallback = data.get("use_js_fallback", False)

    scraping_status = {
        "running": True,
        "progress": 0,
        "total": 0,
        "current_club": "",
        "results": [],
        "errors": [],
        "mode_counts": {},
        "changed_since_last_run": False,
        "review_queue": [],
        "review_queue_count": 0,
        "coverage_metrics": {},
    }

    thread = threading.Thread(target=background_scraping_task, args=(max_clubs, use_js_fallback))
    thread.daemon = True
    thread.start()

    return jsonify({"message": "Scraping started", "js_fallback_enabled": bool(use_js_fallback and PLAYWRIGHT_AVAILABLE)})


@app.route("/api/scraping-status")
def get_scraping_status():
    return jsonify(
        {
            "running": scraping_status["running"],
            "progress": scraping_status["progress"],
            "total": scraping_status["total"],
            "current_club": scraping_status["current_club"],
            "errors_count": len(scraping_status["errors"]),
            "results_count": len(scraping_status["results"]),
            "mode_counts": scraping_status.get("mode_counts", {}),
            "changed_since_last_run": scraping_status.get("changed_since_last_run", False),
            "review_queue_count": scraping_status.get("review_queue_count", 0),
            "coverage_metrics": scraping_status.get("coverage_metrics", {}),
        }
    )


@app.route("/api/results")
def get_results():
    active_records = _ensure_status_compatibility(_get_active_records())
    return jsonify({
        "results": active_records,
        "known_emails": _collect_known_emails(active_records),
        "errors": scraping_status.get("errors", []),
    })


@app.route("/api/dashboard-data")
def get_dashboard_data():
    records = _get_active_records()
    records = _ensure_status_compatibility(records)
    known_emails = _collect_known_emails(records)

    markers = []
    dashboard_records = _build_payload_records(records)
    for row_data in dashboard_records:
        row_data["court_bucket"] = row_data.get("court_bucket") or _court_bucket(_parse_int(row_data.get("Number of Courts", "N/A")))
        marker = _build_marker(row_data)
        if marker is not None:
            row_data["lat"] = marker["lat"]
            row_data["lng"] = marker["lng"]
            markers.append(marker)

    court_distribution: Counter[str] = Counter()
    membership_distribution: Counter[str] = Counter()
    for row in dashboard_records:
        courts = _parse_int(row.get("Number of Courts", "N/A"))
        court_distribution[_court_bucket(courts)] += 1
        membership_distribution[row.get("Membership Status Normalized", _normalize_membership(row.get("Membership Status", "")))] += 1

    known_email_count = len(known_emails)
    acceptance_count = sum(1 for row in dashboard_records if row.get("Taking Players Now") is True)

    return jsonify(
        {
            "records": dashboard_records,
            "total_clubs": len(records),
            "known_emails": known_emails,
            "known_emails_count": known_email_count,
            "success_count": len([row for row in records if row.get("Scrape Status") == "Success"]),
            "needs_update_count": len([row for row in records if row.get("Scrape Status") != "Success"]),
            "acceptance_count": acceptance_count,
            "court_distribution": dict(court_distribution),
            "membership_distribution": dict(membership_distribution),
            "map_data": {"markers": markers},
        }
    )


@app.route("/api/review-queue")
def review_queue():
    return jsonify(
        {
            "review_queue": scraping_status.get("review_queue", []),
            "count": scraping_status.get("review_queue_count", 0),
        }
    )


@app.route("/api/court-count-research", methods=["POST"])
def court_count_research():
    payload = request.get_json(silent=True) or {}
    requested_records = payload.get("clubs") or []
    max_records = payload.get("max_records", 8)

    if not isinstance(max_records, int):
        try:
            max_records = int(max_records)
        except (TypeError, ValueError):
            max_records = 8

    if max_records <= 0:
        max_records = 8
    if max_records > 20:
        max_records = 20

    if requested_records:
        candidate_rows = [row for row in requested_records if isinstance(row, dict)]
    else:
        candidate_rows = [
            row
            for row in _get_active_records()
            if _parse_int(row.get("Number of Courts", "N/A")) is None
        ]

    results: list[dict[str, object]] = []
    for row in candidate_rows[:max_records]:
        name = _safe_text(row.get("Club Name", "Unknown"))
        location = _safe_text(row.get("Location", ""))
        result = _estimate_courts_from_search(name, location)
        results.append(
            {
                "club_name": name,
                "location": location,
                "website": _safe_text(row.get("Website", "")),
                "estimated_courts": result["courts"],
                "confidence": result["confidence"],
                "evidence": result["evidence"],
            }
        )

    return jsonify({"results": results})


@app.route("/api/email-preview", methods=["POST"])
def preview_emails():
    try:
        data = request.get_json()
        template = data.get("template", "")

        clubs_to_contact = []
        for result in scraping_status["results"]:
            if (
                result.get("Email") != "N/A"
                and result.get("Email")
                and (result.get("Waitlist Length") == "N/A" or result.get("Membership Status") == "N/A")
            ):
                clubs_to_contact.append(result)

        email_agent = EmailAgent()
        previews = []

        for club in clubs_to_contact[:5]:
            subject, body = email_agent.generate_email(club, template)
            previews.append(
                {
                    "club_name": club["Club Name"],
                    "email": club["Email"],
                    "subject": subject,
                    "body": body,
                }
            )

        return jsonify({"total_emails": len(clubs_to_contact), "previews": previews})

    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@app.route("/api/send-emails", methods=["POST"])
def send_emails():
    try:
        data = request.get_json()
        template = data.get("template", "")
        dry_run = data.get("dry_run", True)

        clubs_to_contact = []
        for result in scraping_status["results"]:
            if (
                result.get("Email") != "N/A"
                and result.get("Email")
                and (result.get("Waitlist Length") == "N/A" or result.get("Membership Status") == "N/A")
            ):
                clubs_to_contact.append(result)

        if dry_run:
            return jsonify({"message": "Dry run completed", "total_emails": len(clubs_to_contact), "dry_run": True})

        email_agent = EmailAgent()
        sent_count = 0
        failed_count = 0

        for club in clubs_to_contact:
            try:
                subject, body = email_agent.generate_email(club, template)
                email_agent.send_email(club["Email"], subject, body)
                sent_count += 1
            except Exception as exc:  # noqa: BLE001
                failed_count += 1
                print(f"Failed to send to {club['Club Name']}: {exc}")

        return jsonify({"message": "Emails sent", "sent": sent_count, "failed": failed_count, "total": len(clubs_to_contact)})

    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
