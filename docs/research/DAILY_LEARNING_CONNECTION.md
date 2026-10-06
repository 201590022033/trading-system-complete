# R2 daily learning connection

6 October 2026. Railway PostgreSQL owns the existing scheduled paper and Swing research records. Local SQLite is a separate runtime and is not a replica. The owner authorized connecting/verifying daily learning after R1.

## Operational repair

The Windows task `Trading System Local Swing Daily Data` now runs the main checkout's collector at its existing 07:30 SAST schedule, preserving triggers, interactive-user principal and 20-minute bound. Existing private upload configuration, dated chart archive and weekly-news settings/receipts were copied to the main checkout's ignored configuration/runtime directories. No tokens or raw model responses enter Git. A retry of the saved 21-chart dataset returned LOCAL_DATA_STORED_AND_UPLOADED. This retry does not fetch new prices or invent later sessions.

Railway web and worker both use LOCAL_UPLOAD and the shared PostgreSQL backend. The existing worker cron is 08:00 SAST and next run is 7 October; the collector's next run precedes it. Neither cron nor hosted deployment was changed. Dataset observation is 6 October 07:30 SAST but the latest saved price session is 2 October. Fresh upload time is not fresh market coverage.

Observed Railway records: 25 frozen Swing 1.1.0 feature decisions, zero matured 3/4/5-session outcomes; 17 current-version candidate comparisons awaiting outcomes; bounded AI research ran on 6 October at 08:00 SAST using Ollama Cloud. Baseline and candidate holdouts both have zero completed samples and 680 blocked/unresolved checks. These are not losing trades or evidence of improvement. Later actual sessions are required to mature prospective outcomes.

## Learning interface

GET `/api/v1/learning/overview` returns an aggregate allowlist with runtime, database, worker timing, dataset/decision clocks, frozen strategy version, pending/matured/negative counts, present/absent condition cohorts, latest feature quality, Sasol missing inputs, selected-versus-other comparisons and AI sample counts. The Trading Strategies panel labels the source explicitly.

Default source is LOCAL. On this local dashboard, private `SWING_LEARNING_SOURCE=RAILWAY` and the existing `SWING_RESEARCH_URL` choose the pinned deployed status endpoints. Requests are GET only, five-second timeouts, no redirects, at most 2 MB each and cached for 60 seconds. Invalid source/backend or transport failure returns UNAVAILABLE without silently substituting local zeros. Hosted Railway ignores this remote-source setting and reads its own database to prevent recursion. No account values, positions, credentials, raw charts or AI rationale are proxied. Dashboard refresh does not start a worker, replay or model call.

The existing worker freezes decisions and labels every eligible decision after a later completed-close entry plus 3/4/5 observed sessions. This includes condition-absent and negative cases. Labels are forward returns with assumed 10 bps costs, not policy stop/target fills or actual broker costs. Pending counts refer to the bounded read window. Overlap and observed-calendar limits remain explicit; B5 admission is not changed. Indicator changes, prospective candidate promotion and model fine-tuning remain unimplemented/unapproved.

## Verification and limits

Six new projection tests verify provenance, safe fields, controls/negative cases, missing-versus-zero, counter consistency, pinned remote reads, no local fallback on failure and recursion prevention. Existing causal Swing tests cover future exclusion, frozen clock/version identity, retries, next-close maturity and both repository implementations. Fifty focused tests and 932 full safe tests passed (93.188s); all 54 protected checks passed. Main-app browser review verified Railway provenance, schedule, per-horizon pending/negative/matured counts, Sasol missing inputs, control cohorts and saved-status refresh. The new panel is installed locally; no hosted code deployment was performed.

Sasol still reports partial inputs. Complete trusted OHLC/benchmark history and corporate-action/provider semantics must be resolved separately. An unavailable input does not become neutral evidence, an inferred price or an admitted backtest.
