# Daily local collection and online Swing research

Baseline hypothesis: liquid JSE cash shares (liquidity still needs validation),
daily completed observations, EMA20/50 uptrend, breakout20 or EMA20 reclaim,
RSI50–70, volume above previous20-day average and outperformance of STX40.
Entry at the first later completed close within seven calendar days; stop at
the lower of prior10-session low and signal-close-minus-ATR14; fixed2R target;
three/four/five observed-session exits. Daily ambiguous stop/target uses stop
first; hypothetical cost stress is10/25/50bps. No live trading.

Local daily task: `Trading System Local Swing Daily Data`, 07:30 South African
time while powered on and signed in. Stores full daily one-year snapshots at
`runtime/local-swing-data/YYYY-MM-DD.json` and `latest.json`. Keeps the local copy
if upload fails. Run `python scripts/collect_swing_data.py --retry-upload` to retry
saved data without fetching again. It does not invoke Alpha Vantage; provider
coverage/repair remains unverified, and its existing bounded fallback is separate.

Private setup: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
scripts/configure_swing_research.ps1 -PythonPath <project-python> -ConfigureRailway`.
This uses a process-only execution-policy override, preserves other .env settings,
generates a private upload token and registers the daily task. Railway must be
linked to the correct production project before setting variables. No key in chat.

Cloud working copy: POST `/api/v1/swing-research/datasets`, bearer authenticated.
Read-only status: GET `/api/v1/swing-research/status`. Worker sets
`SWING_RESEARCH_ENABLED=1`; after a confirmed upload set
`SWING_DATA_SOURCE=LOCAL_UPLOAD` to stop its direct Yahoo daily polling. Keep
news scanning and dashboard live chart/quote reads separate. Worker remains
scheduled at08:00 SA (cron06UTC; SWING_WORKER_CRON_HOUR=6). This follows the
existing next-UTC-midnight availability convention. A late local upload waits
for the next cloud run or explicit evaluation. Explicit bounded first evaluation:
`python scripts/run_swing_research.py`; same one-attempt daily budget applies.

Ollama Cloud receives technical/training evidence and proposes one registered
volume/RSI/holding-period variation. A chronological historical comparison is
stored with a frozen proposal, parameters/model/context/dataset/version and
shown in Trading Strategies. Zero samples or unavailable AI are disclosed.
The old strategy is never automatically replaced. This does not retrain Ollama.

Missing local uploads become visible as stale/missing, rather than fallback
downloads or invented prices. Keep the existing source until a first upload is
confirmed. Rollback of the source switch: `SWING_DATA_SOURCE=YAHOO`; research can
be disabled with `SWING_RESEARCH_ENABLED=0`. Neither setting enables live trading.
Task can be disabled through Windows Task Scheduler without deleting data.

Limitations: exchange calendar, source OHLC anomalies, actual liquidity/fees,
corporate actions, prospective validation and portfolio risk remain unresolved.
The initial grid refines volume/RSI/holding time only; stop/target-rule refinement
needs its own versioned evaluation contract. See ADR0042.
