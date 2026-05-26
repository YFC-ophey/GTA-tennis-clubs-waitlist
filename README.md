# 🎾 GTA Tennis Clubs Data Portal

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![Pages](https://img.shields.io/badge/pages-live-2ea44f.svg)](https://yfc-ophey.github.io/GTA-tennis-clubs-waitlist/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Live site:** [yfc-ophey.github.io/GTA-tennis-clubs-waitlist](https://yfc-ophey.github.io/GTA-tennis-clubs-waitlist/) (public dashboard + club finder, auto-deployed from `main`)

A Wimbledon-inspired data portal for collecting and visualizing GTA tennis club information. Includes scraping orchestration, interactive dashboard pages, and a data review pipeline suitable for handling large-scale extraction gaps.

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
- `templates/` — Jinja templates (`index`, `results`, `scraper`, `email`) for the Flask app.
- `data/` — working Excel source and `current_club_state.json` snapshot.
- `GTA_Tennis_clubs_raw_data .xlsx` — root-level raw data source used by current app.
- `docs/` — pre-rendered static snapshot served by GitHub Pages (`index.html`, `results/index.html`).
- `scripts/build_github_pages.py` — regenerates `docs/` from current data.
- `.github/workflows/static.yml` — Actions workflow that deploys `docs/` to Pages on every push to `main`.

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

## 🌐 GitHub Pages Deployment

The public site at [yfc-ophey.github.io/GTA-tennis-clubs-waitlist](https://yfc-ophey.github.io/GTA-tennis-clubs-waitlist/) is auto-deployed from `main` via the workflow in `.github/workflows/static.yml`. It uploads the `docs/` folder as the Pages artifact, so `docs/index.html` becomes the site root.

**To refresh the live site with current data:**

```bash
python scripts/build_github_pages.py   # regenerates docs/ from current_club_state.json
git add docs/
git commit -m "chore: refresh docs snapshot"
git push origin main                    # workflow deploys within ~1 min
```

The Pages snapshot exposes the public dashboard and club finder. The scraping and email tools remain in the Flask app for local use.

## 🧭 Default Development Workflow

See [`WORKFLOW.md`](./WORKFLOW.md) for the required sequence.

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
