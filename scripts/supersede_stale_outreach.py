#!/usr/bin/env python3
"""
Mark older duplicate outreach drafts as `superseded` when a newer
`pending_approval` draft exists for the same lead.

This cleans up the case where a lead has multiple `pending_approval` drafts
(e.g. O-0001 + O-0032). The queue already picks the newest by outreach_id,
but the duplicates clutter the data.

Run:  python scripts/supersede_stale_outreach.py
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTREACH = REPO / "data" / "outreach"


def main() -> int:
    if not OUTREACH.exists():
        print("No outreach dir.")
        return 0

    by_lead: dict[str, list[tuple[str, dict]]] = {}
    for f in sorted(OUTREACH.glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        lid = rec.get("lead_id", "")
        by_lead.setdefault(lid, []).append((f.name, rec))

    superseded_count = 0
    for lid, drafts in by_lead.items():
        pending = [d for _, d in drafts if d.get("status") == "pending_approval"]
        if len(pending) < 2:
            continue  # only one or zero pending drafts — no cleanup needed
        # Find the newest by outreach_id desc
        pending.sort(key=lambda r: r.get("outreach_id", ""), reverse=True)
        newest = pending[0]
        older = pending[1:]
        for old in older:
            old_id = old.get("outreach_id")
            fpath = OUTREACH / f"{old_id}.json"
            old["status"] = "superseded"
            old["superseded_at"] = "2026-08-27T00:00:00+06:00"
            old["superseded_by"] = newest.get("outreach_id", "")
            fpath.write_text(
                json.dumps(old, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            superseded_count += 1
            print(f"✅ {old_id} → superseded (by {newest.get('outreach_id')}) for {lid}")

    print(f"\nTotal superseded: {superseded_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
