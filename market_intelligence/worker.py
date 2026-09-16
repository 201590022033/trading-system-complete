"""One bounded, change-driven Market Intelligence refresh."""
from uuid import uuid4

class BoundedMarketIntelligenceRefresh:
    def __init__(self, source_registry, orchestrator, text_loader, max_documents=1):
        self.source_registry = source_registry
        self.orchestrator = orchestrator
        self.text_loader = text_loader
        self.max_documents = max(1, int(max_documents))

    def run_once(self, documents):
        """Process at most max_documents; cache/provider failures are isolated."""
        processed = []; failures = []
        enabled = {p.source_id for p in self.source_registry.list_policies() if getattr(p, "enabled", False)}
        for document in list(documents)[:self.max_documents]:
            if document.source_id not in enabled:
                continue
            try:
                text = self.text_loader(document)
                result = self.orchestrator.analyse(document, text=text, analysis_id=f"analysis:{uuid4().hex}")
                processed.append(result)
            except Exception as exc:
                failures.append({"document_id": document.document_id, "category": type(exc).__name__})
        return {"processed": len(processed), "failures": failures, "bounded": True}
