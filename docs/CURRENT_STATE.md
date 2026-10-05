# Current project state — 5 October 2026

This is the current operating snapshot, reconciled against code at `c2ef802` and the dated acceptance records. Settings and provider results below are observations from that checkpoint, not promises of permanent availability. See the [document index](DOCUMENTATION_INDEX.md), [recent changes](changes/2026-09-21-to-2026-10-05.md), [current architecture](architecture/CURRENT_ARCHITECTURE.md), and [target architecture](architecture/TARGET_ARCHITECTURE.md).

## What is running

The dashboard uses the canonical opportunity pipeline: public research inputs → M13 opportunity ranking → M14 TradePolicy → M15 RiskEngine veto → paper sizing/broker → durable outcomes and contextual evaluation. M16 StrategyTarget records evaluation requirements separately; a target is not permission to trade. The old multi-agent and 60/30/10 paths remain preserved benchmarks and diagnostics, not the default Top-5 implementation.

The dashboard has Portfolio & demo, Trading Strategies, Canonical Top-5, Market AI / News, Technical Intelligence, and System sections. Strategy cards come from a read-only backend registry. Printable paper worksheets and authenticated manual Demo trade capture are implemented. A captured trade is operator-reported evidence, not an independently verified fill or AI training sample. IG account reads distinguish Demo and Live balances; the paper simulator's R100,000 is separate from connected cash.

| Profile | Registry default | Capability today |
| --- | --- | --- |
| JSE Swing Trader 3–5 Day | `jse_swing_3_5d@1.0.1` | ACTIVE_RESEARCH/PAPER; canonical workflow with exact attribution |
| Intraday CFD 5–60 min | `intraday_cfd@1.0.0` | DEVELOPMENT/DATA_VALIDATION_REQUIRED; reusable HR11 infrastructure, no admitted strategy |
| Long-Term Investment | `long_term_investment@1.0.0` | DEVELOPMENT; no investment model, ranking or execution capability |

Swing versions are immutable experiments, not automatic upgrades:

| Version | Meaning |
| --- | --- |
| 1.0.0 | Original foundation record; attribution was then planned |
| 1.0.1 | Current canonical default; paired profile ID/version retained through new records |
| 1.1.0 | Separate EMA20/50, Wilder RSI/ATR14, relative volume, and 3/4/5-session technical shadow |
| 1.2.0 | Separate cash LONG daily stop/target policy replay with hypothetical costs |
| 1.3.0 | Separate bounded AI hypothesis/replay research loop |

Selecting a card does not switch ranking weights, paper configuration, or broker execution. Legacy rows remain `LEGACY_UNATTRIBUTED`; later versions do not retrospectively label them.

## Home PC and Railway

| Location | Current responsibility | Schedule / dependency |
| --- | --- | --- |
| Home PC | Collect and retain daily Yahoo OHLCV; send authenticated snapshots | Windows task at 07:30 SAST; PC powered on and user signed in |
| Home PC | Weekly-brief/news relationship analysis with local Ollama, local receipts/outboxes and archive screen | After a successful daily upload when enabled; one automatic attempt per UTC day |
| Railway web | Dashboard/API, read-only state, source feeds and authenticated imports | Online service; on-demand dashboard charts can still use Yahoo |
| Railway worker | Bounded paper processing and isolated strategy hypothesis/comparison jobs | `0 6 * * *` = 08:00 SAST, exits after scheduled work |
| Railway PostgreSQL | Shared durable paper/research ledger | Persists state across service restarts |

Current settings include `SWING_DATA_SOURCE=LOCAL_UPLOAD`, `SWING_RESEARCH_ENABLED=1`, and `ALPHA_VANTAGE_ENABLED=0` locally and on Railway. Cloud paper input acquisition fails closed when uploads are absent; it does not secretly fetch a replacement daily dataset. News and dashboard chart reads have separate paths. The current collector uploads all 21 configured chart histories (17 active shares and four ETFs), not only radar triggers.

The owner's intended next architecture is daily local calculations and backtests, selective 30-minute radar events sent to Railway, and six separately tested hypotheses. The full local backtest/radar/event loop is **not yet implemented**. Do not infer it from the daily uploader or cloud research panel.

The [Swing rule refinement 0.2](research/SWING_RULE_REFINEMENT.md) adds source-backed candidate entry/trailing/exit experiments, volume-weight learning and measured sector/share momentum profiles to that proposal. It changes documentation only; candidates are not registered, backtested or activated by writing them down.

