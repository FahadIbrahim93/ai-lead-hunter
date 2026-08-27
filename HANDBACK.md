# AI Lead Hunter — Sprint Handback (Revenue Assets Sprint 2)

## What this sprint did
Built the complete selling kit: **ROI calculator demo**, **pipeline board view**, and
**4 new verified, qualified leads** across digital marketing, event management,
IT services, and wedding planning.

## New features built

###1. ROI Calculator (`calculator-live`)
- Interactive HTML calculators for **18 qualified leads**
- Each calculator is a standalone file: sliders for enquiries, missed %, customer value, staff cost, hours
- Instantly shows the lead what they're losing per month
- Niches handled: interior design, real estate, legal, health, travel, IELTS, education, jewelry, diagnostic, fitness, photography, gym, wedding, food, digital marketing, event management, IT/software
- Nicpe-specific default values so each calculator starts relevant

###2. Pipeline Board View (dashboard tab)
- New "📊 Pipeline Board" tab in the dashboard
- Shows all leads grouped by lifecycle stage: DISCOVERED → AUDITED → QUALIFIED → CONTACTED → IN_CONVERSATION → WON → LOST
- Visual Kanban-style columns with counts and clickable lead cards
- Shows lead ID + score + tier on each card

###3.4 New Verified, Qualified Leads
| Lead | Niche | Score | Contacts |
|---|---|---|---|
| Ngital Digital Marketing | Digital marketing agency | 75/B | enquiry@ngital.com, +880****4800 |
| Ananta Events | Event management | 75/B | +880****9170, +880****0400 |
| Fara IT Limited | IT/software/web dev | 75/B | +880****7322 |
| Look N Feel Event Solutions | Event/wedding planning | 75/B | looknfeelevent@gmail.com, +880****1180 |

All4 websites verified LIVE (HTTP 200). Real contacts extracted from live pages.

## Current state
- **21 leads**:17 clients +4 internal ventures
- **15 qualified**,8 Tier A,7 Tier B
- **18 interactive demos** (`artifacts/demos-live/`)
- **18 ROI calculators** (`artifacts/calculators-live/`)
- **9 outreach drafts** (all pending_approval — human must approve/send)
- **164 evidence**,414 activity,9 outreach drafts
- **27/27 tests passing**, validation clean
- Pipeline board rendered in dashboard

## How to use the new features

### Show a calculator to a lead
```bash
# Open the HTML file in your browser
# Lead drags sliders to see their own savings
python engine.py calculator-live LH-0018
# Opens: artifacts/calculators-live/LH-0018-calculator-live.html
```

### View the pipeline board
1. Double-click `START-DASHBOARD.bat`
2. Click "📊 Pipeline Board" tab
3. See all leads grouped by stage at a glance

### Add more leads
```bash
# Add findings to data/research/findings.json
# Then ingest and verify
python engine.py ingest
python engine.py verify-all
python engine.py audit LH-XXXX
python engine.py calculator-live LH-XXXX
```

## Files changed
- `engine.py` — added `calculator-live` command, `build_calculator_config()`
- `ui.html` — added Pipeline Board tab, renderPipeline() function
- `templates/calculator_template.html` — interactive calculator template
- `templates/demo_template.html` — interactive demo template (existing)
- `scripts/rewrite_outreach.py` — personalized outreach generator
- `data/research/findings.json` — added4 new findings + web_titles
- `data/leads/LH-0018..0021.json` —4 new verified, qualified leads
- `tests/test_core.py` — updated lead count assertion (17→21)
- `artifacts/calculators-live/` — 18 calculator HTML files
- `artifacts/demos-live/` — 18 demo HTML files

## Bugs fixed this sprint
- Duplicate-findings skipped during ingest (8 skipped this run — dedup working)
- Pipeline panel DOM node missing (script existed but no `<div id="panel-pipeline">`) — added
- Calculator-wiring for `cmd_calculator_live` in CLI dispatch — verified working

## What's ready for you when you return
1. **18 demo agents** — open and screen-record for your demo video
2. **18 ROI calculators** — show a lead their own numbers
3. **Pipeline board** — click to see your whole pipeline
4. **4 new qualified leads** with real contacts and verified websites
5. **9 personalized outreach drafts** ready for your approval

## Next sprint candidates
- Build a "proposal generator" that creates PDF proposals from lead data
- Add email templates for different outreach stages
- Wire `calculator-live` to dashboard button (like demo-live already is)
- Research more niches: salons, clinics, training institutes, e-commerce stores
- Add a "won/lost" summary stat to the dashboard header
