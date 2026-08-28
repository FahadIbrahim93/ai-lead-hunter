# Architecture — AI Lead Hunter

The 5-minute tour for an engineer or future agent who needs to understand
how this system works end-to-end.

## What it is, in one sentence

A local-first CLI + dashboard that turns raw Bangladesh business research
into **send-ready outreach packages** (interactive demo HTML + ROI
calculator HTML + WhatsApp draft) — nothing leaves the system without
human approval.

## The pipeline

```
┌──────────────────────┐
│ 1. RESEARCH  (manual)│
│ Find a real biz on the│
│ web. Add to research  │
│ inbox.                │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 2. INGEST  (dedupe)  │  data/research/findings.json
│ python engine.py     │  → data/leads/LH-NNNN.json
│        ingest        │  (canonical lead record)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 3. VERIFY  (live)    │  HTTP GET to the website.
│ python engine.py     │  Extracts phones/emails.
│        verify LH-... │  Writes E-NNNN evidence.
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 4. ENRICH  (deep)    │  Add 4-5 pain signals + offer
│ Manual or scripted.  │  surface to lead.pain_signals[].
│ Either via           │  Optional: business_profile block
│ enrich_research_     │  (the A+ differentiator).
│ leads.py or inline.  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 5. AUDIT + SCORE      │  python engine.py audit LH-...
│ Deterministic score  │  → 0-100 score + Tier A/B/C
│ from pain_signals,   │  → may set lifecycle to QUALIFIED
│ contact_paths,       │     (if score >= 70)
│ evidence, scale.     │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 6. BUILD ARTIFACTS    │  python engine.py demo-live LH-...
│   - interactive demo │  python engine.py calculator-live LH-...
│   - ROI calculator   │  → artifacts/demos-live/LH-NNNN-...html
│   - outreach draft   │  → artifacts/calculators-live/...
│                      │  → data/outreach/O-NNNN.json (pending_approval)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 7. HUMAN APPROVAL     │  You read the draft. You copy.
│ YOU open dashboard   │  You paste into WhatsApp.
│ OR read O-NNNN.json  │  You send from your phone.
│ and send manually.   │  Then: engine.py sent O-...
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 8. LIFECYCLE          │  sent → IN_CONVERSATION
│ python engine.py     │  reply received → IN_CONVERSATION
│   reply O-...        │  won → WON 🎉
│   won O-...          │  lost → LOST
│   lost O-...         │
└──────────────────────┘
```

## Source-of-truth hierarchy

There is exactly one canonical record per concept. The other records
reference it by ID.

| Concept | Canonical location | Append-only? |
|---|---|---|
| Lead | `data/leads/LH-NNNN.json` | Mutate in place (state changes) |
| Evidence | `data/evidence/E-NNNN.json` | YES — append-only |
| Activity | `data/activity/A-NNNN.json` | YES — append-only |
| Outreach | `data/outreach/O-NNNN.json` | Mutate (status transitions) |
| Demo HTML | `artifacts/demos-live/LH-NNNN-demo-live.html` | Generated, regenerable |
| Calculator HTML | `artifacts/calculators-live/LH-NNNN-calculator-live.html` | Generated, regenerable |
| Research inbox | `data/research/findings.json` | Append-only |

**If you can't find a record, you don't have it. Don't invent it.**

## Append-only means: never delete A- or E- records

Evidence and activity records are the audit trail. If you think one is
wrong, append a new one that supersedes it. Never edit or delete.

## Lead lifecycle

```
DISCOVERED → AUDITED → QUALIFIED → OUTREACH_READY → CONTACTED
                                                      → IN_CONVERSATION → WON
                                                      → LOST
[any state] → DO_NOT_CONTACT (terminal exception)
```

Transitions:
- `audit` (score ≥ 70) sets `QUALIFIED`
- `outreach` sets `OUTREACH_READY`
- `sent` (you marked it sent) sets `CONTACTED`
- `reply` (you logged a reply) sets `IN_CONVERSATION`
- `won` / `lost` are terminal

## Scoring

Composite 0-100 from:
- Commercial intensity (pricing, scale, client roster)
- Pain observability (public weaknesses, missing automation)
- Decision-maker accessibility (real phones, emails, WhatsApp)
- Verification (live HTTP 200, contact extraction worked)
- Evidence (number and quality of E- records attached)

