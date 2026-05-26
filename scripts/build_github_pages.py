#!/usr/bin/env python3
"""Build a static GitHub Pages snapshot for the GTA Tennis Clubs site."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

BASE_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BASE_DIR / "docs"
PUBLIC_BASE_URL = "https://yfc-ophey.github.io/GTA-tennis-clubs-waitlist/"

import sys

sys.path.insert(0, str(BASE_DIR))

import app as app_module


def _render(template_name: str, request_path: str, context: dict[str, object]) -> str:
    with app_module.app.test_request_context(request_path):
        return app_module.render_template(template_name, **context)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_public_context(*, active_nav: str, home_href: str, results_href: str, canonical_url: str) -> dict[str, object]:
    return {
        "active_nav": active_nav,
        "home_href": home_href,
        "results_href": results_href,
        "canonical_url": canonical_url,
    }


def main() -> None:
    with app_module.app.test_request_context("/api/dashboard-data"):
        dashboard_payload = app_module.get_dashboard_data().get_json()
    with app_module.app.test_request_context("/api/results"):
        results_payload = app_module.get_results().get_json()

    dashboard_json = json.dumps(dashboard_payload, ensure_ascii=False)
    results_json = json.dumps(results_payload, ensure_ascii=False)

    index_context = _build_public_context(
        active_nav="overview",
        home_href="./",
        results_href="results/",
        canonical_url=PUBLIC_BASE_URL,
    )
    index_context["total_clubs"] = dashboard_payload.get("total_clubs", 0)
    index_context["dashboard_data_json"] = dashboard_json
    index_context["page_description"] = (
        "Find and compare GTA tennis clubs with published membership signals, map discovery, and public record coverage."
    )

    results_context = _build_public_context(
        active_nav="results",
        home_href="../",
        results_href="./",
        canonical_url=urljoin(PUBLIC_BASE_URL, "results/"),
    )
    results_context["results_data_json"] = results_json
    results_context["page_description"] = (
        "Browse GTA tennis club records, published contact details, and membership signals in a searchable directory."
    )

    _write(DOCS_DIR / "index.html", _render("index.html", "/", index_context))
    _write(DOCS_DIR / "results" / "index.html", _render("results.html", "/results/", results_context))

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{PUBLIC_BASE_URL}</loc>
    <lastmod>{generated_at}</lastmod>
  </url>
  <url>
    <loc>{urljoin(PUBLIC_BASE_URL, 'results/')}</loc>
    <lastmod>{generated_at}</lastmod>
  </url>
</urlset>
"""
    _write(DOCS_DIR / "sitemap.xml", sitemap)
    _write(
        DOCS_DIR / "robots.txt",
        f"User-agent: *\nAllow: /\nSitemap: {PUBLIC_BASE_URL}sitemap.xml\n",
    )
    _write(DOCS_DIR / ".nojekyll", "")


if __name__ == "__main__":
    main()
