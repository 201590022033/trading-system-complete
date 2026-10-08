# R11 — Sasol Open routing and second prospective capture

8 October 2026. Owner requested independent source, pipeline and acceptance investigations, then a narrow numerical research fix. The reviewer reconciled both reports before implementation and both subsequent assertion failures before continuing.

## Source finding and route

OST's signed-in Sasol native history table has Date, Closing (c), High (c), Low (c), Volume and auxiliary columns, but no Open. Its existing parser already accepts an explicit Opening (c) if supplied; none was observed in the native table. Retained canonical Sasol remains 600 OST bars through 5 October with all Open values absent. IRESS's independent `SOL.JSE` daily table supplies full OHLCV. No previous close, auction value or first intraday print is substituted for daily Open.

The missing route was a v3 cutover regression: IRESS candidate registration did not enter the collector, v3 normalization dropped a supplemental chart, and the research selector returned OST HLCV. ADR 0061 extends those existing paths with a separate whole IRESS chart. Canonical charts and accounting retain OST. The local onboarding API and hosted research status show numerical source receipts and unresolved definitions. The read-only audit reports exact differences from both full histories.

## Capture two

Browser Copy supplied 537 raw rows; 536 completed sessions span 16 August 2024–7 October 2026. The live 8 October zero-volume row was excluded. Copy timestamps at 22:00 UTC on the previous day map to the displayed SAST session date. All 2,680 completed OHLCV values, including 536 Opens, were checked against the raw export with prices converted from integer cents to ZAR and volumes retained as whole reported units.

| Receipt | Value |
| --- | --- |
| Actual acquisition | 2026-10-08T06:40:48.731954+00:00 / 08:40:48.731954 SAST |
| Raw SHA-256 | `3f0cfc3d7a8a96414b655d6fa7f55757ecb14a74835726ed2a78c5573fa66bf2` |
| Latest completed session | 7 October 2026 |
| Latest Open / High / Low / Close | R237.30 / R246.35 / R233.90 / R240.46 |
| Latest reported volume | 2,831,535; eligibility definition unverified |
| Original capture | 308 bars through 6 October; SHA `e4de05c92eeca2027d35976263fd54314d9fe49c2651fe8b1a83af3cbe2dea13` |
| Change versus original | One new latest session plus 227 older context sessions; zero revisions across all 308 overlapping bars |
| R10 | Two separate immutable IRESS captures; two first-seen anchor sessions; 0 clean and 2 pending for each 3/4/5-session cohort |

The older context rows are not new prospective observations. Neither capture nor historical availability was backdated. The first capture file is unchanged. Further genuinely later captures are needed; capture count is not mature outcome count.

A separate native OST STX40 export was downloaded at 06:46:21.140281 UTC and imported with its file receipt time. It retains 600 completed HLCV benchmark bars through 7 October, no fabricated Opens, raw SHA `a6af9fc9dcc1dbbb83d56c4bc62a3bd09861c9cba2e469df4e8efcb1ad2c303e`. Refreshing the benchmark resolves latest-session alignment without mixing any Sasol fields.

## Independent comparison

An independent expected comparison of archived raw exports was saved before changing the float comparator. Its 534-session overlap has zero closing differences, 14 high/low discrepancy dates and nine volume discrepancy dates: 23 distinct dates. The expanded history accounts for the increase over yesterday's shorter-window seven dates. All dates, fields, integer values and deltas match the refreshed audit. The expected file's informal volume label “shares” was preserved but not accepted as a verified definition; comparison separately checks conservative `VOLUME_UNITS_UNVERIFIED` labels.

High/low dates: 2024-08-16, 09-13, 09-17, 09-30, 11-06, 12-02; 2025-01-13, 05-13, 05-20; 2026-02-04, 07-16, 07-27, 07-31, 08-25. Volume dates: 2024-10-02, 10-15, 10-16, 10-21, 11-21; 2025-02-24, 03-14, 12-08; 2026-01-19. Raw and parsed source fields remain separate. These differences are unresolved provider observations, not reasons to synthesize a bar or deny use of already observed Open for descriptive numerical research.

## Proof of numerical consumption

The actual collector saves six canonical OST charts plus the separate 536-bar IRESS chart in v3. Raw-bound normalization and repository roundtrip tests prove research Open survives collection/storage and is returned by `get_research_chart`, while canonical `get_chart` still has no OST Open. Worker composition tests prove the frozen shadow chart is IRESS, its technical receipt is IRESS, and canonical identity/accounting inputs remain OST. Removing Open from that same research input makes the actual OHLC gate report `REAL_OHLC_UNAVAILABLE` and ATR null.

