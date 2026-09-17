import tempfile
import unittest
from pathlib import Path
from market_intelligence.store import MarketIntelligenceStore
from market_intelligence.worker import BoundedMarketIntelligenceRefresh

class Policy:
    def __init__(self, source_id, enabled=True): self.source_id, self.enabled = source_id, enabled
class Registry:
    def __init__(self, enabled=True): self.enabled = enabled
    def list_policies(self): return [Policy("source", self.enabled)]
class Document:
    source_id = "source"; document_id = "doc"; content_hash = "hash"
    metadata = {}; title = "Test"

class Orchestrator:
    def __init__(self): self.calls = 0
    def analyse(self, document, *, text, analysis_id): self.calls += 1; return {"document_id": document.document_id}

class MarketIntelligenceWorkerTests(unittest.TestCase):
    def test_bounded_new_content_and_no_work_or_disabled_source(self):
        o = Orchestrator(); calls = []
        worker = BoundedMarketIntelligenceRefresh(Registry(), o, lambda d: calls.append(d.document_id) or "text", max_documents=1)
        first = worker.run_once([Document()]); second = worker.run_once([])
        self.assertEqual(first["processed"], 1); self.assertEqual(second["processed"], 0); self.assertEqual(o.calls, 1)
        disabled = BoundedMarketIntelligenceRefresh(Registry(False), o, lambda _: (_ for _ in ()).throw(AssertionError("called")))
        self.assertEqual(disabled.run_once([Document()])["processed"], 0)
    def test_provider_failure_is_fail_closed(self):
        o = Orchestrator()
        o.analyse = lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("invalid"))
        result = BoundedMarketIntelligenceRefresh(Registry(), o, lambda _: "text").run_once([Document()])
        self.assertEqual(result["processed"], 0); self.assertEqual(result["failures"][0]["category"], "PROVIDER_OR_VALIDATION_FAILURE")
if __name__ == "__main__": unittest.main()
