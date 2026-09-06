# Laptop handoff

## Verified checkpoint — 2026-09-06

- Repository: `https://github.com/201590022033/trading-system-complete`
- Branch/upstream: `master` / `origin/master`.
- Research commit: **`8b7c591`**, already pushed before this handoff.
  Pull the later **`chore: add reproducible development environment and laptop handoff`**
  commit for these setup files; `git log -1 --oneline` identifies the exact checkpoint.
- **OI3** (letter I, not “O13”): DEFERRED and unfinished. Local Ollama
  (`llama3.2:3b`) is now installed and verified on this laptop; cloud/Kimi keys
  remain MISSING, ticker discovery and additional permitted sources remain to verify.
  Earlier SENS challenges/NewsAPI gaps are recorded, not bypassed.
- **HR11:** COMPLETE, committed/pushed. Research engineering only: 180 insufficient
  cells because actual 5m history/session/cost inputs remain unavailable.
- **HR12:** NOT STARTED; no files or commits found in pre-handoff tracked state/history.
- Last completed research milestone: HR11. Active research milestone: none.
  Current deliverable: this environment/handoff checkpoint, not a new research phase.
- No unfinished source edits found. One pre-existing **empty** Windows-path-named
  untracked file remains untouched; its actual prompt is already in HR11_REQUEST.md.

## At home: local Windows setup

1. Have Git (or GitHub Desktop), VS Code and **Python 3.12.x** installed. Sign into
   GitHub, clone this repository or fetch/pull `master`; open its folder in VS Code.
   If continuing in the same Codespace instead, reconnect to it and use `.venv/bin/python`.
2. Install the workspace's recommended Python extensions and select `.venv` as the
   interpreter after setup. Settings Sync is optional, not a replacement for setup.
3. From the repository root run:

   ```powershell
   .\scripts\setup_dev.ps1
   ```

   If local policy blocks `.ps1`, use the same bootstrap without changing policy:

   ```powershell
   py -3.12 scripts/setup_dev.py
   ```

4. No credentials or data copies are required for offline development. For optional
   live providers, create `.env` **only if absent** and add credentials privately:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

   Leave commented HOST/PORT/REDDIT_USER_AGENT unset unless assigning valid values.
   Reauthenticate Git/editor AI tools separately. Never copy the Linux `.venv`.
5. Ollama is optional. Use the repository helper to install/verify it and pull
   the default model:

   ```powershell
   powershell -ExecutionPolicy Bypass -File ./setup_ai.ps1 -InstallOllama -PullModel -SkipKimiKey
   ```

   Then verify with `.venv\Scripts\python.exe scripts/check_dev_environment.py --ollama`.
   See [OLLAMA_MODELS.md](OLLAMA_MODELS.md) for model details and
   [WORKSTATION_HANDOFF.md](WORKSTATION_HANDOFF.md) for the primary work desktop
   reproduction checklist.
6. Run the one-command diagnostic and safe tests:

   ```powershell
   .\.venv\Scripts\python.exe scripts/check_dev_environment.py
   .\.venv\Scripts\python.exe scripts/run_tests.py
   ```

   Expect diagnostic **PASS (offline development)** and **208 tests, OK**. Missing
   optional credentials or stopped Ollama do not fail the offline diagnostic.
   Windows runtime/PowerShell execution was not available here; report any local
   failure before proceeding. Clean Linux execution and Windows wheel downloads
   are documented in the [validation record](handoffs/2026-09-06-LAPTOP-VALIDATION.md).
7. Start the UI with VS Code **Tasks: Run Task → Start dashboard**, then open
   `http://127.0.0.1:5000/`. `/health` is only a health response. Feed failures and
   keyword fallback remain explicit; no successful live AI connection is assumed.
8. Optional HR11 audit, preserving committed evidence:

   ```powershell
   .\.venv\Scripts\python.exe hr11_research.py --output analysis/results/hr11-local
   ```

   Expect 180 insufficient-evidence cells without real input files. This folder is
   ignored. Do not overwrite the committed research report for a setup smoke test.

## Exact next development action

Read `AGENTS.md`, the mandatory architecture/roadmap files, then this handoff.
With the owner's continuation instruction, reactivate **OI3** and work on the first
unchecked provider-verification item in `docs/roadmap/CURRENT_MILESTONE.md`:
verify one configured provider produces valid, attributed AI headline output, then
exercise provider failure/fallback and permitted ticker-discovery/source coverage.
Do not reimplement the existing `SentimentProviders` router or invent HR12.
Keep broker integrations paper/read-only and preserve frozen research artifacts.

The accidental **Windows MCP entry is still unresolved**: no accessible remote
candidate was found and Windows user storage was unavailable. Investigate it from
a genuinely local Windows assistant session before removing anything. Nothing was
cleaned or synced into this repository as an MCP workaround.

Further details: [environment](DEVELOPMENT_ENVIRONMENT.md),
[local data](LOCAL_DATA_MANIFEST.md), [HR11 report](reports/HR11_REPORT.md).
