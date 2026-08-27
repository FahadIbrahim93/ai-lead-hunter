# RUNBOOK.md — AI Lead Hunter Day-to-Day Operations

## Quick start

```bash
cd ~/ai-lead-hunter
python engine.py status       # system state
python engine.py leads        # list leads
python engine.py validate     # check integrity
```

## Daily flow

1. **Check status.** `python engine.py status`. Look for pending approvals (outreach with status `pending_approval`).
2. **Review any pending outreach.** Open the draft in `data/outreach/`, approve or revise.
3. **Process new leads.** If discovery found new leads, add them and run `audit`.
4. **Build demos + outreach for qualified leads.** For each QUALIFIED lead without an outreach draft: `demo <id>` then `outreach <id>`.
5. **Validate.** Always `python engine.py validate` before ending the session.

## Per-lead deep dive

```bash
# Audit a lead
python engine.py audit LH-0001

# Re-score
python engine.py score LH-0001

# Build demo spec
python engine.py demo LH-0001

# Draft outreach
python engine.py outreach LH-0001

# Review
cat data/outreach/O-0002.json
cat artifacts/demos/LH-0001-demo.md
```

## Adding a lead manually

Edit or create `data/leads/LH-NNNN.json` with required fields, then run `audit`.

Required fields: `lead_id`, `business_name`, `discovered_at`, `source`, `lifecycle_status`, `score`.

## Approving an outreach

1. Open the outreach JSON in `data/outreach/`.
2. Set `status` to `approved`.
3. Set `human_approved_at` to the current ISO timestamp.
4. Send via the channel in the record.
5. After sending, set `status` to `sent` and `sent_at`.

Do NOT send without this approval step.

## Handling failures

- **Validation fails:** read the error, fix the offending record or flag it. Do not proceed with outbound actions until clean.
- **Audit produces no pain signals:** lead stays DISCOVERED. Add manual evidence or park.
- **Low-confidence evidence (< 60):** flag in the lead notes. Do not build a high-stakes demo on shaky evidence.
- **Missing contact path:** outreach draft uses a placeholder. Verify the contact path before approving.

## Cron / scheduled work (future)

Discovery jobs can run on a schedule to find new leads. Audit and outreach jobs run per-lead after human triage.

## Emergency rollback

Data is append-only. To reverse a bad decision:
- Set lifecycle status to a prior stage (e.g., QUALIFIED → DISCOVERED).
- Do NOT delete records. Append a note activity explaining the change.
