#!/usr/bin/env python3
"""
scripts/audit_outreach_consistency.py

Cross-checks data/outreach/*.json against data/activity/*.json
and reports inconsistencies. Does NOT mutate any data — read-only.

The activity log is the canonical source of truth for what really
happened. Outreach JSON files can drift (test runs, rollbacks, manual
edits). The lead's lifecycle_status is also cross-checked against
the latest status_changed activity.

Run:
  python scripts/audit_outreach_consistency.py
Exit 0 if clean, exit 1 if inconsistencies found.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "outreach"
ACT_DIR = ROOT / "data" / "activity"
LEADS = ROOT / "data" / "leads"


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def latest_status(lead_id: str) -> tuple[str, str, str]:
    """Return (latest_status, latest_actor, activity_filename) for this lead
    by walking activity records in filename order. Filename is monotonic
    (A-NNNN.json) so this is effectively chronological."""
    latest = None
    for f in sorted(ACT_DIR.glob("A-*.json")):
        rec = load(f)
        if rec.get("lead_id") != lead_id:
            continue
        action = rec.get("action", "")
        if action in ("status_changed", "outreach_sent", "reply_received"):
            latest = (rec.get("detail", ""), rec.get("actor", ""), f.name)
    return latest if latest else ("", "", "")


def latest_outreach_event(outreach_id: str) -> tuple[str, str, str]:
    """Return (latest_action, latest_actor, activity_filename) for this outreach id."""
    latest = None
    for f in sorted(ACT_DIR.glob("A-*.json")):
        rec = load(f)
        if outreach_id not in rec.get("detail", ""):
            continue
        if rec.get("action") not in ("outreach_sent", "reply_received"):
            continue
        latest = (rec.get("action", ""), rec.get("actor", ""), f.name)
    return latest if latest else ("", "", "")


def main() -> int:
    issues = []

    # 1) Check every outreach file against the activity log
    for f in sorted(OUT_DIR.glob("O-*.json")):
        rec = load(f)
        oid = rec.get("outreach_id", f.stem)
        status = rec.get("status", "?")
        sent_at = rec.get("sent_at", "")
        response = rec.get("response", "")

        # Find related activity records
        sent_act = None
        reply_act = None
        for af in sorted(ACT_DIR.glob("A-*.json")):
            a = load(af)
            if oid in a.get("detail", "") and a.get("action") == "outreach_sent":
                sent_act = a
            if oid in a.get("detail", "") and a.get("action") == "reply_received":
                reply_act = a

        # Inconsistency: status=pending but sent_at is set
        if status == "pending_approval" and sent_at:
            issues.append(
                f"OUTREACH {oid} (lead {rec.get('lead_id')}): status=pending_approval "
                f"but sent_at='{sent_at}' and response='{response[:40] if response else ''}' — "
                f"activity log shows it was actually sent (see {sent_act['activity_id'] if sent_act else '?'})"
            )
        # Inconsistency: status=sent but no sent activity
        if status == "sent" and not sent_act:
            issues.append(
                f"OUTREACH {oid} (lead {rec.get('lead_id')}): status=sent but no outreach_sent activity record"
            )

    # 2) Check every lead's lifecycle_status against the latest status activity
    for lf in sorted(LEADS.glob("LH-*.json")):
        lead = load(lf)
        lid = lead.get("lead_id", lf.stem)
        current = lead.get("lifecycle_status", "?")
        latest_detail, latest_actor, latest_file = latest_status(lid)

        # Parse latest terminal status from detail
        terminal_map = {
            "WON": "WON",
            "LOST": "LOST",
            "CONTACTED": "CONTACTED",
            "IN_CONVERSATION": "IN_CONVERSATION",
            "OUTREACH_READY": "OUTREACH_READY",
            "QUALIFIED": "QUALIFIED",
            "AUDITED": "AUDITED",
            "DISCOVERED": "DISCOVERED",
        }
        expected = None
        for status_name in terminal_map:
            if status_name in latest_detail:
                expected = status_name
                break

        if expected and current != expected:
            issues.append(
                f"LEAD {lid} ({lead.get('business_name', '')}): current status='{current}' "
                f"but latest activity ({latest_file}) shows '{expected}' "
                f"(detail: '{latest_detail[:60]}')"
            )

    # 3) Report
    print(f"Outreach / lead consistency audit")
    print("=" * 70)
    if not issues:
        print("✓ All outreach and lead records are consistent with the activity log.")
        print()
        print("This script is read-only. It does not modify any data.")
        return 0

    print(f"Found {len(issues)} inconsistency(ies):\n")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    print()
    print("Recommended actions:")
    print("  - For each 'pending_approval but sent_at' issue: re-evaluate")
    print("    whether the lead was actually sent. If yes, set status to 'sent'")
    print("    via 'python engine.py sent <oid>'. If the activity log is")
    print("    wrong (e.g. test artifact), add a new activity record flagging it.")
    print("  - For each 'lead status mismatch' issue: check the activity log")
    print("    to see which is correct. Update the lead JSON if the activity")
    print("    is correct (append a 'corrected_status' activity record).")
    print()
    print("This script is read-only. It does not modify any data.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
