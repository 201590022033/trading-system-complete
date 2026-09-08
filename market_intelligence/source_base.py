"""Abstract base for market-intelligence sources.

A source is anything that produces EvidenceRecords or document references:
RSS feeds, HTML scrapers, PDF archives, APIs, or manual imports. The registry
stores configuration; each source implementation knows how to fetch and parse.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from evidence import EvidenceRecord


@dataclass(frozen=True)
class SourceFetchResult:
    """Result of one source fetch cycle."""
    source_id: str
    fetched_at: str
    evidence: List[EvidenceRecord] = field(default_factory=list)
    document_references: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarketSource(ABC):
    """Base class for all configurable market-intelligence sources."""

    def __init__(self, source_id: str, config: Optional[Dict[str, Any]] = None) -> None:
        self.source_id = source_id
        self.config = config or {}

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return a type label such as 'rss', 'html', 'pdf_archive', 'api', 'manual'."""

    @abstractmethod
    def fetch(self, *, since: Optional[datetime] = None) -> SourceFetchResult:
        """Fetch new/updated evidence from this source.

        Implementations should respect domain allowlists, timeouts, size limits,
        and rate-limiting configured in self.config. They must never submit orders
        or perform authenticated broker actions.
        """

    def health(self) -> Dict[str, Any]:
        """Optional health check; default reports source_id and type."""
        return {"source_id": self.source_id, "source_type": self.source_type}
