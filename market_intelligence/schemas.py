"""Structured schemas for market intelligence, narrative, and explainability.

All dataclasses are frozen and serialisable. They deliberately carry provenance
fields so the UI can show *what information the AI had* without conflating LLM
interpretation with original source content.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


SCHEMA_VERSION = "market-intelligence-v2"


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


@dataclass(frozen=True)
class MarketDocument:
    document_id: str
    source_id: str
    title: str
    author: Optional[str]
    publication_date: Optional[str]
    canonical_url: Optional[str]
    pdf_url: Optional[str]
    retrieved_at: str
    content_hash: str
    extraction_method: str
    extraction_status: str
    text_hash: Optional[str] = None
    processing_status: str = "DISCOVERED"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentFact:
    fact: str
    source_span: str = ""
    confidence: float = 1.0


@dataclass(frozen=True)
class MarketDocumentAnalysis:
    analysis_id: str
    document_id: str
    provider: str
    model: str
    schema_version: str
    prompt_version: str
    content_hash: str
    analysed_at: str
    facts: List[DocumentFact] = field(default_factory=list)
    themes: List[MarketTheme] = field(default_factory=list)
    candidates: List[InstrumentCandidate] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    usage: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProvenanceEdge:
    provenance_id: str
    from_type: str
    from_id: str
    relationship_type: str
    to_type: str
    to_id: str
    snapshot_id: Optional[str] = None
    confidence: Optional[float] = None
    reason: str = ""
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class MarketIntelligenceSnapshot:
    snapshot_id: str
    generated_at: str
    schema_version: str
    enabled_sources: List[str]
    document_hashes: List[str]
    themes: List[MarketTheme] = field(default_factory=list)
    candidates: List[InstrumentCandidate] = field(default_factory=list)
    selections: List[TickerSelection] = field(default_factory=list)
    provider_metadata: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
