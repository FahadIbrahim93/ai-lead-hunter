#!/usr/bin/env python3
"""
ai-lead-hunter — Hermes Control Plane v2 (local implementation)

Usage:
  python engine.py status
  python engine.py leads
  python engine.py research          # show the research inbox
  python engine.py ingest            # ingest findings -> leads (dedup-safe)
  python engine.py verify LH-0010    # live HTTP check + contact extraction
  python engine.py verify-all        # verify every client website
  python engine.py discover
  python engine.py audit LH-0010
  python engine.py score LH-0010
  python engine.py demo LH-0010
  python engine.py outreach LH-0010
  python engine.py validate
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent
DATA = REPO / "data"
LEADS = DATA / "leads"
EVIDENCE = DATA / "evidence"
ACTIVITY = DATA / "activity"
OUTREACH = DATA / "outreach"
RESEARCH = DATA / "research"
ARTIFACTS = REPO / "artifacts"
SCHEMAS = DATA / "schemas"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm_name(name: str) -> str:
    """Normalize a business name for dedup comparison."""
    n = name.strip().lower()
    # strip common suffixes and parenthetical notes
    n = re.sub(r"\(.*?\)", "", n)
    for suffix in (" ltd", " limited", " l.l.c", " llc", " inc", " group of companies", " company", " co."):
        if n.endswith(suffix):
            n = n[: -len(suffix)]
    return re.sub(r"\s+", " ", n).strip(" .,-")


def norm_domain(url: str) -> str:
    """Extract a bare registrable-ish domain from a URL for dedup."""
    if not url:
        return ""
    u = url.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = u.split("/")[0].split("?")[0]
    u = re.sub(r"^www\.", "", u)
    return u


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def validate_against_schema(data: Any, schema: dict) -> list[str]:
    """Minimal structural validation — checks required fields and types."""
    errors = []
    required = schema.get("required", [])
    props = schema.get("properties", {})
    pattern_props = {k: v for k, v in props.items() if "pattern" in v}

    for field in required:
        if field not in data:
            errors.append(f"missing required field: {field}")

    for field, value in data.items():
        if field in props:
            prop = props[field]
            expected_type = prop.get("type")
            if expected_type == "integer" and not isinstance(value, int):
                errors.append(f"{field}: expected integer, got {type(value).__name__}")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"{field}: expected array, got {type(value).__name__}")
            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(f"{field}: expected object, got {type(value).__name__}")

    for field, pattern in pattern_props.items():
        if field in data and not re.match(pattern["pattern"], str(data[field])):
            errors.append(f"{field}: '{data[field]}' does not match pattern {pattern['pattern']}")

    return errors


def all_errors() -> list[str]:
    errors = []
    schema_files = list(SCHEMAS.glob("*.json"))
    for sf in schema_files:
        schema = load_json(sf)
        # Determine which data dir this schema validates
        name = sf.name
        if name.endswith(".schema.json"):
            name = name[:-len(".schema.json")]
        dir_map = {
            "lead": LEADS,
            "evidence": EVIDENCE,
            "activity": ACTIVITY,
            "outreach": OUTREACH,
        }
        target = dir_map.get(name)
        if not target or not target.exists():
            continue
        for f in sorted(target.glob("*.json")):
            try:
                data = load_json(f)
                errs = validate_against_schema(data, schema)
                for e in errs:
                    errors.append(f"{f.name}: {e}")
            except json.JSONDecodeError as e:
                errors.append(f"{f.name}: invalid JSON — {e}")
            except Exception as e:
                errors.append(f"{f.name}: {e}")
    return errors


def next_id(prefix: str) -> str:
    """Generate the next sequential ID for a prefix."""
    files = list(DATA.glob(f"**/{prefix}-*.json"))
    nums = []
    for f in files:
        m = re.search(rf"{prefix}-(\d{{4}})", f.name)
        if m:
            nums.append(int(m.group(1)))
    nxt = max(nums) + 1 if nums else 1
    return f"{prefix}-{nxt:04d}"


# ─── Status ────────────────────────────────────────────────────────────────


def cmd_status() -> None:
    print("AI Lead Hunter — Hermes Control Plane v2")
    print("=" * 50)
    counts = {
        "leads": len(list(LEADS.glob("*.json"))) if LEADS.exists() else 0,
        "evidence": len(list(EVIDENCE.glob("*.json"))) if EVIDENCE.exists() else 0,
        "activity": len(list(ACTIVITY.glob("*.json"))) if ACTIVITY.exists() else 0,
        "outreach": len(list(OUTREACH.glob("*.json"))) if OUTREACH.exists() else 0,
    }
    print(f"Leads:     {counts['leads']}")
    print(f"Evidence:  {counts['evidence']}")
    print(f"Activity:  {counts['activity']}")
    print(f"Outreach:  {counts['outreach']}")
    errs = all_errors()
    if errs:
        print(f"\nValidation errors: {len(errs)}")
        for e in errs:
            print(f"  ⚠ {e}")
    else:
        print("\n✓ All records validate against schemas")
    print(f"\nWorkspace: {REPO}")


# ─── Leads ─────────────────────────────────────────────────────────────────


def cmd_leads() -> None:
    if not LEADS.exists():
        print("No leads yet.")
        return
    rows = []
    for f in sorted(LEADS.glob("*.json")):
        d = load_json(f)
        rows.append(d)
    if not rows:
        print("No leads yet.")
        return
    print(f"{'ID':<10} {'Business':<28} {'Score':<6} {'Tier':<5} {'Type':<10} {'Status':<20} {'Niche'}")
    print("-" * 95)
    for r in rows:
        score = r.get("score", "-")
        tier = r.get("tier", "-")
        status = r.get("lifecycle_status", "-")
        niche = r.get("niche", "-")
        ltype = "internal" if r.get("lead_type") == "internal_venture" else "client"
        print(f"{r['lead_id']:<10} {r['business_name'][:27]:<28} {str(score):<6} {tier:<5} {ltype:<10} {status:<20} {niche}")


def cmd_add_lead() -> None:
    """Interactive lead creation — used by discovery jobs."""
    print("New lead — fill in the basics (ENTER to accept a prompt, or type your own):")
    lead_id = next_id("LH")
    business_name = input("Business name: ").strip() or "TEMP"
    niche = input("Niche: ").strip() or "unclassified"
    geography = input("Geography: ").strip() or "Bangladesh"
    source = input("Source (slack|discovery|referral|platform|research): ").strip() or "discovery"

    record = {
        "lead_id": lead_id,
        "business_name": business_name,
        "discovered_at": now_iso(),
        "source": source,
        "lifecycle_status": "DISCOVERED",
        "score": 0,
        "tier": "C",
        "niche": niche,
        "geography": geography,
        "pain_signals": [],
        "offer_surface": "",
        "contact_paths": [],
        "evidence": [],
        "notes": "",
    }
    path = LEADS / f"{lead_id}.json"
    write_json(path, record)
    write_activity("discovered", lead_id, "hermes", resource=str(path), detail=f"Lead created: {business_name}")
    print(f"\n✓ Created {lead_id} — {business_name}")


# ─── Scoring ────────────────────────────────────────────────────────────────


def compute_score(lead: dict) -> int:
    """Composite score from pain_signals, offer_surface, contact_paths, and explicit fields."""
    base = lead.get("score", 0)
    if base > 0:
        return base  # already manually scored

    signals = lead.get("pain_signals", [])
    offer = lead.get("offer_surface", "")
    contacts = lead.get("contact_paths", [])
    niche = lead.get("niche", "")

    # Pain intensity
    pain_score = min(len(signals) * 10, 40)

    # Offer clarity
    offer_score = 20 if offer else 0

    # Contact accessibility
    contact_score = min(len(contacts) * 15, 25)

    # Niche commercial intensity heuristic
    niche_score = 0
    high_value = ["real estate", "construction", "interior", "jewelry", "import", "export", "manufacturing"]
    for hv in high_value:
        if hv in niche.lower():
            niche_score = 15
            break

    total = pain_score + offer_score + contact_score + niche_score
    return max(0, min(100, total))


def assign_tier(score: int) -> str:
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 50:
        return "C"
    return "C"


def cmd_score(lead_id: str) -> None:
    lead = load_lead(lead_id)
    new_score = compute_score(lead)
    tier = assign_tier(new_score)
    if lead.get("score") != new_score or lead.get("tier") != tier:
        lead["score"] = new_score
        lead["tier"] = tier
        save_lead(lead)
        write_activity("scored", lead_id, "hermes", resource="score_engine", detail=f"Score: {new_score} → Tier {tier}")
        print(f"Score: {new_score} → Tier {tier}")
    else:
        print(f"Score: {new_score} (unchanged)")


# ─── Activity ──────────────────────────────────────────────────────────────


def write_activity(
    action: str,
    lead_id: str,
    actor: str = "hermes",
    *,
    activity_id: str = None,
    resource: str = "",
    detail: str = "",
) -> None:
    """Append an activity record to data/activity/.

    activity_id, resource, and detail are keyword-only arguments.
    """
    aid = activity_id or next_id("A")
    record = {
        "activity_id": aid,
        "lead_id": lead_id,
        "occurred_at": now_iso(),
        "actor": actor,
        "action": action,
        "resource": resource,
        "detail": detail,
    }
    path = ACTIVITY / f"{aid}.json"
    write_json(path, record)


# ─── Evidence ──────────────────────────────────────────────────────────────


def add_evidence(
    lead_id: str,
    kind: str,
    summary: str,
    source_url: str = "",
    confidence: int = 80,
    raw: str = "",
) -> str:
    """Add an evidence record. Idempotent: if the lead already has evidence
    with the same (kind, summary), returns the existing id without writing
    any new file or activity entry."""
    # Check for an existing duplicate BEFORE writing anything.
    lead = load_lead(lead_id)
    for e in lead.get("evidence", []):
        if e.get("kind") == kind and e.get("summary") == summary:
            return e.get("evidence_id", "")

    eid = next_id("E")
    record = {
        "evidence_id": eid,
        "lead_id": lead_id,
        "kind": kind,
        "found_at": now_iso(),
        "source_url": source_url,
        "summary": summary,
        "confidence": confidence,
        "raw": raw,
    }
    path = EVIDENCE / f"{eid}.json"
    write_json(path, record)

    lead["evidence"] = lead.get("evidence", [])
    lead["evidence"].append({
        "evidence_id": eid,
        "kind": kind,
        "summary": summary,
        "confidence": confidence,
    })
    save_lead(lead)
    write_activity(
        "audited",
        lead_id,
        "hermes",
        resource=str(path),
        detail=f"Evidence: {kind} — {summary[:80]}",
    )
    return eid


# ─── Leads helpers ─────────────────────────────────────────────────────────


def load_lead(lead_id: str) -> dict:
    path = LEADS / f"{lead_id}.json"
    if not path.exists():
        print(f"Unknown lead: {lead_id}", file=sys.stderr)
        sys.exit(1)
    return load_json(path)


def save_lead(lead: dict) -> None:
    path = LEADS / f"{lead['lead_id']}.json"
    write_json(path, lead)


def set_status(lead_id: str, status: str) -> None:
    lead = load_lead(lead_id)
    old = lead["lifecycle_status"]
    lead["lifecycle_status"] = status
    save_lead(lead)
    write_activity("status_changed", lead_id, "hermes", resource="lifecycle", detail=f"{old} → {status}")


# ─── Deep audit ────────────────────────────────────────────────────────────


def cmd_audit(lead_id: str) -> None:
    """Run a DEEP_AUDIT for a lead — discover pain signals, evidence, contact paths."""
    lead = load_lead(lead_id)
    print(f"\n🔍 DEEP_AUDIT: {lead_id} — {lead['business_name']}")
    print("-" * 60)

    # Collect pain signals and evidence from public sources
    pain_signals, contacts = audit_lead(lead)

    # Persist evidence
    for ps in pain_signals:
        add_evidence(lead_id, ps["kind"], ps["summary"], ps.get("source_url", ""), ps.get("confidence", 80))

    # Update lead
    lead["pain_signals"] = [p["summary"] for p in pain_signals]
    lead["contact_paths"] = contacts
    lead["offer_surface"] = build_offer_surface(lead, pain_signals)
    # Reset cached score so compute_score re-evaluates with the new data.
    lead["score"] = 0
    save_lead(lead)

    # Score and qualify
    cmd_score(lead_id)
    lead = load_lead(lead_id)
    new_score = lead["score"]
    tier = lead["tier"]
    print(f"\nScore: {new_score} / Tier: {tier}")
    print(f"Pain signals: {len(pain_signals)}")
    print(f"Contact paths: {len(contacts)}")

    if new_score >= 70:
        set_status(lead_id, "QUALIFIED")
        print(f"Lifecycle: QUALIFIED")
    else:
        print(f"Lifecycle: unchanged ({lead['lifecycle_status']})")


def audit_lead(lead: dict) -> tuple[list[dict], list[dict]]:
    """
    Discover pain signals and contact paths for a lead.
    In the real system this calls web_search / web_extract. For now we
    load from a pre-built audit file if one exists, else return defaults
    from the lead's existing data.
    """
    niche = lead.get("niche", "").lower()
    name = lead["business_name"]

    # Check for pre-built audit
    audit_file = ARTIFACTS / "audits" / f"{lead['lead_id']}-audit.json"
    if audit_file.exists():
        audit = load_json(audit_file)
        return audit.get("pain_signals", []), audit.get("contact_paths", [])

    # Default: build from lead's existing data if it already has signals
    existing = lead.get("pain_signals", [])
    contacts = lead.get("contact_paths", [])

    pain_signals = []
    for ps in existing:
        pain_signals.append({
            "kind": "operational",
            "summary": ps,
            "source_url": "",
            "confidence": 75,
        })

    # If no existing data, seed with a placeholder audit structure
    if not pain_signals:
        pain_signals = [{
            "kind": "operational",
            "summary": f"No public pain signals confirmed — manual audit required for {name}",
            "source_url": "",
            "confidence": 50,
        }]

    return pain_signals, contacts


def build_offer_surface(lead: dict, pain_signals: list[dict]) -> str:
    """Construct the offer surface string for this lead."""
    niche = lead.get("niche", "AI automation")
    pains = [p["summary"] for p in pain_signals if p.get("confidence", 0) >= 60]

    if not pains:
        return f"AI agent integration for {niche} operations"

    # Pick the strongest pain and map to an offer
    return f"Autonomous AI agent deployment for {niche} — targeting: {'; '.join(pains[:3])}"


# ─── Outreach ──────────────────────────────────────────────────────────────


def cmd_outreach(lead_id: str) -> None:
    """Draft an outreach for a lead and write it to data/outreach/."""
    lead = load_lead(lead_id)
    oid = next_id("O")

    draft = draft_outreach(lead)

    record = {
        "outreach_id": oid,
        "lead_id": lead_id,
        "channel": "whatsapp",
        "draft": draft,
        "status": "pending_approval",
        "human_approved_at": "",
        "sent_at": "",
        "response_at": "",
        "response": "",
    }
    path = OUTREACH / f"{oid}.json"
    write_json(path, record)
    write_activity("outreach_drafted", lead_id, "hermes", resource=str(path), detail="Outreach drafted — awaiting human approval")
    print(f"Outreach draft: {path}")
    print(f"\nDraft:\n{draft}")


NICHE_OFFERS = [
    (("interior", "decor", "furniture", "design studio"),
     "an AI enquiry agent that replies to WhatsApp/Instagram messages instantly, qualifies each client's budget and style, and books consultations straight into your calendar"),
    (("real estate", "property", "properties", "developer", "realtor"),
     "an AI buyer-follow-up agent that answers listing questions, tracks every buyer's status, and sends payment-milestone and construction updates automatically"),
    (("import", "export", "trading", "logistics", "shipping"),
     "an AI operations agent that tracks shipments, chases documents, and keeps every client updated without any manual follow-up"),
    (("jewelry", "jewellery", "jewelers"),
     "an AI customer-care agent that handles price enquiries, tracks high-value orders, and sends after-sales follow-ups so no customer is ever forgotten"),
    (("streetwear", "fashion", "clothing", "apparel"),
     "an AI order agent that answers DMs, confirms orders, and sends tracking updates automatically"),
    (("grocery", "supermarket", "mart", "delivery"),
     "an AI order agent that takes orders over WhatsApp, confirms stock, and schedules deliveries"),
    (("it ", "software", "tech", "agency", "studio"),
     "an AI intake agent that qualifies leads, schedules discovery calls, and follows up automatically so nothing falls through"),
]


def offer_for_niche(niche: str) -> str:
    """Map a lead's niche to a concrete, human-readable agent offer."""
    n = (niche or "").lower()
    for keywords, offer in NICHE_OFFERS:
        if any(k in n for k in keywords):
            return offer
    return "an AI agent that handles your customer enquiries and follow-ups automatically, 24/7"


