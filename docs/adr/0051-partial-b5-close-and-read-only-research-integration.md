# ADR 0051: Owner-approved partial B5 close and read-only integration

Status: Accepted, 5 October 2026. The owner explicitly approved the proposed partial close and start of research integration.

B5 closes as PARTIAL_CLOSED: software verification, source acquisition, calendars, price comparison and independent conditional accounting are accepted deliverables. Verified real-data admission, complete RAW/action treatment, intraday volume/interval semantics and the admitted real-trade audit are deferred evidence gates. This is not full engine acceptance or strategy validation. Zero admitted real trades remains the recorded result.

R1 is the next milestone: read-only dashboard research integration. Reuse the existing Trading Strategies surface and Flask blueprint pattern. Export a bounded, sanitized, hashed summary of local verified reports; an optional configured report directory supplies it to a read-only API. Missing, malformed or changed artifacts display unavailable rather than invented results. No raw browser text, credentials, account records or local paths are returned. Refresh reads the report only; it cannot call providers, replay, modify ranking or submit orders.

The panel presents B5's partial outcome, dated software verification, observed source comparisons and unresolved data gates. It keeps conditional accounting distinct from an admitted trade audit. IG availability requires a separate read-only runtime/provider check; adding the panel neither grants entitlement nor establishes that history is accessible.

R1 acceptance: endpoint returns only the bounded safe schema; unknown/malformed/tampered input fails closed; unconfigured installations remain usable; UI shows provisional data and zero admitted trades; local preview and focused/full safe tests pass; protected artifacts remain unchanged. The report exporter is offline and local. Hosted deployment, automatic provider collection, strategy optimization, default trading changes and execution remain outside R1.
