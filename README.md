# AI Lead Hunter — Revenue Acquisition OS

A local-first lead machine for selling AI agents to Bangladesh businesses.
Discovers real companies, verifies them live, audits their pain, scores them,
builds demo specs, and drafts outreach — with a human approval gate on every send.

## The pipeline

```
RESEARCH INBOX ──ingest──▶ LEADS ──verify──▶ VERIFIED ──audit──▶ QUALIFIED
   (findings.json)         (dedup)  (live HTTP)  (score)          │
                                                                   ▼
                                              DEMO SPEC ──▶ OUTREACH DRAFT
                                                              (human approves)
```

1. **Research** — real findings (business name + website + niche) go into
   `data/research/findings.json`.
2. **Ingest** — `python engine.py ingest` converts findings to leads,
   deduplicating by normalized name AND domain.
3. **Verify** — `python engine.py verify <id>` (or `verify-all`) does a live
   HTTP check of the website and extracts real phone numbers / emails from the page.
4. **Audit** — `python engine.py audit <id>` attaches pain signals, evidence,
   scores the lead, and qualifies it (score ≥ 70).
5. **Demo** — `python engine.py demo <id>` writes a demo spec.
6. **Outreach** — `python engine.py outreach <id>` drafts a message.
   **Nothing is ever sent automatically — a human approves and sends.**

## Quick start

```bash
cd ~/ai-lead-hunter
python engine.py status          # system state + validation
python engine.py leads           # list all leads
python engine.py research        # show the research inbox
python engine.py ingest          # ingest findings (dedup-safe)
python engine.py verify-all      # live-verify every client website
python engine.py audit LH-0010   # deep audit one lead
python engine.py demo LH-0010    # build a demo spec
python engine.py outreach LH-0010  # draft outreach
python engine.py validate        # schema integrity check
python -m pytest tests/ -q       # run the test suite (27 tests)
```

## Visual dashboard (no coding needed)

Double-click `START-DASHBOARD.bat` (or run `python dashboard.py`).
A browser opens at `http://localhost:8765` showing:

- **Stats** — client leads, qualified, Tier A, verified-live, awaiting approval
- **Client Leads** — score, tier, pain signals, real contacts, ✓ VERIFIED badge
- **My Ventures** — Fahad's own businesses (portfolio, not for sale)
- **Outreach Drafts** — copy-to-clipboard, human sends manually
- **Activity Log** — every action the system has taken

Buttons on the dashboard run the engine under the hood:
Discover, Ingest Research, Verify Websites, Validate, Re-Audit, Demo, Outreach.

## Data model

| Store | Path | Purpose |
|---|---|---|
| Leads | `data/leads/` | One JSON per lead (score, tier, pain, contacts, verified) |
| Evidence | `data/evidence/` | Append-only proof per lead |
| Activity | `data/activity/` | Append-only audit log of every action |
| Outreach | `data/outreach/` | Drafts, all `pending_approval` until a human acts |
| Research | `data/research/findings.json` | Candidate businesses awaiting ingest |
| Schemas | `data/schemas/` | JSON schemas — every record validates |
| Demos | `artifacts/demos/` | Demo spec per qualified lead |

Lead types: `client` (external business to sell to) vs `internal_venture`
(Fahad's own businesses — built with AI agents, used as portfolio demos).

## Scoring

0–100 composite: pain intensity (≤40) + offer clarity (20) + contact
accessibility (≤25) + niche commercial intensity (15).
Tier A ≥ 85, Tier B ≥ 70, Tier C ≥ 50. Qualification threshold: 70.

## Human approval gate

No external outreach leaves this system without explicit human approval.
Agents draft; only the owner approves and sends. This is enforced by design —
there is no send mechanism in the codebase at all.

## Docs

- `AGENTS.md` — how an autonomous agent runs the system
- `HERMES.md` — control plane summary
- `SYSTEM_SPEC.md` — full specification
- `RUNBOOK.md` — day-to-day operations

## License

Internal — Hope Theory.
