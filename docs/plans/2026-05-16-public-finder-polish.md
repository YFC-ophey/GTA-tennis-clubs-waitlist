# Public Finder Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the existing GTA tennis data portal into a premium public-facing tennis club finder with a clean data-dashboard backbone.

**Architecture:** Keep the Flask backend and existing template structure. Use the backfilled `data/current_club_state.json` as the immediate dataset, expose the existing dashboard/results APIs, and polish the user-facing experience through server-rendered templates plus lightweight JavaScript.

**Tech Stack:** Flask, Jinja templates, vanilla CSS, jQuery, Leaflet, pytest.

---

### Task 1: Global Shell Polish

**Files:**
- Modify: `templates/base.html`

**Steps:**
1. Refine the global color tokens, typography, header, navigation, buttons, form controls, and responsive spacing.
2. Keep all existing block names and script includes working.
3. Avoid adding external frontend build tooling.
4. Verify by running `python -m pytest -q`.

### Task 2: Public Finder Dashboard

**Files:**
- Modify: `templates/index.html`

**Steps:**
1. Rework the dashboard first viewport into a club finder: search, key filters, concise stats, and map/list discovery.
2. Keep existing API calls to `/api/dashboard-data`.
3. Ensure empty/unknown fields display as honest “Not published” style labels rather than fake completeness.
4. Verify the dashboard loads against `data/current_club_state.json`.

### Task 3: Directory Results Polish

**Files:**
- Modify: `templates/results.html`

**Steps:**
1. Polish the directory page as the deeper browse/export surface.
2. Keep CSV/JSON export, search, known-email display, and court research behavior.
3. Improve status pills, table readability, responsive behavior, and empty states.
4. Verify `/api/results` returns records and the page JavaScript still references valid fields.

### Task 4: Verification and Review

**Files:**
- Test: `tests/test_app_contract.py`
- Test: `tests/test_scraper_pipeline.py`

**Steps:**
1. Run `python -m pytest -q`.
2. Start Flask locally on port 5001 or another free port.
3. Inspect `/`, `/results`, `/api/results`, and `/api/dashboard-data`.
4. Request code review and fix critical or important issues.
5. Commit only relevant source/template/test/data/plan files.
