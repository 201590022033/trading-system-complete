# Fusion Roadmap Completion Report

Completed: 2026-09-03

## Outcome

M0–M10 are complete. The adaptive intelligence layer remains research/shadow
only. The promotion-gate recommendation is **continue shadow collection**.
Production/default signal scoring remains the characterized legacy path, and
execution remains an in-memory paper simulation.

## Changes by milestone

- M0 protected the imported baseline, characterized fixed scoring, restored the
  canonical six-ticker backtest and audited secrets.
- M1 added normalized `EvidenceRecord` provenance and deduplication around the
  existing `NewsItem` contract.
- M2 added the configurable source registry and SQLite reliability outcomes with
  no-lookahead checks and sample-size shrinkage.
- M3 added transparent versioned trend/volatility/risk regimes and the stability
  report (700 observations each for NPN, SASOL and BHP).
- M4 added `market_profiles.py` for required sector/instrument groups and moved
  legacy macro coefficients behind configurable profiles.
- M5 added `research_indicators.py` with capability-gated ADX/DMI, ATR, MACD,
  Bollinger/z-score, relative-strength, volume/liquidity and intraday features.
- M6 added `adaptive_fusion.py`, normalized factor contributions, bounded
  reliability/context multipliers and legacy-vs-adaptive shadow telemetry.
- M7 added `evaluation.py`, multi-horizon/segmented ablations and configurable
  transaction-cost assumptions, plus `adaptive_evaluation_report.*`.
- M8 added `source_catalog.py` with source access policy, independent switches,
  polling gates and evidence/reliability integration.
- M9 added `agent_intelligence.py`, researcher context and disagreement telemetry
  without changing Trader/Risk/Manager decisions.
- M10 audited evidence, safety and promotion readiness and retained shadow mode.

## Preserved functionality

- Existing collectors, `UnifiedDataPipeline`, legacy `SignalGenerator`, fixed
  `JSESignalEngine` weights/thresholds and the multi-agent governance chain.
- Direct macro mention weight `0.10`, rand coefficients `+/-0.05`, gold/oil
  coefficients `0.08`, and macro clamp `+/-0.15`.
- Existing Standard Bank OST code remains isolated; no live order action was
  added or enabled.

## Validation evidence

- Final focused offline suite: 41 tests passing through standard-library
  `unittest` in the workspace virtual environment.
- Core research, pipeline, adapter and governance modules compile successfully.
- M7 historical report: 760 Yahoo daily observations for each of NPN, SASOL,
  BHP, IMPJ, SHPJ and ABSPJ; 1,200 finite segmented result rows.
- M7 includes 1/3/5/20-session horizons, spread/fee/slippage assumptions,
  turnover, decision-path drawdown, close-path MFE/MAE, Wilson win-rate
  intervals and trend/volatility/profile segments.
- Of 24 sufficient-sample adaptive overall rows, 9 had positive and 15 had
  negative mean net return. In the available report adaptive falls back to
  technical evidence because aligned historical macro/source series are absent.

## Source status

- Live/enabled: Moneyweb RSS and Moneyweb-hosted SENS listing.
- Available research price source: Yahoo Finance daily history; not intraday
  derivative/order-book data.
- Mocked/manual-only: existing mock price/news paths; IG South Africa, Standard
  Bank public commentary and BlackStone Futures Telegram remain link/manual
  evidence pending a permitted stable connector.
- Licence/API/permission blocked: official JSE market-data products, Reuters,
  BusinessLIVE, Reddit OAuth, X official API, permitted Telegram API and Discord
  bot/message-content access.
- Deliberately excluded: TradingView automated non-display use under current
  terms; private Facebook/community credential scraping; unauthenticated Reddit
  JSON polling; CAPTCHA/access-control bypasses.

## Known limitations and data gaps

- No time-aligned historical macro, authoritative-event or community evidence
  is available for a fair adaptive ablation.
- Daily closes cannot validate intraday VWAP/opening range, SSF basis/open
  interest, spread, depth or actual derivative execution costs.
- M7 drawdown is an overlapping decision-path research metric, not a
  capital-constrained portfolio simulation.
- Current source availability and platform terms can change and must be
  reverified before enabling a disabled source.
- Legacy polling code retains some “live trading” terminology although its
  execution target is the simulated portfolio.

## Security and trading-safety audit

- `.env` is ignored and untracked; its contents were not inspected or copied.
- Browser profile/state is ignored and untracked.
- No credential values, cookies or generated secrets are committed.
- No live broker order capability was added or enabled.
- Agent-integrated execution output is explicitly marked `paper`.

## Promotion gate

**Recommendation: continue shadow collection.**

Do not promote adaptive recommendations or weights yet. Collect time-aligned
macro/source outcomes, rerun M7 across rolling periods with realistic licensed
instrument costs/liquidity, and require stable profile/regime improvements over
legacy before considering paper-trading promotion. Live trading would require a
separate explicit safety milestone, user approval and ADR.
