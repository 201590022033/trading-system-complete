"""Provider-neutral, validated Market AI analysis boundary."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
from .schemas import DocumentFact, MarketDocumentAnalysis, SCHEMA_VERSION

PROMPT_VERSION = "market-intelligence-prompt-v1"

class StructuredAnalysisProvider(Protocol):
    name: str
    model: str
    def analyse(self, *, title: str, text: str) -> dict[str, Any]: ...

def validate_analysis(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict): raise ValueError("analysis must be an object")
    for key in ("facts", "themes", "candidates", "uncertainties", "contradictions"):
        if not isinstance(raw.get(key, []), list): raise ValueError(f"{key} must be a list")
    return raw

def analyse_document(document, provider: StructuredAnalysisProvider, *, content_hash: str, analysis_id: str, now: str | None = None) -> MarketDocumentAnalysis:
    raw=validate_analysis(provider.analyse(title=document.title, text=document.metadata.get("text", "")))
    facts=[DocumentFact(str(x.get("fact", "")), str(x.get("source_span", "")), float(x.get("confidence", 1.0))) for x in raw["facts"] if isinstance(x,dict) and x.get("fact")]
    return MarketDocumentAnalysis(analysis_id, document.document_id, provider.name, provider.model, SCHEMA_VERSION,
        PROMPT_VERSION, content_hash, now or datetime.now(timezone.utc).isoformat(), facts,
        raw["themes"], raw["candidates"], [str(x) for x in raw["uncertainties"]], [str(x) for x in raw["contradictions"]],
        dict(raw.get("usage", {})))
