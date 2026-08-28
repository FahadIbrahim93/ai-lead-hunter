#!/usr/bin/env python3
"""
scripts/daily_refresh.py

Daily unattended lead-refresh pass. Designed to run via cron.

What it does:
  1. Re-verifies every client lead with a website (live HTTP check + contact
     extraction). Updates `verified` / `verified_at` and writes a `verified`
     activity record.
  2. Flags any lead whose last verification is older than 14 days
     (stale_lead = true in a new activity record).
  3. Regenerates the human-approval queue and writes it to
     data/runs/queue-latest.txt and data/runs/digest-latest.md so the
     owner can read it without booting the engine.
  4. Runs the outreach consistency audit and appends a summary to the
     digest.

Output:
  data/runs/YYYY-MM-DD__digest.md   (human-readable, the morning brief)
  data/runs/queue-latest.txt        (just the queue, easy to skim)
  data/runs/last_refresh.json       (machine-readable summary)

Exit codes:
  0 = clean, no issues
  1 = run completed but consistency audit found issues
  2 = run failed (caller should alert)

Append-only activity is preserved on every verified_lead and stale_lead event.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINE = REPO / "engine.py"
RUNS = REPO / "data" / "runs"
RUNS.mkdir(parents=True, exist_ok=True)

# Configurable
STALE_DAYS = 14
TIMEOUT_PER_REQUEST = 12  # seconds


def run_python(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE)] + args,
        cwd=REPO, capture_output=True, text=True, timeout=600,
    )


def main() -> int:
    started_at = datetime.now(timezone.utc)
    summary = {
        "started_at": started_at.isoformat(),
        "completed_at": None,
        "status": "running",
        "verified": 0,
        "stale_flagged": 0,
        "queue_size": 0,
        "consistency_issues": 0,
        "errors": [],
    }

    # 1) Verify all leads (re-checks every client with a website).
    print("Step 1: live verification pass", flush=True)
    verify = run_python(["verify-all"])
    if verify.returncode != 0:
        summary["errors"].append(f"verify-all failed: {verify.stderr[:200]}")
    else:
        # parse "   ✓ LIVE ..." lines
        live_count = verify.stdout.count("LIVE (HTTP 200)")
        failed_count = verify.stdout.count("FAILED")
        summary["verified"] = live_count
        summary["verify_failed"] = failed_count
        print(f"  verified {live_count}, failed {failed_count}", flush=True)

    # 2) Flag stale leads (last verified > STALE_DAYS ago)
    print(f"Step 2: stale-lead sweep (>{STALE_DAYS} days)", flush=True)
    leads_dir = REPO / "data" / "leads"
    cutoff = started_at - timedelta(days=STALE_DAYS)
    stale_count = 0
    for lf in sorted(leads_dir.glob("LH-*.json")):
        lead = json.loads(lf.read_text(encoding="utf-8"))
        if lead.get("lead_type") == "internal_venture":
            continue
        if not lead.get("website"):
            continue
        v_at = lead.get("verified_at", "")
        if not v_at:
            # Never verified -> write a stale event
            _write_stale_event(lead["lead_id"], "never_verified")
            stale_count += 1
            continue
        try:
            v_dt = datetime.fromisoformat(v_at.replace("Z", "+00:00"))
        except Exception:
            continue
        if v_dt < cutoff:
            _write_stale_event(lead["lead_id"], f"verified {int((started_at - v_dt).total_seconds() // 86400)}d ago")
            stale_count += 1
    summary["stale_flagged"] = stale_count
    print(f"  flagged {stale_count} stale", flush=True)

    # 3) Regenerate the queue and write to disk
    print("Step 3: build approval queue", flush=True)
    q = run_python(["queue", "25"])
    if q.returncode != 0:
        summary["errors"].append(f"queue failed: {q.stderr[:200]}")
    else:
        (RUNS / "queue-latest.txt").write_text(q.stdout, encoding="utf-8")
        # count "#N  LH-" headers
        queue_size = sum(1 for ln in q.stdout.splitlines() if ln.startswith("#") and " LH-" in ln)
        summary["queue_size"] = queue_size
        print(f"  queue size: {queue_size}", flush=True)

    # 4) Run consistency audit
    print("Step 4: outreach consistency audit", flush=True)
    audit = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "audit_outreach_consistency.py")],
        cwd=REPO, capture_output=True, text=True, timeout=120,
    )
    audit_text = audit.stdout
    summary["consistency_issues"] = audit_text.count("Found ") and _parse_int(audit_text, "Found ", " inconsistency")
    summary["consistency_issues"] = summary["consistency_issues"] or 0

    # 5) Finalize status BEFORE writing the digest so the digest reflects truth
    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    summary["status"] = "clean" if not summary["errors"] and not summary["consistency_issues"] else "issues"

    # 6) Write the human-readable digest
    print("Step 5: write digest", flush=True)
    today = started_at.strftime("%Y-%m-%d")
    digest_path = RUNS / f"{today}__digest.md"
    digest_path.write_text(_format_digest(summary, q.stdout, audit_text), encoding="utf-8")
    (RUNS / "last_refresh.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"\nDone. status={summary['status']}  errors={len(summary['errors'])}  issues={summary['consistency_issues']}")
    return 0 if summary["status"] == "clean" else 1


def _parse_int(text: str, prefix: str, suffix: str) -> int:
    try:
        i = text.index(prefix) + len(prefix)
        j = text.index(suffix, i)
        return int(text[i:j].strip())
    except (ValueError, IndexError):
        return 0


def _write_stale_event(lead_id: str, reason: str) -> None:
    """Append an activity record flagging a lead as stale. Append-only."""
    act_dir = REPO / "data" / "activity"
    existing = sorted(act_dir.glob("A-*.json"))
    last_n = max(int(f.stem.split("-")[1]) for f in existing)
    aid = f"A-{last_n + 1:04d}"
    rec = {
        "activity_id": aid,
        "lead_id": lead_id,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "actor": "hermes.cron",
        "action": "stale_lead_flagged",
        "resource": "scripts/daily_refresh.py",
        "detail": f"Stale-lead flag: {reason}. Re-verify or refresh research.",
    }
    (act_dir / f"{aid}.json").write_text(
        json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _format_digest(summary: dict, queue_text: str, audit_text: str) -> str:
    today = summary["started_at"][:10]
    body = []
    body.append(f"# Daily Lead-Hunter Digest — {today}\n")
    body.append(f"- Started: `{summary['started_at']}`")
    body.append(f"- Completed: `{summary.get('completed_at', '—')}`")
    body.append(f"- Status: **{summary['status']}**\n")

    body.append("## Verification pass")
    body.append(f"- Live websites re-verified: **{summary.get('verified', 0)}**")
    body.append(f"- Failed: **{summary.get('verify_failed', 0)}**")
    body.append(f"- Stale leads flagged: **{summary.get('stale_flagged', 0)}**\n")

    body.append("## Queue")
    body.append(f"- Pending outreach drafts: **{summary.get('queue_size', 0)}**")
    body.append("- See `data/runs/queue-latest.txt` for the full list, or run:")
    body.append("  ```\n  python engine.py queue 10\n  ```\n")

    body.append("## Outreach consistency audit")
    if summary.get("consistency_issues"):
        body.append(f"- ⚠ **{summary['consistency_issues']} inconsistency(ies) found**")
        body.append("- Re-run: `python scripts/audit_outreach_consistency.py`")
    else:
        body.append("- ✓ Clean.")
    body.append("")

    body.append("---\n")
    body.append("## Approval queue (top 5)\n")
    body.append("```")
    # show first 5 entries from the queue
    kept = []
    in_row = False
    row_lines = 0
    for ln in queue_text.splitlines():
        if ln.startswith("#") and " LH-" in ln:
            if kept and row_lines >= 4:
                break
            kept.append(ln)
            row_lines = 0
            in_row = True
        elif in_row:
            if ln.startswith("-" * 5):
                kept.append("")  # separator
                in_row = False
            else:
                kept.append(ln)
                row_lines += 1
    body.append("\n".join(kept[:60]))
    body.append("```\n")

    body.append("---\n")
    body.append("Run by `scripts/daily_refresh.py` · cron: see `data/runs/README.md`\n")
    return "\n".join(body)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(2)
