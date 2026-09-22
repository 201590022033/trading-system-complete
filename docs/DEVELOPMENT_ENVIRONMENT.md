# Development environment — verified 2026-09-06

## Actual environment and reproducibility

The accessible working machine is **Ubuntu 24.04.4 LTS, x86_64**, in GitHub
Codespaces; Linux kernel 6.8.0-1052-azure. It is not the Windows desktop. Python
**3.12.1** runs the existing `.venv`; Git is **2.53.0**. Remote VS Code product
metadata identifies **Stable 1.136.1**, commit
`a44adf7f53e00964ab890f9f8758a334f1fc15bc`. The client Windows build/profile and
Settings Sync status cannot be established from this remote filesystem. The
`code` wrapper reports no local desktop installation; metadata is the source of
the remote version above.

Use Python **3.12.x**, a repository-local `.venv`, and the existing pip
`requirements.txt` system. `constraints-dev.txt` records the project-only resolved
dependency closure from a fresh venv. It is used with requirements, not instead
of them. No Poetry/uv/Pipfile/pyproject packaging system exists or was added.
Windows-only conditional dependencies are resolved by pip on Windows. The generic
Codespace `python` lacks the declared Ollama Python package; use `.venv` explicitly.

```powershell
# Windows, repository root; creates .venv without touching .env or system software
.\scripts\setup_dev.ps1
# Equivalent if PowerShell script execution is restricted (no policy change needed)
py -3.12 scripts/setup_dev.py
.\.venv\Scripts\python.exe scripts/check_dev_environment.py
.\.venv\Scripts\python.exe scripts/run_tests.py
```

```bash
# Linux/macOS with Python 3.12 already installed
python3.12 scripts/setup_dev.py
.venv/bin/python scripts/check_dev_environment.py
.venv/bin/python scripts/run_tests.py
```

No global package installation, PATH mutation, secret copying, model download or
system-software installation is performed. Existing non-venv folders are refused.
Dependency installation needs internet access. A clean Linux venv validates the
shared Python bootstrap; Windows-specific checks and their limitations are in
`docs/handoffs/2026-09-06-LAPTOP-VALIDATION.md`.

## VS Code

Project recommendations in `.vscode/extensions.json` use IDs verified in the
remote extension inventory:

| Role | ID | Observed version | Needed for |
|---|---|---|---|
| Recommended core | `ms-python.python` | 2026.4.0 | Interpreter selection and Python editing |
| Recommended core | `ms-python.vscode-pylance` | 2026.3.1 | Python language support |
| Recommended core | `ms-python.debugpy` | 2026.6.0 | Optional Python debugging |
| Optional | `davidanson.vscode-markdownlint` | 0.62.1 | Documentation editing |
| Optional | `github.vscode-pull-request-github` | 0.164.0 | GitHub review workflow |

The app and command-line tests require no editor extension. Other observed
project-useful options are `mechatroner.rainbow-csv` 3.24.1 and
`ms-python.vscode-python-envs` 1.36.0. The installed `openai.chatgpt` extension is
optional developer AI tooling; its configuration was not modified. Continue was
also installed but was not added to recommendations. Copilot/Kimi desktop
extension installation is **unverified**, so no guessed Kimi extension ID or MCP
troubleshooting extension is recommended. Copilot, Codex and Kimi Code are not
trading-runtime dependencies.

Workspace settings select `${workspaceFolder}/.venv`; choose that interpreter
once on the new machine. The existing terminal `.env` behavior is preserved.
Automatic pytest/unittest discovery is disabled because root `test_*.py` includes
manual credential/network probes; use the safe tasks instead. No pytest package
is needed: the safe suite uses standard-library unittest. No prior project
`launch.json` was present, so no speculative debugging workflow was created.
User-specific themes, tool paths, agent settings and accounts were not copied.

Tasks cover environment check, constrained dependency install, focused/full safe
tests, compile validation, dashboard start, separate HR11 local reports and an
optional local Ollama check. They use the selected Python interpreter. On
Windows, **Start dashboard** loads the ignored `.env.local`, refuses any
non-local PostgreSQL host, and binds `127.0.0.1:5000`; run additive migrations
first with `python -m scripts.migrate_postgres`. **Start dashboard (isolated
SQLite)** retains the dependency-free fallback. Visit `/`, not just `/health`
(which returns health status). Existing Linux `scripts/start_dashboard.sh`
remains available.

## Tests, providers and optional software

