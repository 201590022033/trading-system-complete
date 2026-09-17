# Shadow runtime environment

| Setting | Use |
| --- | --- |
| DATABASE_URL | Shared PostgreSQL repository when using a PostgreSQL URL. Never logged. |
| SQLITE_DB_PATH | Shared local SQLite file; default `market_intelligence.db`. |
| APP_MODE | Deployment/read-only health classification; no trading enablement. |
| PORT | Web port only. |
| COMMIT_SHA | Worker release metadata. |
| WORKER_ID | Stable worker identity; not a broker credential. |
| PYTHON_DOTENV_DISABLED | `1`, `true`, or `yes` disables repository dotenv loading globally. |

`project_environment()` preserves explicit mapping/process precedence over the
repository-root `.env`. A process-wide dotenv opt-out cannot be bypassed by
passing a mapping which omits the flag or sets it to false. File-loading tests
must explicitly clear the process opt-out while mocking the file loader; they
must never read real secrets. The canonical regression runner sets the opt-out.
Broker authentication protocol and endpoint logic are unchanged.

Web/worker persistence reads process configuration; it does not load `.env`
implicitly. Runtime reliability uses the same repository. The old standalone
research `reliability.db` is left untouched, not automatically migrated. Network
MI provider/text-loader dependencies must be explicitly approved and supplied by
the host; absent dependencies fail jobs closed. No provider or IG settings are
invented or reconstructed. No connection URL, token or arbitrary job checkpoint
is exposed by readiness/LearningStatus responses.
