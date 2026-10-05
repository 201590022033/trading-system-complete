# PAPER loop runbook — current v3 deployment

Reviewed 5 October 2026. The configured account is `railway-paper-zar-v3`, using `config/paper.railway.json` and exact default Swing profile 1.0.1. Older v1/v2 repair instructions remain [historical checkpoints](../history/PAPER_LOOP_RUNBOOK_PRE_2026-10-05.md), not current account settings.

## Inputs and schedule

The home PC uploads completed daily observations at 07:30 SAST. Railway uses `SWING_DATA_SOURCE=LOCAL_UPLOAD`; the bounded worker runs at 08:00 SAST (`0 6 * * *`). Absent uploads fail closed in that paper-input path. The four-calendar-day freshness bound is a delay/weekend allowance, not a verified exchange calendar. Source-session fingerprinting skips duplicate completed sessions with `NO_NEW_COMPLETED_SESSION`. `NO_USABLE_MARKET_DATA` is a blocked cycle, not a healthy trade opportunity.

Current configuration is PAPER/ZAR, R100,000 simulated capital, conservative aggression, 0.005 risk fraction, 0.001 volume participation cap, daily interval, three observed-session holding/learning horizon, 2R target and seven-calendar-day maximum hold. The catalog filters inactive/retired configured instruments; its 17 active shares are not a certified liquid universe. Simulator balances are separate from connected IG cash. Display estimates are not accepted trade inputs.

## Run safely

Use a distinct account ID and reviewed configuration for a local experiment; existing account configuration is immutable. In a shared deployment, web and worker use the same database and `PAPER_LOOP_CONFIG`. Configured PostgreSQL failure never falls back to SQLite. Explicit additive migrations require a reviewed target and backup; startup performs no migration.

For a deliberately isolated local paper experiment, use [Quick Start's isolated environment](../../QUICKSTART.md), then a reviewed example configuration:

```powershell
python -m scripts.run_paper --config config/paper.example.json
```

One bounded tick processes at most one due job and does not promise a fill. `--continuous` is a local execution option, not the deployed daily cron schedule. Do not run manual workers against production as a test or create a fresh account to disguise losses.

Read `/api/paper/status` and `/api/v1/opportunities?limit=5` for committed state. Web refresh in configured paper mode is read-only. Authenticated Portfolio controls can enqueue a check, adjust allowed aggression or pause new entries; none enables real-money execution. Keep `PAPER_CONTROL_TOKEN` private.

`PAPER_PAUSED=1` blocks new entries while valid existing exits may still close. Stopping the worker stops processing and does not liquidate positions. Restart preserves ledger state; it is not a balance reset. Do not enable IG streaming to replace missing daily Swing data.

## Model boundaries

The canonical cash simulator is long-only and whole-share funded. M15 veto, volume capacity, closing-fee reserves and explicit simulation costs constrain sizing. Later observations drive entry/exit; gaps can exceed stop budgets. New outcomes carry exact profile/horizon lineage. The current learning horizon is three observed sessions, not the earlier runbook's one-session description; contextual learned cells require 30 mature samples.

Swing 1.2.0 stop/ATR daily replay and 1.3.0 AI comparisons are separate research accounts/records and do not change this simulator. ETFs retain a separate research path. Real OST costs, instrument entitlement, corporate actions, verified calendars, derivative/short execution and portfolio walk-forward evidence remain unresolved. No profitability is claimed.

## Acceptance

Run `python scripts/run_tests.py` and `python scripts/verify_protected_artifacts.py`. External broker/model/provider probes are excluded. Native PostgreSQL acceptance uses the separately constrained disposable localhost validator; it must never target production. Review health, committed cycles, source freshness and attributable closed outcomes separately. A successful deployment alone establishes no trading edge.
