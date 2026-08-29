#!/usr/bin/env python3
"""
Export a static, read-only snapshot of the lead pipeline to dist/.

Run:  python scripts/export_static.py
Output:
  dist/index.html           — self-contained dashboard (no server needed)
  dist/data-snapshot.json   — raw data for programmatic access
  dist/demos/               — interactive demo HTML files
  dist/calcs/               — ROI calculator HTML files
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIST = REPO / "dist"
UI_SRC = REPO / "ui.html"
ARTIFACTS = REPO / "artifacts"
DATA = REPO / "data"


def read_json_dir(folder: Path) -> list:
    if not folder.exists():
        return []
    out = []
    for f in sorted(folder.glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def build_snapshot() -> dict:
    leads = read_json_dir(DATA / "leads")
    evidence = read_json_dir(DATA / "evidence")
    activity = read_json_dir(DATA / "activity")
    outreach = read_json_dir(DATA / "outreach")
    demos = []
    if (ARTIFACTS / "demos").exists():
        for f in sorted((ARTIFACTS / "demos").glob("*.md")):
            demos.append({"name": f.stem, "content": f.read_text(encoding="utf-8")})

    clients = [l for l in leads if l.get("lead_type") != "internal_venture"]
    ventures = [l for l in leads if l.get("lead_type") == "internal_venture"]
    qualified = sum(1 for l in clients if l.get("lifecycle_status") == "QUALIFIED")
    tier_a = sum(1 for l in clients if l.get("tier") == "A")
    verified = sum(1 for l in clients if l.get("verified"))
    pending = sum(1 for o in outreach if o.get("status") == "pending_approval")
    sent = sum(1 for o in outreach if o.get("status") == "sent")

    public_outreach = [
        o for o in outreach
        if o.get("lead_id") in {l["lead_id"] for l in clients}
    ]

    activity.sort(key=lambda a: a.get("activity_id", ""), reverse=True)
    clients.sort(key=lambda l: l.get("score", 0), reverse=True)
    ventures.sort(key=lambda l: l.get("score", 0), reverse=True)

    return {
        "stats": {
            "leads": len(leads),
            "clients": len(clients),
            "ventures": len(ventures),
            "qualified": qualified,
            "tier_a": tier_a,
            "verified": verified,
            "evidence": len(evidence),
            "activity": len(activity),
            "outreach": len(outreach),
            "pending_approval": pending,
            "sent": sent,
            "demos": len(demos),
        },
        "leads": clients,
        "ventures": ventures,
        "outreach": public_outreach,
        "activity": activity[:60],
        "demos": demos,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": "https://github.com/FahadIbrahim93/ai-lead-hunter",
    }


def build_static_html(snapshot: dict) -> str:
    """Read ui.html, inject snapshot data, replace loadState() to use
    inline data instead of fetching /api/state."""
    html = UI_SRC.read_text(encoding="utf-8")
    snapshot_json = json.dumps(snapshot, ensure_ascii=False)

    # 1. Inject snapshot data before </head>
    data_script = f'<script>window.__SNAPSHOT__ = {snapshot_json};</script>'
    html = html.replace("</head>", f"{data_script}\n</head>", 1)

    # 2. Replace the loadState() function to use inline data
    old_load = (
        'async function loadState() {\n'
        '  try {\n'
        '    const res = await fetch("/api/state");\n'
        '    STATE = await res.json();\n'
        '    renderStats();\n'
        '    renderLeads();\n'
        '    renderOutreach();\n'
        '    renderActivity();\n'
        '    renderPipeline();\n'
        '  } catch (e) {\n'
        '    document.getElementById("leads-list").innerHTML = \'<div class="empty">Failed to load data. Is the server running?</div>\';\n'
        '  }\n'
        '}'
    )
    new_load = (
        'async function loadState() {\n'
        '  try {\n'
        '    // Static build: data is embedded at build time\n'
        '    STATE = window.__SNAPSHOT__;\n'
        '    renderStats();\n'
        '    renderLeads();\n'
        '    renderOutreach();\n'
        '    renderActivity();\n'
        '    if (typeof renderPipeline === "function") renderPipeline();\n'
        '  } catch (e) {\n'
        '    document.getElementById("leads-list").innerHTML = \'<div class="empty">Failed to load embedded data.</div>\';\n'
        '  }\n'
        '}'
    )
    html = html.replace(old_load, new_load)

    # 3. Replace the runAction() to be a no-op in public view
    old_action = 'async function runAction(action, leadId, btn) {'
    new_action = (
        'async function runAction(action, leadId, btn) {\n'
        '  toast("🔒 Actions disabled in public view. Clone the repo to run locally.", true);\n'
        '  return;\n'
        '  // --- original code below (disabled) ---\n'
        '  if (false) {'
    )
    html = html.replace(old_action, new_action)

    # 4. Add public snapshot banner after <body>
    banner = (
        '<div style="background:linear-gradient(90deg,#1f6feb,#388bfd);color:#fff;'
        'padding:14px 20px;border-radius:8px;margin-bottom:20px;font-size:14px;'
        'line-height:1.6;">'
        '<strong>📊 AI Lead Hunter — Public Dashboard</strong><br>'
        'Read-only snapshot of the Revenue Acquisition OS pipeline. '
        'The live Python pipeline (audit, scoring, outreach) runs locally. '
        '<a href="https://github.com/FahadIbrahim93/ai-lead-hunter" '
        'style="color:#fff;text-decoration:underline;font-weight:600;">'
        'View the repo →</a> · '
        '<a href="data-snapshot.json" '
        'style="color:#fff;text-decoration:underline;">Download raw JSON</a>'
        f' · <span style="opacity:0.8">Generated {snapshot["generated_at"][:10]}</span>'
        '</div>'
    )
    html = html.replace("<body>", f"<body>\n{banner}", 1)

    return html


def copy_artifacts() -> tuple[int, int]:
    demos_out = DIST / "demos"
    calcs_out = DIST / "calcs"
    demos_out.mkdir(parents=True, exist_ok=True)
    calcs_out.mkdir(parents=True, exist_ok=True)

    n_demos = 0
    live_demos = ARTIFACTS / "demos-live"
    if live_demos.exists():
        for f in live_demos.glob("*.html"):
            shutil.copy2(f, demos_out / f.name)
            n_demos += 1

    n_calcs = 0
    live_calcs = ARTIFACTS / "calculators-live"
    if live_calcs.exists():
        for f in live_calcs.glob("*.html"):
            shutil.copy2(f, calcs_out / f.name)
            n_calcs += 1

    return n_demos, n_calcs


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)
    snapshot = build_snapshot()

    # Write .nojekyll so GitHub Pages doesn't mangle underscores/JSON
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    # Write snapshot JSON
    (DIST / "data-snapshot.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Write static HTML
    html = build_static_html(snapshot)
    (DIST / "index.html").write_text(html, encoding="utf-8")

    # Copy artifacts
    n_demos, n_calcs = copy_artifacts()

    print(f"✅ Static export written to {DIST}/")
    print(f"   index.html:           {(DIST / 'index.html').stat().st_size:,} bytes")
    print(f"   data-snapshot.json:   {(DIST / 'data-snapshot.json').stat().st_size:,} bytes")
    print(f"   demos/:               {n_demos} files")
    print(f"   calcs/:               {n_calcs} files")
    print(f"   stats: {snapshot['stats']['clients']} clients, "
          f"{snapshot['stats']['tier_a']} Tier A, "
          f"{snapshot['stats']['outreach']} outreach drafts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
