#!/usr/bin/env python3
"""One-time enrichment: attach structured pain signals + offer surfaces to the
5 research-ingested leads (LH-0010..0014), then re-score. Preserves verification."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root (script lives in scripts/)
LEADS = ROOT / "data" / "leads"

ENRICH = {
    "LH-0010": {  # Rongin Interior Solution
        "pain_signals": [
            "Intake is phone-only ('Call now for free consultation') — no online booking or quote-request form",
            "No visible CRM or lead-tracking; enquiries depend on a single phone line being answered",
            "Serves residential + commercial + hospitality across all of Bangladesh — high enquiry volume, manual triage",
            "Competitors with online consultation booking capture leads that phone-only intake misses",
        ],
        "offer_surface": "Autonomous AI agent that runs 24/7 design-enquiry intake: captures requests from the website, qualifies by project type and budget, books free consultations, and keeps a client pipeline — replacing phone-only intake with an always-on booking engine.",
    },
    "LH-0011": {  # Kazi Law Chamber
        "pain_signals": [
            "Client intake routes through a raw WhatsApp wa.me link and a basic enquiry form — no triage or scheduling intelligence",
            "International clientele (UK/USA/Canada/etc) across time zones, but no automated after-hours intake",
            "High-value corporate/maritime/tax matters require document collection — currently manual back-and-forth",
            "Three decades of practice and global awards, yet appointment booking is not systematized",
        ],
        "offer_surface": "Autonomous AI agent for client intake: triages enquiries by practice area, schedules appointments across time zones, automates document-request checklists, and maintains a matter pipeline — turning WhatsApp-first intake into a professional client-onboarding engine.",
    },
    "LH-0012": {  # Padma Diagnostic Centre
        "pain_signals": [
            "Online appointment form is a basic 'Send Request' — no instant confirmation or real-time slot selection",
            "No automated report-delivery notification; patients must check a separate portal",
            "Hotline runs 7am-11pm but booking outside those hours is unattended",
            "No patient follow-up or recall automation for repeat tests",
        ],
        "offer_surface": "Autonomous AI agent for patient coordination: real-time appointment booking with instant confirmation, automated report-ready notifications, and recall reminders — upgrading a request-form into a full patient-engagement system.",
    },
    "LH-0013": {  # Obokash Travel
        "pain_signals": [
            "Visa processing is document-heavy and status-query-driven — applicants repeatedly ask 'what's my status?'",
            "Live chat is a manually staffed tawk.to widget — no 24/7 automated responses",
            "Hajj/Umrah + tour packages require quotation back-and-forth that is not automated",
            "Large site with many destinations but no self-service document checklist or status bot",
        ],
        "offer_surface": "Autonomous AI agent for travel operations: visa-status lookup bot, automated document-checklist delivery, package quotation agent, and 24/7 chat responses — replacing manual chat staffing with an always-on service desk.",
    },
    "LH-0014": {  # MIE English Academy
        "pain_signals": [
            "7 Dhaka branches generate high admission-enquiry volume, handled via a single 'Enroll Now' form",
            "No automated batch scheduling or free-class booking visible",
            "Lead nurturing (follow-up after enquiry) appears manual",
            "Heavy investment in video testimonials but no conversational funnel to convert viewers",
        ],
        "offer_surface": "Autonomous AI agent for admissions: answers course enquiries, books free classes, schedules batches across 7 branches, and nurtures leads with timely follow-ups — turning a static enrol form into a multi-branch admission engine.",
    },
}


def main():
    for lead_id, data in ENRICH.items():
        path = LEADS / f"{lead_id}.json"
        if not path.exists():
            print(f"skip {lead_id} (not found)")
            continue
        lead = json.loads(path.read_text(encoding="utf-8"))
        lead["pain_signals"] = data["pain_signals"]
        lead["offer_surface"] = data["offer_surface"]
        lead["score"] = 0  # reset so compute_score recalculates from signals
        path.write_text(json.dumps(lead, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        # re-score
        r = subprocess.run([sys.executable, str(ROOT / "engine.py"), "score", lead_id],
                           capture_output=True, text=True)
        print(f"{lead_id}: {r.stdout.strip()}")


if __name__ == "__main__":
    main()
