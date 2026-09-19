# ADR 0024 — Canonical durable paper loop

Accepted locally, 2026-09-19. Extends and corrects ADR 0023.

Gate 1's input bundle alone did not connect learned evidence to ranking. It also
left a discovery display consuming the old response shape. The repair retains
M11, M12, M13, M14, M15 and PaperBroker rather than replacing their engines.

`application/opportunities/paper_loop.py` composes a single account transaction:
existing positions -> observed exits -> persisted outcomes -> causal M11 evidence
-> M13 ranking -> earlier pending proposal -> paper M14 geometry -> M15 veto and
conservative cash/cost/volume caps -> PaperBroker -> checkpoint and audit records.
Provider I/O is outside the transaction. A separate frozen-input record makes
retries independent of subsequently changed provider responses. PostgreSQL locks
the account row; immutable IDs and atomic commits prevent duplicate fills.

Completed paper outcomes belong to the versioned strategy, not individual
indicators. Only available, matured one-observed-session outcomes feed the
existing contextual learner, with its sample thresholds and uncertainty intact.
Delayed exits are retained but excluded from the one-session evidence cell.
Legacy adaptive aggregates retain their provenance as context: absent a verified
horizon/feature/outcome mapping, they cannot silently impersonate strategy skill.

Existing dated news sentiment is explicitly an opinion input. Macro asset tags
are context only; a macro directional mapping or event calendar is not invented.
Technical and regime observations retain causal clocks. No new collector or
indicator is introduced; production adaptive_fusion weights remain unchanged.

When PAPER_LOOP_CONFIG is present, both Top-5 and the compatibility opportunities
route read only committed worker rankings. Unavailable storage yields 503; stale
rankings yield no ranked opportunities. No scanner or memory fallback is allowed.
Without that explicit configuration, the prior on-demand M13 research-only mode
remains available; it does not start a paper account or execute anything.

The M14 adapter is a disclosed daily-close paper model: later observation entry,
preceding 20-close stop, configured R-multiple target, next observed session exit
and elapsed expiry. It does not assert intrabar stop execution. M15 sees simulated
fully funded ZAR cash shares, real paper ledger exposure and explicit costs.
Missing volume/marks, unavailable short borrow, or a failed veto blocks entry.
All JSE shares share a conservative exposure bucket, not an estimated correlation.

No live broker, remote migration, deployment, profit claim or weight promotion is
part of this decision. See `docs/repair/PAPER_LOOP_RUNBOOK.md` for runtime limits.
