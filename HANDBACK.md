# AI Lead Hunter — Sprint Handback (Architecture Sprint)

## What this sprint did
Turned the system from a prototype with fake discovery into a **real, verified
lead machine** with a state-of-the-art architecture.

## New architecture (the big change)

```
RESEARCH INBOX ──ingest──▶ LEADS ──verify──▶ VERIFIED ──audit──▶ QUALIFIED
```

1. **Research inbox** (`data/research/findings.json`) — real findings with
   name + live website + niche. No more hardcoded fake discovery.
2. **`ingest`** — converts findings to leads with **dedup by normalized name
   AND domain** (strips Ltd/Limited/parentheticals, www, paths).
3. **`verify` / `verify-all`** — **live HTTP check** of each website +
   **real phone/email extraction** from the page HTML. Filters placeholders
   (you@example.com) and image filenames.
4. **Dashboard v2** — separates Client Leads from My Ventures, shows
   ✓ VERIFIED badges, website links, and per-lead Verify buttons.
   Now multi-threaded (fixed a request-blocking bug).

## Proof it works (real execution, not claims)
- Ingested 5 real researched businesses → LH-0010..0014
- **All 5 websites verified LIVE (HTTP 200)** by the verify command
- Real contacts extracted: e.g. Kazi Law Chamber → info@kazilawchamber.com,
  +8801748848487, +8801711540084 (all pulled from the live page)
- Audited + scored: Rongin 90/A, Kazi Law 85/A, MIE 85/A, Padma 75/B, Obokash 60/C
- 4 of 5 qualified (Obokash correctly stayed DISCOVERED at 60 — the system
  honestly rejected a weak lead)

## Current state
- **14 leads**: 11 clients + 3 internal ventures (MARJAHANS, SNAPTRAP, JG Mart)
- **5 verified-live** client websites
- **10 qualified**, 7 Tier A
- 126 evidence, 200 activity, 9 outreach drafts (all pending_approval)
- **27/27 tests passing**, validation clean

## Bugs found & fixed this sprint
- `add_evidence` wrote the file BEFORE the dedup check → orphan duplicates. Fixed.
- Dashboard was single-threaded → one slow connection blocked the API. Fixed (ThreadingHTTPServer).
- Phone regex missed spaced numbers (+880 1748 848487). Fixed.
- `you@example.com` form placeholder was captured as a contact. Fixed.
- 5 activity records had invalid lead_id "—". Fixed (SYSTEM sentinel + schema update).
- Enrichment script resolved paths from scripts/ not repo root. Fixed.

## How to use it (non-technical)
Double-click `START-DASHBOARD.bat`. Everything is clickable.
To add leads: put findings in `data/research/findings.json`, click "Ingest Research",
then "Verify Websites". See RUNBOOK.md.

## Next sprint candidates
- Wire `discover` to actually call web_search and write findings.json automatically
- Build one WORKING demo artifact (not just a spec) for the #1 lead (Rongin, 90/A)
- Rewrite outreach drafts with per-lead personalization from verified evidence
- Response tracking: mark outreach sent → log replies → WON/LOST
