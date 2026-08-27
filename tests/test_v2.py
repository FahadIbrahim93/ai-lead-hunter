#!/usr/bin/env python3
"""
Tests for the v2 architecture: research inbox, ingest dedup, live verification,
contact extraction, and idempotent evidence.

Run: python -m pytest tests/test_v2.py -v
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINE = REPO / "engine.py"

# Import engine as a module for unit-testing its pure functions
spec = importlib.util.spec_from_file_location("engine", ENGINE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


def run_cmd(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ENGINE)] + list(args),
        cwd=REPO,
        capture_output=True,
        text=True,
    )


# ─── Dedup normalization ───────────────────────────────────────────────────


class TestNormalization:
    def test_norm_name_strips_ltd(self):
        assert engine.norm_name("Acme Ltd") == engine.norm_name("Acme Limited")

    def test_norm_name_strips_parenthetical(self):
        assert engine.norm_name("JG Mart (expanded opportunity)") == engine.norm_name("JG Mart")

    def test_norm_name_case_insensitive(self):
        assert engine.norm_name("KAZI LAW CHAMBER") == engine.norm_name("kazi law chamber")

    def test_norm_domain_strips_www_and_path(self):
        assert engine.norm_domain("https://www.rongininterior.com/about") == "rongininterior.com"

    def test_norm_domain_empty(self):
        assert engine.norm_domain("") == ""


# ─── Contact extraction ────────────────────────────────────────────────────


class TestContactExtraction:
    def test_extracts_bd_phone(self):
        body = "Call us: +880 1748 848487 or 01711540084"
        contacts = engine.extract_contacts(body)
        phones = [c["value"] for c in contacts if c["channel"] == "phone"]
        assert "+8801748848487" in phones

    def test_extracts_email(self):
        body = "Email info@kazilawchamber.com for details"
        contacts = engine.extract_contacts(body)
        emails = [c["value"] for c in contacts if c["channel"] == "email"]
        assert "info@kazilawchamber.com" in emails

    def test_skips_placeholder_email(self):
        body = "Form field: you@example.com and real info@padma-bd.com"
        contacts = engine.extract_contacts(body)
        emails = [c["value"] for c in contacts if c["channel"] == "email"]
        assert "you@example.com" not in emails
        assert "info@padma-bd.com" in emails

    def test_skips_image_extensions(self):
        body = "logo@2x.png and contact@site.com"
        contacts = engine.extract_contacts(body)
        emails = [c["value"] for c in contacts if c["channel"] == "email"]
        assert "logo@2x.png" not in emails
        assert "contact@site.com" in emails

    def test_dedupes_repeated_phone(self):
        body = "01677139529 ... call 01677139529 again"
        contacts = engine.extract_contacts(body)
        phones = [c["value"] for c in contacts if c["channel"] == "phone"]
        assert phones.count("+8801677139529") == 1


# ─── Research inbox ────────────────────────────────────────────────────────


class TestResearchInbox:
    def test_inbox_loads(self):
        findings = engine.load_research_inbox()
        assert isinstance(findings, list)
        assert len(findings) >= 5

    def test_research_command_runs(self):
        result = run_cmd("research")
        assert result.returncode == 0
        assert "Research inbox" in result.stdout


# ─── Ingest idempotency ────────────────────────────────────────────────────


class TestIngest:
    def test_ingest_is_idempotent(self):
        """All 5 findings are already ingested — a re-run must add 0."""
        result = run_cmd("ingest")
        assert result.returncode == 0
        assert "0 added" in result.stdout or "added, " in result.stdout
        # Must report the duplicates skipped
        assert "duplicate" in result.stdout.lower()


# ─── Evidence idempotency ──────────────────────────────────────────────────


class TestEvidenceIdempotency:
    def test_add_evidence_no_duplicate(self, tmp_path):
        """Adding the same (kind, summary) twice returns the same id, no new file.
        Runs against an isolated temp directory — production data untouched."""
        # Isolate the engine's data dirs
        leads_dir = tmp_path / "leads"
        ev_dir = tmp_path / "evidence"
        act_dir = tmp_path / "activity"
        for d in (leads_dir, ev_dir, act_dir):
            d.mkdir()
        orig = (engine.LEADS, engine.EVIDENCE, engine.ACTIVITY)
        engine.LEADS, engine.EVIDENCE, engine.ACTIVITY = leads_dir, ev_dir, act_dir
        try:
            # Seed a minimal lead
            lead = {
                "lead_id": "LH-9999",
                "business_name": "Test Co",
                "discovered_at": "2026-01-01T00:00:00+00:00",
                "source": "research",
                "lifecycle_status": "DISCOVERED",
                "score": 0,
                "evidence": [],
            }
            (leads_dir / "LH-9999.json").write_text(json.dumps(lead), encoding="utf-8")

            id1 = engine.add_evidence("LH-9999", "other", "idempotency-test-marker", "", 50)
            id2 = engine.add_evidence("LH-9999", "other", "idempotency-test-marker", "", 50)
            files = list(ev_dir.glob("*.json"))
            assert id1 == id2
            assert len(files) == 1  # exactly one file created, not two
        finally:
            engine.LEADS, engine.EVIDENCE, engine.ACTIVITY = orig


# ─── Verification state ────────────────────────────────────────────────────


class TestVerification:
    def test_verified_leads_have_timestamp(self):
        leads_dir = REPO / "data" / "leads"
        verified = []
        for f in leads_dir.glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.get("verified"):
                verified.append(d)
                assert d.get("verified_at"), f"{d['lead_id']} verified but no timestamp"
        assert len(verified) >= 5

    def test_verified_leads_have_website(self):
        leads_dir = REPO / "data" / "leads"
        for f in leads_dir.glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.get("verified"):
                assert d.get("website"), f"{d['lead_id']} verified but no website"


# ─── Schema validation ─────────────────────────────────────────────────────


class TestValidation:
    def test_validate_passes(self):
        result = run_cmd("validate")
        assert result.returncode == 0
        assert "validate" in result.stdout.lower()

    def test_status_reports_counts(self):
        result = run_cmd("status")
        assert result.returncode == 0
        assert "Leads:" in result.stdout
        assert "✓ All records validate" in result.stdout
