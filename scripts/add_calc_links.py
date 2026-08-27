#!/usr/bin/env python3
"""Add calculator links to outreach drafts that have demos but no calculators."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTREACH = ROOT / "data" / "outreach"
CALC_DIR = ROOT / "artifacts" / "calculators-live"

added = 0
for f in sorted(OUTREACH.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    lead_id = d["lead_id"]
    if "calculators-live" in d["draft"]:
        continue
    calc_file = CALC_DIR / f"{lead_id}-calculator-live.html"
    if calc_file.exists():
        calc_line = (
            f"\n\nYou can also try the quick ROI calculator — open "
            f"artifacts/calculators-live/{lead_id}-calculator-live.html, "
            f"drag the sliders, and see what you're losing each month."
        )
        # Insert before the last signature line
        draft = d["draft"]
        sig = draft.rfind("\nBest,")
        if sig != -1:
            new_draft = draft[:sig] + calc_line + draft[sig:]
        else:
            new_draft = draft + calc_line
        d["draft"] = new_draft
        f.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        added += 1
        print(f"✅ {d['outreach_id']} -> {lead_id}: calculator link added")

print(f"\n✅ {added} drafts got calculator links")
