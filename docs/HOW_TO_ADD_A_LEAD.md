# How to add a new lead

A step-by-step manual for the next session, the next agent, or future-you
on a 3am "I need to add a lead" brain.

## The fast path (5 minutes)

If you already have a business in mind and the basics on hand:

```bash
cd ~/ai-lead-hunter

# 1. Add to research inbox
$EDITOR data/research/findings.json
# Append a finding block (see template below)

# 2. Ingest (dedupes, creates lead record)
python engine.py ingest

# 3. Verify the website is live
python engine.py verify LH-NNNN

# 4. Add pain signals + offer (edit the lead JSON directly, or use
#    scripts/enrich_research_leads.py to bulk-enrich a whole batch)
$EDITOR data/leads/LH-NNNN.json

# 5. Audit (re-score, may mark QUALIFIED if score >= 70)
python engine.py audit LH-NNNN

# 6. Build the 3 artifacts
python engine.py demo-live LH-NNNN
python engine.py calculator-live LH-NNNN
python engine.py outreach LH-NNNN

# 7. Review the draft
python dashboard.py    # open http://localhost:8765
# Or: cat data/outreach/O-NNNN.json
```

## Research-inbox finding template

Append this block to `data/research/findings.json` inside the
`findings` array:

```json
{
  "business_name": "Acme Interior Design",
  "website": "https://acmeinterior.com/",
  "niche": "Interior design and decoration",
  "geography": "Dhaka, Bangladesh",
  "source_url": "https://acmeinterior.com/",
  "contact_hints": [
    "phone +880XXXXXXXXXX",
    "email info@acmeinterior.com"
  ],
  "notes": "Why this business, what you saw, what makes it a fit.",
  "found_at": "2026-08-27T12:00:00+06:00"
}
```

**Required fields:** `business_name`, `website`, `niche`.
**Recommended:** `geography`, `source_url`, `contact_hints`, `notes`.

`ingest` will dedupe by `(business_name, website)` — re-adding the same
finding is a no-op.

## Lead record template (post-ingest)

After `ingest` you'll have a record like this. Most fields are
optional; the audit step fills in `score` and `tier`.

```json
{
  "lead_id": "LH-0026",
  "business_name": "Tech Dental Care",
  "discovered_at": "2026-08-27T00:00:00+06:00",
  "source": "research",
  "lifecycle_status": "DISCOVERED",
  "score": 0,
  "tier": "?",
  "website": "https://techdentalcare.com/",
  "verified": false,
  "lead_type": "client",
  "niche": "Dental clinic chain",
  "geography": "Dhaka, Bangladesh (4 branches)",
  "pain_signals": [],
  "offer_surface": "",
  "contact_paths": [],
  "evidence": [],
  "notes": ""
}
```

## Pain-signal quality bar

A pain signal is **not** a generic statement. It's a specific, observable
weakness with a known cost. Compare:

| Generic (don't) | Specific (do) |
|---|---|
| "They could use AI" | "Quote requests are phone/email only — no online form on a B2B manufacturer with 30 years of operation" |
| "Their website is basic" | "Site is 2,500 words of product catalog with no ROI calculator, no case studies, no comparison tool" |
| "They have many customers" | "30+ Google reviews averaging 4.2 stars, several mentioning long wait times for callback" |

Good pain signals all have:
- **Observable** (you saw it on their site / review / LinkedIn)
- **Quantified** (number, frequency, scale)
- **Cost-implicating** (what's it worth in ৳/month or ৳/year to fix?)

4-5 specific pain signals → score typically lands 85-100 (Tier A).
3 generic signals → score 70-84 (Tier B).
<3 signals → stays DISCOVERED, needs more research.

## The A+ business profile (the differentiator)

For your top-priority leads, add a `business_profile` block. This is
what closes deals — it shows you did the homework. Block shape:

```json
{
  "business_profile": {
    "business_overview": "Who they are, scale, real clients, real locations",
    "offer_surface": "AI agent deployment for <niche> — targeting: <pain 1>; <pain 2>; <pain 3>",
    "website": "https://...",
    "verified": true,
    "verified_at": "2026-08-27T12:00:00+06:00",
    "pain_signals": ["...", "..."],
    "contact_paths": [
      {"type": "phone", "value": "+880...", "source": "web_extract: example.com"},
      {"type": "email", "value": "info@...", "source": "web_extract: example.com"},
      {"type": "website", "value": "https://...", "source": "verified LIVE (HTTP 200)"}
    ],
    "pricing_knowledge": {
      "model": "Project-based / retainer / fee-for-service / etc.",
      "from_website": ["actual price point 1", "actual price point 2"],
      "note": "Why this matters — what the pain is worth in ৳/yr"
    },
    "operational_gaps": [
      "Specific weakness 1",
      "Specific weakness 2",
      "Specific weakness 3"
    ],
    "competitive_position": "How they compare to Dhaka peers",
    "opportunity_size": "What the pain costs them annually",
    "how_the_agent_helps": "1. AI agent step 1\n2. AI agent step 2\n3. AI agent step 3",
    "demo_scenario": "A walkthrough of the agent in action for this specific business"
  }
}
```

Building 1 of these takes 20-30 minutes of real web research (read their
site, check their reviews, look at competitors). It's the single
highest-leverage thing you can do for a lead.

## Outreach personalization checklist

Before you copy an `O-NNNN.json` draft into WhatsApp, spend 30 seconds:

- [ ] Open their website — what do you actually see on the homepage?
- [ ] Check their Google reviews (or Facebook) — any specific complaints?
- [ ] Glance at their LinkedIn — what's the founder been posting about?
- [ ] Open the demo HTML for this lead (`artifacts/demos-live/LH-NNNN-demo-live.html`) — does it look right?
- [ ] Open the calculator HTML — do the default sliders make sense for this niche?

If any of those surface something concrete, replace the template opener
("While researching X, a few things stood out to me") with a one-line
specific hook. 30 seconds per lead × 5 leads = 2.5 minutes. Will 5x your
reply rate.

## Common mistakes

1. **Don't invent pain signals.** If you don't have evidence, leave the
   signal out. Score will be lower, but the lead is honest.
2. **Don't re-write the lead JSON without backing it up.** Activity
   records reference lead_ids, not lead contents. But a re-write that
   changes a phone number silently can mislead a future you.
3. **Don't send outreach before reading it.** Always read the draft in
   `data/outreach/O-NNNN.json` (or in the dashboard) before sending.
4. **Don't mark an outreach as `sent` until you've actually sent it.**
   The system trusts you to be honest about this.
5. **Don't put API keys or credentials in lead records.** Outreach goes
   over WhatsApp from your phone. No tokens needed.

## How to know you're done with a lead

A lead is "done" (ready to send) when:
- ✅ `verified: true` (live HTTP 200)
- ✅ `pain_signals` has 4+ specific items
- ✅ `score >= 70` and `tier` is A or B
- ✅ `lifecycle_status` is `QUALIFIED` or later
- ✅ Demo HTML exists, opens, shows the right business name
- ✅ Calculator HTML exists, opens, shows the right business name
- ✅ Outreach draft exists, is `pending_approval`, and you've read it
- ✅ For top-5 leads: A+ business_profile block exists

If any of those is missing, the lead is "in progress" and you should
complete it before sending. Sending a half-baked lead damages your
reputation more than not sending at all.
