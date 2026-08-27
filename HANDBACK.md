# AI Lead Hunter — 3-Hour Sprint Handoff

**Date:** Thursday, August 27, 2026
**Agent:** ai-lead-hunter (autonomous sprint, full permission)
**Owner:** Fahad Ibrahim

---

## What was built

The **AI Lead Hunter** Revenue Acquisition OS is now a real, working, git-versioned system — not a specification. It lives at:

> **https://github.com/FahadIbrahim93/ai-lead-hunter**

(local clone: `~/ai-lead-hunter`)

It is a Python CLI orchestrator (`engine.py`) with JSON schemas, append-only data stores, acceptance tests, and full documentation. Every record validates. Every command is deterministic.

---

## System architecture

```
HUMAN OWNER
    │  approval / strategy / sales
    ▼
┌─────────────────┐
│  HERMES ORCHESTRATOR │  ← engine.py
└────────┬────────┘
    │
┌──────────────┬──────────────┬──────────────┐
▼              ▼              ▼
DISCOVERY     INTELLIGENCE    SALES PREP
   ...            ...             ...

Source of truth: data/leads → evidence → activity → outreach → artifacts
Slack #ai-lead-hunter: coordination only (not canonical storage)
```

## Run it

```bash
cd ~/ai-lead-hunter

python engine.py status       # system state + validation
python engine.py leads        # list all leads
python engine.py audit LH-0001   # DEEP_AUDIT a lead
python engine.py score LH-0001   # recompute score
python engine.py demo LH-0001    # write demo spec
python engine.py outreach LH-0001  # draft outreach (pending_approval)
python engine.py validate     # validate all records (exit 1 on error)
python -m pytest tests/ -v   # run acceptance tests
```

## What's in the repo

| Path | Purpose |
|---|---|
| `engine.py` | CLI orchestrator — the core engine. Run it. |
| `data/schemas/*.schema.json` | JSON schemas: Lead, Evidence, Activity, Outreach |
| `data/leads/LH-*.json` | Canonical lead records (immutable IDs) |
| `data/evidence/E-*.json` | Append-only evidence records |
| `data/activity/A-*.json` | Append-only activity log |
| `data/outreach/O-*.json` | Append-only outreach drafts (human approval gate) |
| `artifacts/demos/LH-*-demo.md` | Demo specs per lead |
| `tests/test_core.py` | 9 acceptance tests |
| `AGENTS.md` | Instructions for autonomous agent runs |
| `HERMES.md` | Control plane summary |
| `SYSTEM_SPEC.md` | Full specification |
| `RUNBOOK.md` | Day-to-day operations |
| `README.md` | Project overview |
| `.gitignore` | Python/pytest/IDE/OS artifacts |

## Current pipeline state

All 4 migrated leads are fully processed end-to-end:

| Lead | Business | Score | Tier | Status | Demo | Outreach |
|---|---|---|---|---|---|---|
| LH-0001 | Best Interior Design | 91 | A | QUALIFIED | ✓ | ✓ (O-0003) |
| LH-0002 | A.K. Developments Ltd. | 85 | A | QUALIFIED | ✓ | ✓ (O-0004) |
| LH-0003 | Mazada Group | 82 | B | QUALIFIED | ✓ | ✓ (O-0005) |
| LH-0004 | Hitech Inter Studio | 78 | B | QUALIFIED | ✓ | ✓ (O-0006) |

**System counts:** 4 leads / 37 evidence / 48 activity / 6 outreach drafts.
**Validation:** clean (exit 0).
**Tests:** 9/9 passing.

## Outreach drafts — your approval queue

Six outreach drafts are waiting in `data/outreach/`. Each is `pending_approval`. To send any of them:

1. Open the JSON in `data/outreach/`.
2. Set `status` to `"approved"`.
3. Set `human_approved_at` to the current ISO timestamp.
4. Send via the channel (WhatsApp by default).
5. After sending, set `status` to `"sent"` and `sent_at`.

### LH-0001 — Best Interior Design (highest priority, 91/A)

Draft (O-0003):
> Hi, this is Fahad from Hope Theory.
>
> I noticed no visible online booking or enquiry flow — customers can't request a quote digitally and Instagram-only presence means discovery depends on algorithmic reach, not owned pipeline — I build autonomous AI agents that handle exactly that kind of workload.
>
> For Best Interior Design, I'd suggest starting with a focused agent that automates deployment for interior design and decor.
>
> Happy to walk you through a 15-minute demo at your convenience. No commitment — just show you what it does.
>
> Best,
> Fahad

### LH-0002 — A.K. Developments Ltd. (85/A)

> I noticed project updates likely manual — buyers and investors want status, photos, payment milestones and sales enquiries across phone/visit/WhatsApp with no unified tracking — I build autonomous AI agents that handle exactly that kind of workload.
>
> For A.K. Developments Ltd., I'd suggest starting with a focused agent that automates deployment for real estate development.

