# Local Swing replay: operating and integration guide

Engine version `local-daily-replay-v1`; runner `local-indicator-selection-v1`. Research-only working implementation. B1–B4 are complete locally. B5 software verification is complete when recorded below; real-market acceptance is BLOCKED. No dashboard, Railway worker, default strategy or broker wiring is included.

## Run offline

Use Python 3.12 with the existing project environment/dependencies. From the existing repository checkout:

```powershell
$taskPython = 'C:\Users\Deon\Documents\GitHub\trading-system-complete\.venv\Scripts\python.exe'
$taskOutput = 'C:\Users\Deon\Documents\Codex\2026-10-05\local-swing-backtest-engine\outputs\reports'
& $taskPython scripts/run_local_backtest_example.py --output $taskOutput
& $taskPython scripts/run_local_indicator_example.py --output $taskOutput
& $taskPython scripts/audit_local_backtest_data.py --output "$taskOutput\real-data-admission-audit.json"
& $taskPython scripts/run_tests.py
& $taskPython scripts/verify_local_backtest_mutations.py
& $taskPython scripts/verify_local_selection_mutations.py
& $taskPython scripts/verify_protected_artifacts.py
```

Examples are synthetic, deterministic and use no provider/model/broker calls or credentials. The safe suite disables external sockets and dotenv. The indicator journal freezes code/config/dataset versions: after changing code or inputs use a distinct new study with a fresh final period, not deletion/reuse of a viewed evaluation period. The supplied toy experiment is never market evidence. Keep the real research programme's journal and immutable input/report files together with backups.

## Callable boundary for later wiring

```python
from domain.backtest.engine import replay, Signal, Costs, Action
from domain.backtest.data import Manifest, Session, Bar
from domain.backtest.products import Forex, Gold, GoldListed
from domain.backtest.legacy import from_frozen_policy
from domain.backtest.selection import Candidate, Fold, Journal, run_study
```

`Manifest` is immutable and hashes the complete instrument/product/currency/provider, raw price and activity basis, retrieval/revision, universe/action basis, declared sessions and bars. `Session` records timezone-aware open/close times. `Bar` records availability independently of session completion. `Manifest.admit(start, end, as_of, activity_required=...)` refuses missing/duplicate/out-of-order windows, delayed/unavailable data, estimates, invalid prices, unknown calendars and invalid required activity. Declare synthetic calendars honestly. A historical download does not prove point-in-time availability. If an unaffected window is independently qualified, build and freeze a separate explicit window manifest with sufficient signal/feature history; do not compress gaps.

`Signal` declares immutable ID, instrument, source session, decision time, initial stop, maximum cash/collateral reservation, price-risk budget, direction and horizon. Optional profile ID/version must be an exact pair. Initial stop must already be observable. Risk budget is price-distance sizing; fees/carry and adverse gaps can increase total loss beyond that budget. Capital sizing includes entry fees. `from_frozen_policy` accepts only the unchanged Swing 1.2.0 definition and retains its exact profile lineage; it does not change that profile's rules or activate a new version.

`replay(manifests, signals, as_of=..., initial_cash=..., account_currency=..., costs=..., actions=..., adapters=...)` returns JSON primitives: decisions, hypothetical trades, explicit fees/financing/distributions, cash ledger, equity series, reserved funds, pending orders/open positions, dataset/config hashes and semantic hash. No broker capability is exposed. Full-fill assumptions and close proxies are explicit. Accounting uses 28-digit Decimal arithmetic and cent half-up rounding; supported account currencies are ZAR/USD. Repeated frozen inputs yield identical semantic reports. Changing future input/revision hashes changes provenance, while earlier observable decisions/fills stay invariant.

New orders reserve their full maximum in ID order at equal timestamps. First later completed close supplies entry; pre-entry stop touches invalidate. Entry session is excluded from 3/4/5 held sessions. Carried opening gaps precede daily range tests, stop precedes target on ambiguous ranges, then horizon close. Completed-close trails arm at +1 initial R, tighten only, and apply next session. Daily favorable/adverse excursion values are range bounds with unresolved exit-bar ordering. End-of-data positions remain open and marked, never silently closed. No partial-fill, order-book capacity or exact intrabar-fill claim is supported.

