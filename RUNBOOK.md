# RUNBOOK — Day-to-Day Operations

## Daily loop (5 minutes)

```bash
cd ~/ai-lead-hunter
python engine.py status        # health check — must say "✓ All records validate"
python engine.py leads         # see the board
```

Or just double-click `START-DASHBOARD.bat` and look at the dashboard.

## Adding new leads

1. Research a business (web search). You need: **name, live website, niche**.
2. Add it to `data/research/findings.json` under `findings` (copy an existing entry).
3. Run `python engine.py ingest` — dedup is automatic (name + domain).
4. Run `python engine.py verify <lead_id>` — confirms the website is live and
   pulls real phone/email from the page.
5. Run `python engine.py audit <lead_id>` — scores and qualifies.

## Working a qualified lead

```bash
python engine.py demo LH-0010       # write the demo spec
python engine.py outreach LH-0010   # draft the message
```

Then: open the dashboard → Outreach Drafts → **Copy to Clipboard** → paste into
WhatsApp/email → **you send it**. Log the outcome by editing the outreach record's
`status` field (`pending_approval` → `approved` → `sent`).

## Weekly maintenance

- `python engine.py verify-all` — re-check all client websites are still live.
- `python -m pytest tests/ -q` — confirm the system is healthy (27 tests).
- `git add -A && git commit -m "..." && git push` — keep the repo current.

## Rules

- **Never send outreach without human approval.** Drafts only.
- **Never fabricate evidence.** Every pain signal must trace to a real source.
- **Internal ventures** (MARJAHANS, SNAPTRAP, JG Mart) are portfolio pieces —
  build them up, don't sell to them.
- If `validate` fails, fix the data before doing anything else.
