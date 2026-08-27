#!/usr/bin/env python3
"""Build demos and calculators for LH-0022..0025, then run tests."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_LEADS = ["LH-0022", "LH-0023", "LH-0024", "LH-0025"]

print("=== Building demos + calculators for 4 new leads ===\n")
for lead_id in NEW_LEADS:
    print(f"[{lead_id}]")
    r_demo = subprocess.run(["python", "engine.py", "demo-live", lead_id], cwd=ROOT, capture_output=True, text=True)
    r_calc = subprocess.run(["python", "engine.py", "calculator-live", lead_id], cwd=ROOT, capture_output=True, text=True)
    demo_ok = "✅" in r_demo.stdout
    calc_ok = "✅" in r_calc.stdout
    print(f"  demo: {'✅' if demo_ok else '❌'} | calc: {'✅' if calc_ok else '❌'}")
    if not demo_ok:
        print(f"    demo stderr: {r_demo.stderr[:200]}")
    if not calc_ok:
        print(f"    calc stderr: {r_calc.stderr[:200]}")

print("\n=== Running tests ===")
r_tests = subprocess.run(["python", "-m", "pytest", "tests/", "-q"], cwd=ROOT, capture_output=True, text=True)
print(r_tests.stdout.splitlines()[-5] if r_tests.stdout else r_tests.stderr[:300])

print("\n=== Status ===")
r_status = subprocess.run(["python", "engine.py", "status"], cwd=ROOT, capture_output=True, text=True)
print(r_status.stdout.splitlines()[0])

# Show new leads
print("\n=== New leads state ===")
r_leads = subprocess.run(["python", "engine.py", "leads"], cwd=ROOT, capture_output=True, text=True)
for line in r_leads.stdout.splitlines():
    if any(x in line for x in ["LH-0022", "LH-0023", "LH-0024", "LH-0025"]):
        print(line.strip())

# Count generated artifacts
demos = list((ROOT / "artifacts" / "demos-live").glob("*.html"))
calcs = list((ROOT / "artifacts" / "calculators-live").glob("*.html"))
print(f"\nTotal demos: {len(demos)} | Total calculators: {len(calcs)}")