`Costs` requires explicit nonnegative fee bps/minimum, quoted full spread bps and per-side slippage bps with a named provenance basis. Spread/slippage are embedded in adverse fill prices; ledger metadata discloses their impacts without charging them twice. Gross P&L, net P&L, fees and financing reconcile. Raw split actions rebase positions, pending stops and prior feature history; dividends create one cash distribution. Input manifests remain immutable; adjusted prices are refused to prevent double counting. Do not use the selection runner on unresolved action histories: its first catalogue fixture is action-free, and real action-dependent indicator experiments require an explicit feature-adjustment adapter before admission.

Cash equity is LONG-only. `Forex` handles explicit USD/ZAR margin/carry, with price-only or named tick/exchange activity; it has no traded-share gate. `Gold` accepts a specific spot CFD or fixed futures contract, refusing theoretical gold and rolled continuous prices. Rolls require separately manifested contract close/reopen and actual prices/costs. `GoldListed` models cash LONG listed units with their own venue calendar and optional dated conversion, without a share-volume requirement. Miners remain equities. Before-open conversion snapshots declare a conservative session-fixed rate; their historical accuracy and actual settlement timing need separate validation. Margin is a collateral/P&L model, with no maintenance-margin liquidation, futures daily variation settlement, broker-specific triple-roll schedule or guaranteed short borrowing.

`run_study` requires existing registered, exactly attributed `ExperimentDefinition` records with every dataset/fold/final boundary and candidate hash. `Candidate` changes one bounded indicator relative to the baseline; a simple price-only control is mandatory. `Fold` fits features on chronological training only, selects on validation only and tests frozen rules on an outer period. Full five-session label intervals and embargo are shared across instruments. Final period is durably locked before inspection. All 3/4/5 outcomes, matched controls, radar/non-radar cohorts, rejected/warmup/purged denominators and trial receipts remain in the report. Definitions, code and dataset hashes enter the frozen study hash. Registry results reuse existing metric contexts; event observations never supply portfolio drawdown/annualized return. The runner is exploratory, with bounded trials and clustered descriptive uncertainty, not multiple-testing-adjusted proof or automatic adoption. Preserve journal provenance even for failures and inconclusive candidates.

## Acceptance and integration review

Completed synthetic gates: independent cash/price fixtures, calendar/availability admission, conservative LONG/SHORT gaps and ambiguity, trailing timing, three horizons, competing capital, cent rounding and explicit costs, raw split/dividend accounting, FX quote/margin/carry, gold multiplier/conversion/listed identity, training-only normalization, shared purging, immutable trials/final lock, deterministic restart and seven assertion-killed defects. Existing baseline replay and protected artifacts are preserved. Independent numeric tolerances: exact cents for cash; fixed rational/Decimal answers for price/risk; existing floating indicator seeds tested to their repository tolerances (approximately 1e-12 in numeric comparisons).

B5 external gates remain BLOCKED: source-verified sessions; consistent raw OHLC/actions and units; dated historical identities/universe; defensible historical availability; actual vehicle costs, spreads, liquidity/full-fill envelope; actual intraday path comparison; and FX/gold conversion, carry, margin/roll/product validation. The archived 21-instrument daily slice contains 5271 bars and 883 OHLC inconsistencies; it has no qualifying manifest. Four older HR2 CSVs are reconstructed histories without the required execution manifests. The available prior IG research manifest has zero admitted bars. No real trade audit or real-market fill validation was possible; none was fabricated. These gates require external source/data evidence, then independent recalculation of admitted real trades and cost/liquidity stress. Sufficient prospective independent evidence and existing M15 gates are additionally required before strategy adoption.

Integration review may inspect/reuse this local callable boundary and reports. Full engine acceptance, feedback-loop/dashboard wiring, production promotion, deployment and Live orders remain outside this delivery.
