# Historical Feature Store

Phase HR1 introduces `historical_feature_store.py`, an additive research/shadow
boundary. It does not replace live observations, alter signal weights, or feed
production decisions.

## Normalized schema

One `HistoricalFeature` represents one raw observation or one reproducible
derived value. It records instrument, asset class, sector/profile, feature group
and name, typed JSON value, feature version, revision state, capability state,
provenance, raw/derived identity and lineage.

Feature groups are `raw_market`, `technical`, `regime`, `macro`, `cross_asset`,
`commodity`, `fx`, and `source_event`. OHLCV is stored as distinct raw-market
records rather than mixed into derived indicators. Technical, regime, macro,
cross-asset, commodity, FX and event features remain independently queryable.

## Storage

The v1 canonical local format is append-only, deterministic JSON Lines. It is
dependency-light, diffable, hash-identifiable and exactly round-trippable. A
Parquet projection is appropriate for large HR2+ datasets when a declared
Parquet engine is installed, but Parquet is not canonical yet because neither
PyArrow nor fastparquet is declared by this repository. This avoids an implicit
binary dependency and does not prevent later partitioned columnar export.

`PointInTimeFeatureStore.as_of()` selects only records available and materialized
for a reconstructed decision by the query cutoff, then keeps the latest revision
that was actually available then. Record
IDs are stable SHA-256 identities over the observation's source/time/version
identity. Duplicate appends are rejected.

The executable schema summary is
`analysis/results/historical_feature_store_schema.json`.

## Raw/derived separation

- Raw records cannot claim input lineage.
- Available derived records must list their raw/derived `input_record_ids`.
- Unavailable capabilities store `value=null` and a required reason.
- Derived values carry explicit feature versions; changing a formula requires a
  new version, not mutation of old output.

## Integration direction

HR2 loaders should normalize source data into raw records first. HR3+ feature
builders should consume as-of-selected raw records and emit derived records with
lineage. Existing `EvidenceRecord`, `MarketBar`, profile and regime objects are
inputs/adapters, not competing stores.