| Work | Requirements |
|---|---|
| Safe tests and imports | Python packages plus tracked fixtures/artifacts; no keys, login, Ollama daemon or paid APIs |
| Existing historical research | Tracked CSV/JSON evidence; downloads require authorized public/provider internet access |
| HR11 offline capability report | No providers; zero real inputs honestly gives 180 insufficient cells |
| HR11 empirical evaluation | Authorized real 5m history, explicit session calendars, instrument units/costs; supply files per HR11 method |
| Dashboard public feeds | Internet to Yahoo/Moneyweb; no key for those public paths; availability is not guaranteed |
| Additional news/Reddit | Optional NewsAPI key or approved Reddit API credentials/access |
| AI headline comprehension | Optional local Ollama, authenticated Ollama Cloud, or authenticated Moonshot/Kimi; keyword fallback remains labelled |
| Broker/browser probes | Optional separately authorized login/browser setup; excluded from tests; no live-order authorization |

Node/npm, Docker, Java and a database server are not required for this Python
workflow. SQLite is built into Python. Optional existing browser-check scripts
use Playwright/Chromium: install `playwright` with pip in `.venv`, then
`python -m playwright install chromium` only when doing the opt-in browser checks.
Those scripts are not part of the safe suite and contain Linux `/tmp` screenshot
paths; they are not claimed Windows-portable by this handoff. No browser or model
binaries are committed.

## Environment variables (names and public defaults only)

No environment variable is required for offline work. `.env.example` has blank
optional names; commented entries must remain unset until a valid value is chosen.
The diagnostic reports process-variable SET/MISSING only and never reads `.env`.
Tests/import checks disable dotenv loading. The application can load `.env` at
runtime; transfer credentials securely or recreate them manually, never through Git.

| Names | Use | Default when unset |
|---|---|---|
| `NEWSAPI_KEY` | Optional additional news | Disabled/unconfigured |
| `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` | Optional approved Reddit API | Disabled/unconfigured |
| `REDDIT_USER_AGENT` | Reddit client identity | `jse-trading-intel/1.0`; do not set an empty override |
| `OLLAMA_HOST` | Optional local sentiment endpoint | `http://127.0.0.1:11434` |
| `OLLAMA_LOCAL_MODEL` | Optional local sentiment model | `llama3.2:3b` |
| `OLLAMA_CLOUD_MODEL`, `OLLAMA_API_KEY` | Optional cloud sentiment | `gpt-oss:20b`; disabled without key |
| `MOONSHOT_API_KEY`, `KIMI_API_KEY` | Optional Moonshot auth, first name preferred | Disabled without either key |
| `MOONSHOT_MODEL`, `KIMI_MODEL` | Optional Moonshot model, first name preferred | `kimi-k3` (code default, not verified provider availability) |
| `HOST`, `PORT` | App listener | `0.0.0.0`, `5000`; tasks use loopback; never set empty PORT |

The host uses existing provider code; `.env.example` cannot make unsupported
provider models available. There are no required database or broker environment
variables in the current safe workflow. Constructor-only optional integrations
are not invented as environment settings.

## Settings Sync and MCP reality

Settings Sync can carry selected settings, extensions, profiles, snippets and
user tasks. Machine-specific settings are excluded by default; extensions do
not synchronize to/from a remote window. Workspace settings/tasks in this repo
travel through Git. Current client Sync enablement is unknown.
[VS Code Settings Sync documentation](https://code.visualstudio.com/docs/configure/settings-sync).

MCP user/profile definitions can participate in the supported MCP sync workflow;
review what is selected before syncing the unresolved accidental Windows entry.
Installed server software, runtime dependencies, authorization and extension
storage should not be assumed portable merely because a definition syncs.
[VS Code MCP documentation](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

| Item | Handoff method |
|---|---|
| Workspace settings, tasks, extension recommendations, AGENTS/roadmap | Git |
| Selected editor/extension/agent settings | Settings Sync where supported; per-tool state/auth separately |
| MCP settings | No project MCP required or added; Windows residual entry still unverified |
| Python venv and packages | Rebuild using bootstrap; do not copy Linux venv to Windows |
| `.env`, API keys, Git credentials, AI-tool login | Secure manual recreation/reauthentication; never rely on Git or generic Sync |
| Ollama software and model binaries | Install/pull separately if desired |
| Tracked datasets and reports | Git |
| Local databases/caches | See LOCAL_DATA_MANIFEST; Sync is not a data backup |

The preceding MCP investigation found no candidate in accessible workspace or
remote VS Code/Copilot configuration. It could not access the Windows user
profile, so **cleanup was not completed and Windows absence is not verified**.
No MCP file is added by this task. No user-level AI configuration is changed.
