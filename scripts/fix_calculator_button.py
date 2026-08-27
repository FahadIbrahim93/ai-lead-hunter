#!/usr/bin/env python3
"""Fix duplicate calculator-live button and ensure exactly one exists."""
from pathlib import Path

ui = Path("ui.html")
text = ui.read_text(encoding="utf-8")

target = """<button class="primary" onclick="runAction('demo-live','${esc(l.lead_id)}',this)">🚀 Generate Live Demo</button>
        <button onclick="runAction('outreach','${esc(l.lead_id)}',this)">✉️ Draft Outreach</button>"""

replacement = """<button class="primary" onclick="runAction('demo-live','${esc(l.lead_id)}',this)">🚀 Generate Live Demo</button>
        <button class="primary" onclick="runAction('calculator-live','${esc(l.lead_id)}',this)">🧮 Generate ROI Calculator</button>
        <button onclick="runAction('outreach','${esc(l.lead_id)}',this)">✉️ Draft Outreach</button>"""

count = text.count(target)
print(f"Target block found {count} time(s)")

if count == 1:
    new_text = text.replace(target, replacement)
    ui.write_text(new_text, encoding="utf-8")
    print("✅ Fixed: added calculator-live button (exactly one)")
elif count == 0:
    # Check what's there now
    demo_line_idx = text.find("🚀 Generate Live Demo")
    if demo_line_idx == -1:
        print("❌ Cannot find demo-live button at all")
    else:
        ctx = text[demo_line_idx:demo_line_idx+250]
        print(f"Context around demo-live button:\n{ctx}")
else:
    # Multiple - remove duplicates, then add one
    new_text = text.replace(target, replacement, 1)  # Replace first occurrence
    # Remove any remaining duplicate calculator-live buttons
    import re
    new_text = re.sub(r'(<button class="primary" onclick="runAction\(\'calculator-live\',\'\\$\{esc\(l\.lead_id\)\}\}','.*?</button>)\s*\1', r'\1', new_text)
    ui.write_text(new_text, encoding="utf-8")
    print(f"✅ Fixed: removed {count-1} duplicates, kept one calculator-live button")

# Verify
final = Path("ui.html").read_text(encoding="utf-8")
calc_count = final.count("calculator-live")
print(f"\nFinal calculator-live button count: {calc_count}")
print(f"File size: {len(final)} bytes")
