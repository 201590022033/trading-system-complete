# Local data and durable-state manifest

Reviewed 5 October 2026. Source control holds code/contracts and frozen benchmark artifacts, not the complete operating dataset. [Earlier handoff inventory](history/LOCAL_DATA_MANIFEST_PRE_2026-10-05.md) records the old machine's state.

| Data | Location / owner | Handling |
| --- | --- | --- |
| Daily raw OHLCV | Ignored `runtime/local-swing-data/` on the home PC | Preserve dated/latest histories, source metadata and collection receipts; do not commit |
| Weekly-news research | Ignored `runtime/weekly-news-research/` | Preserve brief editions, actual receipt times, raw responses, attempts and outboxes; retry idempotently |
| Alpha probe cache | Ignored `runtime/alpha-vantage-probe.db` | Preserve to maintain request budget; do not create extra caches to bypass limits |
| Local private settings | Ignored `.env` / `.env.local` | Transfer through a private channel; never paste into chat/Git/logs |
| Local model | Ollama's machine-managed model store | Current observed model is `llama3:latest`; reinstall explicitly on a replacement PC |
| Railway state | Shared PostgreSQL | Snapshots, proposals, research runs, paper accounts, journals and outcomes persist independently of Git |
| Frozen benchmarks | Versioned artifacts listed in `docs/handoffs/2026-09-06-ARTIFACT-CHECKSUMS.json` | Verify 54 artifacts; do not overwrite with newly generated reports |
| Virtual environment | Machine-specific `.venv` | Rebuild from requirements/constraints, do not copy as a dataset |

Back up local archives/receipts privately before changing machine or clearing runtime files. Preserve original timestamps; restoring a file is not a new market observation. PostgreSQL backups/migrations are separate operator-reviewed operations; this documentation change performs neither. Historical source files and local artifacts must not be assumed present on a fresh clone.
