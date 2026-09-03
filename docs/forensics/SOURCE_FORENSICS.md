# Source Forensics

## Producing observations

No source supplied a historical score series to M7/M10. Source-only rows have
zero signals and the reliability store contains no committed outcome database.
Historical coverage, timeliness, hit rate, false-positive rate, lead time,
decay, sector relevance and source independence are therefore all
`INSUFFICIENT DATA`.

Moneyweb RSS and Moneyweb-hosted SENS are enabled collectors, but “enabled” is
not evidence that their observations were persisted or evaluated. All other
catalogued sources remain disabled/manual/licensed as documented in
`DATA_SOURCES.md`.

## Duplication

`EvidenceRecord` deduplicates identical stable IDs, but no corpus exists to test
cross-outlet syndication. Five rewritten Reuters-derived headlines could still
receive distinct IDs. Common-origin clustering cannot be quantified here.

## Required evidence

Persist immutable publication/ingestion timestamps, URL/canonical origin,
ticker/sector mapping, direction/confidence and later outcomes. Record deletion
and licensing constraints. Evaluate authoritative SENS separately from media
and community content, with syndicated clusters counted once.
