#!/usr/bin/env python3
"""
ai-lead-hunter — Hermes Control Plane v2 (local implementation)

Usage:
  python engine.py status
  python engine.py leads
  python engine.py audit LH-0001
  python engine.py score LH-0001
  python engine.py outreach LH-0001
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
ARTIFACTS = REPO / "artifacts"
SCHEMAS = DATA / "schemas"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    print(f"{'ID':<10} {'Business':<28} {'Score':<6} {'Tier':<5} {'Status':<20} {'Niche'}")
    print("-" * 85)
    for r in rows:
        score = r.get("score", "-")
        tier = r.get("tier", "-")
        status = r.get("lifecycle_status", "-")
        niche = r.get("niche", "-")
        print(f"{r['lead_id']:<10} {r['business_name'][:27]:<28} {str(score):<6} {tier:<5} {status:<20} {niche}")


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

    # Append reference to the lead — skip if an evidence record with the
    # same summary + kind already exists (idempotent re-runs).
    lead = load_lead(lead_id)
    existing = {(e.get("kind"), e.get("summary")) for e in lead.get("evidence", [])}
    if (kind, summary) in existing:
        # Already recorded — don't create a duplicate evidence file or write
        # a new activity entry for it.
        return eid
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
    save_lead(lead)

    # Score and qualify
    cmd_score(lead_id)
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


def draft_outreach(lead: dict) -> str:
    """Build a human-ready outreach draft."""
    name = lead["business_name"]
    pains = lead.get("pain_signals", [])

    # Use the first 1-2 pain signals as the hook
    pain_line = ""
    if pains:
        pain_line = pains[0]
        if len(pains) > 1 and len(pain_line) < 120:
            pain_line += f" and {pains[1]}"

    # Extract a clean offer headline from the offer_surface
    offer_surface = lead.get("offer_surface", "")
    offer_headline = extract_offer_headline(offer_surface)

    return (
        f"Hi, this is Fahad from Hope Theory.\n\n"
        f"I noticed {pain_line.lower()} — I build autonomous AI agents that handle exactly that kind of workload.\n\n"
        f"For {name}, I'd suggest starting with a focused agent that {offer_headline}.\n\n"
        f"Happy to walk you through a 15-minute demo at your convenience. No commitment — just show you what it does.\n\n"
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


# ─── CLI ───────────────────────────────────────────────────────────────────

CMD_MAP = {
    "status": cmd_status,
    "leads": cmd_leads,
    "add": cmd_add_lead,
    "audit": cmd_audit,
    "score": cmd_score,
    "outreach": cmd_outreach,
    "demo": cmd_demo,
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

    if cmd in ("status", "leads", "validate"):
        CMD_MAP[cmd]()
    else:
        if not arg:
            print(f"Usage: python engine.py {cmd} <lead_id>", file=sys.stderr)
            sys.exit(1)
        CMD_MAP[cmd](arg)


if __name__ == "__main__":
    main()
