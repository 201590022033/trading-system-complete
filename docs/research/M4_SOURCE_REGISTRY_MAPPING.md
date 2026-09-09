# M4 source registry mapping

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
