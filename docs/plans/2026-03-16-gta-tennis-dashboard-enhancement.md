# Wimbledon-Themed Dashboard Enhancement Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete a frontend/backend iteration that serves a Wimbledon-style interactive tennis-club dashboard, removes scraping from the landing workflow, and makes player directory data reliably available from source+scrape outputs.

**Architecture:** Keep existing Flask app but enrich it with a canonical record builder, merge scraped rows with static data, and expose dashboard/directory APIs that always return a stable dataset.

**Tech Stack:** Flask, pandas, jQuery, Chart.js, Leaflet.

---

### Task 1: Stabilize dataset pipeline

**Files:**
- Modify: `app.py`
- Test: `python -m py_compile app.py`

1. Write a minimal check for `_build_base_records()` returning deterministic merged records.
2. Run check.
3. Implement `_build_base_records`, `_build_payload_records`, `_get_current_records` helpers in `app.py`.
4. Run check.
5. Commit helper-only changes if passing.

### Task 2: Add dashboard API contract

**Files:**
- Modify: `app.py`
- Update: `templates/index.html`

1. Write a failing test/quick check for `/api/dashboard-data` returning records + known emails.
2. Implement `/api/dashboard-data` and augment `/api/results` payload with `known_emails` + `_meta`.
3. Update `templates/index.html` to use `/api/dashboard-data` for counts and interactive filters.
4. Run manual endpoint check.
5. Commit.

### Task 3: Player directory cleanup

**Files:**
- Modify: `templates/results.html`

1. Confirm JS render path and status mapping behavior.
2. Fix JS runtime issues in `results.html` and verify data load from new payload shape.
3. Add known-emails block + update summary behavior.
4. Commit.

### Task 4: Court-count research endpoint

**Files:**
- Modify: `app.py`

1. Add `/api/court-count-research` endpoint with graceful fallback.
2. Add confidence/evidence fields for unresolved courts suggestions.
3. Smoke-check with a request payload.
4. Commit.

### Task 5: Visual and interaction review

**Files:**
- Modify: `templates/base.html`, `templates/index.html`

1. Verify clickable states, map visibility, and keyboard-accessible controls.
2. Run a browser smoke check and capture screenshot for dashboard + directory.
3. Code-review pass and second review pass for defects and accessibility gaps.
4. Commit finalized UI polish.

---

Execution choice (for next stage):
1. Subagent-Driven (this session)
2. Parallel Session (separate)
