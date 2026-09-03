# Linear Fusion Roadmap

Only one milestone is ACTIVE. Advancement requires tests, docs and a commit.

## M0 — Protect and characterize baseline [COMPLETE 2026-09-03]
- Inspect Git state and secrets.
- Confirm `.env` is ignored/untracked; do not print secret values.
- Preserve all current uncommitted user work.
- Run existing tests/verification scripts that are safe/offline where possible.
- Add minimal characterization tests around `JSESignalEngine` fixed scoring if missing.
- Create a clean baseline commit named approximately `baseline: preserve pre-adaptive trading system` if safe and Git identity exists.
Acceptance: baseline behaviour reproducible; no secrets committed; working tree understood.

Evidence: `test_legacy_scoring.py` passes 3 characterization tests; the canonical two-year report contains 24 finite metric rows; `.env` is ignored and untracked.

## M1 — Evidence/provenance contracts [ACTIVE]
- Add normalized evidence/source models without replacing current `NewsItem` immediately.
- Add adapters/conversion from current news/macro objects.
- Add deduplication keys and timestamps.
Acceptance: existing collectors can emit/convert to evidence records; tests pass.

## M2 — Source registry + reliability store
- Configurable registry for existing and planned sources.
- Persistent local research store (SQLite is acceptable unless repo already has a preferred DB).
- Outcome evaluation by horizon; sample-size-aware score.
- No production weight changes.
Acceptance: synthetic/historical tests demonstrate score updates without leakage.

## M3 — Regime engine
- Implement transparent regime feature calculation and labels.
- Add versioned `MarketRegime` output.
- Backtest regime classification stability.
Acceptance: no future leakage; deterministic tests; docs updated.

## M4 — Sector/instrument profiles
- Replace scattered ticker-specific macro logic with configurable profiles, while preserving legacy behaviour as benchmark.
- Profiles: index futures/CFDs, SSF/share CFD, banks, gold miners, PGM/diversified mining, energy/Sasol, retail/consumer, agri-linked, USD/ZAR.
Acceptance: profile selection tested; legacy mode unchanged.

## M5 — Expanded indicator research layer
- Add ADX/DMI, ATR, MACD, Bollinger/z-score, relative strength and volume/liquidity features where data supports them.
- Add intraday VWAP/opening range only behind an intraday-data capability flag.
- Do not pretend daily Yahoo data is intraday derivatives data.
Acceptance: unit tests + no-lookahead calculations + feature availability metadata.

## M6 — Adaptive fusion in SHADOW mode
- Create adaptive fusion beside legacy fixed score.
- Weight by regime, sector/instrument profile, source reliability and feature evidence.
- Every decision logs factor contributions and legacy-vs-adaptive comparison.
Acceptance: production/default signal remains legacy unless explicit config selects shadow output for research.

## M7 — Backtest/evaluation upgrade
- Multi-horizon walk-forward.
- Costs, slippage/spread assumptions, turnover, drawdown, MFE/MAE where data allows.
- Segment results by bull/bear/range, volatility, sector and instrument profile.
- Reliability calibration/ablation tests: technical-only vs macro-only vs source-only vs fused.
Acceptance: report can justify or reject adaptive weighting.

## M8 — Public specialist/community source expansion
Verify before integration; do not assume availability:
- TradingView SA/JSE ideas;
- IG South Africa public analysis/client sentiment where permitted;
- Moneyweb/BusinessLIVE/Reuters local markets;
- Standard Bank public commentary;
- MyBroadband JSE/stock-watch discussions;
- Reddit local finance/JSE communities;
- public X/Twitter via approved API/provider;
- legitimate public Telegram/Discord channels;
- BlackStone Futures public resources if active and accessible.
Normalize as low/medium-authority evidence and learn reliability. No Facebook private-group credential scraping.
Acceptance: access method documented, rate-limited, provenance preserved, source can be disabled independently.

## M9 — Multi-agent integration
- Feed adaptive evidence/regime explanations into existing Bull/Bear/General researchers.
- Preserve Risk/Manager governance.
- Add disagreement telemetry: when legacy, adaptive, bull and bear strongly disagree.
Acceptance: existing manager/executor interfaces remain stable or have a documented adapter.

## M10 — Promotion gate
Do NOT automatically promote adaptive trading.
Produce a final evidence report recommending one of:
1. reject adaptive changes;
2. continue shadow collection;
3. enable adaptive recommendations/paper trading;
4. propose a separate live-trading safety milestone for explicit user approval.
