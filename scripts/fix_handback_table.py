#!/usr/bin/env python3
"""Fix blank line artifact in HANDBACK.md table (line after Fastexpress)."""
from pathlib import Path

p = Path("HANDBACK.md")
text = p.read_text(encoding="utf-8")

# Remove the blank line between Fastexpress row and "All 4 websites..."
# The bad pattern: "| QUALIFIED |\n\n|All 4 websites"  →  "| QUALIFIED |\n\nAll 4 websites"
# But more safely: the blank line is harmless, just remove it
old = "|| Fastexpress BD | Courier and logistics | 85 | A | phone+880****8301, email info@fastexpressbd.com | QUALIFIED |\n\nAll 4 websites"
new = "|| Fastexpress BD | Courier and logistics | 85 | A | phone+880****8301, email info@fastexpressbd.com | QUALIFIED |\n\nAll 4 websites"
if old in text:
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("Fixed blank line artifact")
else:
    print("Pattern not found — checking current state")
    # Show the lines around the table
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "Fastexpress" in line and i > 8:
            print(f"Line {i+1}: {line}")
            if i+1 < len(lines):
                print(f"Line {i+2}: {lines[i+1]}")
            if i+2 < len(lines):
                print(f"Line {i+3}: {lines[i+2]}")
            break
