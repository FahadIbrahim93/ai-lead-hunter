# AI Lead Hunter — Revenue Acquisition OS

A local-first lead machine that discovers real Bangladesh businesses, verifies them live,
audits their pain, scores them, builds interactive demos and ROI calculators, and
generates personalized outreach drafts — all auditable, all local, nothing sent automatically.

## What it does

```
Research Inbox → Ingest (dedup) → Verify (live HTTP) → Audit → Score → Demo/Calculator → Outreach
                                                                  ↓
                                                         Pipeline Board (Kanban)
```

## Quick start

```bash
cd ~/ai-lead-hunter
python engine.py status          # health check + counts
python engine.py leads           # list all leads with scores
python engine.py research        # show research inbox
```

### Full pipeline (per lead)

```bash
python engine.py verify-all      # check all websites live (HTTP 200)
python engine.py audit LH-0001   # audit + score a lead
python engine.py demo-live LH-0001    # build interactive demo
python engine.py calculator-live LH-0001  # build ROI calculator
python engine.py outreach LH-0001     # draft personalized outreach
```

### Lifecycle (close the loop)

```bash
python engine.py sent O-0001            # mark outreach as sent
python engine.py reply O-0001 "..."    # log a reply
python engine.py won O-0001            # mark deal won
python engine.py lost O-0001           # mark deal lost
```

### Dashboard

```bash
python dashboard.py          # opens http://localhost:8765
# Or double-click START-DASHBOARD.bat (Windows)
```

The dashboard has tabs: **Leads** (with Re-Audit/Demo/Calculator/Outreach buttons), **Outreach Drafts**, **Activity Log**, and **Pipeline Board** (Kanban by lifecycle stage).

## Architecture

```
data/
  leads/        JSON records (LH-0001..NNNN.json) — canonical
  evidence/     JSON records (E-0001..NNNN.json) — append-only
  activity/     JSON records (A-0001..NNNN.json) — append-only log
  outreach/     JSON records (O-0001..NNNN.json) — drafts, pending_approval
  research/     findings.json — research inbox (before ingest)
  schemas/      4 JSON schemas (lead, evidence, activity, outreach)

artifacts/
  demos-live/       standalone interactive HTML demos (per lead)
  calculators-live/ standalone ROI calculator HTML (per lead)
  demos/            legacy markdown demo specs

scripts/
  enrich_research_leads.py   attach pain signals + offer surfaces to research leads
  rewrite_outreach.py        personalize outreach from verified evidence
  inject_outreach_links.py   inject demo/calc HTML paths into drafts
  add_calc_links.py          add calculator links to outreach drafts
  fix_calculator_button.py   ensure exactly one calculator-live button in UI

templates/
  demo_template.html         interactive demo template
  calculator_template.html   interactive ROI calculator template

engine.py            CLI orchestrator (discover, research, ingest, verify, audit, score,
                     demo, demo-live, calculator-live, outreach, sent, reply, won, lost, validate, status, leads)
dashboard.py         zero-dependency local web server (port 8765)
ui.html              dashboard UI (XSS-safe via esc())
START-DASHBOARD.bat  Windows double-click launcher
.github/workflows/ci.yml  GitHub Actions CI (status + pytest on push/PR)
tests/test_core.py   27 acceptance tests
tests/test_v2.py     v2 architecture tests (research inbox, dedup, verify, idempotency)
```

## Key features

- **Research inbox** — `data/research/findings.json` is the queue; `ingest` deduplicates by name + domain and converts findings to leads
- **Live verification** — `verify` does real HTTP GETs, confirms 200, extracts real phone/email from the page, saves verified_at
- **Scoring** — composite 0-100 from pain signals, contact paths, evidence, operational gaps, scale, decision-maker access, fit
- **Tier bands** — A (85-100 act today), B (70-84 worth building), C (50-69 monitor)
- **Lifecycle** — DISCOVERED → AUDITED → QUALIFIED → OUTREACH_READY → CONTACTED → IN_CONVERSATION → WON/LOST
- **Interactive demos** — standalone HTML, double-click to open, fully personalized (business name, services, pains, contacts), walks user through intake flow
- **ROI calculators** — standalone HTML, sliders for enquiries/missed%/value/staff cost/hours, shows monthly loss + annual savings
- **No automatic sending** — outreach drafts are `pending_approval`; you review, copy, paste, send yourself
- **Append-only audit trail** — every action logs an A-NNNN activity record
- **JSON Schema validation** — all 4 record types validated on every run
- **GitHub Actions CI** — on push/PR to main: `python engine.py status` + `pytest -q`

## Adding a lead

1. Research a real business (web_search), find its website
2. Add to `data/research/findings.json`
3. `python engine.py ingest` (dedups, converts to lead, logs activity)
4. `python engine.py verify <lead_id>` (live HTTP check + contact extraction)
5. `python engine.py audit <lead_id>` (audit + score + qualify if score >= 70)
6. `python engine.py demo-live <lead_id>` (build interactive demo)
7. `python engine.py calculator-live <lead_id>` (build ROI calculator)
8. `python engine.py outreach <lead_id>` (draft personalized outreach)

## Current state

| Metric | Count |
|---|---|
| Leads | 25 (17 clients + 4 ventures + 4 new) |
| Verified live | 16 |
| Qualified | 15 |
| Tier A | 8 |
| Tier B | 7 |
| Evidence | 168 |
| Activity log | 544 records |
| Outreach drafts | 9 (all pending_approval) |
| Interactive demos | 14 |
| ROI calculators | 22 |
| Tests | 27/27 passing |

## Repositories

- Code: https://github.com/FahadIbrahim93/ai-lead-hunter
- Live dashboard: http://localhost:8765 (when server running)

## Rules

- Nothing gets sent automatically — only drafts, you pull the trigger
- No API keys or credentials in the codebase
- All data is local JSON — auditable, git-versioned
- Human approval gate: no external outreach leaves the system without a human-approved outreach record
