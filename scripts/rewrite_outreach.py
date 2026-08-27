#!/usr/bin/env python3
"""Rewrite outreach drafts with personalized evidence + demo CTA."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEADS = ROOT / "data" / "leads"
OUTREACH = ROOT / "data" / "outreach"

# Map lead_id -> outreach_id
OUTREACH_MAP = {
    "LH-0001": "O-0001",
    "LH-0002": "O-0002",
    "LH-0003": "O-0003",
    "LH-0004": "O-0004",
    "LH-0005": "O-0005",
}

def rewrite_outreach(lead_id: str, outreach_id: str):
    lead = json.loads((LEADS / f"{lead_id}.json").read_text(encoding="utf-8"))
    outreach_path = OUTREACH / f"{outreach_id}.json"
    outreach = json.loads(outreach_path.read_text(encoding="utf-8"))
    
    name = lead["business_name"]
    pain = lead["pain_signals"][0] if lead["pain_signals"] else "operational inefficiency"
    niche = lead.get("niche", "your industry")
    website = lead.get("website", "")
    score = lead.get("score", 0)
    
    # Personalized draft
    draft = f"""Hi, this is Fahad from Hope Theory.

I was researching {name} and noticed something that caught my attention: {pain.lower()}.

I build AI agents that solve exactly this kind of problem — automated intake, instant responses, and zero missed leads. For a business like yours in {niche}, this typically means:
• 24/7 enquiry handling (no more missed calls)
• Automatic lead qualification (saves your team hours)
• Instant booking/consultation scheduling

I've built a quick interactive demo specifically for {name} so you can see exactly how it would work for your clients. It takes 2 minutes to try:

[Demo link will be inserted here]

Would you be open to a 15-minute call this week to walk through it? I can show you the demo live and answer any questions.

Best,
Fahad Ibrahim
Hope Theory
"""
    
    outreach["draft"] = draft.strip()
    outreach["status"] = "pending_approval"
    outreach_path.write_text(json.dumps(outreach, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ Rewrote {outreach_id} for {name}")

if __name__ == "__main__":
    for lead_id, outreach_id in OUTREACH_MAP.items():
        rewrite_outreach(lead_id, outreach_id)
    print("\nDone — all outreach drafts rewritten with personalized evidence.")
