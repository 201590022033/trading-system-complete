"""Normalized evidence and provenance contracts.

This module wraps existing NewsItem objects without replacing them. It gives
future reliability and learning components a stable, auditable record for
news, SENS, social and macro evidence.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from data_pipeline import NewsItem

PROVENANCE_VERSION = "evidence-v1"


@dataclass(frozen=True)
class EvidenceRecord:
    """One normalized directional or contextual evidence item."""

    evidence_id: str
    source_id: str
    source_name: str
    source_class: str
    authority_tier: int
    headline: str
    text: str
    url: Optional[str]
    observed_at: str
    published_at: Optional[str]
    ingested_at: str
    tickers: List[str] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    sentiment: str = "neutral"
    score: float = 0.0
    confidence: float = 0.0
    horizon: Optional[str] = None
    parser_version: str = PROVENANCE_VERSION
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


def _timestamp(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _canonical(*parts: str) -> str:
    return "|".join(re.sub(r"\s+", " ", p or "").strip().lower() for p in parts)


def evidence_id(source_id: str, headline: str, published_at=None, url: Optional[str] = None) -> str:
    """Return a stable ID for deduplication of repeated/syndicated evidence."""
    canonical = _canonical(source_id, headline, _timestamp(published_at) or "", url or "")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def infer_source_class(source: str) -> str:
    """Map current collector labels to conservative source classes."""
    low = (source or "").lower()
    if "sens" in low or "jse" in low:
        return "authoritative_event"
    if "reddit" in low or "twitter" in low or "x/" in low:
        return "community"
    if "newsapi" in low or "moneyweb" in low or "reuters" in low:
        return "financial_media"
    return "other"


def infer_authority_tier(source_class: str) -> int:
    return {
        "authoritative_event": 1,
        "market_data": 2,
        "financial_media": 3,
        "community": 4,
    }.get(source_class, 4)


def normalize_news_item(
    item: NewsItem,
    *,
    source_id: Optional[str] = None,
    source_class: Optional[str] = None,
    authority_tier: Optional[int] = None,
    url: Optional[str] = None,
    tickers: Optional[Iterable[str]] = None,
    assets: Optional[Iterable[str]] = None,
    sectors: Optional[Iterable[str]] = None,
    observed_at=None,
    ingested_at=None,
    parser_version: str = PROVENANCE_VERSION,
    metadata: Optional[Dict] = None,
) -> EvidenceRecord:
    """Convert an existing NewsItem while preserving its original semantics."""
    source_name = item.source or "unknown"
    resolved_class = source_class or infer_source_class(source_name)
    observed = observed_at or item.timestamp or datetime.now(timezone.utc)
    ingested = ingested_at or datetime.now(timezone.utc)
    score = max(-1.0, min(1.0, float(item.sentiment_score or 0.0)))
    sentiment = item.sentiment_label.value if item.sentiment_label else "neutral"
    resolved_tickers = list(tickers or ([] if item.ticker in (None, "JSE") else [item.ticker]))
    return EvidenceRecord(
        evidence_id=evidence_id(source_id or source_name, item.headline, item.timestamp, url),
        source_id=source_id or re.sub(r"[^a-z0-9]+", "_", source_name.lower()).strip("_") or "unknown",
        source_name=source_name,
        source_class=resolved_class,
        authority_tier=authority_tier or infer_authority_tier(resolved_class),
        headline=item.headline.strip(),
        text=(item.text or item.headline).strip(),
        url=url,
        observed_at=_timestamp(observed) or datetime.now(timezone.utc).isoformat(),
        published_at=_timestamp(item.timestamp),
        ingested_at=_timestamp(ingested) or datetime.now(timezone.utc).isoformat(),
        tickers=sorted(set(t.upper() for t in resolved_tickers if t)),
        assets=sorted(set(a.upper() for a in (assets or []))),
        sectors=sorted(set(s.lower() for s in (sectors or []))),
        sentiment=sentiment,
        score=score,
        confidence=min(1.0, abs(score)),
        parser_version=parser_version,
        metadata=dict(metadata or {}),
    )


def deduplicate_evidence(records: Iterable[EvidenceRecord]) -> List[EvidenceRecord]:
    """Keep the first record for each stable evidence ID, preserving order."""
    seen = set()
    unique = []
    for record in records:
        if record.evidence_id in seen:
            continue
        seen.add(record.evidence_id)
        unique.append(record)
    return unique