## What AI does and learns

Local Ollama categorizes candidate relationships between a manually imported Monday brief and retrieved articles. It cannot independently search the web without a retrieval tool. It produces referenced descriptions, not OHLCV. The installed local model observed in this session is `llama3:latest`; weekly research uses CPU because the observed GPU driver rejected the CUDA/PTX workload. The weekly request has a 480-second bound; ordinary news sentiment keeps its existing timeout.

Ollama Cloud separately proposes bounded volume/RSI/holding-period hypotheses for Swing 1.3.0. A daily attempt is reserved before the model call. Frozen proposals are compared against 1.2.0 on chronological historical slices, with train/holdout separation and a purge. Repeated holdout comparisons remain `NOT_ELIGIBLE_PROSPECTIVE_WALK_FORWARD_REQUIRED`. Neither loop fine-tunes LLM weights or automatically promotes strategy settings. The M11 outcome learner evaluates attributed closed outcomes separately.

## Data quality and actual results

Yahoo supplies real completed daily observations, but individual bars can have impossible/incomplete OHLC. An otherwise present dataset can therefore fail the strict structural/ATR gate. Earlier probes found defects in Sasol, Naspers and the STX40 proxy; those counts describe that probe, not today's permanent inventory.

Display-only estimates use up to five previous real bars, with explicit estimated flags, no invented volume and no recursive estimates. They do not create missing calendar sessions and are excluded from ATR, stop/target replay and validation. A real close may still support the older close-based ranking while an OHLC-dependent experiment is blocked. The independent recent-window diagnostics do not relax frozen policy admission.

IG Demo authentication/account reads work. JSE epic discovery worked, but the tested equity detail and daily-history requests returned 403 entitlement errors. CFD/tick volume cannot be treated as JSE cash traded-share volume. Alpha Vantage setup, cache and request budgets exist; the bounded probes did not establish verified JSE coverage. Foreign listings were rejected. Free compact history is not a proven 20-year JSE dataset. Scheduled Alpha Vantage requests remain off.

The first real cloud proposal used volume 1.2, RSI ceiling 65 and a four-session hold. Baseline and candidate both had **zero closed holdout samples**, with 680 blocked/unresolved checks; those checks are not trades. There is no measured profitability or accuracy to report.

The 28 September and 5 October Monday briefs were manually imported as unverified derived research. The repaired local CPU scan completed in approximately 6m38s. Its two EARNINGS/INFLATION cases referenced Moneyweb only, so they remain `SOURCE_REVIEW_REQUIRED`: **zero historical flags, zero boosts, zero historical samples**. Earlier same-category/instrument cases enter historical screening only if already corroborated and FLAGGED. Saved outboxes can be delivered again without another model call.

## News weighting and event research

The Monday brief is a lead, never an independent confirming publisher. A corroborated relationship can add up to `+0.05` to research attention priority, capped at 1.0, after distinct-publisher and duplicate checks. This does not change trade ranking or risk approval. Semantic similarity is not measured price correlation or causation.

Current historical screening uses real local closes after actual receipt, and only earlier eligible flags; it does not backdate availability to a brief's nominal edition. It is descriptive and lacks sector controls, event costs, stops, volume tests and statistical inference. Historic SENS retrieval, verified economic-event timestamps and the six-family strategy backtest remain planned. Future Monday task editions still need manual import.

## Safety and unresolved work

LIVE execution is disabled. Demo order boundaries remain separately gated; research versions and dashboard cards authorize no order. Standard Bank OST, ViewPoint/IRESS, Shyft and MT5 are not verified automatic data/execution connections in this workflow. No broad persistence migration was needed for profiles or the newer append-only research records.

Before strategy promotion: obtain admissible real OHLCV, verify corporate actions and sessions, establish actual volume semantics/liquidity, retrieve dated event evidence, model real account fees/spreads, and run prospective walk-forward comparisons with sufficient independent samples. A running website, accepted dataset, or completed LLM response does not satisfy these gates.

## Documentation acceptance

The baseline safe suite passed 869 tests. This documentation reconciliation changes descriptions/navigation only; the final acceptance record is in [the current milestone](roadmap/CURRENT_MILESTONE.md). Eleven protected Markdown benchmark reports remain byte-preserved and explicitly indexed as historical evidence.
