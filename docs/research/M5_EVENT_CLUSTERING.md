# M5 event clustering

## Current context — 5 October 2026

The original module/design contract below is retained. Its delivered/planned labels describe that scope/checkpoint; use the current snapshot for later integration and deployment state.

Manual Monday briefs and local Ollama research cases now extend the existing source catalog. Distinct-publisher corroboration gates the +0.05 research attention boost; it never changes trade weights. Current single-publisher cases have zero flags, and historic SENS/event retrieval remains planned. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

Existing Tier-1 exact deduplication remains `evidence.deduplicate_evidence()`;
it preserves the first `EvidenceRecord` for each stable evidence ID. M5 adds an
isolated Tier-2 `EventClusterer` that never deletes or rewrites those records.

`EventClusterPolicy` makes the event window, token-Jaccard method, threshold,
entity-overlap requirement, normalization version and language explicit. The
default test policy is research configuration, not production truth. Clusters
use normalized headline-token Jaccard similarity, optional shared references,
and bounded published/observed-time proximity. No embeddings, LLMs, paid APIs,
or external services are used.

Cluster IDs deterministically hash policy identity/version and ordered evidence
IDs. Each `ClusteredEvent` retains every member ID, source ID, entity/macro
references, representative headline, directional summary and aggregate
strength. Source-level provenance therefore remains inspectable.

The `as_of` snapshot excludes evidence ingested after the decision cutoff, so a
later syndicated article cannot alter an earlier snapshot. False-positive safety
prefers separate events when entities differ, text similarity is insufficient,
or the configured event window is exceeded. Similar boilerplate alone is not a
production admission criterion.

The engine is intentionally disconnected from sentiment weighting, dashboard
feeds, source reliability, opportunity ranking, persistence schemas and trading
decisions. Persistence and later runtime consumption are deferred.
