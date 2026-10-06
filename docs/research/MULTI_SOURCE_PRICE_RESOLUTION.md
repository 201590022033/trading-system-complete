# Multi-source JSE price-resolution workflow — 6 October 2026

Earlier Sasol opening prices came from the captured ViewPoint/IRESS `SOL.JSE` daily table. That table has 250 complete OHLCV sessions through 5 October. The local R6 audit registered it as an independent, hash-backed candidate. All 250 overlapping OST closes match; four sessions differ on high/low and two on volume. Its historical adjustment/action, volume and availability definitions are unverified. Saved pre-cutover Yahoo has 19 invalid Sasol OHLC bars. The primary OST series remains HLCV, with Open absent; no fields were blended or silently repaired.

On each local dashboard refresh, `/api/v1/ost/onboarding` now includes a source-resolution plan for all 22 registered JSE instruments. The existing daily collector also writes the same audit to ignored `runtime/local-swing-data/source-resolution-latest.json` before any scheduled upload. The plan identifies a specific next action: import OST history, obtain or refresh a whole-source OHLCV alternative, review provider disagreement, or verify source semantics. In the local Trading Strategies dashboard, **Register an IRESS full-history candidate** accepts an explicit stock, captured daily CSV and actual SAST time. The same-origin local route is disabled on Railway. A CLI alternative is `python scripts/register_price_candidate.py --instrument SASOL --origin-symbol SOL.JSE --file <captured-table.csv> --acquired-at <actual-time-with-offset>`. A future stock uses its own exact registered JSE symbol. Raw exports and normalized candidate receipts live only in ignored local runtime storage. Repeated bytes retain the original receipt. A missing or modified raw file invalidates the candidate; stale receipts expire after four days.

Source route status is deliberately evidence-based:

| Source | Current role | Current limit |
| --- | --- | --- |
| OST | Primary JSE HLCV history | No opening field in observed exports; some HLC inconsistencies |
| ViewPoint/IRESS | Separate complete Sasol OHLCV candidate | Other instrument exports and provider definitions still needed |
| Yahoo | Archived quality comparison | Saved JSE histories contain invalid OHLC; no automatic fallback |
| ShareData/ProfileData | Candidate data/export route | Free versus subscriber export entitlement and a reusable OHLCV format have not been verified. [ShareData FAQ](https://www.sharedata.co.za/v2/Scripts/Directory/FAQ/faq_General.aspx); [ProfileData downloader](https://www.profile.co.za/chart_downloads.htm) |
| JSE | Exchange historical-data route | Historical products and licensing/access are separate from a free CSV feed. [JSE equity data](https://www.jse.co.za/market-data/our-market-data-products/equity-market-data); [historical data](https://www.jse.co.za/data/historical-data) |
| SharePoint | Optional storage for approved source files | It creates no market prices. [Microsoft documentation](https://learn.microsoft.com/en-us/sharepoint/sharepoint-storage-planning) |

The comparison does not certify corporate-action adjustment, volume coverage, historical point-in-time availability, exchange calendar or execution prices. It never promotes IRESS, Yahoo or a future source into the OST primary lane automatically. B5 stays PARTIAL_CLOSED and historical AI remains gated. R6 removes the repeated investigative dead end by making source evidence and the next acquisition/verification action part of the normal workflow.

Railway displays the generic provider route and explicitly labels alternative exports as local-only. It does not hold the captured IRESS table or pre-cutover Yahoo archive; the local dashboard is authoritative for those source-candidate checks.
