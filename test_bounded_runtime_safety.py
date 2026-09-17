"""Batch 4 reproductions: resource bounds, untrusted output and read models."""
import json
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from market_intelligence.schemas import MarketDocument
from market_intelligence.orchestrator import DocumentOrchestrator
from market_intelligence.worker import BoundedMarketIntelligenceRefresh
from market_intelligence.store import MarketIntelligenceStore
from test_market_intelligence_worker import Registry
from persistence.sqlite_repository import SQLiteRepository
from reliability_store import ReliabilityStore, RepositoryReliabilityStore, SourceDefinition
from shadow_learning import ObservationRecord

class Provider:
    name='fixture'; model='fixture-v1'
    def __init__(self): self.calls=0
    def analyse(self,**kwargs):
        self.calls+=1
        return {'facts':[{'fact':'Published fact'}],'themes':[],'candidates':[],
                'uncertainties':[],'contradictions':[]}

def document(identity='d'):
    return MarketDocument(identity,'source','Report',None,None,None,None,
        '2026-01-01T00:00:00Z','same-content','embedded_text','EXTRACTED')

class BoundedRuntimeSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'state.db'
        self.repo=SQLiteRepository(self.path); self.addCleanup(self.repo.close)

    def test_discovery_generator_consumed_only_to_bound(self):
        calls=[]
        def documents():
            for n in range(1000): calls.append(n); yield document(str(n))
        runner=BoundedMarketIntelligenceRefresh(Registry(),DocumentOrchestrator(self.repo.store,Provider()),lambda d:'body',max_documents=1)
        runner.run_once(documents())
        self.assertEqual(calls,[0])

    def test_durable_cache_precedes_extraction_and_survives_new_document_id(self):
        provider=Provider(); loads=[]
        def worker(repo):
            return BoundedMarketIntelligenceRefresh(Registry(),DocumentOrchestrator(repo.store,provider),lambda d:loads.append(1) or 'body')
        worker(self.repo).run_once([document()]); self.repo.close()
        self.repo=SQLiteRepository(self.path); self.addCleanup(self.repo.close)
        worker(self.repo).run_once([document('new-id')])
        self.assertEqual(provider.calls,1); self.assertEqual(loads,[1])

    def test_nested_malformed_output_never_becomes_trusted(self):
        base=Provider().analyse()
        for field,value in (('themes',['bogus']),('candidates',[42]),('facts',[{'fact':'x','confidence':float('nan')}]),('uncertainties',[{}])):
            provider=Provider()
            provider.analyse=lambda **kwargs: {**base,field:value}
            with self.subTest(field=field),self.assertRaises(ValueError):
                DocumentOrchestrator(self.repo.store,provider).analyse(document(field),text='body',analysis_id=field)

    def test_provider_exceptions_are_redacted_in_audit(self):
        provider=Provider()
        provider.analyse=lambda **kwargs: (_ for _ in ()).throw(RuntimeError('SYNTHETIC_SECRET_SENTINEL'))
        with self.assertRaises(ValueError):
            DocumentOrchestrator(self.repo.store,provider).analyse(document(),text='body',analysis_id='a')
        rows=self.repo.store._connection.execute('SELECT after_json FROM audit_log').fetchall()
        self.assertNotIn('SYNTHETIC_SECRET_SENTINEL',str([tuple(r) for r in rows]))

    def test_reliability_exact_rounding_and_source_contract(self):
        original=ReliabilityStore(':memory:'); self.addCleanup(original.close)
        shared=RepositoryReliabilityStore(self.repo)
        source=SourceDefinition('s','Source','public',1)
        original.register_source(source); shared.register_source(source)
        for i,value in enumerate((.123456789,-.1,0)):
            args=dict(evidence_id=str(i),source_id='s',scope_key='global',horizon='5d',
                observed_at='2026-01-01T00:00:00Z',evaluated_at='2026-01-06T00:00:00Z',direction=1,forward_return=value)
            original.record_outcome(**args); shared.record_outcome(**args)
        self.assertEqual(original.summarize('s'),shared.summarize('s'))

    def test_future_records_are_excluded_from_status(self):
        self.repo.save_observation(ObservationRecord('future','NPN','2099-01-01T00:00:00Z','1',{}))
        status=self.repo.learning_status()
        self.assertEqual(status['observations']['24h'],0)
        self.assertIsNone(status['latest_timestamps']['observations'])

    def test_mi_job_integration_cache_provenance_snapshot_and_failure(self):
        from dataclasses import asdict
        from workers.runtime import runtime_handlers
        from workers.shadow_learning import ShadowWorker
        from shadow_learning import JobCheckpoint
        from market_intelligence.source_registry import SourceRegistry
        from source_catalog import SourcePolicy
        registry=SourceRegistry(self.repo.store)
        registry.add_policy(SourcePolicy('source','Fixture','financial_media',3,'public_manual','live_existing','https://example.test',enabled=True))
        provider=Provider(); loads=[]
        handlers=runtime_handlers(self.repo,mi_provider=provider,mi_text_loader=lambda d:loads.append(1) or 'body')
        job=JobCheckpoint('mi','market-intelligence-refresh','2026-01-01T00:00:00Z',checkpoint={'documents':[asdict(document())]})
        worker=ShadowWorker(self.repo,'w',handlers)
        worker.run_once([job]); worker.run_once([job])
        self.assertEqual(self.repo.get_job('mi')['status'],'COMPLETED')
        self.assertEqual(provider.calls,1); self.assertEqual(loads,[1])
        self.assertEqual(self.repo.store._connection.execute('SELECT COUNT(*) FROM intelligence_snapshots').fetchone()[0],1)
        self.assertTrue(self.repo.store.provenance_for('document','d'))
        bad=replace(job,job_key='bad',checkpoint={'documents':[asdict(replace(document('bad'),content_hash='different'))]})
        provider.analyse=lambda **kwargs:{'facts':'malformed'}
        worker.run_once([bad])
        self.assertEqual(self.repo.get_job('bad')['status'],'FAILED')
        self.assertEqual(self.repo.store._connection.execute('SELECT COUNT(*) FROM intelligence_snapshots').fetchone()[0],1)
