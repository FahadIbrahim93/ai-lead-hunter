# SYSTEM_SPEC.md — AI Lead Hunter Control Plane v2

## 1. Executive definition

AI Lead Hunter is a revenue acquisition system, not a generic lead scraper. Its primary objective is to discover Bangladesh businesses with verified commercial pain, convert that pain into a specific high-value offer, produce evidence-backed sales assets, prepare personalized outreach, and move qualified opportunities toward human-approved conversations and revenue.

Target initial market: Bangladesh businesses with:
- High-ticket or high-margin products/services
- Existing public digital/social presence
- Observable website, funnel, enquiry, credibility, follow-up, or operational weaknesses
- A plausible decision-maker path
- A service opportunity that can realistically be sold by Hope Theory

Initial revenue thesis: prioritize opportunities capable of supporting roughly $100–$500+ project value rather than maximizing raw lead count.

North-star metric: qualified opportunities converted into revenue.

## 2. Current state

What exists now (post-bootstrap):
- `engine.py` — deterministic CLI orchestrator with status / leads / audit / score / demo / outreach / validate commands.
- `data/schemas/` — JSON schemas for Lead, Evidence, Activity, Outreach. All records validate.
- `data/leads/` — 4 canonical machine-readable leads (LH-0001..LH-0004) with scores, tiers, pain signals, evidence refs, and contact paths.
- `data/evidence/` — append-only evidence records with source URLs, summaries, and confidence.
- `data/activity/` — append-only activity log recording every action the system takes.
- `data/outreach/` — append-only outreach drafts with channel, draft text, status, and human approval gate.
- `artifacts/demos/` — demo specs per lead.
- `tests/test_core.py` — 9 acceptance tests covering status, leads, schemas, validation pass/fail, and ID format.
- `AGENTS.md` — agent operating instructions.

Critical weaknesses already fixed by this implementation:
1. Specification-heavy but execution-light → resolved: deterministic CLI, schemas, tests, run contract.
2. Slack as temporary data store → resolved: canonical `data/leads/` with immutable IDs + append-only evidence/activity.
3. Four leads not machine-readable → resolved: LH-0001..0004 migrated with full evidence.
4. No formal discovery strategy matrix → partially resolved: niche × geography × pain × offer × evidence thresholds encoded in scoring.
5. No hard definition of outreach-ready lead → resolved: score ≥ 70 + QUALIFIED status + demo built + outreach drafted.
6. No artifact naming/versioning contract → resolved: `artifacts/demos/<lead_id>-demo.md`, `data/outreach/O-NNNN.json`.
7. No explicit retry/failure/stale/duplicate/confidence protocol → resolved: AGENTS.md Section 6 + confidence flags + dedup rule.
8. Research vs external communication authority → resolved: human approval gate on outreach.

Remaining gaps for future work:
- Discovery jobs that actually call web_search / web_extract to find new leads.
- Real web audits for each lead (public presence review, funnel walk, competitor scan).
- Contact path verification (phone/email/WhatsApp confirmation).
- Human-in-the-loop on approval (no automated sending).
- Analytics: pipeline conversion rates, lead source attribution, aging reports.

## 3. Lead lifecycle

DISCOVERED → AUDITED → QUALIFIED → OUTREACH_READY → CONTACTED → IN_CONVERSATION → WON / LOST
Terminal exception: DO_NOT_CONTACT

- DISCOVERED: lead exists, no audit run yet.
- AUDITED: audit completed, evidence collected.
- QUALIFIED: score ≥ 70.
- OUTREACH_READY: demo built + outreach drafted.
- CONTACTED: outreach sent.
- IN_CONVERSATION: reply received, active discussion.
- WON: deal closed.
- LOST: explicit rejection or decay.
- DO_NOT_CONTACT: owner decision to stop pursuing.

## 4. Scoring

Score = 0-100 composite:
- Pain signals intensity: len(pain_signals) × 10, capped at 40.
- Offer clarity: 20 if offer_surface non-empty, else 0.
- Contact accessibility: len(contact_paths) × 15, capped at 25.
- Niche commercial intensity: +15 if niche matches high-value list (real estate, construction, interior, jewelry, import, export, manufacturing).

Tier bands:
- A: 85-100 — act today.
- B: 70-84 — worth building.
- C: 50-69 — monitor.
- Below 50: revisit or discard.

## 5. Evidence rules

- Every pain signal must have a corresponding evidence record.
- Evidence kinds: website, social, review, operational, financial, competitive, other.
- Confidence is 0-100. Signals below 60 are flagged.
- Evidence is append-only. Do not edit or delete.
- Each evidence record references its lead_id.

## 6. Outreach rules

- Outreach drafts are written by the agent, status = `pending_approval`.
- Human owner must approve before sending.
- Channels: email, whatsapp, linkedin, x, phone, slack, in_person.
- Outreach is append-only. Do not edit a sent outreach.
- Outreach records are never deleted.

## 7. Source of truth hierarchy

1. `data/leads/` — canonical machine-readable lead records.
2. `data/evidence/` — append-only evidence.
3. `data/activity/` — append-only activity log.
4. `data/outreach/` — append-only outreach drafts.
5. `artifacts/` — generated audits, demos, proposals.
6. Slack #ai-lead-hunter — coordination layer, not canonical storage.

## 8. Directory layout

```
ai-lead-hunter/
├── engine.py              # CLI orchestrator
├── AGENTS.md              # agent operating instructions
├── HERMES.md              # control plane summary
├── SYSTEM_SPEC.md         # this file
├── RUNBOOK.md             # day-to-day operations
├── README.md              # project overview
├── data/
│   ├── schemas/           # JSON schemas (lead, evidence, activity, outreach)
│   ├── leads/             # LH-NNNN.json — canonical lead records
│   ├── evidence/          # E-NNNN.json — append-only evidence
│   ├── activity/          # A-NNNN.json — append-only activity log
│   └── outreach/          # O-NNNN.json — append-only outreach drafts
├── artifacts/
│   ├── audits/            # per-lead audit artifacts (future)
│   ├── demos/             # <lead_id>-demo.md — demo specs
│   └── proposals/         # per-lead proposal drafts (future)
└── tests/
    └── test_core.py       # acceptance tests
```

## 9. Adding a new lead

1. Create `data/leads/LH-NNNN.json` with required fields.
2. Add discovery activity record.
3. Run `python engine.py audit LH-NNNN`.
4. If qualified, run `demo` then `outreach`.
5. Validate with `python engine.py validate`.

Lead IDs are sequential: LH-0001, LH-0002, ... generated by the engine's `next_id` helper.

## 10. Acceptance criteria

- `python engine.py validate` exits 0 with all records valid.
- `python -m pytest tests/test_core.py -v` passes all tests.
- `python engine.py leads` lists all leads with scores and tiers.
- `python engine.py audit LH-0001` produces a qualified lead with evidence and activity records.
- `python engine.py demo LH-0001` produces a demo spec artifact.
- `python engine.py outreach LH-0001` produces a pending_approval outreach draft.
