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
)
from .source_base import MarketSource, SourceFetchResult
from .source_registry import SourceRegistry
from .store import MarketIntelligenceStore

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
]
