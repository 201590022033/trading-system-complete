# M12B — IG Historical Data Ingestion & Validation

## Status

**BLOCKED — local candidate complete; operator IG Demo validation required**

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
partially malformed results remain explicit. Exclusions now include reason
occurrence counts for missing/null components, missing/invalid UTC timestamp,
invalid numeric input, OHLC invariant failure, out-of-range record or other.
One excluded record may contribute more than one reason. Optional
`--malformed-samples 1..5` output contains only timestamp, component presence
states, volume presence and reasons; it never includes price values or raw rows.

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

## Automated evidence

Mocked tests cover retrieval, resolutions, canonical OHLC, quote preservation,
derived-mid versioning, UTC/DST handling, naive-time rejection, incomplete bars,
pagination, ordering, overlaps, duplicates, discontinuities, truncation, empty
and malformed responses, allowance errors, redaction, M8 lineage, factual
suitability metadata, and disabled execution.

The full safe suite passes 360 tests. All 39 protected research artifacts match
their baseline SHA-256 values.

## External IG Demo evidence and required revalidation

After the version-header repair, the operator obtained non-truncated Brent `$1`
history: DAY accepted 26 and excluded 1; HOUR accepted 39 and excluded 6;
MINUTE_5 accepted 457 and excluded 70 over two pages, with remaining allowance
9401. The old candidate retained only one aggregate malformed counter, so the
exact causes of those 77 records cannot be reconstructed from that output. The
similar hourly/5-minute rates are an observation, not proof that transitions or
any particular component caused them.

Re-run the bounded windows to obtain reason counts. At most three safe shapes
may be requested when component presence needs inspection.

Run from the repository root with existing Demo secrets in the environment:

```text
python -m scripts.ig_discovery history "CC.D.LCO.BMU.IP" "DAY" "2026-08-01T00:00:00Z" "2026-09-01T00:00:00Z"
python -m scripts.ig_discovery history "CC.D.LCO.BMU.IP" "HOUR" "2026-09-01T00:00:00Z" "2026-09-03T00:00:00Z"
python -m scripts.ig_discovery history "CC.D.LCO.BMU.IP" "MINUTE_5" "2026-09-01T00:00:00Z" "2026-09-03T00:00:00Z"
python -m scripts.ig_discovery history "CC.D.LCO.BMU.IP" "MINUTE_5" "2026-09-01T00:00:00Z" "2026-09-03T00:00:00Z" --malformed-samples 3
```

Confirm non-empty output, chronological and sane UTC timestamps, consistent OHLC,
zero duplicate output timestamps, retained metadata, and no unexplained
truncation. The 5-minute feed is only a **CANDIDATE FOR LATER HR11 VALIDATION**
if external results demonstrate sufficient depth and quality. Do not run HR11
during M12B.
