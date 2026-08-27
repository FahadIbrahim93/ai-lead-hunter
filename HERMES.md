# AI Lead Hunter — Hermes Control Plane v2 (Local Implementation)

## Canonical architecture

```
HUMAN OWNER
    │  approval / strategy / sales
    ▼
┌─────────────────┐
│  HERMES ORCHESTRATOR │
└────────┬────────┘
    │
┌──────────────┬──────────────┬──────────────┐
▼              ▼              ▼
DISCOVERY     INTELLIGENCE    SALES PREP
Find businesses  Audit + evidence  Offer + demo
Deduplicate      Score + qualify   Outreach draft
    │              │              │
    └──────────────┼──────────────┘
                   ▼
            OPPORTUNITY RECORD
                   │
          ┌────────┴────────┐
          ▼                 ▼
     data/leads/      artifacts/
     (canonical)      (audits/demos/proposals)
```

## Source of truth hierarchy

1. `data/leads/` — canonical machine-readable lead records (immutable IDs)
2. `data/evidence/` — append-only evidence artifacts
3. `data/activity/` — append-only activity log
4. `data/outreach/` — append-only outreach drafts
5. `artifacts/` — generated audits, demos, proposals
6. Slack #ai-lead-hunter — coordination layer (not canonical storage)

## Lead lifecycle

DISCOVERED → AUDITED → QUALIFIED → OUTREACH_READY → CONTACTED → IN_CONVERSATION → WON / LOST
Terminal exception: DO_NOT_CONTACT

## Scoring

Score = 0-100 composite of:
- Commercial intensity (budget signals, price points, scale)
- Pain observability (public weaknesses, funnel gaps, credibility issues)
- Decision-maker accessibility (public contact paths, org size)
- Fit with Hope Theory offer surface

Tier bands:
- A: 85-100 — act today
- B: 70-84 — worth building
- C: 50-69 — monitor
- Below 50: revisit or discard

## Human approval gate

No external outreach leaves the system without a human-approved outreach record in `data/outreach/`.
The orchestrator may draft; only the human owner may release.
