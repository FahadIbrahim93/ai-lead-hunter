# Artifact Quality Audit Report

**Audited:** 2026-08-29  
**Files:** 31 demo-live + 31 calculator-live = 62 HTML files  
**Location:** `C:/Users/fhdib/ai-lead-hunter/artifacts/`

## Summary

| Check | Result |
|-------|--------|
| Missing files | ✅ All 62 present |
| Local filesystem paths | ✅ None found |
| Relative artifact paths | ✅ None found |
| Missing images/assets | ✅ None — all files are self-contained (no external images) |
| External broken links | ✅ None — no external URLs at all |
| Empty/stub files | ✅ None — all files are substantial (11–13 KB) |
| CSS/JS | ✅ All files have inline `<style>` and `<script>` |
| Branding ("Hope Theory" in body/footer) | ✅ Present in all 62 files footer: *"Built by Fahad Ibrahim · Hope Theory"* |
| **Branding in `<title>` tag** | ⚠️ **62/62 files missing "Hope Theory"** |

## The One Real Issue: Title Tags Lack Brand Name

Every file's `<title>` follows the pattern:
- Demos: `AI Agent Demo — {Company Name}`
- Calculators: `AI Agent ROI Calculator — {Company Name}`

None include "Hope Theory". When a prospect opens the file in a browser tab, they see the company name but not the brand.

**Recommended fix** — change all titles to include the brand:
- Demos: `Hope Theory — AI Agent Demo for {Company Name}`
- Calculators: `Hope Theory — AI Agent ROI Calculator for {Company Name}`

## Non-Issues Flagged Then Dismissed

| What looked like an issue | Why it's fine |
|--------------------------|---------------|
| `placeholder` matches in demo files | These are `<input placeholder="Type a message…">` attributes — normal HTML, not placeholder content |

## Per-File Detail

All 62 files share the same structure and quality level. The only issue across all files is the title tag branding noted above.

### demos-live/ (LH-0001 through LH-0031)

| File | Company | Size (KB) | Issues |
|------|---------|-----------|--------|
| LH-0001-demo-live.html | Best Interior Design | 12.1 | Title missing brand |
| LH-0002-demo-live.html | A.K. Developments Ltd. | 12.2 | Title missing brand |
| LH-0003-demo-live.html | Mazada Group | 12.3 | Title missing brand |
| LH-0004-demo-live.html | Hitech Inter Studio | 12.3 | Title missing brand |
| LH-0005-demo-live.html | BD INTERIOR | 12.3 | Title missing brand |
| LH-0006-demo-live.html | Notun Thikana Properties Ltd. | 12.4 | Title missing brand |
| LH-0007-demo-live.html | MARJAHANS Jewelers | 12.4 | Title missing brand |
| LH-0008-demo-live.html | SNAPTRAP Streetwear | 12.5 | Title missing brand |
| LH-0009-demo-live.html | JG Mart | 12.5 | Title missing brand |
| LH-0010-demo-live.html | Rongin Interior Solution | 12.5 | Title missing brand |
| LH-0011-demo-live.html | Kazi Law Chamber | 12.4 | Title missing brand |
| LH-0012-demo-live.html | Padma Diagnostic Centre Ltd | 12.5 | Title missing brand |
| LH-0013-demo-live.html | Obokash Travel | 12.4 | Title missing brand |
| LH-0014-demo-live.html | MIE English Academy Bangladesh | 12.5 | Title missing brand |
| LH-0015-demo-live.html | Gold's Gym Bangladesh | 12.5 | Title missing brand |
| LH-0016-demo-live.html | Wedding Diary Bangladesh | 12.6 | Title missing brand |
| LH-0017-demo-live.html | Metro Weddings | 12.5 | Title missing brand |
| LH-0018-demo-live.html | Ngital Digital Marketing | 12.5 | Title missing brand |
| LH-0019-demo-live.html | Ananta Events and Entertainment | 12.6 | Title missing brand |
| LH-0020-demo-live.html | Fara IT Limited | 12.5 | Title missing brand |
| LH-0021-demo-live.html | Look N Feel Event Solutions | 12.5 | Title missing brand |
| LH-0022-demo-live.html | Cooper's Bakery Bangladesh | 12.6 | Title missing brand |
| LH-0023-demo-live.html | Rejuvenate Salon & Spa | 12.6 | Title missing brand |
| LH-0024-demo-live.html | JobaidaPack Packaging Ltd | 12.6 | Title missing brand |
| LH-0025-demo-live.html | Fastexpress BD | 12.5 | Title missing brand |
| LH-0026-demo-live.html | Tech Dental Care | 12.5 | Title missing brand |
| LH-0027-demo-live.html | Enhance English BD | 12.5 | Title missing brand |
| LH-0028-demo-live.html | Dhaka Event Planner | 12.8 | Title missing brand |
| LH-0029-demo-live.html | Manchester English Academy | 12.6 | Title missing brand |
| LH-0030-demo-live.html | Laser Dental BD | 12.5 | Title missing brand |
| LH-0031-demo-live.html | Little Arabia Restaurant | 12.6 | Title missing brand |

