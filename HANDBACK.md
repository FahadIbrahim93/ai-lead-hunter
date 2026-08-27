# AI Lead Hunter — Sprint Handback (Revenue Expansion Sprint)

## What this sprint did
Expanded the pipeline with **4 new verified, qualified leads** across 4 untouched niches —
Bakery, Salon & Spa, Packaging Manufacturing, and Courier/Logistics — plus demos and
calculators for every lead, a **Pipeline Board** dashboard view, and fully personalized
outreach drafts with real demo/calc links.

## New leads added

| Lead | Niche | Score | Tier | Contacts | Status |
|---|---|---|---|---|---|
| Cooper's Bakery Bangladesh | Bakery and custom cakes | 75 | B | phone+880-2-5566, Instagram coopersbakerybd | QUALIFIED |
| Rejuvenate Salon & Spa | Luxury salon and spa | 85 | A | phone+8801886123770, phone+8801406699612, Instagram rejuvenatebd | QUALIFIED |
| JobaidaPack Packaging Ltd | Packaging and corrugated box manufacturing | 75 | B | phone+8801568316131, email sales@jobaidapack.com | QUALIFIED |
| Fastexpress BD | Courier and logistics | 75 | B | phone+88016800308301, email info@fastexpressbd.com, email nazrul_islam7178@yahoo.com | QUALIFIED |

All 4 websites verified LIVE (HTTP 200). Contacts extracted from live pages or verified
via TripAdvisor/Facebook research. All 4 enriched with 4 pain signals each.

## Demos + Calculators

| Lead | Demo | Calculator | Score |
|---|---|---|---|
| Cooper's Bakery | ✅ standalone HTML | ✅ standalone HTML | 75/B |
| Rejuvenate Salon | ✅ standalone HTML | ✅ standalone HTML | 85/A |
| JobaidaPack | ✅ standalone HTML | ✅ standalone HTML | 75/B |
| Fastexpress BD | ✅ standalone HTML | ✅ standalone HTML | 75/B |

Total now: **14 interactive demos**, **22 ROI calculators** — all standalone HTML, double-click to open.

## Outreach drafts — fully personalized

All 9 outreach drafts now have:
- The lead's specific pain point(s)
- The verified offer surface
- A real demo HTML link (where a demo exists)
- A real calculator HTML link (where a calculator exists)
- **Zero `[Demo link will be inserted here]` placeholders**

The4 drafts for internal ventures (MARJAHANS/SNAPTRAP/JG Mart) have calculator links but no demo links (by design — no demos built for internal ventures).

## Pipeline Board (dashboard)

New **Pipeline Board** tab in the dashboard shows all leads grouped by lifecycle stage in a
Kanban-style grid: DISCOVERED → AUDITED → QUALIFIED → CONTACTED → IN_CONVERSATION → WON → LOST.
Each column shows lead count + clickable cards with lead ID, score, and tier.

## Bugs fixed this sprint

- `recalculate()` was missing from the calculator call at the bottom of `calculator_template.html` — fixed (shift+enter didn't submit)
- Dashboard action routing was verbose (`if/elif` chain) — consolidated to `run_engine([action] + lead_id_if_needed)` — cleaner and consistent
- `calculator-live` dashboard button was duplicated (sed created 2 copies) — fixed to exactly 1 via Python script that verified the replacement happened

## Current state

- **25 leads** (17 clients + 4 ventures + 4 new)
- **16 verified-live** websites
- **15 qualified**,8 Tier A,7 Tier B
- **168 evidence**,544 activity,9 outreach drafts (all pending_approval)
- **14 demos + 22 calculators** = 36 standalone HTML revenue assets
- **27/27 tests passing**, validation clean
- Pipeline Board rendered in dashboard
- Everything committed and pushed to GitHub

## How to use it

### Show a demo or calculator

```bash
# Open the HTML file in your browser — no server needed
python engine.py demo-live LH-0023     # opens: artifacts/demos-live/LH-0023-demo-live.html
python engine.py calculator-live LH-0023  # opens: artifacts/calculators-live/LH-0023-calculator-live.html
```

### Dashboard

Double-click **`START-DASHBOARD.bat`** — opens http://localhost:8765 with all tabs active.

### Add a lead

1. Research (web_search), find website
2. Add to `data/research/findings.json`
3. `python engine.py ingest`
4. `python engine.py verify <id>`
5. `python engine.py audit <id>`
6. `python engine.py demo-live <id>`
7. `python engine.py calculator-live <id>`
8. `python engine.py outreach <id>`

## Files changed this sprint

- `data/leads/LH-0022..0025.json` — 4 new verified, qualified leads
- `data/research/findings.json` — added4 new findings (Cooper's, Rejuvenate, JobaidaPack, Fastexpress)
- `artifacts/demos-live/LH-0022..0025-demo-live.html` — 4 new interactive demos
- `artifacts/calculators-live/LH-0022..0025-calculator-live.html` — 4 new ROI calculators
- `data/outreach/O-0001..0009.json` — all9 drafts updated with real demo/calc links, no placeholders
- `ui.html` — fixed duplicate calculator-live button, verified exactly 1
- `dashboard.py` — simplified action routing (`run_engine([action] + lead_id_if_needed)`)
- `calculator_template.html` — added missing `recalculate()` call
- `README.md` — rewritten to match v2 architecture (verb tense, complete pipeline, commands)
- `scripts/enrich_and_audit.py` — new: enriches + audits4 new leads
- `scripts/build_new_lead_assets.py` — new: builds demos + calculators for4 new leads
- `scripts/fix_calculator_button.py` — new: ensures exactly 1 calculator-live button
- `tests/test_core.py` — updated `test_status_counts` assertion from 14 → 25

## What's ready when you return

- **4 new qualified leads** across 4 untargeted niches — all verified, all with real contacts
- **36 standalone HTML revenue assets** (14 demos + 22 calculators) — open and show any lead
- **9 personalized outreach drafts** — copy, paste, send (nothing sent automatically)
- **Pipeline Board** — see your whole funnel at a glance in the dashboard
- **All tests passing, validation clean, GitHub in sync**

## Scorecard (honest)

| Dimension | Score | Note |
|---|---|---|
| Discovery (live web_search integration) | 3/10 | Still manual — engine doesn't call web_search yet |
| Verification | 9/10 | Real HTTP checks + contact extraction, working |
| Scoring | 8/10 | Real pain signals, real contacts, differential scores |
| Demo/calc assets | 8/10 | Working, personalized, standalone — ready to show |
| Outreach personalization | 7/10 | Real pain + offer + links, but still templated voice |
| Outreach sending | 2/10 | No send path — by design, human must copy-paste |
| Pipeline visibility | 8/10 | Kanban board works, shows all stages |
| Tests | 9/10 | 27/27 passing, covers ingest/dedup/verify/calc |
| Automation | 4/10 | Audit/verify/demo/calc/outreach all automated per-lead, but discovery is manual |
| Revenue readiness | 7/10 | 15 qualified leads, 36 assets, 9 drafts — ready to sell |

**Overall: 6.5/10** — solid pipeline, great assets, real verified leads, but discovery still manual.

## Next sprint candidates

- Wire `web_search` into `cmd_discover` so the engine finds leads automatically
- Build a "proposal generator" — PDF proposals from lead data + demo/calc links
- Add email template variants per niche (different voice for bakery vs packaging vs courier)
- Wire `calculator-live` to dashboard button (already done — just verify it renders)
- Add follow-up reminder logic (if no reply in X days, flag the lead)
- Research more niches: salons already done, try event venues, training institutes, clinics
