"""Market intelligence package: sources, narratives, ticker selection and audit.

This package provides the structured foundation for the configurable market-
intelligence layer described in ADR 0024. It is research/shadow-only and does
not submit orders or bypass the existing signal contract.
"""

from .schemas import (
    InstrumentCandidate,
    MarketNarrative,
    MarketTheme,
    SCHEMA_VERSION,
    SourceEvidence,
    TickerSelection,
    DocumentFact, MarketDocument, MarketDocumentAnalysis, MarketIntelligenceSnapshot,
    ProvenanceEdge,
)
from .source_base import MarketSource, SourceFetchResult
from .source_registry import SourceRegistry
from .store import MarketIntelligenceStore
from .efficient_group import EfficientGroupSource
from .watchlist import select_watchlist
from .research_priority import InvestigationPriority, build_priorities
from .cache import AnalysisCache, cache_key
from .orchestrator import DocumentOrchestrator

__all__ = [
    "InstrumentCandidate",
    "MarketNarrative",
    "MarketSource",
    "MarketTheme",
    "MarketIntelligenceStore",
    "SCHEMA_VERSION",
    "SourceEvidence",
    "SourceFetchResult",
    "SourceRegistry",
    "TickerSelection",
    "EfficientGroupSource", "select_watchlist",
    "InvestigationPriority", "build_priorities",
    "AnalysisCache", "cache_key",
    "DocumentOrchestrator",
    "DocumentFact", "MarketDocument", "MarketDocumentAnalysis",
    "MarketIntelligenceSnapshot", "ProvenanceEdge",
]
