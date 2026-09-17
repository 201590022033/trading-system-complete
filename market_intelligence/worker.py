"""One bounded, change-driven Market Intelligence refresh."""
from uuid import uuid4
from itertools import islice

class BoundedMarketIntelligenceRefresh:
    def __init__(self, source_registry, orchestrator, text_loader, max_documents=1):
        self.source_registry = source_registry
        self.orchestrator = orchestrator
        self.text_loader = text_loader
        if not 1<=int(max_documents)<=10: raise ValueError('document bound must be 1..10')
        self.max_documents = int(max_documents)

    def run_once(self, documents):
        """Process at most max_documents; cache/provider failures are isolated."""
        processed = []; failures = []
        enabled = {p.source_id for p in self.source_registry.list_policies() if getattr(p, "enabled", False)}
        for document in islice(documents,self.max_documents):
            if document.source_id not in enabled:
                continue
            try:
                lookup=getattr(self.orchestrator,'cached',lambda d:None)
                result=lookup(document)
                if result is None:
                    text = self.text_loader(document)
                    result = self.orchestrator.analyse(document, text=text, analysis_id=f"analysis:{uuid4().hex}")
                if hasattr(self.orchestrator,'store'):
                    self._publish(document,result)
                processed.append(result)
            except Exception:
                failures.append({"document_id": document.document_id, "category": 'PROVIDER_OR_VALIDATION_FAILURE'})
        return {"processed": len(processed), "failures": failures, "bounded": True}

    def _publish(self,document,analysis):
        from .schemas import MarketIntelligenceSnapshot,ProvenanceEdge,MarketTheme,InstrumentCandidate,SourceEvidence
        from .watchlist import select_watchlist
        from shadow_learning import stable_id
        store=self.orchestrator.store
        snapshot_id=stable_id('snapshot',analysis.analysis_id)
        with store.transaction():
            store.save_provenance_edge(ProvenanceEdge(stable_id('analysis-edge',document.document_id,analysis.analysis_id),
                'document',document.document_id,'analysed_as','analysis',analysis.analysis_id,
                snapshot_id=snapshot_id,created_at=analysis.analysed_at))
            if store.get_snapshot(snapshot_id): return
            themes=[]
            for item in analysis.themes:
                if isinstance(item,MarketTheme): themes.append(item); continue
                value=dict(item)
                for key in ('supporting_evidence','contradictory_evidence'):
                    value[key]=[SourceEvidence(**entry) for entry in value.get(key,[])]
                themes.append(MarketTheme(**value))
            candidates=[item if isinstance(item,InstrumentCandidate) else InstrumentCandidate(**item) for item in analysis.candidates]
            existing=store.active_ticker_selections()
            selections=select_watchlist(candidates,pinned=[s for s in existing if s.pinned],existing=existing)
            store.save_snapshot(MarketIntelligenceSnapshot(snapshot_id,analysis.analysed_at,analysis.schema_version,
                [document.source_id],[document.content_hash],themes,candidates,list(selections),
                {'provider':analysis.provider,'model':analysis.model},{'governance':'RESEARCH_ONLY'}))
            for selection in selections:
                if selection not in existing: store.save_ticker_selection(selection)
