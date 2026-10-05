# Current milestone — R1 read-only research integration

Owner approved B5's partial close and proceeding on 5 October 2026. B5 is PARTIAL_CLOSED, not fully accepted: its software/source/accounting preparation is delivered while real-data admission and provider semantics remain deferred gates. Zero admitted real trades. ADR 0051 records the explicit scope change.

R1 is ACTIVE: integrate a bounded safe report summary into the existing Trading Strategies dashboard through a read-only API. Show source comparisons, dated verification and unresolved data gates; retain unavailable states. No provider calls or engine replay on refresh. IG runtime access is a separate check, not an assumed integration benefit. Acceptance includes safe schema/tamper refusal, a reviewed local preview, focused/full safe tests and protected checks.

## Historical B5 checkpoints

Latest continuation: source research now includes 33 official Sasol SENS PDFs and issuer dividend corroboration. A separately written offline cash oracle prepares 36 conditional observed-price probes and passes 72 directional fee comparisons. No manifest/replay admission bypass occurred; real trades admitted remain zero. RAW/action and provider interval/volume contracts remain unresolved. Cash-only research scope is permitted by the original specification; real broker fills and historical invoices limit execution readiness, while unsupported real FX/gold can remain blocked. See ADR 0050 and the latest section of `LOCAL_BACKTEST_B5_CONTINUATION.md`. No following milestone is active.

Verification for this continuation: 921 safe tests pass (87.686s), 54 protected artifacts pass, independent reference byte-identical on repeat, all 736 existing stress-report fees match its independent arithmetic, and two fixed hand fee answers pass. No engine/selection change; eight killed mutation results are retained from the earlier applicable run.

## Autonomous continuation — 5 October 2026

Owner requested autonomous completion. This continuation resolved the official daily calendar/access gate and implemented the outstanding directional cash fee adapter; **full B5 remains BLOCKED on external evidence**, with zero admitted real trades. No following milestone is active.

Browser-acquired JSE notice 380/2025 and EquityMarketTradingHours PDFs were frozen and inspected. The 1 September–2 October window has 23 weekdays excluding the green-marked 24 September public holiday; broad equity hours are explicitly 09:00–17:00 SAST. This establishes the daily schedule, not every trade-reporting phase or the chart's interval convention.

OST native history export contains 8,457 unique dates from 1994–2026. Pilot high/low/close/volume matches IRESS daily on 23/23 dates and Sharenet on ten available dates. IRESS 391 intraday observations aggregate to all 23 daily OHLC values; daily volume remains larger on every date. A native IRESS OHLC CSV in Downloads has 177 UTC-stamped rows matching the captured table interpreted in SAST on all 177; it contains no volume. The bar start/end convention and adjustment/volume policy remain unverified.

Opt-in `OSTCashShareCosts` reuses the published component formula, includes fees in sizing, applies purchase-only tax and rejects inappropriate products. ADR 0049 records scope and assumptions. 368 post-hoc cost/daily-capacity cases were generated; maximum modeled position is 0.024953% of observed daily volume, which does not certify closing liquidity or full fills. ShareData's detailed calendar required Premium, the 2016 broker chart guide did not define volume/timestamp filters, and both available local .env files still lacked complete IG credentials. No subscription, terms acceptance, authentication credential export or broker mutation was performed.

Verification: 26 focused tests pass; 921/921 safe tests pass in 87.851s; five engine/cost and three selection mutations killed; protected 54/54 pass. Existing equity/FX/gold example semantic hashes remain identical. Stress report reproduces byte-identically. Remaining gates: complete action/adjustment evidence; provider interval/volume semantics; reconstructed historical availability contract; historical account tariff/quotes/fill evidence; own real FX/gold product evidence. See `docs/research/LOCAL_BACKTEST_B5_CONTINUATION.md` for artifact navigation and resolution criteria.

## Earlier checkpoints

Historical SENS integration/test slice completed locally on 5 October 2026: ShareData ten full-text notices, Moneyweb ten search leads with subscriber body still gated, Sharenet one public full-text notice. Twenty-one records group into ten releases in the same Sasol window; zero qualify as September point-in-time evidence. 917 safe tests and 54 protected artifacts passed; the final capture-provenance hardening passed 17 focused tests. Offline context audit reproduced byte-identically. See [SENS evidence and operating interface](../research/LOCAL_SENS_HISTORY.md). Full B5 remains BLOCKED on the external acceptance evidence below; no following milestone is active. The earlier acquisition/audit results are preserved as a checkpoint.

Date: 5 October 2026. Status: BLOCKED on external acceptance evidence; the resumed acquisition/audit slice is completed locally. Starting master HEAD 9ce6ea0ed416e7ec4db13621579c271b43c4cf4a; working tree was clean, expected origin verified. Owner authorized full B5 with flexible use of existing Yahoo, IG and Alpha Vantage integrations. No following milestone is active; wider integration remains deferred.

Work: bounded provider discovery/acquisition with isolated caches, source-verified identity/units/session/action/availability contracts, independent real-trade/accounting audit and cost/liquidity/intraday/product checks. Do not relax admission when a provider is absent, blend cash and CFD products, synthesize bars, print credentials, bulk-call paid APIs, change hosted configuration or submit broker orders. Continue independent gates if another data gate blocks.

Prior delivery: B1–B4 completed; 900 safe tests and 54 protected artifacts passed. Seven deliberate defects caught. Prior daily archive contained 883 inconsistent OHLC bars among 5271; prior intraday manifest had zero admitted bars. Provider access and new evidence must be reassessed rather than assumed from those old results.

New results: 23 fresh numerically valid Yahoo SOL daily bars and 368 actual 30-minute bars frozen; zero complete daily/intraday aggregates reconcile. Issuer identity/no-final-dividend evidence and current cash-share fee sensitivity recorded. Alpha search found no verified JSE mapping, and the shared five-reservation local probe budget was exhausted; no further FX/gold calls made. IG credentials unavailable in both relevant local checkouts. Official JSE calendar/session libraries returned HTTP 403. No action-complete, calendar-verified window was admitted; zero real trades audited.

Final verification: 906/906 safe tests passed in 86.994s, all seven disposable mutations killed, 54/54 protected artifacts passed. New diagnostics have six independent tests. Frozen offline report reproduced byte-identically. No default strategy, scheduled collector, external broker account, hosted configuration or production wiring changed. No push/deploy.

Required to unblock: verified exchange/session/action evidence; explicit reconstructed availability contract; complete intraday closing coverage and units; dated costs/quotes/capacity; own executable FX/gold contract/conversion/carry/margin evidence. Then admit the bounded window and independently reconcile actual-price hypothetical trades/cash/equity. See [full B5 attempt and evidence](../research/LOCAL_BACKTEST_REAL_DATA_ACCEPTANCE.md).
