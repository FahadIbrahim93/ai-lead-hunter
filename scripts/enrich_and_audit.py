#!/usr/bin/env python3
"""Enrich LH-0022..0025 with pain signals, then audit + score them.
Uses real data from web_extract + web_search research notes."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
LEADS = ROOT / "data" / "leads"

enrichments = {
    "LH-0022": {
        "pain_signals": [
            "Custom wedding cakes and pastries — high-ticket, seasonal demand spikes (wedding season +150%)",
            "Orders come via phone/Instagram/WhatsApp — no online order form to capture custom cake requests automatically",
            "Delivers via foodpanda — no direct ordering or automated order tracking for custom orders",
            "Competitors without online booking or automated order intake lose custom cake orders during peak wedding season"
        ],
        "offer_surface": "Autonomous AI agent deployment for bakery and custom cake businesses — targeting: seasonal wedding demand peaks, phone/Instagram/WhatsApp orders only, no online order form, delivery via third-party aggregator"
    },
    "LH-0023": {
        "pain_signals": [
            "Bangladesh premier luxury salon (3+ branches, 4.9 rating) — appointment-driven, high-ticket services",
            "Booking is phone-only — no online booking system, no automated appointment reminders",
            "High margin services (hair spa BDT2,600+, facial BDT3,500+, bridal prep) — every missed appointment is significant revenue",
            "No automated waitlist for peak times — walk-in clients turned away during busy periods"
        ],
        "offer_surface": "Autonomous AI agent deployment for luxury salon and spa businesses — targeting: phone-only booking, no online appointment system, high-ticket services, no waitlist management, peak-time walk-in turnaways"
    },
    "LH-0024": {
        "pain_signals": [
            "Leading packaging manufacturer (since 1996) — custom corrugated boxes, mailer boxes, rigid boxes, offset printing",
            "Quote requests via phone/email only — no online quote form, no automated lead qualification for B2B inquiries",
            "High-volume orders (BDT25K+ average) — manual quote process is slow, every delayed quote risks losing the order to a faster competitor",
            "No automated order tracking or project status updates for B2B clients"
        ],
        "offer_surface": "Autonomous AI agent deployment for packaging and corrugated box manufacturers — targeting: phone/email-only quote requests, no online quote form, manual B2B lead qualification, slow quote turnaround on high-value orders"
    },
    "LH-0025": {
        "pain_signals": [
            "Courier and logistics service with shipment tracking on website — but no automated booking form",
            "Booking via phone/email/walk-in — no AI-powered booking assistant to handle volume spikes",
            "No automated shipment status updates via SMS/email for customers — manual follow-up on each shipment",
            "High-volume B2B and personal shipments — manual booking process creates bottlenecks during peak seasons"
        ],
        "offer_surface": "Autonomous AI agent deployment for courier and logistics companies — targeting: no automated booking form, phone/email/walk-in booking only, no automated shipment status updates, manual process during peak seasons"
    }
}

for lead_id, data in enrichments.items():
    lead_path = LEADS / f"{lead_id}.json"
    lead = json.loads(lead_path.read_text(encoding="utf-8"))
    lead["pain_signals"] = data["pain_signals"]
    lead["offer_surface"] = data["offer_surface"]
    lead["score"] = 0  # reset for fresh scoring
    lead_path.write_text(json.dumps(lead, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ Enriched {lead_id}: {lead['business_name']} ({lead['niche']})")

# Now run audit + score for each
print("\n--- Running audit + score ---")
for lead_id in ["LH-0022", "LH-0023", "LH-0024", "LH-0025"]:
    r = subprocess.run(["python", "engine.py", "audit", lead_id], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip().split("\n")[-3:])

# Verify final state
print("\n--- Final state ---")
r = subprocess.run(["python", "engine.py", "leads"], cwd=ROOT, capture_output=True, text=True)
for line in r.stdout.splitlines():
    if any(x in line for x in ["LH-0022", "LH-0023", "LH-0024", "LH-0025"]):
        print(line)