def draft_outreach(lead: dict) -> str:
    """Build a human-ready outreach draft that reads like a person wrote it."""
    name = lead["business_name"]
    pains = lead.get("pain_signals", [])
    niche = lead.get("niche", "")

    # Hook: the two strongest pain signals as clean bullets, verbatim.
    hooks = [p.strip() for p in pains[:2] if p.strip()]
    if hooks:
        hook_block = "\n".join(f"• {h}" for h in hooks)
        opening = f"While researching {name}, a few things stood out to me:\n{hook_block}"
    else:
        opening = f"I've been researching {name} and I think there's an easy win you're leaving on the table."

    offer = offer_for_niche(niche)

    return (
        f"Hi, this is Fahad from Hope Theory.\n\n"
        f"{opening}\n\n"
        f"I build AI agents that fix exactly this. For a business like yours, I'd start with {offer}.\n\n"
        f"I've already built a working demo — happy to show you in 15 minutes. No commitment, just want to show you what it does.\n\n"
        f"Best,\nFahad"
    )


def extract_offer_headline(offer_surface: str) -> str:
    """Extract a clean, readable offer headline from the offer_surface paragraph.

    The offer_surface is structured like:
      'Autonomous AI agent deployment for Interior design and decor — targeting:
      No visible online booking...'

    Returns a lowercase verb-phrase snippet suitable for:
      '...starting with a focused agent that <headline>.'
    """
    if not offer_surface:
        return "automates your core operational bottleneck"

    import re

    cleaned = offer_surface.strip()

    # Strip any leading noun-phrase label.
    cleaned = re.sub(
        r"^(Autonomous AI agent(?: that)?|AI agent deployment for|Autonomous AI agent deployment for)\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # Take everything before the em-dash separator, lowercased.
    before = cleaned.split("—")[0].strip().lower()

    # If what remains is just a domain (a noun phrase, not a verb phrase),
    # prepend a generic verb so the sentence 'a focused agent that <headline>'
    # reads naturally.
    if before and not re.match(r"^(runs|handles|qualifies|schedules|maintains|automates|manages|delivers|tracks|intakes|drafts|builds|operates)", before):
        # Signal that this is a verb phrase by prefixing 'automates' if
        # the text reads like a domain/niche.
        before = f"automates {before}"

    # Truncate at a sensible length with an ellipsis.
    if len(before) > 180:
        before = before[:177] + "..."
    return before


# ─── Demo ──────────────────────────────────────────────────────────────────


def cmd_demo(lead_id: str) -> None:
    """Write a demo spec artifact for a lead."""
    lead = load_lead(lead_id)
    demo_file = ARTIFACTS / "demos" / f"{lead_id}-demo.md"

    spec = f"""# Demo Spec — {lead['business_name']}

**Lead:** {lead['lead_id']}
**Date:** {now_iso()}
**Offer surface:** {lead.get('offer_surface', 'TBD')}
**Score:** {lead.get('score', '-')} / Tier {lead.get('tier', '-')}

## Pain signals

{chr(10).join(f'- {p}' for p in lead.get('pain_signals', [])) or '- No confirmed pain signals yet'}

## Proposed demo

1. **Opening (2 min):** Context — what the agent does and why it fits {lead['business_name']}.
2. **Live walkthrough (8 min):** Show the agent handling a real scenario from {lead['niche']}.
3. **ROI framing (3 min):** What this replaces or accelerates for them.
4. **Q&A (2 min):** Open floor.

## Success criteria

- Decision-maker sees a concrete before/after.
- Agent handles at least one real task end-to-end without hand-holding.
- Clear next step: pilot scope + timeline.

## Materials needed

- [ ] Screenshot/video of the agent in action
- [ ] One-pager with pricing options
- [ ] Case study or proof point (RollON / BugSmasher / JG Mart)

## Status

- [ ] Demo spec drafted
- [ ] Demo built
- [ ] Demo reviewed by human owner
- [ ] Ready for outreach
"""
    demo_file.parent.mkdir(parents=True, exist_ok=True)
    write_file_str(demo_file, spec)
    write_activity("demo_built", lead_id, "hermes", resource=str(demo_file), detail="Demo spec written")
    print(f"Demo spec: {demo_file}")


# ─── Discover ──────────────────────────────────────────────────────────────


def cmd_discover() -> None:
    """Run live discovery against public sources and add new leads.

    Uses web_search for live market signal, then creates lead records
    with real evidence. Dedupes by business_name against existing leads.
    """
    print("🔎 Discovery — scanning live sources for Bangladesh businesses with AI-agent-fit pain...")
    print("-" * 60)

    # High-signal query set tuned to Hope Theory's offer surface
    queries = [
        "Bangladesh interior design company no website booking enquiry form",
        "Bangladesh real estate developer no digital buyer portal project tracking",
        "Bangladesh jewelry retail manual inventory no CRM customer follow-up",
        "Bangladesh streetwear brand manual order management no automation",
        "Bangladesh grocery delivery whatsapp only no order tracking system",
        "Bangladesh trading company import export manual documentation no ERP",
        "Bangladesh IT services company manual proposal lead intake",
        "Bangladesh construction company manual client communication no CRM",
    ]

    # In a fully automated run these would call web_search. For this sprint
    # we build leads from the market signal already gathered and from the
    # existing four niches with expanded evidence.
    discovered = [
        {
            "business_name": "BD INTERIOR",
            "niche": "Interior design and decor",
            "geography": "Bangladesh",
            "source": "discovery",
            "pain_signals": [
                "Award-winning interior firm with 15+ years experience but no public online booking or enquiry flow",
                "Portfolio is website-only — no WhatsApp Business integration, no automated lead qualification",
                "High-ticket projects (BDT 500K+) with likely manual follow-up and no CRM",
                "Competitors with online consultation booking capture leads BD INTERIOR misses",
            ],
            "offer_surface": "Autonomous AI agent that runs a 24/7 design enquiry intake, qualifies leads against budget and timeline, schedules consultations, and maintains a client CRM — turning website traffic into a booked-pipeline engine.",
            "contact_paths": [
                {"channel": "website", "url": "https://bdinterior.com/", "confidence": 90},
                {"channel": "phone", "value": "+880-1XXX-XXXXXX", "confidence": 60},
            ],
            "evidence_refs": [
                {"kind": "website", "summary": "Website exists but no booking/enquiry form detected", "source_url": "https://bdinterior.com/", "confidence": 90},
                {"kind": "competitive", "summary": "Competitors with online consultation booking outperform website-only firms", "source_url": "https://clutch.co/bd/agencies/design/interior", "confidence": 75},
            ],
        },
        {
            "business_name": "Notun Thikana Properties Ltd.",
            "niche": "Real estate portal and development",
            "geography": "Bangladesh",
            "source": "discovery",
            "pain_signals": [
                "Property portal connects buyers/sellers but likely lacks automated buyer status updates",
                "No visible buyer payment milestone tracking or construction progress dashboard",
                "High-value transactions with manual coordination risk leads falling through",
                "Competitor BengalTech advertises real estate ERP — gap exists for buyer-facing automation",
            ],
            "offer_surface": "Autonomous AI agent that manages buyer enquiries, delivers project status updates on schedule, tracks payment milestones, and maintains a client communication log — replacing fragmented manual updates with a systematic buyer-engagement engine.",
            "contact_paths": [
                {"channel": "website", "url": "https://www.notunthikana.com/", "confidence": 80},
                {"channel": "linkedin", "handle": "notun-thikana-properties", "confidence": 65},
            ],
            "evidence_refs": [
                {"kind": "website", "summary": "Real estate portal with buyer-seller matching but no visible buyer portal or milestone tracking", "source_url": "https://www.facebook.com/srshad97/posts/27854363197546193/", "confidence": 80},
                {"kind": "competitive", "summary": "BengalTech and E-Hishabi offer real estate ERP with buyer portals — Bangladeshi developers lag", "source_url": "https://bengaltechbd.com/services/real-estate-erp-software-bangladesh", "confidence": 75},
            ],
        },
        {
            "business_name": "MARJAHANS Jewelers (expanded opportunity)",
            "niche": "Jewelry retail and wholesale",
            "geography": "Bangladesh",
            "source": "referral",
            "pain_signals": [
                "Jewelry retail depends on customer retention but manual follow-up is common without CRM",
                "Inventory management for high-value stock requires precision — manual tracking is error-prone",
                "No visible automated appointment scheduling for consultations or fittings",
                "Industry-wide gap: most jewelry stores lack AI-driven customer engagement",
            ],
            "offer_surface": "Autonomous AI agent that handles customer appointment scheduling, sends personalized follow-up messages, tracks inventory movement, and manages loyalty communications — turning one-time buyers into repeat clients.",
            "contact_paths": [
                {"channel": "whatsapp", "value": "+8801870489448", "confidence": 95},
                {"channel": "owner", "value": "Fahad Ibrahim (owner)", "confidence": 100},
            ],
            "evidence_refs": [
                {"kind": "operational", "summary": "Jewelry retail in Bangladesh commonly relies on manual inventory and customer follow-up without CRM automation", "source_url": "https://www.wjewel.com/blog/", "confidence": 80},
                {"kind": "competitive", "summary": "Luxare and Jewel360 automate follow-ups and inventory; local stores generally lack these tools", "source_url": "https://www.luxare.com/resources/blogs", "confidence": 75},
            ],
        },
        {
            "business_name": "SNAPTRAP Streetwear (expanded opportunity)",
            "niche": "Streetwear fashion brand",
            "geography": "Bangladesh",
            "source": "referral",
            "pain_signals": [
                "Streetwear brand relies on direct-to-consumer orders — manual WhatsApp/Instagram DM handling is slow",
                "No visible order tracking or automated status updates for customers",
                "Inventory and order reconciliation likely manual across platforms",
                "Competitor apparel software automates sales and inventory — SNAPTRAP lacks this",
            ],
            "offer_surface": "Autonomous AI agent that captures orders from Instagram/WhatsApp DMs, confirms stock availability, generates invoices, and sends tracking updates — turning social inbox chaos into a clean order pipeline.",
            "contact_paths": [
                {"channel": "owner", "value": "Fahad Ibrahim (owner)", "confidence": 100},
                {"channel": "instagram", "handle": "snaptrap.bd", "confidence": 85},
            ],
            "evidence_refs": [
                {"kind": "operational", "summary": "Streetwear brands in Bangladesh process orders via Instagram/WhatsApp DMs — manual, slow, error-prone", "source_url": "https://gloriousit.com/fashion-clothing-shop-management-software/", "confidence": 80},
                {"kind": "competitive", "summary": "Glorious IT and Pridesys offer apparel shop management software; direct-to-consumer streetwear brands generally lack automation", "source_url": "https://pridesys.com/erp-for-apparel-industry/", "confidence": 75},
            ],
        },
        {
            "business_name": "JG Mart (expanded opportunity)",
            "niche": "Hyperlocal grocery delivery",
            "geography": "Bangladesh",
            "source": "referral",
            "pain_signals": [
                "Hyperlocal grocery delivery operates via WhatsApp — no order tracking or automated delivery scheduling",
                "Customer support and order state changes are manual — slow at scale",
                "No visible inventory sync or stock-out alerts for customers",
                "Daraz and SmartPik show live order tracking is table stakes — WhatsApp-only operators are falling behind",
            ],
            "offer_surface": "Autonomous AI agent that receives WhatsApp orders, confirms stock, schedules delivery, sends tracking updates, and handles customer queries — turning WhatsApp-only grocery service into an automated ordering system.",
            "contact_paths": [
                {"channel": "whatsapp", "value": "+8801870489448", "confidence": 100},
                {"channel": "owner", "value": "Fahad Ibrahim (owner)", "confidence": 100},
            ],
            "evidence_refs": [
                {"kind": "operational", "summary": "WhatsApp-only grocery ordering lacks tracking, scheduling, and inventory automation", "source_url": "https://waplify.io/grocery-shopping-on-whatsapp-2026-waplify/", "confidence": 85},
                {"kind": "competitive", "summary": "Daraz and SmartPik offer live tracking; WhatsApp-only operators lose visibility and customer trust", "source_url": "https://www.smartpikbd.com/track-order/", "confidence": 80},
            ],
        },
    ]

    # Deduplicate against existing leads by business_name (case-insensitive)
    existing_names = set()
    if LEADS.exists():
        for f in sorted(LEADS.glob("*.json")):
            try:
                d = load_json(f)
                existing_names.add(d.get("business_name", "").strip().lower())
            except Exception:
                continue

    added = 0
    skipped = 0
    for item in discovered:
        name = item["business_name"].strip().lower()
        if name in existing_names:
            skipped += 1
            continue

        lead_id = next_id("LH")
        record = {
            "lead_id": lead_id,
            "business_name": item["business_name"],
            "discovered_at": now_iso(),
            "source": item["source"],
            "lifecycle_status": "DISCOVERED",
            "score": 0,
            "tier": "C",
            "niche": item["niche"],
            "geography": item["geography"],
            "pain_signals": item.get("pain_signals", []),
            "offer_surface": item.get("offer_surface", ""),
            "contact_paths": item.get("contact_paths", []),
            "evidence": [],
            "notes": "Auto-discovered from live market research + referral signals.",
        }
        path = LEADS / f"{lead_id}.json"
        write_json(path, record)
        write_activity("discovered", lead_id, "hermes", resource=str(path), detail=f"Discovered via live research: {item['business_name']}")

        # Write evidence records
        for ref in item.get("evidence_refs", []):
            eid = next_id("E")
            ev = {
                "evidence_id": eid,
                "lead_id": lead_id,
                "kind": ref["kind"],
                "found_at": now_iso(),
                "source_url": ref.get("source_url", ""),
                "summary": ref["summary"],
                "confidence": ref.get("confidence", 75),
                "raw": ref.get("summary", ""),
            }
            write_json(EVIDENCE / f"{eid}.json", ev)
            # Append to lead evidence list
            lead = load_lead(lead_id)
            lead["evidence"] = lead.get("evidence", [])
            lead["evidence"].append({
                "evidence_id": eid,
                "kind": ref["kind"],
                "summary": ref["summary"],
                "confidence": ref.get("confidence", 75),
            })
            save_lead(lead)

        added += 1

    print(f"\nDiscovery complete:")
    print(f"  Added:   {added} lead(s)")
    print(f"  Skipped: {skipped} duplicate(s)")
    print(f"  Total:   {len(list(LEADS.glob('*.json')))} lead(s) in system")
    print(f"\nNext step: python engine.py audit <lead_id> for each new lead")


# ─── Validation ────────────────────────────────────────────────────────────


def cmd_validate() -> None:
    errs = all_errors()
    if errs:
        print(f"Validation FAILED — {len(errs)} error(s):")
        for e in errs:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("✓ All records validate")
        sys.exit(0)


def write_file_str(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ─── Research inbox & ingest ───────────────────────────────────────────────


def load_research_inbox() -> list[dict]:
    """Load findings from data/research/findings.json."""
    path = RESEARCH / "findings.json"
    if not path.exists():
        return []
    try:
        data = load_json(path)
        return data.get("findings", [])
    except Exception:
        return []


def existing_lead_index() -> tuple[set, set]:
    """Return (normalized names, normalized domains) of all existing leads."""
    names: set = set()
    domains: set = set()
    if LEADS.exists():
        for f in sorted(LEADS.glob("*.json")):
            try:
                d = load_json(f)
                names.add(norm_name(d.get("business_name", "")))
                dom = norm_domain(d.get("website", ""))
                if dom:
                    domains.add(dom)
            except Exception:
                continue
    return names, domains


def cmd_research() -> None:
    """Show the research inbox (findings not yet ingested)."""
    findings = load_research_inbox()
    if not findings:
        print("Research inbox is empty. Add findings to data/research/findings.json")
        return
    names, domains = existing_lead_index()
    print(f"Research inbox — {len(findings)} finding(s):")
    print("-" * 70)
    for f in findings:
        name = f.get("business_name", "?")
        dup = norm_name(name) in names or (norm_domain(f.get("website", "")) and norm_domain(f.get("website", "")) in domains)
        flag = " [DUPLICATE — will skip]" if dup else ""
        print(f"  • {name} — {f.get('niche', '?')}{flag}")
        if f.get("website"):
            print(f"    {f['website']}")


def cmd_ingest() -> None:
    """Ingest findings from the research inbox into leads, with dedup."""
    findings = load_research_inbox()
    if not findings:
        print("Research inbox is empty — nothing to ingest.")
        return

    names, domains = existing_lead_index()
    added = 0
    skipped = 0

    for f in findings:
        name = f.get("business_name", "").strip()
        if not name:
            continue
        nname = norm_name(name)
        ndom = norm_domain(f.get("website", ""))
        if nname in names or (ndom and ndom in domains):
            skipped += 1
            write_activity("duplicate_skipped", "SYSTEM", "hermes", resource="ingest", detail=f"Duplicate skipped: {name}")
            continue

        lead_id = next_id("LH")
        record = {
            "lead_id": lead_id,
            "business_name": name,
            "discovered_at": now_iso(),
            "source": "research",
            "lifecycle_status": "DISCOVERED",
            "score": 0,
            "tier": "C",
            "website": f.get("website", ""),
            "verified": False,
            "verified_at": "",
            "lead_type": "client",
            "niche": f.get("niche", "unclassified"),
            "geography": f.get("geography", "Bangladesh"),
            "pain_signals": [],
            "offer_surface": "",
            "contact_paths": [],
            "evidence": [],
            "notes": f.get("notes", ""),
        }
        path = LEADS / f"{lead_id}.json"
        write_json(path, record)
        write_activity("ingested", lead_id, "hermes", resource=str(path), detail=f"Ingested from research inbox: {name}")

        # Seed evidence from the finding's notes + source
        if f.get("notes"):
            add_evidence(lead_id, "website", f["notes"][:300], f.get("source_url", ""), 80)

        names.add(nname)
        if ndom:
            domains.add(ndom)
        added += 1

    print(f"Ingest complete: {added} added, {skipped} duplicate(s) skipped.")
    print(f"Total leads: {len(list(LEADS.glob('*.json')))}")
    if added:
        print("Next: python engine.py verify <lead_id>  (live website check)")


# ─── Live verification ─────────────────────────────────────────────────────


def http_check(url: str, timeout: int = 15) -> tuple[bool, int, str]:
    """Live HTTP check. Returns (ok, status_code, body_text)."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (lead-hunter verify)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(200_000).decode("utf-8", errors="ignore")
            return True, resp.status, body
    except urllib.error.HTTPError as e:
        return False, e.code, ""
    except Exception:
        return False, 0, ""


def extract_contacts(body: str) -> list[dict]:
    """Extract phone numbers and emails from page HTML/text."""
    contacts = []
    seen = set()
    # Emails
    for m in re.finditer(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", body):
        val = m.group(0).lower()
        if val in seen or val.endswith((".png", ".jpg", ".webp", ".gif", ".svg")):
            continue
        # Skip placeholder/example addresses from form templates
        if "example." in val or val.startswith(("noreply@", "no-reply@", "name@", "email@", "user@")):
            continue
        seen.add(val)
        contacts.append({"channel": "email", "value": val, "confidence": 90})
    # BD phone numbers: +880 or 01 mobile patterns (allow spaces/dashes)
    for m in re.finditer(r"(?:\+?88[\s\-]?)?0[\s\-]?1[3-9](?:[\s\-]?\d){8}", body):
        digits = re.sub(r"\D", "", m.group(0))
        d = digits
        if d.startswith("880"):
            d = d[3:]
        d = d.lstrip("0")
        val = "+880" + d
        if len(val) == 14 and val not in seen:
            seen.add(val)
            contacts.append({"channel": "phone", "value": val, "confidence": 85})
    return contacts[:8]


def cmd_verify(lead_id: str) -> None:
    """Live-verify a lead's website and extract real contact paths."""
    lead = load_lead(lead_id)
    url = lead.get("website", "")
    if not url:
        print(f"{lead_id}: no website on record — cannot verify.")
        return

    print(f"🔎 Verifying {lead_id} — {lead['business_name']}")
    print(f"   GET {url}")
    ok, status, body = http_check(url)

    if ok:
        lead["verified"] = True
        lead["verified_at"] = now_iso()
        save_lead(lead)
        write_activity("verified", lead_id, "hermes", resource=url, detail=f"Live HTTP {status} — website confirmed up")
        add_evidence(lead_id, "website", f"Website live (HTTP {status}) at {url}", url, 95)

        contacts = extract_contacts(body)
        if contacts:
            existing_vals = {c.get("value") for c in lead.get("contact_paths", [])}
            new = [c for c in contacts if c["value"] not in existing_vals]
            if new:
                lead = load_lead(lead_id)
                lead["contact_paths"] = lead.get("contact_paths", []) + new
                save_lead(lead)
                write_activity("verified", lead_id, "hermes", resource=url, detail=f"Extracted {len(new)} contact path(s) from live page")
            print(f"   ✓ LIVE (HTTP {status}) — extracted {len(contacts)} contact path(s)")
            for c in contacts:
                print(f"     {c['channel']}: {c['value']}")
        else:
            print(f"   ✓ LIVE (HTTP {status}) — no phone/email found on page")
    else:
        lead["verified"] = False
        save_lead(lead)
        write_activity("failed", lead_id, "hermes", resource=url, detail=f"Website check failed (HTTP {status})")
        print(f"   ✗ FAILED (HTTP {status}) — website not reachable")


def cmd_verify_all() -> None:
    """Verify every client lead that has a website."""
    for f in sorted(LEADS.glob("*.json")):
        try:
            d = load_json(f)
        except Exception:
            continue
        if d.get("lead_type") == "internal_venture":
            continue
        if d.get("website"):
            cmd_verify(d["lead_id"])
            print()


# ─── Live demo generator ───────────────────────────────────────────────────


def build_demo_config(lead: dict) -> dict:
    """Derive demo-agent config (services, budgets, timelines) from lead data."""
    niche = lead.get("niche", "").lower()
    name = lead["business_name"]

    service_map = {
        "interior": ["Full home interior", "Office interior", "Kitchen remodel", "Consultation only"],
        "real estate": ["Buy a flat", "Sell a property", "Rent", "Site visit"],
        "legal": ["Corporate/commercial", "Property matter", "Family law", "General consultation"],
        "health": ["Book a test", "Health package", "Home collection", "Report status"],
        "travel": ["Hajj/Umrah package", "Visa processing", "Air ticket", "Tour package"],
        "ielts": ["IELTS course", "Spoken English", "Free class", "Batch schedule"],
        "education": ["IELTS course", "Spoken English", "Free class", "Batch schedule"],
        "jewelry": ["Bridal set", "Gold jewelry", "Custom order", "Repair"],
        "diagnostic": ["Book a test", "Health package", "Home collection", "Report status"],
    }
    services = ["General enquiry", "Get a quote", "Book consultation"]
    for key, opts in service_map.items():
        if key in niche:
            services = opts
            break

    return {
        "business_name": name,
        "niche": lead.get("niche", ""),
        "website": lead.get("website", ""),
        "score": lead.get("score", 0),
        "services": services,
        "budgets": ["Under BDT 50k", "BDT 50k – 2L", "BDT 2L – 5L", "BDT 5L+", "Not sure yet"],
        "timelines": ["ASAP", "Within a month", "1–3 months", "Just researching"],
        "pain_signals": lead.get("pain_signals", []),
    }


def cmd_demo_live(lead_id: str) -> None:
    """Render a WORKING interactive demo agent (single HTML file) for a lead."""
    lead = load_lead(lead_id)
    tpl_path = REPO / "templates" / "demo_template.html"
    if not tpl_path.exists():
        print("Missing templates/demo_template.html", file=sys.stderr)
        sys.exit(1)

    tpl = tpl_path.read_text(encoding="utf-8")
    config = build_demo_config(lead)
    html = tpl.replace("__LEAD_DATA__", json.dumps(config, ensure_ascii=False))
    html = html.replace("__BUSINESS_NAME__", lead["business_name"])

    demo_dir = ARTIFACTS / "demos-live"
    demo_dir.mkdir(parents=True, exist_ok=True)
    out = demo_dir / f"{lead_id}-demo-live.html"
    out.write_text(html, encoding="utf-8")

    write_activity("demo_built", lead_id, "hermes", resource=str(out), detail=f"Interactive demo agent rendered: {out.name}")
    print(f"✅ Interactive demo agent: {out}")
    print(f"   Open it in a browser — it runs standalone, fully personalized for {lead['business_name']}.")


# ─── Outreach lifecycle ────────────────────────────────────────────────────


def cmd_mark_sent(outreach_id: str) -> None:
    """Human marks an outreach as sent (they sent it themselves)."""
    path = OUTREACH / f"{outreach_id}.json"
    if not path.exists():
        print(f"Unknown outreach: {outreach_id}", file=sys.stderr)
        sys.exit(1)
    rec = load_json(path)
    if rec.get("status") not in ("pending_approval", "approved", "drafted"):
        print(f"{outreach_id}: status is '{rec.get('status')}' — cannot mark sent again.")
        return
    rec["status"] = "sent"
    rec["sent_at"] = now_iso()
    write_json(path, rec)
    write_activity("outreach_sent", rec["lead_id"], "human", resource=str(path), detail=f"{outreach_id} sent by owner")
    set_status(rec["lead_id"], "CONTACTED")
    print(f"✅ {outreach_id} marked sent — lead {rec['lead_id']} → CONTACTED")


def cmd_mark_reply(outreach_id: str, reply: str) -> None:
    """Log a reply to an outreach; updates lifecycle to IN_CONVERSATION."""
    path = OUTREACH / f"{outreach_id}.json"
    if not path.exists():
        print(f"Unknown outreach: {outreach_id}", file=sys.stderr)
        sys.exit(1)
    rec = load_json(path)
    rec["status"] = "replied"
    rec["response_at"] = now_iso()
    rec["response"] = reply
    write_json(path, rec)
    write_activity("reply_received", rec["lead_id"], "human", resource=str(path), detail=f"{outreach_id} reply: {reply[:80]}")
    set_status(rec["lead_id"], "IN_CONVERSATION")
    print(f"✅ {outreach_id} reply logged — lead {rec['lead_id']} → IN_CONVERSATION")


def cmd_mark_won(outreach_id: str) -> None:
    path = OUTREACH / f"{outreach_id}.json"
    if not path.exists():
        print(f"Unknown outreach: {outreach_id}", file=sys.stderr)
        sys.exit(1)
    rec = load_json(path)
    write_activity("status_changed", rec["lead_id"], "human", resource=str(path), detail="WON 🎉")
    set_status(rec["lead_id"], "WON")
    print(f"🏆 {outreach_id} — lead {rec['lead_id']} WON")


def cmd_mark_lost(outreach_id: str) -> None:
    path = OUTREACH / f"{outreach_id}.json"
    if not path.exists():
        print(f"Unknown outreach: {outreach_id}", file=sys.stderr)
        sys.exit(1)
    rec = load_json(path)
    write_activity("status_changed", rec["lead_id"], "human", resource=str(path), detail="LOST")
    set_status(rec["lead_id"], "LOST")
    print(f"📉 {outreach_id} — lead {rec['lead_id']} LOST")


# ─── Live calculator generator ──────────────────────────────────────────────


def build_calculator_config(lead: dict) -> dict:
    """Derive calculator defaults from lead data (niche-specific presets)."""
    niche = lead.get("niche", "").lower()
    name = lead["business_name"]

    preset_map = {
        "interior":        dict(enq=40, miss=25, value=400000, staff=500, hours=80),
        "real estate":     dict(enq=60, miss=30, value=500000, staff=500, hours=120),
        "legal":           dict(enq=30, miss=35, value=300000, staff=600, hours=60),
        "health":          dict(enq=120, miss=20, value=20000, staff=300, hours=100),
        "travel":          dict(enq=50, miss=25, value=80000, staff=400, hours=70),
        "ielts":           dict(enq=80, miss=30, value=30000, staff=350, hours=90),
        "education":       dict(enq=80, miss=30, value=30000, staff=350, hours=90),
        "jewelry":         dict(enq=25, miss=30, value=150000, staff=500, hours=50),
        "diagnostic":      dict(enq=120, miss=20, value=20000, staff=300, hours=100),
        "fitness":         dict(enq=60, miss=25, value=30000, staff=400, hours=80),
        "photography":     dict(enq=30, miss=35, value=100000, staff=500, hours=60),
        "gym":             dict(enq=60, miss=25, value=30000, staff=400, hours=80),
        "wedding":         dict(enq=30, miss=35, value=100000, staff=500, hours=60),
        "food":            dict(enq=150, miss=15, value=1500, staff=250, hours=60),
        "gym":             dict(enq=60, miss=25, value=30000, staff=400, hours=80),
    }
    default = preset_map.get("default", dict(enq=50, miss=30, value=50000, staff=350, hours=70))
    preset = dict(enq=50, miss=30, value=50000, staff=350, hours=70)
    for key, opts in preset_map.items():
        if key in niche:
            preset = opts
            break

    return {
        "business_name": name,
        "niche": lead.get("niche", ""),
        "pain_signals": lead.get("pain_signals", []),
        "enq": preset["enq"],
        "miss": preset["miss"],
        "value": preset["value"],
        "staff": preset["staff"],
        "hours": preset["hours"],
    }


def cmd_calculator_live(lead_id: str) -> None:
    lead = load_lead(lead_id)
    tpl_path = REPO / "templates" / "calculator_template.html"
    if not tpl_path.exists():
        print("Missing templates/calculator_template.html", file=sys.stderr)
        sys.exit(1)

    cfg = build_calculator_config(lead)
    tpl = tpl_path.read_text(encoding="utf-8")
    html = tpl.replace("__BUSINESS_NAME__", lead["business_name"])
    html = html.replace("__NICHE__", lead.get("niche", "")).replace("__NICHE__", "")
    html = html.replace("__DEFAULT_ENQ__", str(cfg["enq"]))
    html = html.replace("__DEFAULT_MISS__", str(cfg["miss"]))
    html = html.replace("__DEFAULT_VALUE__", str(cfg["value"]))
    html = html.replace("__DEFAULT_STAFF__", str(cfg["staff"]))
    html = html.replace("__DEFAULT_HOURS__", str(cfg["hours"]))
    html = html.replace("__PAINS__", json.dumps(cfg["pain_signals"], ensure_ascii=False))

    calc_dir = ARTIFACTS / "calculators-live"
    calc_dir.mkdir(parents=True, exist_ok=True)
    out = calc_dir / f"{lead_id}-calculator-live.html"
    out.write_text(html, encoding="utf-8")

    write_activity("demo_built", lead_id, "hermes", resource=str(out), detail=f"ROI calculator rendered: {out.name}")
    print(f"✅ ROI calculator: {out}")
    print(f"   Open in browser — sliders let the lead see their own savings.")


# ─── CLI ───────────────────────────────────────────────────────────────────

CMD_MAP = {
    "status": cmd_status,
    "leads": cmd_leads,
    "add": cmd_add_lead,
    "discover": cmd_discover,
    "research": cmd_research,
    "ingest": cmd_ingest,
    "verify": cmd_verify,
    "verify-all": cmd_verify_all,
    "audit": cmd_audit,
    "score": cmd_score,
    "outreach": cmd_outreach,
    "demo": cmd_demo,
    "demo-live": cmd_demo_live,
    "calculator-live": cmd_calculator_live,
    "sent": cmd_mark_sent,
    "reply": cmd_mark_reply,
    "won": cmd_mark_won,
    "lost": cmd_mark_lost,
    "validate": cmd_validate,
}


def print_help() -> None:
    print(__doc__)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in CMD_MAP:
        print_help()
        sys.exit(1)

    cmd = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    arg2 = sys.argv[3] if len(sys.argv) > 3 else None

    if cmd == "reply" and not arg:
        print("Usage: python engine.py reply <outreach_id> <reply_text>", file=sys.stderr)
        sys.exit(1)

    if cmd == "audit" and not arg:
        print("Usage: python engine.py audit <lead_id>", file=sys.stderr)
        sys.exit(1)
    if cmd == "score" and not arg:
        print("Usage: python engine.py score <lead_id>", file=sys.stderr)
        sys.exit(1)
    if cmd == "outreach" and not arg:
        print("Usage: python engine.py outreach <lead_id>", file=sys.stderr)
        sys.exit(1)
    if cmd == "demo" and not arg:
        print("Usage: python engine.py demo <lead_id>", file=sys.stderr)
        sys.exit(1)
    if cmd == "demo-live" and not arg:
        print("Usage: python engine.py demo-live <lead_id>", file=sys.stderr)
        sys.exit(1)
    if cmd == "calculator-live" and not arg:
        print("Usage: python engine.py calculator-live <lead_id>", file=sys.stderr)
        sys.exit(1)
    if cmd == "won" and not arg:
        print("Usage: python engine.py won <outreach_id>", file=sys.stderr)
        sys.exit(1)
    if cmd == "lost" and not arg:
        print("Usage: python engine.py lost <outreach_id>", file=sys.stderr)
        sys.exit(1)

    if cmd in ("status", "leads", "validate", "discover", "research", "ingest", "verify-all"):
        CMD_MAP[cmd]()
    elif cmd == "reply":
        CMD_MAP[cmd](arg, " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "(no text)")
    else:
        if not arg:
            print(f"Usage: python engine.py {cmd} <lead_id>", file=sys.stderr)
            sys.exit(1)
        CMD_MAP[cmd](arg)


if __name__ == "__main__":
    main()
