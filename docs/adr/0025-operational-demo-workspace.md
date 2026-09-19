# ADR 0025 — Operational demo workspace

2026-09-19, authorized by the user following the deployed end-to-end audit.

The previous checkpoint verified a backend paper slice but omitted deployed
migrations, runtime activation, portfolio UI and paper learning telemetry. The
Railway audit found no paper tables, no worker jobs, zero shadow records, and only
one old validation evidence row. IG and cloud AI configuration were absent.

Implement one portfolio workspace over the existing paper ledger: equity/cash,
positions and geometry, fills/outcomes, learning lineage, queued decisions,
aggression and pause/resume. Persist runtime controls separately from immutable
account assumptions, audit each change and apply it on the next locked cycle.
Protect mutations with an operator secret/session; never expose secrets in page
source, URLs or logs. IG remains explicitly DEMO, with actionable connection
diagnostics. Missing credentials are a missing prerequisite, not a reason to
claim connectivity.

Persist existing news collector results as dated immutable evidence; reuse the
same collector in bounded worker ingestion. Do not relabel cached evidence as new.
Expose paper outcomes separately from legacy shadow counters. Connect existing
IG adapters only where actual credentials and contract mappings can be verified;
preserve source units, availability times, missing-volume semantics and M15.

Deployment acceptance must check actual PostgreSQL tables, job progress, persisted
records, API data and the rendered browser workspace. Component tests alone are
insufficient. Keep real-money execution disabled. A successful deployment is not
proof that a market session has closed or that a learned cell has enough samples.