### calculators-live/ (LH-0001 through LH-0031)

| File | Company | Size (KB) | Issues |
|------|---------|-----------|--------|
| LH-0001-calculator-live.html | Best Interior Design | 11.3 | Title missing brand |
| LH-0002-calculator-live.html | A.K. Developments Ltd. | 11.4 | Title missing brand |
| LH-0003-calculator-live.html | Mazada Group | 11.5 | Title missing brand |
| LH-0004-calculator-live.html | Hitech Inter Studio | 11.4 | Title missing brand |
| LH-0005-calculator-live.html | BD INTERIOR | 11.5 | Title missing brand |
| LH-0006-calculator-live.html | Notun Thikana Properties Ltd. | 11.5 | Title missing brand |
| LH-0007-calculator-live.html | MARJAHANS Jewelers | 11.5 | Title missing brand |
| LH-0008-calculator-live.html | SNAPTRAP Streetwear | 11.6 | Title missing brand |
| LH-0009-calculator-live.html | JG Mart | 11.5 | Title missing brand |
| LH-0010-calculator-live.html | Rongin Interior Solution | 11.5 | Title missing brand |
| LH-0011-calculator-live.html | Kazi Law Chamber | 11.5 | Title missing brand |
| LH-0012-calculator-live.html | Padma Diagnostic Centre Ltd | 11.5 | Title missing brand |
| LH-0013-calculator-live.html | Obokash Travel | 11.5 | Title missing brand |
| LH-0014-calculator-live.html | MIE English Academy Bangladesh | 11.6 | Title missing brand |
| LH-0015-calculator-live.html | Gold's Gym Bangladesh | 11.6 | Title missing brand |
| LH-0016-calculator-live.html | Wedding Diary Bangladesh | 11.6 | Title missing brand |
| LH-0017-calculator-live.html | Metro Weddings | 11.6 | Title missing brand |
| LH-0018-calculator-live.html | Ngital Digital Marketing | 11.6 | Title missing brand |
| LH-0019-calculator-live.html | Ananta Events and Entertainment | 11.6 | Title missing brand |
| LH-0020-calculator-live.html | Fara IT Limited | 11.6 | Title missing brand |
| LH-0021-calculator-live.html | Look N Feel Event Solutions | 11.7 | Title missing brand |
| LH-0022-calculator-live.html | Cooper's Bakery Bangladesh | 11.6 | Title missing brand |
| LH-0023-calculator-live.html | Rejuvenate Salon & Spa | 11.7 | Title missing brand |
| LH-0024-calculator-live.html | JobaidaPack Packaging Ltd | 11.7 | Title missing brand |
| LH-0025-calculator-live.html | Fastexpress BD | 11.6 | Title missing brand |
| LH-0026-calculator-live.html | Tech Dental Care | 11.6 | Title missing brand |
| LH-0027-calculator-live.html | Enhance English BD | 11.7 | Title missing brand |
| LH-0028-calculator-live.html | Dhaka Event Planner | 11.7 | Title missing brand |
| LH-0029-calculator-live.html | Manchester English Academy | 11.7 | Title missing brand |
| LH-0030-calculator-live.html | Laser Dental BD | 11.7 | Title missing brand |
| LH-0031-calculator-live.html | Little Arabia Restaurant | 12.0 | Title missing brand |

## Verdict

**Overall quality: Good.** Files are self-contained, professional, properly sized, and consistently structured. The only systematic issue is the missing "Hope Theory" brand in `<title>` tags across all 62 files — a quick find-and-replace fix.
