# AI Lead Hunter

Revenue acquisition system for Hope Theory — discovers Bangladesh businesses with verified commercial pain, audits them, scores them, builds demos, drafts outreach, and queues everything for human approval.

## What it does

- Discovers leads from job boards, social, referrals, competitor research.
- Runs DEEP_AUDIT per lead: discovers pain signals, collects evidence, scores, and qualifies.
- Builds a demo spec for each qualified lead.
- Drafts human-ready outreach (WhatsApp/email/LinkedIn) with a human approval gate.
- Maintains canonical, append-only data: leads, evidence, activity, outreach.

## Quick start

```bash
cd ~/ai-lead-hunter
python engine.py status       # system state
python engine.py leads        # list leads
python engine.py audit LH-0001   # run a deep audit
python engine.py demo LH-0001    # write a demo spec
python engine.py outreach LH-0001  # draft outreach
python engine.py validate    # check integrity
python -m pytest tests/ -v   # run tests
```

## Current state

- 4 leads migrated from Slack into canonical data: LH-0001 (Best Interior Design, 91/A, QUALIFIED), LH-0002 (A.K. Developments Ltd., 85/A), LH-0003 (Mazada Group, 82/B), LH-0004 (Hitech Inter Studio, 78/B).
- LH-0001 has a full end-to-end artifact: audit, demo spec, and outreach draft.
- All records validate against JSON schemas.
- 9 acceptance tests passing.

## Architecture

See `SYSTEM_SPEC.md` for the full spec. In brief:

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
   ...            ...             ...
```

Source of truth: `data/leads/` → `data/evidence/` → `data/activity/` → `data/outreach/` → `artifacts/`. Slack is coordination only.

## Lead lifecycle

DISCOVERED → AUDITED → QUALIFIED → OUTREACH_READY → CONTACTED → IN_CONVERSATION → WON / LOST (plus DO_NOT_CONTACT terminal).

## Scoring

0-100 composite of pain signal intensity, offer clarity, contact accessibility, and niche commercial intensity. Tier A ≥ 85, B ≥ 70, C ≥ 50.

## Human approval gate

No external outreach leaves the system without a human-approved outreach record. Agents may draft; only the owner may approve and send.

## Docs

- `AGENTS.md` — how an autonomous agent should run the system.
- `HERMES.md` — control plane summary.
- `SYSTEM_SPEC.md` — full specification.
- `RUNBOOK.md` — day-to-day operations.

## License

Internal — Hope Theory.
