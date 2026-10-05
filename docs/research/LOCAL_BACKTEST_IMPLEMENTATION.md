# Local engine implementation record

B1 active: data/time contracts and independent oracle harness. Existing checkout verified clean at e6f47b0, master, expected origin. Baseline 869 offline safe tests passed (60.338s); protected verifier 54/54 passed. Authorization now covers B1–B5, superseding B0's planning-only scope.

B1 interfaces: immutable `domain.backtest.data.Manifest`, `Session`, `Bar`; raw prices, explicit actions, timezone-aware availability, complete expected-session windows, immutable content hashes. Toy holiday calendar is explicitly synthetic. Reconstructed archives do not establish historical availability. New research modules do not wire into runtime.

The independent fixture fixes Monday-close entry 102, stop 90, third subsequent session Friday close 106, ten shares, two-unit fee each way, cash 2036 from 2000. It is authored arithmetic, not implementation-generated truth.

B1 completed: three independent fixture/admission tests passed; full safe suite 872/872 (59.644s); protected 54/54; diff check passed. Calendar fixtures include a holiday, missing-session refusal and future changes ignored before availability. No real calendar/provider admission claim is made.

## B2 implementation semantics

`domain.backtest.engine.replay` is a pure offline callable. Frozen policy adaptation uses `from_frozen_policy`; existing technical snapshots and 1.2.0 definitions stay unchanged. Entry is first later available completed close, with stop-touch invalidation before that close. Entry session excluded; horizons are 3/4/5 manifest sessions. Gap ordering uses open, then adverse stop-first range, then target, then horizon close. Trails are close-armed, tighten only and apply to subsequent sessions. Two trailing choices (ATR/structure) are research parameters; no promotion occurs.

Capital orders reserve their declared maximum; equal-time orders sort by immutable ID, carried exits across instruments precede entries. Costs charge explicit fee/minimum, half-spread and slippage separately. Quantities shrink with risk distance and round down to product lots. Raw split shares/levels and dividends are applied once; adjusted series are refused. Cash ledger plus marked positions supplies equity. Short/margin requires an explicit later adapter. Full fills and cent precision are disclosed assumptions. Daily range excursion ordering is unknown; no intraday bars are fabricated.

Independent oracle and bounded paths cover accounting, stop/target gaps, ambiguous ranges, trail timing, end-of-data censoring, future changes, competing orders, wider-stop sizing and actions. Frozen baseline comparison checks 3/4/5 outcomes, with deliberate differences: declared toy calendar instead of observed sessions, portfolio currency costs instead of return-bps subtraction. Four disposable mutants are killed with assertion failures (future access 1, stop ordering 1, duplicate fill 3, removed fees 2). Tests never alter production files.

B2 completed: 13 focused local tests passed; full safe suite 882/882 (61.116s); four/four mutants killed; protected artifacts 54/54. Independent arithmetic uses Decimal with cent currency rounding. No profitability or real-market fill acceptance claimed.

## B3 product contracts

`Forex` and `Gold` adapters declare quote/account currency, contract multiplier/lot, collateral fraction, session identity, before-open conversion observations and signed LONG/SHORT financing per calendar day. FX has no share-volume requirement: absent activity is a price-only branch; provider ticks and exchange contracts remain separately named. USD/ZAR quote direction is explicit; reciprocal bid/ask swaps ask/bid. Theoretical timestamp-aligned XAU/ZAR is marked nonexecutable. Gold CFD and fixed futures contracts use distinct activity contracts; continuous rolls and instrument changes are refused. Roll research must close the old contract and open a separate contract with its own manifested raw prices and costs; no implicit synthetic roll P&L. ETF/miners continue through cash-equity identity and calendars; underlying gold bars cannot impersonate their traded sessions.

Hand arithmetic: FX LONG 100 units at 18 ->18.5 gives 50 gross, 4 fees and .72 calendar-day financing ->2045.28 cash from 2000. SHORT counterpart at 18 ->17.5 charges 1.44 carry ->2044.56. Gold multiplier/conversion fixture gives 7600 gross ZAR P&L, 4 fees and 27596 final cash from 20000. Quotes at settlement supply P&L translation, collateral is fixed in account currency. Conversion/carry/multiplier inputs enter the config hash. Replay fixes Decimal context to 28 digits and cent half-up rounding independently of caller state. Session availability must be monotonic; unsupported reordered publication is rejected.

Limitations: this is a collateral/P&L research model, not a maintenance-margin/broker liquidation simulator, borrow availability model, exchange variation-margin engine or broker triple-roll schedule. Historical conversion reconstruction and hypothetical financing do not validate actual product costs. Synthetic tests cover mirrored stops/gaps, quotes, financing, missing conversions, future contract identity and calendar mismatch. Real product fill/cost/margin validation remains a B5 gate.

B3 completed: 19 focused local tests passed (including six FX/gold tests); full safe suite 888/888 (60.784s); protected 54/54; four mutants still killed. No broker connection or market acceptance is inferred.
