"""Structured schemas for market intelligence, narrative, and explainability.

All dataclasses are frozen and serialisable. They deliberately carry provenance
fields so the UI can show *what information the AI had* without conflating LLM
interpretation with original source content.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = "market-intelligence-v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SourceEvidence:
    """One provenance link from a market theme back to a source item."""
    evidence_id: str
    source_id: str
    source_name: str
    headline: str
    url: Optional[str]
    published_at: Optional[str]
    direction: int  # -1 bearish, 0 neutral, 1 bullish
    strength: float
    excerpt: str = ""


@dataclass(frozen=True)
class MarketTheme:
    """A directional market theme inferred from one or more sources."""
    theme: str
    direction: int  # -1 bearish, 0 neutral, 1 bullish
    confidence: float
    expected_horizon: str
    affected_sectors: List[str] = field(default_factory=list)
    affected_asset_classes: List[str] = field(default_factory=list)
    potentially_affected_instruments: List[str] = field(default_factory=list)
    supporting_evidence: List[SourceEvidence] = field(default_factory=list)
    contradictory_evidence: List[SourceEvidence] = field(default_factory=list)
    generated_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class InstrumentCandidate:
    """An instrument worth investigating, NOT an executable trade signal."""
    instrument_id: str
    display_symbol: str
    reason: str
    theme: str
    confidence: float
    source_evidence_ids: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_now)
    review_at: Optional[str] = None


@dataclass(frozen=True)
class MarketNarrative:
    """A complete snapshot of current market intelligence."""
    narrative_id: str
    generated_at: str
    model: str
    provider: str
    schema_version: str
    summary: str
    themes: List[MarketTheme] = field(default_factory=list)
    candidates: List[InstrumentCandidate] = field(default_factory=list)
    enabled_sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TickerSelection:
    """One AI-selected or user-pinned ticker slot with inspectable rationale."""
    instrument_id: str
    display_symbol: str
    pinned: bool
    reason: str
    theme: Optional[str]
    confidence: Optional[float]
    source_evidence_ids: List[str] = field(default_factory=list)
    selected_at: str = field(default_factory=_now)
    review_at: Optional[str] = None
