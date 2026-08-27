# AGENTS.md — AI Lead Hunter

**For Hermes Agent autonomous runs.** Tells an agent what to do, what not to do, and how to report.

## Objective

Run the Revenue Acquisition OS: discover Bangladesh businesses with verified commercial pain, audit them, score them, build demos, draft outreach, and queue everything for human approval.

## Golden rules

1. **Never send external outreach without human approval.** Outreach drafts land in `data/outreach/` with status `pending_approval`. Only the human owner may approve and send.
2. **Never invent evidence.** Every pain signal must be traceable to a real source. Confidence ≤ 100. Low-confidence signals are flagged.
3. **Preserve existing data.** Do not overwrite or delete lead records. Append-only for evidence and activity.
4. **Validate before reporting success.** Run `python engine.py validate` after any write. If it fails, fix or flag — do not proceed.
5. **Deduplicate leads.** Before adding a new lead, check `data/leads/` and Slack #ai-lead-hunter for existing records with the same business name.
6. **Score honestly.** Do not inflate scores. The scoring function is deterministic; if a lead lacks signals, it stays in C/DISCOVERED.

## Run contract

| Command | Effect |
|---|---|
| `python engine.py status` | System state: counts + validation |
| `python engine.py leads` | List all leads in a table |
| `python engine.py audit <lead_id>` | DEEP_AUDIT: discover pain signals + evidence, score, qualify if ≥ 70 |
| `python engine.py score <lead_id>` | Recompute score + tier |
| `python engine.py demo <lead_id>` | Write demo spec to `artifacts/demos/` |
| `python engine.py outreach <lead_id>` | Draft outreach → `data/outreach/` with status `pending_approval` |
| `python engine.py validate` | Validate all records. Exit 1 on error. |

## Per-lead workflow

1. Lead appears → run `audit <lead_id>`.
2. Score ≥ 70 → QUALIFIED → run `demo` then `outreach`.
3. Score < 70 → stays DISCOVERED. Add evidence or park.
4. Outreach draft → report to human owner for approval.
5. After approval: send via approved channel, set status to `sent`.

## Channel authority

- **Research/automation:** Hermes agent (discovery, audit, scoring, demo, outreach drafting).
- **Human approval + sending:** Fahad Ibrahim. No agent may send on its own.

## Reporting

After any autonomous run, report: what was done (command + lead_id), results (score, tier, status, evidence count, outreach draft path), and anything needing human attention (pending approval, low-confidence evidence, missing contact paths).
