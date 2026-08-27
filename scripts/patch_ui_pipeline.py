#!/usr/bin/env python3
"""Patch ui.html to add the pipeline board tab."""
from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "ui.html"
text = UI.read_text(encoding="utf-8")

# 1. Add pipeline tab button in the tabs row
old_tabs = '''<button class="tab" data-tab="activity" onclick="switchTab('activity')">📜 Activity Log</button>'''
new_tabs = '''<button class="tab" data-tab="activity" onclick="switchTab('activity')">📜 Activity Log</button>
  <button class="tab" data-tab="pipeline" onclick="switchTab('pipeline')">📊 Pipeline Board</button>'''
assert old_tabs in text, "tabs anchor not found"
text = text.replace(old_tabs, new_tabs)

# 2. Add pipeline panel after the activity panel
anchor = '''<div id="panel-activity" class="tab-panel">
  <h2>Recent Activity <span class="count" id="activity-count"></span></h2>
  <div class="activity-feed" id="activity-list"><div class="loading">Loading activity…</div></div>
</div>'''
pipeline_panel = anchor + '''

<div id="panel-pipeline" class="tab-panel">
  <h2>Pipeline Board</h2>
  <p style="font-size:13px;color:var(--muted);margin-bottom:14px;">
    Leads by lifecycle stage. Drag to reorder (visual only). Click a card to see details.
  </p>
  <div id="pipeline-columns" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;"></div>
</div>'''
assert anchor in text, "activity panel anchor not found"
text = text.replace(anchor, pipeline_panel)

# 3. Add pipeline render function before renderOutreach
outreach_fn_start = "function renderOutreach() {"
pipeline_fn = '''function renderPipeline() {
  const stages = ["DISCOVERED","AUDITED","QUALIFIED","OUTREACH_READY","CONTACTED","IN_CONVERSATION","WON","LOST","DO_NOT_CONTACT"];
  const stageColors = {
    "DISCOVERED":"var(--muted)","AUDITED":"var(--accent)","QUALIFIED":"var(--green)",
    "OUTREACH_READY":"var(--green)","CONTACTED":"var(--amber)","IN_CONVERSATION":"var(--blue)",
    "WON":"var(--green)","LOST":"var(--red)","DO_NOT_CONTACT":"var(--red)"
  };
  const col = document.getElementById("pipeline-columns");
  const all = allLeads();
  col.innerHTML = stages.map(stage => {
    const leads = all.filter(l => l.lifecycle_status === stage);
    return `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px;">
        <div style="font-size:11px;text-transform:uppercase;color:${stageColors[stage]||"var(--muted)"};margin-bottom:10px;letter-spacing:.5px;font-weight:600;">${stage} (${leads.length})</div>
        <div style="display:flex;flex-direction:column;gap:6px;">
          ${leads.map(l => `
            <div style="background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:8px;cursor:pointer;">
              <div style="font-size:12px;font-weight:600;margin-bottom:2px;">${esc(l.business_name)}</div>
              <div style="font-size:10px;color:var(--muted);">${esc(l.lead_id)} · ${l.score} · ${l.tier}</div>
            </div>
          `).join("")}
          ${leads.length === 0 ? '<div style="font-size:11px;color:var(--muted);padding:8px;text-align:center;">empty</div>' : ''}
        </div>
      </div>`;
  }).join("");
}
'''
text = text.replace(outreach_fn_start, pipeline_fn + outreach_fn_start)

UI.write_text(text, encoding="utf-8")
print("✅ ui.html patched with pipeline board tab")
