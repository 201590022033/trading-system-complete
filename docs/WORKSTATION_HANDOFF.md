# Windows Workstation Handoff — Local AI / Ollama Setup

Verified on this laptop: **2026-09-06**.

This document is the exact checklist to reproduce the local-AI setup on the owner's primary Windows work desktop. Git synchronizes the project, scripts, tests and setup documentation. Kimi credentials and Ollama models remain local to each computer and must not be committed or copied through Git.

## Prerequisites on the work desktop

- Windows 10/11 with PowerShell
- Git (or GitHub Desktop)
- Python **3.12.x**
- VS Code (optional but recommended)
- Internet access for the first clone and Ollama download

## Work desktop setup steps

1. **Clone/pull the repository**

   ```powershell
   git clone https://github.com/201590022033/trading-system-complete.git trading
   cd trading
   ```

   Or, if the repository already exists, fetch and checkout `master`:

   ```powershell
   git fetch origin
   git checkout master
   git pull origin master
   ```

2. **Verify expected branch/commit**

   ```powershell
   git branch --show-current
   git log -1 --oneline
   ```

   Expected branch: `master`. The exact commit is recorded in the milestone report and should match the pushed checkpoint.

3. **Create/rebuild the Python environment**

   From the repository root:

   ```powershell
   py -3.12 scripts/setup_dev.py
   ```

   This creates `.venv`, installs pinned dependencies from `requirements.txt`/`constraints-dev.txt`, and runs the development diagnostic.

4. **Install/verify Ollama**

   Check status only:

   ```powershell
   powershell -ExecutionPolicy Bypass -File ./setup_ai.ps1 -CheckOnly -SkipKimiKey
   ```

   If Ollama is missing, install it via winget using the repository script:

   ```powershell
   powershell -ExecutionPolicy Bypass -File ./setup_ai.ps1 -InstallOllama -SkipKimiKey
   ```

   This uses the official `Ollama.Ollama` winget package. If winget is unavailable or elevation is required, install manually from https://ollama.com/download/windows.

5. **Obtain the required Ollama model**

   The repository default is `llama3.2:3b` (~2 GB). Pull it only when missing:

   ```powershell
   powershell -ExecutionPolicy Bypass -File ./setup_ai.ps1 -PullModel -SkipKimiKey
   ```

   The script never silently downloads a model. If you want a different model, pass `-Model <name>`.

6. **Verify the local AI provider**

   ```powershell
   .venv\Scripts\python.exe scripts/check_dev_environment.py --ollama
   ```

   Expected output includes:

   ```text
   OLLAMA: OK
   OLLAMA VERSION: 0.33.3
   OLLAMA INSTALLED: YES
   OLLAMA REACHABLE: YES
   OLLAMA MODEL PRESENT: YES
   OLLAMA MODELS: llama3.2:3b
   ```

7. **Install Kimi Code CLI/VS Code extension if absent**

   Follow the official instructions at https://www.kimi.com/code/docs/en/kimi-code-cli/installation.html.

   In VS Code: Extensions → search "Kimi Code" → Install.

8. **Authenticate Kimi Platform locally on that desktop**

   Open the Kimi Code panel in VS Code and sign in with the Kimi Platform account. The API key or login token is entered **only on that machine** and is stored under:

   ```text
   C:\Users\<user>\.kimi-code\
   ```

   **Never commit, copy, or document this credential in the repository.** Kimi authentication is workstation-local; do not sync `~/.kimi-code` through Git.

9. **Verify Kimi coding-agent access to the repository**

   In VS Code, open the repository folder and confirm Kimi Code can read files and run terminal commands against the project.

10. **Run the project's validation suites**

    Focused tests:

    ```powershell
    .venv\Scripts\python.exe -m unittest test_dev_environment test_ai_config -v
    ```

    Full safe offline suite:

    ```powershell
    .venv\Scripts\python.exe scripts/run_tests.py
    ```

    Development diagnostic:

    ```powershell
    .venv\Scripts\python.exe scripts/check_dev_environment.py --ollama
    ```

    All should pass before any trading research work resumes.

## Optional: add cloud AI credentials

If you later configure Kimi/Moonshot or Ollama Cloud, run `setup_ai.ps1` without `-SkipKimiKey` and enter the key securely. The script writes only to the ignored `.env` file and never stores the key in Git.

Local Ollama requires **no API key**.

## What stays machine-local

| Item | Location | Sync via Git? |
|---|---|---|
| Project code, scripts, docs | Repository | Yes |
| Python virtual environment | `.venv/` | No (rebuild with `scripts/setup_dev.py`) |
| Ollama runtime / models | `C:\Users\<user>\AppData\Local\Programs\Ollama\` and model cache | No (reinstall/repull per machine) |
| Kimi Platform credentials | `C:\Users\<user>\.kimi-code\` | No (authenticate per machine) |
| Local `.env` secrets | Repository root `.env` | No (ignored; create per machine) |

## Next development action

With local AI verified, read `AGENTS.md`, the mandatory architecture/roadmap files, and `docs/roadmap/CURRENT_MILESTONE.md`. Resume the deferred **OI3** provider verification only through an explicit owner instruction. Do not invent HR12, modify protected HR11 artifacts, or enable automated broker submission.
