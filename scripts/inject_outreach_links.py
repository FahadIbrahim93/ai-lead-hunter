#!/usr/bin/env python3
"""Inject real demo + calculator HTML paths into outreach drafts.
Replaces [Demo link will be inserted here] with the actual artifact path."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTREACH = ROOT / "data" / "outreach"
DEMO_DIR = ROOT / "artifacts" / "demos-live"
CALC_DIR = ROOT / "artifacts" / "calculators-live"

def inject(oid: str, lead_id: str, draft: str) -> str:
    demo_path = f"artifacts/demos-live/{lead_id}-demo-live.html"
    calc_path = f"artifacts/calculators-live/{lead_id}-calculator-live.html"
    demo_exists = (DEMO_DIR / f"{lead_id}-demo-live.html").exists()
    calc_exists = (CALC_DIR / f"{lead_id}-calculator-live.html").exists()

    replacements = []
    if demo_exists:
        replacements.append((f"[Demo link will be inserted here]",
            f"I've built a 60-second interactive demo specifically for {lead_id} — open {demo_path} to show it. No installation, just double-click."))
    if calc_exists:
        replacements.append((f"[Calculator link will be inserted here]",
            f"I've also built a quick ROI calculator — open {calc_path} and drag the sliders to see what you're losing each month."))

    for old, new in replacements:
        draft = draft.replace(old, new)

    # Also fix any leftover placeholder even if no artifact
    if "[Demo link will be inserted here]" in draft:
        draft = draft.replace("[Demo link will be inserted here]",
            "I've built a short interactive demo for you — happy to walk through it on a quick call.")
    if "[Calculator link will be inserted here]" in draft:
        draft = draft.replace("[Calculator link will be inserted here]",
            "I can also run a quick ROI calculation to show the numbers — let me know if you'd like to see it.")

    return draft

changed = 0
for f in sorted(OUTREACH.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    orig = d["draft"]
    new = inject(d["outreach_id"], d["lead_id"], orig)
    if new != orig:
        d["draft"] = new
        f.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        changed += 1
        print(f"✅ {d['outreach_id']} -> {d['lead_id']}: injected demo/calc paths")

print(f"\n✅ {changed} outreach drafts updated")
