"""Read-only IG REST v3 historical-price normalization."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from typing import Mapping
from urllib.parse import quote, urlencode

from domain.contracts.market import CanonicalBar, DataGrade, SourcePolicy
from domain.evaluation.suitability import SuitabilityEvidence
from intraday_instruments import DataGrade as SuitabilityDataGrade

VERSION = "ig-history-v1"
PRICE_BASIS_VERSION = "ig-bid-ask-mid-v1"
HISTORY_API_VERSION = 3
OHLC_FIELDS = (("open", "openPrice"), ("high", "highPrice"),
               ("low", "lowPrice"), ("close", "closePrice"))

RESOLUTIONS = {
    "SECOND": ("1s", 1), "MINUTE": ("1m", 60), "MINUTE_2": ("2m", 120),
    "MINUTE_3": ("3m", 180), "MINUTE_5": ("5m", 300),
    "MINUTE_10": ("10m", 600), "MINUTE_15": ("15m", 900),
    "MINUTE_30": ("30m", 1800), "HOUR": ("1h", 3600),
    "HOUR_2": ("2h", 7200), "HOUR_3": ("3h", 10800),
    "HOUR_4": ("4h", 14400), "DAY": ("1d", 86400),
    "WEEK": ("1w", 604800), "MONTH": ("1mo", None),
}


def _finite_number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) and result >= 0 else None


def _utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("historical range timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _source_time(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("IG historical price omitted snapshotTimeUTC")
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%S")
        except ValueError as exc:
            raise ValueError("IG historical price has malformed snapshotTimeUTC") from exc
    if parsed.tzinfo is None:  # IG documents this field as UTC despite its offset-free examples.
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _month_end(start):
    return start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)


@dataclass(frozen=True)
class IGPriceOHLC:
    open: float | None
    high: float | None
    low: float | None
    close: float | None

    @property
    def complete(self):
        return all(value is not None for value in (self.open, self.high, self.low, self.close))


@dataclass(frozen=True)
class IGHistoricalBar:
    """Canonical mid bar plus the uncollapsed IG bid/ask/last components."""
    canonical: CanonicalBar
    epic: str
    resolution: str
    bid: IGPriceOHLC
    ask: IGPriceOHLC
    last_traded: IGPriceOHLC
    last_traded_volume: float | None
    source_time_local: str | None
    source_timezone: str
    price_basis: str = "DERIVED_MID"
    price_basis_version: str = PRICE_BASIS_VERSION


@dataclass(frozen=True)
class IGMalformedShape:
    timestamp: str | None
    component_status: tuple[tuple[str, str], ...]
    volume_status: str
    reasons: tuple[str, ...]

    def to_dict(self):
        return {"timestamp": self.timestamp, "price_components": dict(self.component_status),
                "volume": self.volume_status, "status": "EXCLUDED", "reasons": self.reasons}


class IGNormalizationError(ValueError):
    def __init__(self, reasons, shape):
        self.reasons = tuple(dict.fromkeys(reasons)) or ("other",)
        self.shape = shape
        super().__init__(self.reasons[0])


@dataclass(frozen=True)
class IGHistoricalSeries:
    epic: str
    environment: str
    resolution: str
    canonical_timeframe: str
    requested_start: datetime
    requested_end: datetime
    retrieved_at: datetime
    bars: tuple[IGHistoricalBar, ...]
    duplicates: int
    gaps: int
    excluded_incomplete: int
    excluded_malformed: int
    truncated: bool
    pages_received: int
    remaining_allowance: int | None
    excluded_reasons: tuple[tuple[str, int], ...] = ()
    malformed_samples: tuple[IGMalformedShape, ...] = ()
    price_basis_counts: tuple[tuple[str, int], ...] = ()
    source: str = "IG REST /prices/{epic} v3"
    source_limitations: tuple[str, ...] = (
        "IG historical allowance applies",
        "market-local timezone identifier unavailable",
        "interval discontinuities require a trading calendar to classify",
    )
    data_grade: str = DataGrade.RESEARCH.value
    timestamp_quality: str = "IG_UTC_SOURCE_TIMESTAMP"
    version: str = VERSION

    @property
    def completeness(self):
        if self.truncated:
            return "PARTIAL_TRUNCATED"
        if self.excluded_malformed:
            return "PARTIAL_MALFORMED"
        return "COMPLETE" if self.bars else "EMPTY"

    def summary(self):
        basis_counts = dict(self.price_basis_counts)
        price_basis = next(iter(basis_counts)) if len(basis_counts) == 1 else "MIXED" if basis_counts else None
        return {
            "epic": self.epic, "environment": self.environment, "resolution": self.resolution,
            "source": self.source,
            "canonical_timeframe": self.canonical_timeframe, "bars_received": len(self.bars),
            "requested_start": self.requested_start.isoformat(), "requested_end": self.requested_end.isoformat(),
            "retrieved_at": self.retrieved_at.isoformat(),
            "first_timestamp": self.bars[0].canonical.interval_start.isoformat() if self.bars else None,
            "last_timestamp": self.bars[-1].canonical.interval_start.isoformat() if self.bars else None,
            "gaps": self.gaps, "duplicates": self.duplicates,
            "gap_semantics": "UNCLASSIFIED_INTERVAL_DISCONTINUITIES",
            "excluded_incomplete": self.excluded_incomplete, "excluded_malformed": self.excluded_malformed,
            "excluded_reasons": dict(self.excluded_reasons),
            "excluded_reason_semantics": "COUNTS_ARE_REASON_OCCURRENCES; ONE_RECORD_MAY_HAVE_MULTIPLE_REASONS",
            "malformed_samples": tuple(sample.to_dict() for sample in self.malformed_samples),
            "price_basis_counts": dict(self.price_basis_counts),
            "truncated": self.truncated, "completeness": self.completeness,
            "timestamp_quality": self.timestamp_quality, "price_basis": price_basis,
            "data_grade": self.data_grade, "pages_received": self.pages_received,
            "remaining_allowance": self.remaining_allowance, "source_limitations": self.source_limitations,
        }

    def suitability_evidence(self):
        return SuitabilityEvidence(
            data_status="PARTIAL" if self.truncated or self.excluded_malformed else
                        "AVAILABLE" if self.bars else "UNAVAILABLE",
            data_grade=SuitabilityDataGrade.RESEARCH,
            source_type="IG REST v3 historical prices", resolution=self.canonical_timeframe,
            history_depth=len(self.bars), missingness=None,
            timestamp_quality=self.timestamp_quality,
            coverage_period=(f"{self.bars[0].canonical.interval_start.isoformat()}/"
                             f"{self.bars[-1].canonical.event_time.isoformat()}") if self.bars else None,
        )


def _timestamp_shape(item):
    try:
        return _source_time(item.get("snapshotTimeUTC")).isoformat()
    except ValueError:
        return "INVALID" if item.get("snapshotTimeUTC") is not None else None


def _components(item):
    basis_names = (("bid", "bid"), ("ask", "ask"), ("lastTraded", "last_traded"))
    values = {basis: [] for basis, _ in basis_names}
    statuses, reasons = [], []
    for ohlc_name, field_name in OHLC_FIELDS:
        raw_component = item.get(field_name)
        component = raw_component if isinstance(raw_component, Mapping) else {}
        if not isinstance(raw_component, Mapping):
            reasons.append(f"missing_{ohlc_name}_price")
        for basis, safe_basis in basis_names:
            label = f"{safe_basis}_{ohlc_name}"
            if basis not in component:
                value, status = None, "MISSING"
            elif component[basis] is None:
                value, status = None, "NULL"
            else:
                value = _finite_number(component[basis])
                status = "PRESENT" if value is not None else "INVALID"
                if value is None:
                    reasons.append("invalid_numeric_value")
            values[basis].append(value)
            statuses.append((label, status))
    return (IGPriceOHLC(*values["bid"]), IGPriceOHLC(*values["ask"]),
            IGPriceOHLC(*values["lastTraded"]), tuple(statuses), reasons)


def _missing_reasons(statuses, bases):
    reasons = []
    for label, status in statuses:
        basis, ohlc = label.rsplit("_", 1)
        if basis in bases and status in {"MISSING", "NULL"}:
            reasons.append(f"missing_{basis}_{ohlc}")
    return reasons


def _shape(item, statuses, reasons):
    if "lastTradedVolume" not in item:
        volume_status = "MISSING"
    elif item.get("lastTradedVolume") is None:
        volume_status = "NULL"
    else:
        volume_status = "PRESENT" if _finite_number(item.get("lastTradedVolume")) is not None else "INVALID"
    return IGMalformedShape(_timestamp_shape(item), statuses, volume_status,
                            tuple(dict.fromkeys(reasons)) or ("other",))


def _normalize_price(item, *, epic, environment, resolution):
    try:
        start = _source_time(item.get("snapshotTimeUTC"))
    except ValueError:
        reason = "missing_snapshot_time_utc" if item.get("snapshotTimeUTC") is None else "invalid_snapshot_time_utc"
        _, _, _, statuses, component_reasons = _components(item)
        reasons = [reason, *component_reasons]
        raise IGNormalizationError(reasons, _shape(item, statuses, reasons)) from None
    seconds = RESOLUTIONS[resolution][1]
    end = _month_end(start) if seconds is None else start + timedelta(seconds=seconds)
    bid, ask, last, statuses, component_reasons = _components(item)
    if "invalid_numeric_value" in component_reasons:
        raise IGNormalizationError(component_reasons, _shape(item, statuses, component_reasons))
    if item.get("lastTradedVolume") is not None and _finite_number(item.get("lastTradedVolume")) is None:
        reasons = [*component_reasons, "invalid_numeric_value"]
        raise IGNormalizationError(reasons, _shape(item, statuses, reasons))
    if not bid.complete or not ask.complete:
        reasons = [*component_reasons, *_missing_reasons(statuses, {"bid", "ask", "last_traded"})]
        raise IGNormalizationError(reasons, _shape(item, statuses, reasons))
    ohlc = tuple((left + right) / 2 for left, right in zip(
        (bid.open, bid.high, bid.low, bid.close), (ask.open, ask.high, ask.low, ask.close)))
    canonical_bid, canonical_ask = bid.close, ask.close
    price_basis, price_basis_version = "DERIVED_MID", PRICE_BASIS_VERSION
    raw_id = sha256(json.dumps(item, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    policy = SourcePolicy("IG_REST_HISTORICAL", 1, "licensed", DataGrade.RESEARCH, 1,
                          f"RESEARCH_ONLY; {price_basis_version}; historical-publication availability")
    try:
        canonical = CanonicalBar(epic, RESOLUTIONS[resolution][0], start, end, end,
                                 ohlc[0], ohlc[1], ohlc[2], ohlc[3],
                                 _finite_number(item.get("lastTradedVolume")), canonical_bid, canonical_ask,
                                 policy, (f"ig:{environment}:{epic}:{raw_id}",))
    except ValueError:
        reasons = ["ohlc_invariant_failure"]
        raise IGNormalizationError(reasons, _shape(item, statuses, reasons)) from None
    return IGHistoricalBar(canonical, epic, resolution, bid, ask, last,
                           _finite_number(item.get("lastTradedVolume")), item.get("snapshotTime"),
                           "IG_MARKET_LOCAL_UNSPECIFIED", price_basis, price_basis_version)


def fetch_historical_prices(adapter, epic, resolution, start, end, *, max_points=10_000,
                            page_size=500, max_pages=100, retrieved_at=None,
                            diagnostic_sample_limit=0):
    """Fetch bounded v3 pages and return normalized, completed historical bars."""
    resolution = str(resolution).upper()
    if not isinstance(epic, str) or not epic.strip():
        raise ValueError("IG EPIC is required")
    if resolution not in RESOLUTIONS:
        raise ValueError("unsupported IG historical resolution")
    start, end = _utc(start), _utc(end)
    if start >= end:
        raise ValueError("historical start must precede end")
    if not isinstance(max_points, int) or max_points <= 0:
        raise ValueError("max_points must be a positive integer")
    if not isinstance(page_size, int) or not 1 <= page_size <= 500:
        raise ValueError("page_size must be between 1 and 500")
    if not isinstance(max_pages, int) or max_pages <= 0:
        raise ValueError("max_pages must be a positive integer")
    if not isinstance(diagnostic_sample_limit, int) or not 0 <= diagnostic_sample_limit <= 5:
        raise ValueError("diagnostic_sample_limit must be between 0 and 5")
    retrieved_at = _utc(retrieved_at or datetime.now(timezone.utc))
    normalized, seen = [], set()
    reason_counts, samples, basis_counts = {}, [], {}
    duplicates = malformed = incomplete = pages = 0
    total_pages, remaining_allowance = 1, None
    while pages < total_pages and pages < max_pages and len(normalized) < max_points:
        page_number = pages + 1
        query = urlencode({"resolution": resolution, "from": start.strftime("%Y-%m-%dT%H:%M:%S"),
                           "to": end.strftime("%Y-%m-%dT%H:%M:%S"),
                           "pageSize": min(page_size, max_points - len(normalized)), "pageNumber": page_number})
        payload = adapter._request("GET", "/prices/" + quote(epic, safe="") + "?" + query,
                                   version=HISTORY_API_VERSION)
        prices, metadata = payload.get("prices"), payload.get("metadata")
        if not isinstance(prices, list) or not isinstance(metadata, Mapping):
            raise adapter.malformed_response("IG historical response omitted prices or metadata")
        page_data = metadata.get("pageData")
        if not isinstance(page_data, Mapping):
            raise adapter.malformed_response("IG historical response omitted pageData")
        try:
            response_page, total_pages = int(page_data["pageNumber"]), int(page_data["totalPages"])
        except (KeyError, TypeError, ValueError):
            raise adapter.malformed_response("IG historical response has invalid pageData") from None
        if response_page != page_number or total_pages < response_page or total_pages < 0:
            raise adapter.malformed_response("IG historical response has inconsistent pageData")
        allowance = metadata.get("allowance") or {}
        if isinstance(allowance, Mapping):
            try:
                remaining_allowance = int(allowance.get("remainingAllowance"))
            except (TypeError, ValueError):
                remaining_allowance = None
        pages += 1
        for item in prices:
            if not isinstance(item, Mapping):
                malformed += 1
                reason_counts["other"] = reason_counts.get("other", 0) + 1
                if len(samples) < diagnostic_sample_limit:
                    samples.append(IGMalformedShape(None, (), "UNKNOWN", ("other",)))
                continue
            try:
                bar = _normalize_price(item, epic=epic, environment=adapter.config.environment, resolution=resolution)
            except IGNormalizationError as exc:
                malformed += 1
                for reason in exc.reasons:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                if len(samples) < diagnostic_sample_limit:
                    samples.append(exc.shape)
                continue
            timestamp = bar.canonical.interval_start
            if timestamp < start or timestamp >= end:
                malformed += 1
                reason_counts["outside_requested_range"] = reason_counts.get("outside_requested_range", 0) + 1
                if len(samples) < diagnostic_sample_limit:
                    samples.append(_shape(item, _components(item)[3], ["outside_requested_range"]))
                continue
            if timestamp in seen:
                duplicates += 1
                continue
            seen.add(timestamp)
            if bar.canonical.event_time > retrieved_at:
                incomplete += 1
                continue
            normalized.append(bar)
            basis_counts[bar.price_basis] = basis_counts.get(bar.price_basis, 0) + 1
            if len(normalized) >= max_points:
                break
        if not prices:
            break
    normalized.sort(key=lambda value: value.canonical.interval_start)
    seconds = RESOLUTIONS[resolution][1]
    gaps = 0
    if seconds is not None:
        cadence = timedelta(seconds=seconds)
        gaps = sum(max(0, int((right.canonical.interval_start - left.canonical.interval_start) / cadence) - 1)
                   for left, right in zip(normalized, normalized[1:]))
    return IGHistoricalSeries(epic, adapter.config.environment, resolution, RESOLUTIONS[resolution][0],
                              start, end, retrieved_at, tuple(normalized), duplicates, gaps, incomplete,
                              malformed, pages < total_pages, pages, remaining_allowance,
                              tuple(sorted(reason_counts.items())), tuple(samples), tuple(sorted(basis_counts.items())))


__all__ = ["HISTORY_API_VERSION", "IGHistoricalBar", "IGHistoricalSeries", "IGMalformedShape",
           "IGNormalizationError", "IGPriceOHLC", "PRICE_BASIS_VERSION", "RESOLUTIONS", "VERSION",
           "fetch_historical_prices"]
