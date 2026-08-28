#!/usr/bin/env python3
"""
scripts/daily_refresh_status.py

Quick CLI for the human owner to see what daily_refresh produced
without running the engine.

Usage:
  python scripts/daily_refresh_status.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS = REPO / "data" / "runs"


def main() -> int:
    last = RUNS / "last_refresh.json"
    if not last.exists():
        print("No refresh has been run yet. Run `python scripts/daily_refresh.py`.")
        return 1
    s = json.loads(last.read_text(encoding="utf-8"))
    print("Last refresh:")
    print(f"  Started:    {s.get('started_at', '?')}")
    print(f"  Completed:  {s.get('completed_at', '?')}")
    print(f"  Status:     {s.get('status', '?')}")
    print(f"  Verified:   {s.get('verified', 0)}")
    print(f"  Stale:      {s.get('stale_flagged', 0)}")
    print(f"  Queue size: {s.get('queue_size', 0)}")
    print(f"  Issues:     {s.get('consistency_issues', 0)}")
    print(f"  Errors:     {len(s.get('errors', []))}")
    if s.get("errors"):
        for e in s["errors"]:
            print(f"    - {e}")
    print()
    # find today's digest
    today = (s.get("started_at") or "")[:10]
    digest = RUNS / f"{today}__digest.md"
    if digest.exists():
        print(f"Today's digest: {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
