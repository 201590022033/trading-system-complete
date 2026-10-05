# Laptop handoff — current checkout

Reviewed 5 October 2026. Pull the current `master` of `201590022033/trading-system-complete`; the code checkpoint for this reconciliation is `c2ef802`. Do not use the old September commit as the current release. Historical instructions remain in [the earlier handoff](history/LAPTOP_HANDOFF_PRE_2026-10-05.md).

Follow [development setup](DEVELOPMENT_ENVIRONMENT.md) and [Quick Start](../QUICKSTART.md), select Python 3.12, run the full safe suite and verify protected artifacts before using external providers. Preserve [local archives and receipts](LOCAL_DATA_MANIFEST.md) separately; a Git pull does not recover private runtime data.

The PC must be powered on and signed in for the 07:30 SAST local collection task. Review that task's working directory/interpreter after moving a checkout. Recreate the task explicitly on a new machine, rather than assuming it came from Git. Railway's bounded worker runs at 08:00 SAST and requires uploaded data.

Private configuration includes the upload token/URL, optional local weekly-news switch/model and provider credentials. Do not copy production database settings into an isolated local check or print secret lists. The installed model observed on the current PC is `llama3:latest`; weekly research uses CPU for the observed GPU incompatibility. Alpha Vantage scheduled calls remain off locally and on Railway.

Read [current state](CURRENT_STATE.md) for profile defaults, incomplete-data gates and actual research results. Do not reconnect legacy multi-agent ranking, enable Live execution or reset durable paper balances as part of a handoff. Native PostgreSQL acceptance and external provider/model probes are separate from offline tests.
