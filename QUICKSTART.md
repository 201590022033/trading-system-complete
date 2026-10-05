# Quick Start — current dashboard and safe research

Reviewed 5 October 2026. See [current state](docs/CURRENT_STATE.md) before interpreting research results. Use Python 3.12; the managed environments, secrets and datasets are machine-specific and are not portable Git artifacts.

## Install and test

From the repository root on Windows:

```powershell
py -3.12 scripts/setup_dev.py
.\.venv\Scripts\python.exe scripts/check_dev_environment.py
.\.venv\Scripts\python.exe scripts/run_tests.py
.\.venv\Scripts\python.exe scripts/verify_protected_artifacts.py
```

Select that environment in VS Code. The full safe runner disables dotenv and outbound sockets. Its focused option is narrower than the full application suite and does not cover every recent feature. Ollama and broker credentials are optional for this offline verification.

## Start an isolated dashboard

For a local SQLite check with no inherited deployment credentials, use a new PowerShell process, clear any inherited DATABASE_URL and PAPER_LOOP_CONFIG, and prevent dotenv loading:

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:PAPER_LOOP_CONFIG -ErrorAction SilentlyContinue
$env:APP_MODE='SHADOW'
New-Item -ItemType Directory -Force -Path (Join-Path $PWD 'runtime') | Out-Null
$env:SQLITE_DB_PATH=Join-Path $PWD 'runtime/local-docs-check.db'
$env:HOST='127.0.0.1'
$env:PORT='5000'
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5000. This starts a local dashboard; it does not run the deployed paper worker. Empty research state in an isolated database is expected. Optional feed reads may still occur when requested; the safe test runner, not dashboard startup, provides network isolation.

## Use the reviewed local PostgreSQL setup

VS Code's **Start dashboard** task calls `scripts/start_local_postgres.ps1`, loads ignored `.env.local`, checks a loopback database, and binds the web service to localhost. Explicit additive migrations are required before using a new PostgreSQL schema; service startup does not migrate it. Do not point a local check at production. The task labelled **Start dashboard (isolated SQLite)** only sets host/port; use the explicit environment above to avoid inheriting a database setting.

## Optional local data and news work

The configured Windows task collects daily Yahoo OHLCV at 07:30 SAST. It requires a powered-on PC and a signed-in user. Private configuration uses `SWING_RESEARCH_URL` and `SWING_DATA_UPLOAD_TOKEN`. See [the research loop](docs/SWING_RESEARCH_LOOP.md). The collector is an external data operation, not part of offline tests.

Weekly brief import/scan uses `scripts/weekly_news_research.py`; model failures and unavailable sources remain visible. Use [the weekly news guide](docs/research/WEEKLY_NEWS_RESEARCH.md), not a speculative model installation command. Alpha Vantage scheduled requests remain disabled; [its setup guide](docs/integrations/ALPHA_VANTAGE_SETUP.md) explains the helper's different activation behavior.

Legacy merge instructions and historical demo launch commands remain in [the previous Quick Start](docs/history/QUICKSTART_PRE_2026-10-05.md). They are not the current deployment procedure.
