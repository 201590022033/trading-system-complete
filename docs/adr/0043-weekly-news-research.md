# ADR 0043 — Weekly derived context and local research flags

Date: 2026-10-05. Status: accepted. Starting commit: 7144820.

The owner receives a Monday South African market brief and wants it among news
resources, with a small weight and Ollama cross-source historical-research flags.

Add `weekly_sa_brief` to the existing source catalogue and Sources panel. It is
derived research, authority tier 4, user-provided/unverified, manually imported.
An edition date is not a publication timestamp. Actual receipt time is retained;
imports are content-addressed and retries preserve the first receipt. Text claiming
"verified" does not make the imported brief independently verified evidence.

Reuse the existing shared SQLite/PostgreSQL append-only record ledger in a separate
RESEARCH_ONLY account. No persistence migration. Authenticated import/scan APIs use
the existing operator session or private local-upload token. Public reads contain
briefs and bounded research state, never credentials. Default ranking, policy,
risk, sizing and execution paths do not consume these records.

The local daily collector optionally invokes a bounded local-only Ollama scan
after successful OHLC upload (`WEEKLY_NEWS_RESEARCH_ENABLED=1`). One durable model
automatic attempt per UTC day, plus at most four explicit repair retries via
`--retry-failed`; no cloud fallback. Failed model state is surfaced on the dashboard.
The weekly local request has a bounded480-second timeout and an8192-token context
default and CPU-only inference by default; existing sentiment requests retain their45-second default.
Saved outboxes retry without another model
call. Inputs are at most 20 dated real article URLs from the existing public news
feed, the current brief (14-day freshness gate), and registered cash-share IDs.
The model proposes at most two semantic relationships, not numerical correlations.
Unknown references, future/stale articles, non-finite confidence and unknown
instruments are rejected. Same URLs, same publishers and strongly similar headlines
do not earn the research boost. Distinct publishers are still not proof of source
independence. The brief itself never counts as a second corroborating publisher.

A eligible relationship gets at most +0.05 research priority (cap 1.0) and a
historical research flag. Trading weight stays zero under Constitution section 3.
The flag initiates a local archive screen for earlier category/instrument cases
and observed 3/4/5-session close returns, starting only after actual receipt.
Unknown article publication times, unavailable real bars and estimated closes
block observations. Repeated evidence pairs are deduplicated. These observations
are descriptive, overlap, omit costs/stops/volume, and establish neither causality
nor a validated strategy. No history produces a visible waiting state.

Historical SENS/news retrieval, economic-event matching, adjusted returns versus
sector controls, chronological strategy backtests and statistical correlation
remain separate work. This implementation does not invent archival articles.
Automatic delivery from the existing ChatGPT Monday task is not connected. Import
the attached past editions now; future editions can be pasted into the dashboard
until an actual permitted feed/connector is established. No duplicate reminder.

Generation uses an Ollama JSON schema with real article-ID and instrument enums,
two-case/two-reference limits and required confidence/category fields. Independent
validation remains mandatory. See https://docs.ollama.com/capabilities/structured-outputs.
Rejected output remains private locally; it cannot earn attention or trading weight.