The actual current snapshot, evaluated on 8 October for 7 October, is AVAILABLE with no missing inputs: Open R237.30; Wilder ATR14 8.7517905282; RSI14 68.0481090406; EMA20 227.0697101894; EMA50 213.7550688154; relative volume20 0.6873078493; relative return20 0.2170521823. Dashboard browser verification displays these values with raw hash, original acquisition, provider and unverified definitions. Availability does not assert a qualifying setup or measured edge. Current preview remains separate from older frozen decisions; no manual worker or model run was forced.

One focused test initially indexed the absent canonical Open key. Independent diagnostics and reviewer confirmed the existing worker deliberately omits null optional fields; the assertion now checks `.get('open')`. The raw oracle comparison initially failed only on the volume unit label. Both independent investigators and the reviewer confirmed exact numerical equality before that assertion was corrected; the comparator was not changed again.

Final review also found a validation failure could return a locally attached chart before normalization. Independently reviewed correction validates a separate merged view with the current observation time and returns unchanged canonical data on failure. This supports a genuine IRESS capture newer than the last OST import while preserving both source acquisition times. Regression checks cover validation failure, stale primary data, raw tampering and exclusion of the captured live row. A test-only method-boundary error was independently reconciled and corrected before rerunning verification.

Final verification: 38 focused tests, 980 safe offline tests (92.942 seconds), 54/54 protected artifact checks and JavaScript syntax check pass. Local dashboard restarted hidden and verified visibly. Capture and source evidence are retained in ignored runtime storage, not committed broker files.

## Cost inspection and bounded remaining evidence

The [official OST tariff page](https://onlinesharetrading.standardbank.co.za/standimg/OST/fees-and-costs.html) was inspected on 8 October. It has no established effective date and conflicting Strate footnotes; its statutory table supports the existing cash-share sensitivity: brokerage 0.5%, minimum R110 excluding VAT; purchase-only STT 0.25%; Strate 0.006018% bounded by R6.29/R142.20; levy 0.00033%. Dated account-specific applicability, levy VAT and invoice rounding remain unverified. No cost adapter was changed.

The same public page separately lists CFD fixed brokerage R50 excluding VAT and market-maker commission 0.35%, with a conditional intraday exit rate 0.20%. Basic delayed ViewPoint is free; displayed live packages are R175/R195 including VAT; ad-hoc file/data requests R50 excluding VAT. Displayed quote tariffs are 19c depth, 13c without depth and 11c index, while delayed prices are described as free. These are publicly observed estimates, not the owner's actual invoices.

An observed portfolio CFD link's `Trade/D.aspx?...priceTypeSelection=Delayed` route unexpectedly opened live depth and reduced the quotes bank by 19c. The page was closed immediately; no order quantity, direction or password was entered, and no order was submitted. The effect was disclosed to the owner. The page displayed projected brokerage R50 and VAT R7.50, not settled charges. A transient 26-cent underlying spread was visible; it is not a historical execution/slippage series. The reviewer reconciled both independent cost diagnostics and stopped further authenticated broker navigation to avoid more automatic quotes.

Actual entry brokerage/taxes, posted overnight financing, account data charges and actual exit costs remain unavailable from verified contract notes/statements. An open CFD position cannot establish cash-share costs. The public page has no dated account contract. Existing posted transaction statements/contract notes are the safe next evidence source; a bank reply is not required to continue numerical research. Account identifiers, contact details, holdings and balances are excluded from this committed report. Minimal dated cost observation is retained locally.

## Remaining gates

B5 stays PARTIAL_CLOSED; real-data admission false. Historical AI evaluation remains blocked on price adjustment/corporate-action completeness, volume/interval conventions and reconstructed historical availability. Actual execution also requires dated product/account costs, historical quotes/fills/slippage/capacity and separate FX/gold contracts where used. Live trading remains disabled. R10 outcomes need genuinely future source-consistent captures; two captures do not create 3/4/5-session outcomes. Descriptive numerical research may continue now without awaiting a bank definition or promoting any strategy.

Runtime artifact navigation (ignored): `runtime/local-swing-data/incoming/SASOL-IRESS-2026-10-08.csv`, `alternative-exports/SASOL-IRESS-{sha}.csv`, `prospective-price-captures/SASOL/IRESS/`, `source-resolution-latest.json`, `diagnostics/2026-10-08-independent-comparison.json`, `diagnostics/2026-10-08-routing-verification.json`, `diagnostics/2026-10-08-dashboard-ireSS.jpg`.
