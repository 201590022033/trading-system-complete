# Ollama and model manifest — 2026-09-06

**Required models for offline tests/historical research/HR11: none.**
Ollama can power trading-app headline comprehension; it is not solely an editor
tool. The app's optional AI sentiment path lives in `sentiment_providers.py` and
`sentiment_analyzer.py`, with explicit keyword fallback when no provider works.
Developer Codex/Copilot/Kimi Code tooling is separate.

| Model | Role | Current evidence |
|---|---|---|
| `llama3.2:3b` | Optional default local Ollama model | **Installed and verified** on this Windows laptop via Ollama 0.33.3; direct and provider-boundary inference succeed |
| `gpt-oss:20b` | Optional Ollama **Cloud** default | Code default; cloud access requires OLLAMA_API_KEY; not a mandatory local pull |
| `kimi-k3` | Optional Moonshot/Kimi HTTP default | Code default, not Ollama; account/model availability unverified |

Local Ollama CLI version: **0.33.3**. The default server endpoint
`http://127.0.0.1:11434` is reachable on this laptop. The only pulled model is
`llama3.2:3b` (~2.0 GB); no unrelated model needs copying. Model binaries are
machine-local and must not be committed or synced through Git.

The Python client `ollama==0.6.2` is a declared dependency; installing it does
not install the Ollama service or models.

## Reproducing this setup on a fresh Windows workstation

Use the repository's PowerShell helper (requires PowerShell and winget):

```powershell
powershell -ExecutionPolicy Bypass -File ./setup_ai.ps1 -InstallOllama -PullModel -SkipKimiKey
```

Then verify:

```powershell
.venv\Scripts\python.exe scripts/check_dev_environment.py --ollama
```

Expected result:

```text
OLLAMA: OK
OLLAMA VERSION: 0.33.3
OLLAMA INSTALLED: YES
OLLAMA REACHABLE: YES
OLLAMA MODEL PRESENT: YES
OLLAMA MODELS: llama3.2:3b
```

If Ollama is already installed, the script is idempotent and will not reinstall.
If the model is already present, it will not re-download it. If the download
would exceed ~5 GB, stop and ask the owner before proceeding.

Do not start a second service if the Ollama desktop app already runs one. Use the
project interpreter to run `scripts/check_dev_environment.py --ollama`; it probes
only loopback, reports service/model presence, and performs no generation. Model
presence is not successful structured-output validation. Re-pull on the new
workstation rather than copying model blobs through Git.

Optional overrides: OLLAMA_HOST, OLLAMA_LOCAL_MODEL, OLLAMA_CLOUD_MODEL.
Cloud key: OLLAMA_API_KEY. Kimi keys/models: MOONSHOT_API_KEY/KIMI_API_KEY and
MOONSHOT_MODEL/KIMI_MODEL. Never expose values. The existing providers rotate a
bounded budget and label failures/fallback. OI3 still needs real-provider success
and discovery verification; this environment handoff does not complete it.

The application loads an optional repository-root `.env` through `ai_config.py`;
explicit process variables take precedence. Run `setup_ai.ps1` in PowerShell to
enter a Kimi/Moonshot key without echoing it and write local Ollama defaults.
The helper refuses to continue unless `.env` is Git-ignored and never changes
global Windows, Continue, Codex or Copilot configuration. Local Ollama requires
no API key.
