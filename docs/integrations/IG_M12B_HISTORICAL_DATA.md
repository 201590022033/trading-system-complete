# M12B — IG Historical Data Ingestion & Validation

## Status

**COMPLETE — operator IG Demo validation recorded 2026-09-10**

This milestone adds only authenticated, read-only historical retrieval. It does
not stream prices, place or modify orders, change scoring, rank opportunities,
or run HR11.

## IG contract and request boundary

`IGReadOnlyAdapter.get_historical_prices()` uses `GET /prices/{epic}` version 3
with explicit `resolution`, `from`, `to`, `pageSize`, and `pageNumber` query
parameters. This matches the official [IG Labs v3 prices reference](https://labs.ig.com/reference/prices-epic.html).
The shared adapter constructs the effective URL beneath
`https://demo-api.ig.com/gateway/deal` (or the LIVE gateway) and sends IG's
documented `Version` request header. The initial candidate incorrectly sent
`Accept-Version`; IG therefore treated the v3-only prices request as its default
version 1 and returned a generic HTML/Tomcat 404 even though the effective path
was already `/gateway/deal/prices/{epic}`. The corrected boundary uses
`Version: 3`; it does not switch endpoint versions.

`request_route()` exposes only environment, method, effective host, effective
path and API version for offline routing diagnosis. Query values and all request
headers/credentials are excluded. Absolute URLs and path traversal are rejected;
both leading-slash and plain relative endpoints remain beneath `/gateway/deal`.
The documented resolutions are `SECOND`, `MINUTE`, `MINUTE_2`, `MINUTE_3`,
`MINUTE_5`, `MINUTE_10`, `MINUTE_15`, `MINUTE_30`, `HOUR`, `HOUR_2`,
`HOUR_3`, `HOUR_4`, `DAY`, `WEEK`, and `MONTH`. They map explicitly to `1s`,
`1m`, `2m`, `3m`, `5m`, `10m`, `15m`, `30m`, `1h`, `2h`, `3h`, `4h`,
`1d`, `1w`, and `1mo`; 30-minute bars are never daily-session horizons.

## Canonical normalization and price basis

IG supplies separate `bid`, `ask`, and `lastTraded` values for each open, high,
low, and close component. `lastTraded` and `lastTradedVolume` may be null for
non-exchange-traded instruments. `IGHistoricalBar` preserves all three OHLC
component sets and optional volume. No spread component is discarded.

The embedded M8 `CanonicalBar` uses the explicit, versioned
`ig-bid-ask-mid-v1` basis: each OHLC component is `(bid + ask) / 2`. Its `bid`
and `ask` fields retain the closing quote pair. This derived mid is not an
observed trade price. The official schema names all bid/ask fields and does not
document a last-traded-only substitute for missing quote sides. Consequently,
even complete `lastTraded` OHLC does not replace incomplete bid/ask OHLC without
real shape evidence and an explicit later decision. Such rows remain excluded;
no quote side or OHLC value is fabricated.

The EPIC remains the bar identity at this broker boundary. Each bar carries a
deterministic source-record hash, environment, and IG source identity. Retrieval
metadata remains on the series. M12B does not persist bars; future persistence
must use the existing canonical persistence boundary.

## Timestamps, causality, and completed bars

IG documents `snapshotTimeUTC` as UTC and `snapshotTime` as market-local time.
The UTC value is required and normalized to a timezone-aware UTC interval start.
The original local string is retained with timezone state
`IG_MARKET_LOCAL_UNSPECIFIED`; its offset is not guessed. Requests accept only
timezone-aware start/end values and serialize their UTC equivalents.

The snapshot is the interval start. Event and historical-publication availability
are the calculated interval end. This is the M8 historical-publication convention,
not proof of instantaneous provider delivery. Import time is separately retained.
Bars ending after retrieval are incomplete and excluded.

## Paging, completeness, and quality

The importer follows v3 `metadata.pageData` within explicit `max_points`,
`page_size`, and `max_pages` bounds. It sorts chronologically, deduplicates
overlapping timestamps while reporting duplicates, and reports
`PARTIAL_TRUNCATED` if a bound stops retrieval before `totalPages`. Empty and
partially malformed results remain explicit. Accepted in-range bars, records
outside the requested range, incomplete bars, structurally malformed records
and duplicates have separate counters. Structural reason occurrences cover
missing/null components, missing/invalid UTC timestamp, invalid numeric input,
OHLC invariant failure or other; one malformed record may contribute more than
one reason. A structurally malformed record with a usable out-of-range timestamp
is observable in both applicable counters. Optional
`--malformed-samples 1..5` output contains only timestamp, component presence
states, volume presence and reasons; it never includes price values or raw rows.

IG may return valid records outside the requested boundaries; the observed API
response does not establish why. They remain filtered from the canonical series
and increment `excluded_outside_range`, never `excluded_malformed` on range
status alone. Range-only exclusions do not create `PARTIAL_MALFORMED`.
`COMPLETE_REQUESTED_RANGE` means only that response processing was not truncated
and found no incomplete or structurally malformed rows; it is explicitly scoped
as `API_RESPONSE_FILTERING_ONLY; MARKET_CALENDAR_UNASSESSED`. It does not claim
EPIC-specific market-calendar coverage.

`gaps` counts fixed-cadence interval discontinuities and is labeled
`UNCLASSIFIED_INTERVAL_DISCONTINUITIES`. Without an instrument trading calendar,
closures and genuinely missing bars cannot be separated. Suitability missingness
therefore remains unknown rather than treating closures as missing data. Monthly
cadence is variable and receives no numeric gap inference.

Every series reports source context, environment, EPIC, resolution, requested
range, bar count, discontinuities, duplicates, excluded rows, timestamp quality,
price basis, completeness, page count, remaining allowance when supplied, and
retrieval time. Demo history is conservatively `RESEARCH_DATA`, never execution
grade. Suitability integration supplies only factual availability, resolution,
history depth, coverage and timestamp quality; attractiveness is unchanged.

## Limits and failure handling

IG's [official FAQ](https://labs.ig.com/faq.html) indicates approximately 360
days for 5/10/15/30-minute and 1/2/3/4-hour data, 40 days for 1/2/3-minute data,
four days for one-second data, and 15 years for daily data. It documents a
default 10,000 historical-point weekly allowance and non-trading request limits.
These are indications, not guarantees for any EPIC or account.

Historical failures are not retried automatically, avoiding multiplied quota
use or masked partial results. HTTP 429 and IG's historical-allowance error are
surfaced as `RATE_LIMITED`; the operator can retry after the allowance resets.

Historical CLI failures are emitted as one safe JSON object rather than a Python
traceback. It includes status, HTTP status, bounded response content type, IG
error code/category and safe message. For non-JSON bodies it may also include a
sanitized 240-character text excerpt; HTML tags are removed, whitespace is
collapsed, and configured credentials/session values plus credential-like fields
are redacted. Empty bodies remain explicit. The existing authentication-status
diagnostic format is unchanged.

## AI configuration isolation

The M12B foundation change in `ai_config.py` recognizes
`PYTHON_DOTENV_DISABLED` and skips `.env` loading only when that configuration
flag is explicitly enabled. `scripts/run_tests.py` enables it so offline tests
cannot consume operator secrets. `test_ai_config.py` verifies that isolation.
This is configuration plumbing only: it does not alter provider decisions,
prompts, scoring, signals, execution, or runtime trading behavior. Normal local
configuration continues to load `.env` when the flag is absent.

## Automated evidence

Mocked tests cover retrieval, resolutions, canonical OHLC, quote preservation,
derived-mid versioning, UTC/DST handling, naive-time rejection, incomplete bars,
independent range/malformed classification, requested-range preservation,
pagination, ordering, overlaps, duplicates, discontinuities, truncation, empty
and malformed responses, allowance errors, redaction, M8 lineage, factual
suitability metadata, and disabled execution.

The full safe suite passes 363 tests. All 39 protected research artifacts match
their baseline SHA-256 values.

## Operator-verified external IG Demo evidence

After the version-header repair, the operator obtained non-truncated Brent `$1`
history: DAY accepted 26 and excluded 1; HOUR accepted 39 and excluded 6;
MINUTE_5 accepted 457 and excluded 70 over two pages, with remaining allowance
9401. A subsequent external 5-minute diagnostic established that all 70 excluded
records had complete bid/ask OHLC, valid timestamps and volume; their only reason
was `outside_requested_range`. They were valid extra response records, not
malformed bars. The local candidate now represents that distinction correctly.

The operator's final revalidation of the same 5-minute request returned 457
derived-mid bars, zero malformed, zero incomplete, zero duplicates, 70 valid
out-of-range exclusions, two pages and no truncation. Timestamps span
2026-09-01T00:00:00+00:00 through 2026-09-02T16:00:00+00:00. Completeness is
`COMPLETE_REQUESTED_RANGE`, scoped to
`API_RESPONSE_FILTERING_ONLY; MARKET_CALENDAR_UNASSESSED`; the 24 observed gaps
remain `UNCLASSIFIED_INTERVAL_DISCONTINUITIES`. Daily and hourly requests were
also externally verified non-empty, UTC-normalized, duplicate-free and
non-truncated. This evidence came from the operator's IG Demo environment; the
coding workspace did not access the operator account.

IG historical API, DAY/HOUR/MINUTE_5 retrieval, v3 pagination, UTC
normalization, duplicate handling, range filtering, malformed classification,
incomplete exclusion, truncation handling and price-basis provenance therefore
pass M12B acceptance. IG Demo can provide real 5-minute historical Brent bars
and is a viable candidate data source for later HR11 validation. This does not
prove full long-horizon 5-minute depth, close the HR11 data gap, or authorize an
HR11 rerun.

Remaining limitations are explicit: Demo data remains `RESEARCH_DATA`, the
historical allowance applies, the market-local timezone identifier is
unavailable, no EPIC-specific trading calendar exists, and interval
discontinuities remain unclassified. Execution remains disabled.
