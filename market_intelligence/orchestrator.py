"""Bounded document-to-analysis orchestration; source text remains data."""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timezone
from .analysis import analyse_document
from .cache import AnalysisCache, cache_key
from .schemas import MarketDocument, MarketDocumentAnalysis, SCHEMA_VERSION

class DocumentOrchestrator:
    def __init__(self, store, provider, cache=None):
        self.store, self.provider, self.cache = store, provider, cache or AnalysisCache()

    def analyse(self, document: MarketDocument, *, text: str, analysis_id: str) -> MarketDocumentAnalysis:
        hydrated=replace(document, metadata={**document.metadata, "text": text})
        key=cache_key(document.content_hash, provider=self.provider.name, model=self.provider.model,
                     schema_version=SCHEMA_VERSION, prompt_version="market-intelligence-prompt-v1")
        cached=self.cache.get(key) or self.store.cached_analysis(document.document_id, document.content_hash, self.provider.name, self.provider.model, SCHEMA_VERSION, "market-intelligence-prompt-v1")
        if cached: return cached
        try:
            result=analyse_document(hydrated, self.provider, content_hash=document.content_hash, analysis_id=analysis_id)
        except Exception as exc:
            self.store.audit("analysis_failed", "document", document.document_id, after={"status":"INVALID_PROVIDER_OUTPUT","error":str(exc)[:200]})
            raise ValueError("structured analysis failed validation") from None
        self.store.save_analysis(result); self.cache.put(key,result)
        return result
