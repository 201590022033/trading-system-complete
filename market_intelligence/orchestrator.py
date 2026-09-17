"""Bounded document-to-analysis orchestration; source text remains data."""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timezone
from .analysis import analyse_document, validate_analysis
from .cache import AnalysisCache, cache_key
from .schemas import MarketDocument, MarketDocumentAnalysis, SCHEMA_VERSION

class DocumentOrchestrator:
    def __init__(self, store, provider, cache=None):
        self.store, self.provider, self.cache = store, provider, cache or AnalysisCache()

    def cached(self,document):
        key=cache_key(document.content_hash,provider=self.provider.name,model=self.provider.model,
            schema_version=SCHEMA_VERSION,prompt_version='market-intelligence-prompt-v1')
        result=self.cache.get(key) or self.store.cached_analysis(document.document_id,document.content_hash,
            self.provider.name,self.provider.model,SCHEMA_VERSION,'market-intelligence-prompt-v1')
        if result is not None:
            from dataclasses import asdict
            validate_analysis(asdict(result))
        return result

    def analyse(self, document: MarketDocument, *, text: str, analysis_id: str) -> MarketDocumentAnalysis:
        if not isinstance(text,str) or not text.strip() or len(text)>20000:
            raise ValueError('bounded nonempty extracted text required')
        hydrated=replace(document, metadata={**document.metadata, "text": text})
        key=cache_key(document.content_hash, provider=self.provider.name, model=self.provider.model,
                     schema_version=SCHEMA_VERSION, prompt_version="market-intelligence-prompt-v1")
        cached=self.cached(document)
        if cached: return cached
        try:
            result=analyse_document(hydrated, self.provider, content_hash=document.content_hash, analysis_id=analysis_id)
        except Exception:
            self.store.audit("analysis_failed", "document", document.document_id, after={"status":"INVALID_PROVIDER_OUTPUT","category":"PROVIDER_OR_VALIDATION_FAILURE"})
            raise ValueError("structured analysis failed validation") from None
        self.store.save_analysis(result); self.cache.put(key,result)
        return result