Tier bands:
- A (85-100): act today
- B (70-84): worth building
- C (50-69): monitor
- D (below 50): revisit or discard

`cmd_status` now exposes a **Sales view** row that filters out
`internal_venture` leads so the Tier A headline isn't inflated.

## File layout

```
ai-lead-hunter/
├── engine.py                   ← CLI orchestrator (single source of CLI behavior)
├── dashboard.py                ← local web server, port 8765
├── ui.html                     ← dashboard UI
├── data/
│   ├── leads/LH-NNNN.json     ← 31 lead records
│   ├── outreach/O-NNNN.json   ← 31 draft records
│   ├── activity/A-NNNN.json   ← 1,745 audit trail records
│   ├── evidence/E-NNNN.json   ← 410 verification records
│   ├── research/findings.json  ← research inbox
│   └── schemas/*.schema.json  ← JSON Schema validators
├── artifacts/
│   ├── demos-live/             ← 31 standalone HTML demos
│   └── calculators-live/       ← 31 standalone HTML calculators
├── templates/                  ← demo + calculator HTML templates
├── tests/                      ← 29 tests (test_core, test_v2)
├── scripts/                    ← one-off scripts (enrich, inject, rewrite)
├── docs/                       ← this file + HOW_TO_ADD_A_LEAD + DECISIONS
└── .github/workflows/ci.yml    ← status + tests on push
```

## The 3 outputs that actually close deals

Every qualified lead carries these 3 artifacts:

1. **Interactive demo** — `artifacts/demos-live/LH-NNNN-demo-live.html`
   - Standalone HTML, double-click to open, no server needed
   - Personalised: business name, services, pain signals, contacts
   - Walks a prospect through an intake conversation

2. **ROI calculator** — `artifacts/calculators-live/LH-NNNN-calculator-live.html`
   - Standalone HTML, sliders for enq/miss/value/staff/hours
   - Niche-specific preset (dental=120 enq, bakery=150 enq, etc.)
   - Shows monthly loss + annual savings in ৳

3. **Outreach draft** — `data/outreach/O-NNNN.json`
   - WhatsApp-ready, niche-specific offer
   - Includes both demo + calculator HTML paths
   - All start as `pending_approval` — **you send, not the system**

## Human approval gate (why the system will not send for you)

The system is built to **never**:
- Send an outreach message on its own
- Mark an outreach as `sent` without your action
- Modify an outreach after you've marked it `sent`
- Delete an A- or E- record (audit trail integrity)

The only commands that move the lifecycle forward are:
- `engine.py sent O-NNNN` — you confirm you sent it
- `engine.py reply O-NNNN "..."` — you log a reply you received
- `engine.py won O-NNNN` / `lost O-NNNN` — you close the deal

If you find an agent or a script that does any of these without your
explicit invocation, that's a bug — file it.

## How to extend

### Add a new niche offer
Edit `engine.py` → `NICHE_OFFERS` list. Each entry is:
```python
(("keyword1", "keyword2"), "an AI agent that <verb> <thing>...")
```
The keyword check is case-insensitive substring against the lead's
`niche` field. After editing, re-run `python engine.py outreach <lead_id>`
for any drafts that should pick up the new mapping.

### Add a new calculator preset
Edit `engine.py` → `build_calculator_config()` → `preset_map`.
Each entry is `(niche_keyword, {enq, miss, value, staff, hours})`.

### Add a new lead type
Edit `data/schemas/lead.schema.json` → `lead_type.enum`.
Then update `cmd_leads` to render the new type, and `cmd_status` sales
view if you want it to count.

## Why append-only for evidence/activity

- **Audit trail.** You can prove what happened, when, to whom.
- **Replay.** A future script can rebuild lead state from activity alone.
- **Compliance.** If a lead ever asks "why did you contact me?" you have
  the chain of evidence and the activity that led to the outreach.
- **Debugging.** When something goes wrong (wrong number sent, wrong
  business profiled), the trail tells you which step misfired.

If you want to "correct" a record, append a new one. Don't mutate the
old one. The honest history is more useful than a sanitized one.
