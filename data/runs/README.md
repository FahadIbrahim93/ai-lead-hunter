# data/runs/

Operational artifacts from the daily_refresh cron.

## Files
- `YYYY-MM-DD__digest.md` — morning brief (human-readable).
- `queue-latest.txt` — the human approval queue, plain text.
- `last_refresh.json` — machine-readable summary of the most recent run.

## Cron wiring

To run unattended at 8:00 AM Bangladesh time every day, configure your
scheduler of choice. Examples:

### Windows Task Scheduler
```
schtasks /create /tn "ai-lead-hunter-daily" /tr "python C:\Users\fhdib\ai-lead-hunter\scripts\daily_refresh.py" /sc daily /st 08:00
```

### Cron-style (e.g. via a wrapper that runs the engine)
Run `python scripts/daily_refresh.py` and read the digest at
`data/runs/$(date +%F)__digest.md`.

## Exit codes
- 0 = clean (no errors, no consistency issues)
- 1 = run completed but consistency audit found issues
- 2 = run failed (alert the owner)
