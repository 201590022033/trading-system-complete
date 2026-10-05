# Development environment — current Windows workflow

Reviewed 5 October 2026. The active workstation is Windows/PowerShell. Earlier Ubuntu/Codespaces and September machine checks are historical observations, retained in [the previous guide](history/DEVELOPMENT_ENVIRONMENT_PRE_2026-10-05.md), not claims about this PC.

Use Python 3.12 and the checked-in `requirements.txt`/`constraints.txt`. `scripts/setup_dev.py` prepares a project environment; select that interpreter in VS Code. The current task used the existing project virtual environment at `C:/Users/Deon/Documents/GitHub/trading-system-complete/.venv/Scripts/python.exe`; a different checkout should create/select its own environment instead of assuming that absolute path.

```powershell
py -3.12 scripts/setup_dev.py
.\.venv\Scripts\python.exe scripts/check_dev_environment.py
.\.venv\Scripts\python.exe scripts/run_tests.py
.\.venv\Scripts\python.exe scripts/verify_protected_artifacts.py
```

The full suite blocks dotenv/outbound sockets and excludes manual provider/broker/LLM probes. `--focused` is a narrower convenience subset; run feature-specific tests and the full suite for relevant changes. Preserve immutable benchmark checksums. Do not write new research outputs into frozen benchmark paths.

VS Code tasks cover environment checks, full/focused tests, compile validation, local PostgreSQL dashboard startup and optional Ollama checking. The SQLite-labelled task alone does not clear inherited deployment settings; follow [Quick Start](../QUICKSTART.md) for explicit isolation. Reviewed PostgreSQL startup loads `.env.local`, requires a loopback database and binds localhost. Migrations are explicit, additive and separate from startup.

PowerShell helper scripts may need `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...` for that process only. Do not change machine-wide execution policy to run setup. Use `railway.cmd` on Windows when the PowerShell wrapper treats harmless stderr warnings as failures; still check the native exit code. Configuration migration warnings are not evidence of a failed key update or a completed deployment.

Secrets live in ignored local files and Railway's secret configuration. Never print variable listings or paste keys/passwords into chat. Local CPU weekly-news inference is the verified fallback for the observed GPU incompatibility; see [Ollama roles](OLLAMA_MODELS.md). No external model or provider is required for the safe test suite.
