# Default Development Workflow

This project uses a strict workflow for all implementation sessions.

## 1) Plan
- Define scope and constraints in a dated plan under `docs/plans/`.
- Validate assumptions and data sources before coding.
- Keep plan scoped to deliverable outcomes (no speculative refactors).

## 2) Review the Plan
- Review the plan for correctness before editing code.
- Confirm expected file touch points, risks, and validation steps.
- Approve dependencies/compatibility impact.

## 3) Execute Plan (Build)
- Implement in small, reversible changes.
- Use `exec` branches only (branch prefix: `codex/`).
- If tasks are independent, execute with parallel subagents.
- Keep backend and frontend changes aligned to API contract stability.

## 4) Code Review
- Run local verification (tests, compile, endpoint checks).
- Perform a first review for correctness, regressions, and edge cases.

## 5) Second/Peer Review
- Perform a second independent review pass before PR:
  - API contract compatibility
  - UI/UX regression behavior
  - Error handling and failure modes

## 6) PR
- Update/create PR with summary, files changed, and verification notes.
- Keep PR title/description consistent with plan items.

## 7) Push to Main
- Merge only after both review passes pass.
- Push `main` changes through the branch+PR path.

## 8) Post-Merge Checklist
- Confirm PR is closed and branch state is clean.
- Reconcile any follow-up tasks in a new dated plan.
- Keep evidence for major bug-fix claims in commit/PR description.

## Repository defaults
- Python entrypoint: `python3 app.py`
- App port: `5001`
- Use this workflow for all scraping and dashboard changes unless explicitly overridden.
