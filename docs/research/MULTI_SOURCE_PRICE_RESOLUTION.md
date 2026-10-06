# Multi-source JSE price-resolution workflow — 6 October 2026

Earlier Sasol opening prices came from the captured ViewPoint/IRESS `SOL.JSE` daily table. That table has 250 complete OHLCV sessions through 5 October. The local R6 audit registered it as an independent, hash-backed candidate. All 250 overlapping OST closes match; four sessions differ on high/low and two on volume. Its historical adjustment/action, volume and availability definitions are unverified. Saved pre-cutover Yahoo has 19 invalid Sasol OHLC bars. The primary OST series remains HLCV, with Open absent; no fields were blended or silently repaired.

On each local dashboard refresh, `/api/v1/ost/onboarding` now includes a source-resolution plan for all 22 registered JSE instruments. The existing daily collector also writes the same audit to ignored `runtime/local-swing-data/source-resolution-latest.json` before any scheduled upload. The plan identifies a specific next action: import OST history, obtain or refresh a whole-source OHLCV alternative, review provider disagreement, or verify source semantics. In the local Trading Strategies dashboard, **Register an IRESS full-history candidate** accepts an explicit stock, captured daily CSV and actual SAST time. The same-origin local route is disabled on Railway. A CLI alternative is `python scripts/register_price_candidate.py --instrument SASOL --origin-symbol SOL.JSE --file <captured-table.csv> --acquired-at <actual-time-with-offset>`. A future stock uses its own exact registered JSE symbol. Raw exports and normalized candidate receipts live only in ignored local runtime storage. Repeated bytes retain the original receipt. A missing or modified raw file invalidates the candidate; stale receipts expire after four days.

Source route status is deliberately evidence-based:

| Source | Current role | Current limit |
| --- | --- | --- |
| OST | Primary JSE HLCV history | No opening field in observed exports; some HLC inconsistencies |
| ViewPoint/IRESS | Separate complete Sasol and four ETF OHLCV candidates | Provider definitions still needed; these histories are local research candidates only |
| Yahoo | Archived quality comparison | Saved JSE histories contain invalid OHLC; no automatic fallback |
| ShareData/ProfileData | Candidate data/export route | Free versus subscriber export entitlement and a reusable OHLCV format have not been verified. [ShareData FAQ](https://www.sharedata.co.za/v2/Scripts/Directory/FAQ/faq_General.aspx); [ProfileData downloader](https://www.profile.co.za/chart_downloads.htm) |
| JSE | Exchange historical-data route | Historical products and licensing/access are separate from a free CSV feed. [JSE equity data](https://www.jse.co.za/market-data/our-market-data-products/equity-market-data); [historical data](https://www.jse.co.za/data/historical-data) |
| SharePoint | Optional storage for approved source files | It creates no market prices. [Microsoft documentation](https://learn.microsoft.com/en-us/sharepoint/sharepoint-storage-planning) |

The comparison does not certify corporate-action adjustment, volume coverage, historical point-in-time availability, exchange calendar or execution prices. It never promotes IRESS, Yahoo or a future source into the OST primary lane automatically. B5 stays PARTIAL_CLOSED and historical AI remains gated. R6 removes the repeated investigative dead end by making source evidence and the next acquisition/verification action part of the normal workflow.

Railway displays the generic provider route and explicitly labels alternative exports as local-only. It does not hold the captured IRESS table or pre-cutover Yahoo archive; the local dashboard is authoritative for those source-candidate checks.

## R7 ViewPoint check — 6 October 2026

The signed-in ViewPoint `Chart (New)` widget exposed `SOL.JSE`, `STX40.JSE`, `STXFIN.JSE`, `STXRES.JSE` and `STXIND.JSE`. On a 1-day candle chart, **More Options → Table View → Show Additional Columns** exposed Date, Open, High, Low, Close and Volume. The table's **Copy** action supplied a CSV with the JSE session encoded as 22:00 UTC on the preceding date; the local parser now converts that timestamp to SAST before validating completed sessions. The 6 October live row was excluded from each 250-bar candidate. The copied raw bytes and source receipts are kept in ignored local storage. The Download control did not produce a browser download event in this session; Copy is the verified acquisition path. The chart Events menu offered News and Dividends, while Preferences exposed range, scale and theme controls. Neither displayed an adjustment/RAW price setting or a volume eligibility definition.

| Instrument | IRESS completed sessions | OST overlap | Close differences | High/low differences | Volume differences |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sasol `SOL.JSE` | 250 | 250 | 0 | 4 | 2 |
| Top 40 ETF `STX40.JSE` | 250 | 250 | 0 | 1 | 2 |
| Financial ETF `STXFIN.JSE` | 250 | 250 | 0 | 9 | 0 |
| Resources ETF `STXRES.JSE` | 250 | 250 | 0 | 14 | 1 |
| Industrials ETF `STXIND.JSE` | 250 | 250 | 0 | 18 | 0 |

The comparison is between independent complete histories, not a blended bar. It establishes matching closes over the observed year but does not establish why some extrema and volumes differ. The current [ViewPoint guide](https://www.iress.com/media/documents/AU_ViewPoint_User_Guide.pdf) describes charting and dividend widgets; [Iress's ViewPoint FAQ](https://www.iress.com/software/trading-and-market-data/html-upgrade/frequently-asked-questions/) advertises an extensive historical chart database. Neither states the adjustment, eligible-trade volume or historical as-of/revision contract needed here. One present-day year of history also cannot prove what an analyst could have observed at an earlier date. The R7 decision is **no promotion**: OST remains primary HLCV, IRESS remains five separate local OHLCV candidates, historical AI/B5 admission stays gated, and no source fields are spliced. The next evidence needed is a dated ViewPoint/JSE chart-data definition covering corporate-action adjustments, volume scope, revisions and point-in-time availability, plus a checked corporate-action example. This is a provider evidence request, not another stock-by-stock coding exercise.
