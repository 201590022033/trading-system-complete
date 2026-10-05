# South African trading research platform

A dashboard and durable paper/research workflow for JSE opportunities. The current focus is a 3–5-session Swing research strategy, with truthful Intraday CFD and Long-Term Investment placeholders. No validated profitability or LIVE execution is claimed.

Start with [current project state](docs/CURRENT_STATE.md), [Quick Start](QUICKSTART.md), and the [complete document index](docs/DOCUMENTATION_INDEX.md). The [change log](docs/changes/2026-09-21-to-2026-10-05.md) covers the last two weeks. Older multi-agent work is retained as a benchmark; the canonical Top-5 uses M13 ranking, M14 policy and M15 risk veto.

## Current features

- Backend-populated Strategy Profiles with immutable ID/version lineage; canonical Swing default 1.0.1.
- Public research inputs, technical/regime/news context, durable paper simulation and contextual outcome evaluation.
- Portfolio & demo workspace, printable worksheets, and authenticated manual Demo trade journal.
- Daily local OHLCV archive and authenticated Railway upload; bounded cloud strategy hypothesis comparisons.
- Monday brief import, local Ollama news categorization, and corroboration-gated research flags.
- Explicit incomplete-data/estimated-data states, entitlement checks and separate paper/Demo/Live boundaries.

## Run and verify

Python 3.12 with `requirements.txt` and `constraints.txt` is the reproducible setup. From a fresh checkout:

```powershell
py -3.12 scripts/setup_dev.py
.\.venv\Scripts\python.exe scripts/check_dev_environment.py
.\.venv\Scripts\python.exe scripts/run_tests.py
```

Use the VS Code **Start dashboard** task for the reviewed local PostgreSQL environment, or follow [Quick Start](QUICKSTART.md) for an explicitly isolated SQLite session. `app.py` is the dashboard entry point. `main.py` and historical merge/demo scripts are not instructions for the deployed canonical workflow.

Local data and keys are ignored runtime files. Never copy credentials into Git or chat. External provider/model probes are excluded from the safe test suite. Read [AGENTS.md](AGENTS.md) before development.

## Local and hosted responsibilities

The home PC archives daily histories at 07:30 SAST and runs the optional local news scan. Railway hosts the dashboard and shared PostgreSQL state; its bounded worker runs at 08:00 SAST. The current upload sends the whole configured daily chart collection. Selective 30-minute radar upload and a local six-hypothesis backtest engine are [proposed next work](docs/research/SIX_SWING_HYPOTHESES.md).

Ollama helps describe news and propose experiments. Recorded outcomes can inform research; no LLM weight training or automatic strategy adoption is taking place. Data defects currently leave the cloud candidate with zero closed holdout trades. See [data/provider readiness](docs/integrations/MARKET_DATA_EXECUTION_MATRIX.md).

The previous README is retained as [historical project context](docs/history/README_PRE_2026-10-05.md); its old architecture and setup claims do not describe today's deployment.
