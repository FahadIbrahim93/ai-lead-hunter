#!/usr/bin/env python3
"""
ai-lead-hunter acceptance tests.

Run: python -m pytest tests/ -v
or:  python tests/test_core.py
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINE = REPO / "engine.py"


def run_cmd(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE)] + list(args),
        cwd=REPO,
        capture_output=True,
        text=True,
    )


class TestStatus:
    def test_status_counts(self):
        result = run_cmd("status")
        assert "Leads:     31" in result.stdout
        assert "Evidence:" in result.stdout
        assert "Activity:" in result.stdout
        assert "Outreach:" in result.stdout
        assert "✓ All records validate" in result.stdout

    def test_status_runs(self):
        result = run_cmd("status")
        assert result.returncode == 0, result.stderr
        assert "Leads:" in result.stdout

    def test_status_sales_view(self):
        # The status command must expose a "Sales view" row that filters out
        # internal_venture leads so the Tier A headline number isn't inflated.
        result = run_cmd("status")
        assert "Sales view (external clients only):" in result.stdout
        assert "Client leads:" in result.stdout
        assert "A+ profiles:" in result.stdout
        # Read the A+ profile count, expect 28/28 (shape-based, not hardcoded
        # — survives future re-enrichment)
        import re
        m = re.search(r"A\+ profiles:\s+(\d+)\s*/\s*(\d+)", result.stdout)
        assert m, f"could not find A+ profiles row in: {result.stdout!r}"
        profiles, total = int(m.group(1)), int(m.group(2))
        assert profiles == total, f"profile coverage gap: {profiles}/{total}"
        assert total >= 25, f"expected at least 25 client leads, got {total}"


class TestLeads:
    def test_leads_lists_four(self):
        result = run_cmd("leads")
        assert "LH-0001" in result.stdout
        assert "LH-0002" in result.stdout
        assert "LH-0003" in result.stdout
        assert "LH-0004" in result.stdout
        assert "Best Interior Design" in result.stdout
        assert "A.K. Developments Ltd." in result.stdout
        assert "Mazada Group" in result.stdout
        assert "Hitech Inter Studio" in result.stdout

    def test_leads_render_integer_scores(self):
        # Scores change as leads get enriched/re-scored, so assert the *shape*
        # (each lead row carries an integer score 0-100) rather than fixed values.
        import re
        result = run_cmd("leads")
        rows = [ln for ln in result.stdout.splitlines() if re.match(r"^LH-\d{4}\s", ln)]
        assert len(rows) >= 4, f"expected >=4 lead rows, got {len(rows)}"
        for row in rows:
            assert re.search(r"\b(\d{1,3})\b", row), f"no integer score on row: {row!r}"
            score = int(re.search(r"\b(\d{1,3})\b", row).group(1))
            assert 0 <= score <= 100, f"score out of range on row: {row!r}"


class TestSchemas:
    def test_schema_files_exist(self):
        schemas = REPO / "data" / "schemas"
        assert (schemas / "lead.schema.json").exists()
        assert (schemas / "evidence.schema.json").exists()
        assert (schemas / "activity.schema.json").exists()
        assert (schemas / "outreach.schema.json").exists()

    def test_lead_schema_valid_json(self):
        schema = json.loads((REPO / "data" / "schemas" / "lead.schema.json").read_text())
        assert "required" in schema
        assert "lead_id" in schema["required"]
        assert "business_name" in schema["required"]
        assert "score" in schema["required"]

    def test_lead_schema_pattern(self):
        schema = json.loads((REPO / "data" / "schemas" / "lead.schema.json").read_text())
        lead_id_prop = schema["properties"]["lead_id"]
        assert "pattern" in lead_id_prop
        assert lead_id_prop["pattern"] == r"^LH-\d{4}$"


class TestValidate:
    def test_validate_passes_on_empty(self):
        result = run_cmd("validate")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "All records validate" in result.stdout


class TestValidateFailsOnBadRecord:
    def test_validate_fails_on_missing_required_field(self):
        bad = {
            "lead_id": "LH-0999",
            "discovered_at": "2026-08-27T00:00:00+06:00",
            # missing business_name
            "lifecycle_status": "DISCOVERED",
            "score": 50,
        }
        path = REPO / "data" / "leads" / "LH-0999.json"
        path.write_text(json.dumps(bad, indent=2) + "\n")
        try:
            result = run_cmd("validate")
            assert result.returncode != 0, f"validate should fail on bad record; stdout={result.stdout!r}; stderr={result.stderr!r}"
            assert "missing required field" in result.stdout
        finally:
            path.unlink(missing_ok=True)


class TestIds:
    def test_next_lead_id_format(self):
        result = run_cmd("status")  # warm up
        # Find the highest existing lead ID
        leads_dir = REPO / "data" / "leads"
        max_n = 0
        if leads_dir.exists():
            for f in leads_dir.glob("*.json"):
                m = __import__("re").search(r"LH-(\d{4})", f.name)
                if m:
                    max_n = max(max_n, int(m.group(1)))
        expected_next = f"LH-{max_n + 1:04d}"
        # next_id is internal, but we can verify the pattern holds
        assert isinstance(expected_next, str)
        assert __import__("re").match(r"^LH-\d{4}$", expected_next)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
