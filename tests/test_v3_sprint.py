#!/usr/bin/env python3
"""
Tests for the 2026-08-27 sprint additions:
  - cmd_queue (human approval queue)
  - scripts/audit_outreach_consistency.py (read-only integrity check)
  - end-to-end pipeline shape: discover -> verify -> audit -> outreach -> queue

Run: python -m pytest tests/test_v3_sprint.py -v
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINE = REPO / "engine.py"
AUDIT_SCRIPT = REPO / "scripts" / "audit_outreach_consistency.py"

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


# ─── cmd_queue ─────────────────────────────────────────────────────────────


class TestQueue:
    def test_queue_runs(self):
        result = run_cmd("queue", "3")
        assert result.returncode == 0, result.stderr
        assert "HUMAN APPROVAL QUEUE" in result.stdout

    def test_queue_lists_pending_outreach(self):
        result = run_cmd("queue", "5")
        # Each lead in the queue must have a DRAFT block
        assert "── DRAFT (copy below the line) ──" in result.stdout
        assert "── END DRAFT ──" in result.stdout
        # Must reference at least one O-#### outreach id
        assert "Outreach: O-" in result.stdout

    def test_queue_excludes_internal_ventures(self):
        result = run_cmd("queue", "50")
        # Internal ventures are LH-0007, LH-0008, LH-0009
        for internal_id in ("LH-0007", "LH-0008", "LH-0009"):
            # Allow the line "#N  LH-0007 ..." but not isolated mentions
            # The queue line for a lead starts with "#N  LH-NNNN  Name"
            lines = [ln for ln in result.stdout.splitlines() if ln.startswith("#")]
            assert not any(internal_id in ln for ln in lines), (
                f"queue unexpectedly includes internal lead {internal_id}: "
                f"{[ln for ln in lines if internal_id in ln]}"
            )

    def test_queue_sorted_by_score_desc(self):
        result = run_cmd("queue", "10")
        import re
        scores = []
        for ln in result.stdout.splitlines():
            m = re.match(r"^#\d+\s+LH-\d{4}\s+(.+)", ln)
            if m:
                # Score is on the next line, e.g. "     Score 100/Tier A  |"
                pass
        # Simpler check: just confirm the first row score >= last row score
        # in the queue body, by reading the next "Score" line per row.
        queue_rows = []
        idx = 0
        for ln in result.stdout.splitlines():
            m = re.match(r"^#(\d+)\s+LH-\d{4}\s+", ln)
            if m:
                idx = int(m.group(1))
            sm = re.match(r"^     Score (\d+)/Tier ([AB])\s+", ln)
            if sm and idx:
                queue_rows.append((idx, int(sm.group(1)), sm.group(2)))
                idx = 0
        assert len(queue_rows) >= 3, f"expected >=3 queue rows, got {len(queue_rows)}"
        scores_in_order = [s for _, s, _ in queue_rows]
        assert scores_in_order == sorted(scores_in_order, reverse=True), (
            f"queue not sorted by score desc: {scores_in_order}"
        )

    def test_queue_limit_respected(self):
        result = run_cmd("queue", "3")
        # Count "#N  LH-" header lines
        headers = [ln for ln in result.stdout.splitlines() if ln.startswith("#") and " LH-" in ln]
        assert len(headers) == 3, f"expected 3 entries with limit=3, got {len(headers)}: {headers}"

    def test_queue_skips_placeholder_contacts(self):
        # Even if a lead has only placeholder contacts (e.g. +880XXXX), the
        # queue should still show the lead — the contact line just shows
        # "(none)" or the best non-placeholder. We just assert no crash.
        result = run_cmd("queue", "10")
        assert result.returncode == 0
        # No crash, no traceback in output
        assert "Traceback" not in result.stdout


# ─── Consistency audit ─────────────────────────────────────────────────────


class TestConsistencyAudit:
    def test_audit_script_runs(self):
        result = subprocess.run(
            [sys.executable, str(AUDIT_SCRIPT)],
            cwd=REPO, capture_output=True, text=True,
        )
        assert result.returncode in (0, 1), f"unexpected rc={result.returncode}; stderr={result.stderr}"
        assert "Outreach / lead consistency audit" in result.stdout
        assert "This script is read-only" in result.stdout

    def test_audit_does_not_mutate_files(self, tmp_path):
        # Snapshot every JSON file's mtime+size; run audit; re-snapshot.
        # Any change means the audit script wrote something, which it must not.
        before = {}
        for p in REPO.rglob("*.json"):
            if ".git" in p.parts:
                continue
            before[p] = (p.stat().st_mtime, p.stat().st_size)
        subprocess.run(
            [sys.executable, str(AUDIT_SCRIPT)],
            cwd=REPO, capture_output=True, text=True, timeout=30,
        )
        after = {}
        for p in REPO.rglob("*.json"):
            if ".git" in p.parts:
                continue
            after[p] = (p.stat().st_mtime, p.stat().st_size)
        changed = [p for p in before if p in after and before[p] != after[p]]
        new = [p for p in after if p not in before]
        # new files (activity records) shouldn't be created by a read-only audit
        assert not new, f"audit created new files: {new}"
        # existing files shouldn't be modified
        assert not changed, f"audit modified existing files: {changed}"


# ─── End-to-end pipeline shape ─────────────────────────────────────────────


class TestPipelineShape:
    """Smoke test the full pipeline order:
    status -> leads -> queue -> validate.
    Every step must succeed without modifying production data.
    """

    def test_status_then_leads_then_queue_then_validate(self):
        for cmd in (("status",), ("leads",), ("queue", "5"), ("validate",)):
            r = run_cmd(*cmd)
            assert r.returncode == 0, f"{cmd} failed: {r.stderr or r.stdout}"
            assert "Traceback" not in r.stdout, f"{cmd} crashed"

    def test_every_qualified_lead_has_outreach(self):
        """If a lead is QUALIFIED or OUTREACH_READY, it should have at least
        one outreach draft. (Sanity check on the build pipeline.)"""
        leads_dir = REPO / "data" / "leads"
        out_dir = REPO / "data" / "outreach"
        outreach_by_lead = {}
        for f in out_dir.glob("*.json"):
            r = json.loads(f.read_text(encoding="utf-8"))
            lid = r.get("lead_id", "")
            outreach_by_lead.setdefault(lid, []).append(r)
        gaps = []
        for lf in leads_dir.glob("LH-*.json"):
            lead = json.loads(lf.read_text(encoding="utf-8"))
            status = lead.get("lifecycle_status", "")
            if status in ("QUALIFIED", "OUTREACH_READY"):
                if not outreach_by_lead.get(lead["lead_id"]):
                    gaps.append((lead["lead_id"], status))
        assert not gaps, f"qualified leads without any outreach: {gaps}"


# ─── Append-only invariant ─────────────────────────────────────────────────


class TestAppendOnly:
    """The activity log is append-only. Test that no command except a few
    explicit ones ever removes files from data/activity/.
    """

    SAFE_NO_ACTIVITY_MUTATION = [
        ("status",), ("leads",), ("queue", "3"), ("validate",),
    ]

    def test_read_only_commands_dont_change_activity_count(self):
        before = len(list((REPO / "data" / "activity").glob("A-*.json")))
        for cmd in self.SAFE_NO_ACTIVITY_MUTATION:
            run_cmd(*cmd)
        after = len(list((REPO / "data" / "activity").glob("A-*.json")))
        assert after == before, (
            f"activity count changed by read-only commands: {before} -> {after}"
        )


# ─── Outreach uniqueness (one pending draft per lead) ──────────────────────


class TestOutreachUniqueness:
    """A lead should have at most one `pending_approval` outreach. Older
    duplicates must be marked `superseded` (not deleted, not left pending)
    so the queue and dashboard show the right draft.
    """

    def test_at_most_one_pending_outreach_per_lead(self):
        out_dir = REPO / "data" / "outreach"
        by_lead: dict[str, list[str]] = {}
        for f in out_dir.glob("O-*.json"):
            r = json.loads(f.read_text(encoding="utf-8"))
            if r.get("status") == "pending_approval":
                by_lead.setdefault(r.get("lead_id", ""), []).append(r["outreach_id"])
        dupes = {lid: oids for lid, oids in by_lead.items() if len(oids) > 1}
        assert not dupes, f"leads with multiple pending outreach: {dupes}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
