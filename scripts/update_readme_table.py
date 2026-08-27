#!/usr/bin/env python3
"""Update README.md Current State table to match real data."""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
engine = REPO / "engine.py"

# Get actual status
result = subprocess.run(
    [sys.executable, str(engine), "status"],
    cwd=REPO,
    capture_output=True,
    text=True,
)
assert result.returncode == 0, result.stderr
lines = result.stdout.strip().splitlines()

def find_line(prefix: str) -> int:
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            return i
    raise ValueError(f"Line not found: {prefix}")


def parse_int(line: str) -> int:
    parts = line.split("|")
    if len(parts) < 3:
        raise ValueError(f"Unexpected format: {line.strip()}")
    return int(parts[2].strip())


status_index = find_line("| Status:")
qualified_index = find_line("| Qualified:")
tier_a_index = find_line("| Tier A:")
tier_b_index = find_line("| Tier B:")
evidence_index = find_line("| Evidence:")
activity_index = find_line("| Activity log:")
outreach_index = find_line("| Outreach drafts:")
demos_index = find_line("| Interactive demos:")
calculators_index = find_line("| ROI calculators:")
tests_index = find_line("| Tests:")

status_val = parse_int(lines[status_index])
qualified_val = parse_int(lines[qualified_index])
tier_a_val = parse_int(lines[tier_a_index])
tier_b_val = parse_int(lines[tier_b_index])
evidence_val = parse_int(lines[evidence_index])
activity_val = parse_int(lines[activity_index])
outreach_val = parse_int(lines[outreach_index])
demos_val = parse_int(lines[demos_index])
calculators_val = parse_int(lines[calculators_index])
tests_val = parse_int(lines[tests_index])

print(f"Status: {status_val} (expected 25)")
print(f"Qualified: {qualified_val} (expected 19)")
print(f"Tier A: {tier_a_val} (expected 12)")
print(f"Tier B: {tier_b_val} (expected 7)")
print(f"Evidence: {evidence_val} (expected 204)")
print(f"Activity: {activity_val} (expected 740)")
print(f"Outreach: {outreach_val} (expected 9)")
print(f"Demos: {demos_val} (expected 14)")
print(f"Calculators: {calculators_val} (expected 22)")
print(f"Tests: {tests_val} (expected 27)")

        if ...[truncated]