### LH-0003 — Mazada Group (82/B)

> I noticed import/export workflow likely manual — documentation, supplier follow-up, shipment tracking and multi-channel enquiries (email, phone, WhatsApp) with no unified pipeline — I build autonomous AI agents that handle exactly that kind of workload.
>
> For Mazada Group, I'd suggest starting with a focused agent that automates deployment for import/export and trading.

### LH-0004 — Hitech Inter Studio (78/B)

> I noticed service business likely carries project intake friction — prospects request quotes, follow-ups get lost and no visible automated lead qualification or proposal generation from public presence — I build autonomous AI agents that handle exactly that kind of workload.
>
> For Hitech Inter Studio, I'd suggest starting with a focused agent that automates deployment for IT and software services.

## What you need to do when you return

1. **Review the 6 outreach drafts** in `data/outreach/`. Approve, revise, or skip each one.
2. **Send the approved ones.** The channel is WhatsApp by default. Update status to `sent` after sending.
3. **Track responses.** When a reply comes in, update the outreach record (`status: replied`, `response_at`, `response`) and the lead lifecycle.
4. **Record your demo video.** One demo video per lead is your next move — the demo specs in `artifacts/demos/` give you the structure (opening → live walkthrough → ROI framing → Q&A).

## What the system does NOT do yet (honest gaps)

- **Discovery jobs that call live APIs.** `engine.py` has the scaffolding (schemas, scoring, dedup, activity logging) but the actual discovery command that scrapes job boards / social / referrals is not yet wired to `web_search`/`web_extract`. That's the next big feature.
- **Live web audits.** The audit function currently reuses the pre-loaded pain signals from each lead's data file. A real audit would visit the business's website, Instagram, reviews, and competitors, and write fresh evidence.
- **Contact path verification.** Contact paths are recorded but not verified (no phone/email/WhatsApp confirmation).
- **Automated sending.** The human approval gate is real — nothing sends without you. That's by design.
- **Analytics.** No pipeline conversion dashboard, aging reports, or source attribution yet.
- **CI on GitHub.** No GitHub Actions workflow yet. You can add one later.

## How to add a new lead

```bash
# Option A — manual JSON (recommended for now)
# Create data/leads/LH-NNNN.json with required fields, then:
python engine.py audit LH-NNNN
python engine.py demo LH-NNNN
python engine.py outreach LH-NNNN

# Option B — via the CLI (interactive)
python engine.py add   # prompts for business_name, niche, geography, source
```

## How to extend the system

- **New discovery source:** Add a script in `scripts/` that calls `web_search`/`web_extract`, produces lead JSONs in `data/leads/`, and logs activity. Then `engine.py audit` picks them up.
- **New evidence kind:** Add to `data/schemas/evidence.schema.json` enum.
- **New lifecycle status:** Add to `data/schemas/lead.schema.json` enum and the lifecycle list in `SYSTEM_SPEC.md`.
- **New channel:** Add to `data/schemas/outreach.schema.json` enum.
- **CI:** Add `.github/workflows/ci.yml` that runs `python -m pytest tests/ -v` and `python engine.py validate` on push.

## File locations (absolute)

- Repo: `C:\Users\fhdib\ai-lead-hunter\`
- Engine: `C:\Users\fhdib\ai-lead-hunter\engine.py`
- Leads: `C:\Users\fhdib\ai-lead-hunter\data\leads\`
- Outreach: `C:\Users\fhdib\ai-lead-hunter\data\outreach\`
- Demos: `C:\Users\fhdib\ai-lead-hunter\artifacts\demos\`
- Tests: `C:\Users\fhdib\ai-lead-hunter\tests\test_core.py`
- GitHub: https://github.com/FahadIbrahim93/ai-lead-hunter

## Verification commands (run these if something looks wrong)

```bash
cd ~/ai-lead-hunter
python engine.py validate        # should exit 0
python -m pytest tests/ -v       # should be 9 passed
python engine.py status          # should show counts + "✓ All records validate"
python engine.py leads           # should list all 4 leads
```

## Next sprint priorities (your call)

1. Wire a real discovery job (job boards + social + competitor research) → new leads flow in automatically.
2. Real web audits per lead (visit website, Instagram, reviews, competitors) → fresh evidence, not just migrated placeholders.
3. Contact path verification (call/WhatsApp/email confirmation).
4. GitHub Actions CI (pytest + validate on push).
5. Pipeline analytics — conversion rate, aging, source attribution.
6. Build the actual demo agents (the AI agents themselves) for the top 2-3 leads so you have something live to show.

---

**Bottom line:** The system is real, it runs, it validates, the tests pass, and all 4 leads are fully audited + queued for your outreach approval. When you return, review the 6 drafts, send the ones you like, record your demo videos, and we iterate from there.
