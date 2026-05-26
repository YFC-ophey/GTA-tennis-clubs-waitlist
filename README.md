# 🎾 GTA Tennis Clubs Data Portal

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Wimbledon-inspired data portal for collecting and visualizing GTA tennis club information.  
Current branch includes scraping orchestration, interactive dashboard pages, and a data review pipeline suitable for handling large-scale extraction gaps.

## ✨ Features

- **🏆 Wimbledon-themed UI** for the dashboard and directory pages.
- **📊 Interactive dashboard** with coverage metrics and status overview.
- **🧭 Club directory + map-ready records** served by `/api/dashboard-data`.
- **🕸️ Smart scraping pipeline** that merges raw sources with previous collected data.
- **📧 Outreach support** via `EmailAgent` for follow-up on incomplete records.
- **🔎 Optional court-count enrichment** using DuckDuckGo snippets or Firecrawl when configured.
- **🧱 Deterministic CSV/JSON output** for each scrape run.

## 📂 Project Layout

- `app.py` — Flask server and API endpoints.
- `scraper_simple.py` — scraping logic.
- `data_merger.py` — source data normalization and merge helpers.
- `email_agent.py` — email preview/send utilities.
- `templates/` — HTML templates (`index`, `results`, `scraper`, `email`).
- `data/` — working Excel source.
- `GTA_Tennis_clubs_raw_data .xlsx` — root-level raw data source used by current app.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
git clone <repository-url>
cd GTA-tennis-clubs-waitlist
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

Open:

- `http://localhost:5001/` (dashboard)
- `http://localhost:5001/scraper`
- `http://localhost:5001/results`
- `http://localhost:5001/email`

The app runs on port `5001` to avoid common local conflicts.

## 🌐 GitHub Pages Snapshot

This branch also generates a static public snapshot in `docs/` for GitHub Pages.

Published URL:

- `https://yfc-ophey.github.io/GTA-tennis-clubs-waitlist/`

To enable it in GitHub:

1. Open repository settings.
2. Go to **Pages**.
3. Select the `main` branch and the `/docs` folder as the source.
4. Save and wait for GitHub to publish the site.

The Pages snapshot exposes the public dashboard and club finder. The scraping and email tools remain in the Flask app for local use.

## 🧭 Default Development Workflow

See [`WORKFLOW.md`](/Users/opheliachen/projects/GTA%20Tennis%20Clubs/GTA-tennis-clubs-waitlist/.worktrees/codex-wimbledon-dashboard/WORKFLOW.md) for the required sequence.

## 🔌 API Endpoints

- `GET /api/results` — merged club list and metadata.
- `GET /api/dashboard-data` — dashboard stats + records payload.
- `GET /api/scraping-status` — run progress and error counters.
- `POST /api/start-scraping` — start background scraping task.
- `POST /api/court-count-research` — estimate unknown court counts from web snippets.
- `POST /api/email-preview` — generate preview emails.
- `POST /api/send-emails` — send or dry-run outreach emails.
- `GET /` and `/scraper`, `/results`, `/email` for the HTML pages.

## 🧩 Data Model

Each club record contains:

- `Club Name`
- `Website`
- `Email`
- `Location`
- `Club Type`
- `Membership Status`
- `Waitlist Length`
- `Number of Courts`
- `Court Surface`
- `Operating Season`
- `Scrape Status`

`Scrape Status` supports `Success`, `Partial`, and `Failed` semantics for downstream dashboard filtering.

## 🛠 Configuration

Optional environment variables:

- `SENDER_EMAIL` and `SENDER_PASSWORD` for outbound email workflow.
- `FIRECRAWL_API_KEY` for higher-confidence court-count suggestions.

## 🧪 Data Files

Scrape runs persist:

- `scraped_data_<timestamp>.json`
- `scraped_data_<timestamp>.csv`

You can also inspect merged records at runtime via API payloads.

## 🐞 Troubleshooting

- **Port already in use** — ensure port `5001` is free.
- **Missing Flask dependency** — run `pip install -r requirements.txt`.
- **No emails sent** — verify `.env` / Gmail app-password style credentials.

## 📄 License

MIT. See repository `LICENSE`.

## 🙏 Credits

- Inspired by Wimbledon design language and built for practical club data intelligence.
