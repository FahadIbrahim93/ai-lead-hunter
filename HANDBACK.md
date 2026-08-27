# AI Lead Hunter — Sprint Handback (Revenue Assets Sprint)

## What this sprint did
Built the revenue-generating assets: working interactive demos, personalized outreach, lifecycle tracking, and expanded the lead pipeline with3 new verified businesses.

## New capabilities

###1. Interactive Demo Agents (`demo-live`)
- **10 working demos** generated for all qualified leads
- Each demo is a standalone HTML file that runs offline
- Fully personalized: business name, services, pain signals, contact info
- Interactive conversation flow: service → budget → timeline → name → phone → booking confirmation
- CRM activity log shows what the agent captured
- Side panel shows pain points (today) vs gains (with agent)

###2. Personalized Outreach (`scripts/rewrite_outreach.py`)
- Rewrote all5 outreach drafts with verified evidence
- Each draft references the lead's specific pain point
- Includes demo CTA: "I've built a quick interactive demo specifically for [business]"
- All drafts remain `pending_approval` — human must approve and send

###3. Lifecycle Commands (close the loop)
- `python engine.py sent O-0001` — marks outreach as sent, lead → CONTACTED
- `python engine.py reply O-0001 "Interested"` — logs reply, lead → IN_CONVERSATION
- `python engine.py won O-0001` — marks lead as WON
- `python engine.py lost O-0001` — marks lead as LOST
- Full audit trail in activity log

###4. Dashboard Updates
- Added "🚀 Generate Live Demo" button to every lead card
- Demo-live action wired to dashboard API
- All buttons functional: Re-Audit, Build Demo Spec, Generate Live Demo, Draft Outreach

###5. Lead Pipeline Expansion
- Added3 new verified businesses:
  - **Gold's Gym Bangladesh** (60/C) — fitness/gym, phone-only booking
  - **Wedding Diary Bangladesh** (60/C) — photography, WhatsApp-only booking
  - **Metro Weddings** (85/A) — photography, WhatsApp-only booking, QUALIFIED
- All3 websites verified LIVE (HTTP 200)
- Real contacts extracted: bdmetroweddings@gmail.com, +880****4358

## Current state
- **17 leads**:14 clients +3 internal ventures
- **11 qualified**,8 Tier A
- **10 interactive demos** ready to show clients
- **5 personalized outreach drafts** ready for approval
- **144 evidence**,307 activity,9 outreach drafts
- **27/27 tests passing**, validation clean

## How to use the new features

### Show a demo to a client
```bash
# Generate the demo (already done for all qualified leads)
python engine.py demo-live LH-0010

# Open the HTML file in your browser
# It runs standalone — no server needed
# Walk the client through the conversation flow
# Show them the CRM log and pain/gain comparison
```

### Send outreach
```bash
# Review the draft
cat data/outreach/O-0001.json

# Copy the draft text and send it yourself (WhatsApp/email)
# Then mark it as sent
python engine.py sent O-0001

# When they reply
python engine.py reply O-0001 "Interested, let's schedule a call"

# When you close the deal
python engine.py won O-0001
```

### Add more leads
```bash
# Add findings to data/research/findings.json
# Then ingest and verify
python engine.py ingest
python engine.py verify-all
python engine.py audit LH-0018
```

## Next sprint candidates
- Build a pricing calculator demo (interactive ROI calculator)
- Add email templates for different outreach stages
- Build a "proposal generator" that creates PDF proposals from lead data
- Add a "pipeline view" to the dashboard (Kanban-style board)
- Research more niches: salons, clinics,培训机构, e-commerce stores

## Files changed
- `engine.py` — added demo-live, lifecycle commands (sent/reply/won/lost)
- `dashboard.py` — added demo-live action handler
- `ui.html` — added "🚀 Generate Live Demo" button
- `templates/demo_template.html` — interactive demo template
- `scripts/rewrite_outreach.py` — personalized outreach generator
- `scripts/enrich_research_leads.py` — lead enrichment script
- `data/research/findings.json` — added3 new findings
- `data/leads/LH-0015..0017.json` —3 new verified leads
- `tests/test_core.py` — updated lead count assertion
