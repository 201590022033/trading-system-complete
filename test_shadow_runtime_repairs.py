"""Actual composition and bounded worker regressions; all storage is isolated."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dataclasses import replace
from persistence.sqlite_repository import SQLiteRepository
from shadow_learning import JobCheckpoint
from workers.shadow_learning import ShadowWorker

T='2026-01-01T00:00:00+00:00'

class RuntimeRepairs(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo=SQLiteRepository(Path(self.tmp.name)/'runtime.db'); self.addCleanup(self.repo.close)

    def test_stale_completed_job_object_never_reexecutes(self):
        calls=[]; job=JobCheckpoint('j','observation-generation',T)
        worker=ShadowWorker(self.repo,'w',{job.job_type:lambda job:calls.append(1) or {}})
        worker.run_once([job]); worker.run_once([job])
        self.assertEqual(calls,[1])

class PostgresCompositionRepairs(unittest.TestCase):
    def setUp(self):
        from persistence.postgres_repository import PostgresRepository
        from test_postgres_repository_behavior import SQLiteDBAPIForPostgres
        self.connection=SQLiteDBAPIForPostgres(':memory:')
        self.addCleanup(self.connection.close)
        self.repo=PostgresRepository('postgresql://fixture',connection=self.connection)
        self.repo.initialize()

    def test_migrations_are_tracked_and_repeatable(self):
        before=self.connection.db.execute('SELECT version FROM postgres_schema_migrations ORDER BY version').fetchall()
        self.assertGreaterEqual(len(before),2)
        self.repo.initialize()
        self.assertEqual(before,self.connection.db.execute('SELECT version FROM postgres_schema_migrations ORDER BY version').fetchall())

    def test_pg_market_intelligence_uses_same_connection(self):
        from market_intelligence.source_registry import SourceRegistry
        registry=SourceRegistry(self.repo.store)
        registry.seed_defaults()
        policies=registry.list_policies()
        self.assertTrue(policies)
        self.assertGreater(self.connection.db.execute('SELECT COUNT(*) FROM source_policies').fetchone()[0],0)

    def test_migration_failure_rolls_back_schema_and_tracking(self):
        from test_postgres_repository_behavior import _Cursor, SQLiteDBAPIForPostgres
        from persistence.postgres_repository import PostgresRepository
        connection=SQLiteDBAPIForPostgres(':memory:'); self.addCleanup(connection.close)
        repo=PostgresRepository('postgresql://fixture',connection=connection)
        original=_Cursor.execute
        def fail(cursor,sql,params=()):
            if 'CREATE TABLE IF NOT EXISTS documents (' in sql: raise RuntimeError('DDL crash')
            return original(cursor,sql,params)
        with patch.object(_Cursor,'execute',fail), self.assertRaisesRegex(RuntimeError,'DDL crash'):
            repo.initialize()
        self.assertEqual(connection.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),[])
        repo.initialize()
        self.assertEqual(connection.db.execute('SELECT COUNT(*) FROM postgres_schema_migrations').fetchone()[0],len(repo._migration_files()))

    def test_empty_cycle_does_not_invoke_handlers(self):
        calls=[]
        worker=ShadowWorker(self.repo,'w',{'observation-generation':lambda job:calls.append(1) or {}})
        self.assertEqual(worker.run_once(),0); self.assertFalse(calls)

    def test_actual_due_claim_and_completion_are_authoritative(self):
        job=JobCheckpoint('claim','observation-generation',T)
        self.repo.ensure_job(job)
        first=self.repo.claim_job(job.job_key,'first',T)
        self.assertIsNotNone(first)
        self.assertIsNone(self.repo.claim_job(job.job_key,'second',T))
        done=replace(first,status='COMPLETED')
        self.assertTrue(self.repo.finish_job(first,done))
        self.assertFalse(self.repo.finish_job(first,replace(done,status='FAILED')))
        self.assertEqual(self.repo.get_job(job.job_key)['status'],'COMPLETED')

    def test_runtime_decision_replay_after_lost_checkpoint(self):
        from workers.runtime import runtime_handlers
        from shadow_learning import ObservationRecord
        from shadow_test_fixtures import decision
        obs=ObservationRecord('o','NPN',T,'1',{'history':[]})
        self.repo.save_observation(obs)
        job=JobCheckpoint('decision','shadow-decision-generation',T,
            checkpoint={'observation_id':'o','horizon_context':decision('d','o','NPN',T,'1','HOLD',{}).horizon_context})
        handler=runtime_handlers(self.repo)[job.job_type]
        first=handler(job)
        self.assertEqual(first,handler(job))

    def test_future_and_exhausted_jobs_are_not_executed(self):
        calls=[]; future=JobCheckpoint('future','observation-generation','2099-01-01T00:00:00Z')
        failed=JobCheckpoint('failed','observation-generation',T,'FAILED',retryable=False)
        self.repo.save_job(failed)
        worker=ShadowWorker(self.repo,'w',{future.job_type:lambda job:calls.append(1) or {}})
        self.assertEqual(worker.run_once([future,failed]),0)
        self.assertFalse(calls)

    def test_missing_handler_fails_explicitly(self):
        job=JobCheckpoint('missing','market-data-update',T)
        ShadowWorker(self.repo,'w').run_once([job])
        state=self.repo.get_job(job.job_key)
        self.assertEqual(state['status'],'FAILED')
        self.assertEqual(state['error_category'],'MISSING_HANDLER')

    def test_unexpired_running_job_is_not_recovered(self):
        from datetime import datetime,timezone
        job=JobCheckpoint('running','observation-generation',T,'RUNNING','other',1,last_updated=datetime.now(timezone.utc).isoformat())
        self.repo.save_job(job)
        self.assertEqual(ShadowWorker(self.repo,'w').recover_running([job]),[])

    def test_application_sources_use_the_selected_repository(self):
        import app
        from market_intelligence.source_registry import SourceRegistry
        SourceRegistry(self.repo.store).seed_defaults()
        # No independent SQLite store may be opened by a request.
        with patch.object(app,'runtime_repository',return_value=self.repo), patch.object(app,'MarketIntelligenceStore',side_effect=AssertionError('split persistence')):
            response=app.app.test_client().get('/api/market-intelligence/sources')
            self.assertEqual(response.status_code,200)

    def test_entrypoint_executes_a_bounded_cycle(self):
        from workers import heartbeat
        calls=[]; job=JobCheckpoint('j','observation-generation',T)
        self.repo.save_job(job)
        heartbeat.run(interval_seconds=0,cycles=1,repository=self.repo,
            handlers={job.job_type:lambda job:calls.append(1) or {}})
        self.assertEqual(calls,[1])
