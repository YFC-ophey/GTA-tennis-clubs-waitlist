# Manual Review Queue and Fallback Scraping Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make unresolved clubs explicit by classifying scrape failures into a manual-review queue first, then add a site-specific adapter registry for repeated failure patterns.

**Architecture:** Keep the current layered scraper as the default path. Add structured failure reasons and evidence to each club record, surface unresolved clubs through the existing review queue, and persist that queue so the UI and exports can show what still needs human attention. Once failure classes are visible, add a small adapter registry keyed by host/domain for repeated problem sites. Do not replace the scraper with a brand-new generic script.

**Tech Stack:** Flask, pandas, requests, BeautifulSoup, optional Playwright, existing `scraper_simple.py`, `scraper_hybrid.py`, and `data_merger.py`.

---

### Task 1: Classify unresolved clubs

**Files:**
- Modify: `app.py`
- Modify: `scraper_simple.py`
- Modify: `tests/test_app_contract.py`

**Step 1: Write the failing test**

Add a test that creates a result with missing critical fields and asserts the review queue entry includes a stable failure classification and next action, not just a CSV-style row.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app_contract.py -k review_queue -v`

Expected: fail because the review queue does not yet emit structured failure metadata.

**Step 3: Write minimal implementation**

Add failure classification fields to the record metadata, such as:
- `failure_reason`
- `failed_stage`
- `missing_fields`
- `attempted_urls`
- `recommended_next_action`

Populate these from the existing scraper result metadata and from the review queue builder.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app_contract.py -k review_queue -v`

Expected: pass.

**Step 5: Commit**

```bash
git add app.py scraper_simple.py tests/test_app_contract.py
git commit -m "feat: classify unresolved club records"
```

### Task 2: Persist the review queue and expose it cleanly

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_contract.py`
- Modify: `templates/results.html` if needed for a small queue summary only

**Step 1: Write the failing test**

Add a test that calls `/api/review-queue` and asserts the response contains structured queue items with reason, stage, and suggested next action.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app_contract.py -k review_queue_endpoint -v`

Expected: fail because the API does not yet expose the richer queue shape.

**Step 3: Write minimal implementation**

Use the existing `scraping_status["review_queue"]` path and `_write_outputs()` to persist the queue as a durable artifact. Keep the route as a simple read-only exposure of that queue.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app_contract.py -k review_queue_endpoint -v`

Expected: pass.

**Step 5: Commit**

```bash
git add app.py tests/test_app_contract.py templates/results.html
git commit -m "feat: expose unresolved club review queue"
```

### Task 3: Add a host-based adapter registry

**Files:**
- Create: `scraper_adapters.py`
- Modify: `scraper_simple.py`
- Modify: `scraper_hybrid.py`
- Modify: `app.py`
- Add or modify tests in: `tests/test_scraper_pipeline.py`

**Step 1: Write the failing test**

Add a test for a fake adapter that overrides one extraction method for a known host and confirm it is used before the generic scraper.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scraper_pipeline.py -k adapter -v`

Expected: fail because the adapter registry does not exist yet.

**Step 3: Write minimal implementation**

Create a small registry keyed by hostname/domain. Each adapter should be allowed to:
- change fetch strategy
- add targeted parsing for known DOM patterns
- provide fallback URL candidates

Keep the default scraper untouched unless an adapter is selected.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_scraper_pipeline.py -k adapter -v`

Expected: pass.

**Step 5: Commit**

```bash
git add scraper_adapters.py scraper_simple.py scraper_hybrid.py app.py tests/test_scraper_pipeline.py
git commit -m "feat: add host-based scraper adapters"
```

### Task 4: Verify unresolved clubs are routed correctly

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_contract.py`

**Step 1: Write the failing test**

Add a test that simulates a failed club scrape and asserts it lands in the review queue with a useful reason rather than disappearing as generic `N/A`.

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_app_contract.py -k unresolved -v`

Expected: fail until the classification and queue wiring are complete.

**Step 3: Write minimal implementation**

Make `background_scraping_task()` collect failure evidence from scraper metadata and pass it through `_build_review_queue()` unchanged.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_app_contract.py -k unresolved -v`

Expected: pass.

**Step 5: Commit**

```bash
git add app.py tests/test_app_contract.py
git commit -m "feat: route unresolved clubs to review queue"
```

### Task 5: Final verification

**Files:**
- None

**Step 1: Run the full test suite**

Run: `pytest -q`

Expected: all tests pass.

**Step 2: Exercise the app locally**

Run the Flask app and verify:
- dashboard loads
- results page loads
- review queue endpoint returns structured unresolved items

**Step 3: Commit any final cleanup**

```bash
git add .
git commit -m "chore: finalize review queue and adapter scaffolding"
```
