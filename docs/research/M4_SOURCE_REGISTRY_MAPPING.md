# M4 source registry mapping

## Current context — 5 October 2026

The original module/design contract below is retained. Its delivered/planned labels describe that scope/checkpoint; use the current snapshot for later integration and deployment state.

Manual Monday briefs and local Ollama research cases now extend the existing source catalog. Distinct-publisher corroboration gates the +0.05 research attention boost; it never changes trade weights. Current single-publisher cases have zero flags, and historic SENS/event retrieval remains planned. See [current project state](../CURRENT_STATE.md) and [document index](../DOCUMENTATION_INDEX.md).

---

The canonical `domain.registry.source.CanonicalSourceRegistry` wraps the
existing `market_intelligence.SourceRegistry`, which in turn delegates all
SQLite CRUD, enable/disable updates, manual weights and audit records to
`MarketIntelligenceStore`. No schema migration was introduced.

The 16 built-in `source_catalog.DEFAULT_SOURCE_POLICIES` are represented with
canonical governance states, while their legacy status strings remain available
through `to_legacy()`. Endpoint, access mode, source class, authority tier,
enablement and polling intervals are preserved. Unknown freshness, failure,
health, learned-weight and coverage values remain `None` or empty rather than
being invented.

Evidence provenance can carry the canonical identity through `policy.provenance()`
(`source_id`, `source_class`, `authority_tier`). Existing `EvidenceRecord` and
exact deduplication are unchanged.

No current collector was migrated in M4. Dashboard feeds, sentiment analysis,
Moneyweb/SENS intake and other collectors retain their existing policy paths or
bypass behavior. Learned reliability is a placeholder field only and is not
connected to source weighting. Event-level clustering remains deferred to M5.
