import tempfile
import unittest
from pathlib import Path
from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from shadow_learning import AdaptiveEvidence
from test_postgres_repository_behavior import SQLiteDBAPIForPostgres
from domain.registry.source import default_canonical_policies
from domain.intelligence.clustering import ClusteredEvent
from evidence import EvidenceRecord
from market_intelligence.schemas import MarketNarrative,MarketIntelligenceSnapshot

class ShadowRepositoryParityTests(unittest.TestCase):
    def test_source_evidence_cluster_and_mi_domain_parity(self):
        results=[]
        for backend in ('sqlite','postgresql'):
            with tempfile.TemporaryDirectory() as d:
                repo=SQLiteRepository(Path(d)/'s.db') if backend=='sqlite' else PostgresRepository('postgresql://fixture',connection=SQLiteDBAPIForPostgres(Path(d)/'p.db'))
                if backend=='postgresql': repo.initialize()
                try:
                    policy=default_canonical_policies()[0]
                    repo.save_source_policy(policy)
                    self.assertEqual(repo.get_source_policy(policy.source_id),policy)
                    record=EvidenceRecord('e','source','Fixture','financial_media',3,'headline','body',None,
                        '2026-01-01T00:00:00Z','2026-01-01T00:00:00Z','2026-01-01T00:00:00Z',[],[],[],'neutral',0,0,None,metadata={})
                    repo.save_evidence(record)
                    event=ClusteredEvent('c','p','v1','2026-01-01T00:00:00Z','2026-01-01T00:00:00Z','headline',('e',),('source',),(),(),0,0,0)
                    repo.save_clustered_event(event)
                    narrative=MarketNarrative('n','2026-01-01T00:00:00Z','fixture','fixture','v1','summary')
                    repo.store.save_narrative(narrative)
                    snapshot=MarketIntelligenceSnapshot('s','2026-01-01T00:00:00Z','v1',[],[])
                    repo.store.save_snapshot(snapshot)
                    results.append((repo.get_evidence('e'),repo.list_clustered_events(),repo.store.latest_narrative(),repo.store.get_snapshot('s')))
                finally: repo.close()
        self.assertEqual(results[0],results[1])

    def test_postgres_schema_and_contract_are_present_without_connecting(self):
        repo = PostgresRepository("postgresql://redacted", connection_factory=lambda _: None)
        sql = repo.initialize_sql()
        for table in ("observations", "shadow_decisions", "outcome_labels", "adaptive_evidence", "adaptive_evidence_contributions", "worker_jobs", "worker_status"):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", sql)
        self.assertFalse(repo.connected)

if __name__ == "__main__": unittest.main()
