"""Transaction/identity contracts run against both real SQLite and PG DB-API."""
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from test_postgres_repository_behavior import SQLiteDBAPIForPostgres
from shadow_learning import ObservationRecord, AdaptiveEvidence, JobCheckpoint
from shadow_test_fixtures import decision, complete_label

T='2026-01-01T00:00:00+00:00'
END='2026-01-02T00:00:00+00:00'

class TransactionContracts(unittest.TestCase):
    def repositories(self):
        for backend in ('sqlite','postgresql'):
            tmp=tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            if backend=='sqlite':
                repo=SQLiteRepository(Path(tmp.name)/'state.db')
                db=repo.store._connection
            else:
                fixture=SQLiteDBAPIForPostgres(Path(tmp.name)/'state.db')
                repo=PostgresRepository('postgresql://fixture',connection=fixture)
                repo.initialize(); db=fixture.db
            self.addCleanup(db.close)
            yield repo, db

    def labelled(self,repo,tag=''):
        # Different version is a distinct logical observation at the same time.
        obs=ObservationRecord('o'+tag,'TEST',T,'1',{},source_version='v'+tag)
        dec=decision('d'+tag,obs.observation_id,'TEST',T,'1','BUY',{})
        repo.save_observation(obs); repo.save_shadow_decision(dec)
        outcome=complete_label(dec,now=END,entry_price=100,exit_price=110)
        repo.save_outcome(outcome)
        ev=AdaptiveEvidence('e','TEST','1','UNKNOWN','production',1,1,0,outcome.net_return,'OBSERVED',updated_at=END)
        return outcome,ev

    def test_outer_transaction_rollback_owns_all_writes(self):
        for repo,db in self.repositories():
            with self.assertRaisesRegex(RuntimeError,'crash'):
                with repo.transaction():
                    repo.save_observation(ObservationRecord('o','TEST',T,'1',{}))
                    raise RuntimeError('crash')
            self.assertIsNone(repo.get_observation('o'))

    def test_pg_and_sqlite_aggregate_actual_updates(self):
        for repo,db in self.repositories():
            a,ev=self.labelled(repo,'a'); b,_=self.labelled(repo,'b')
            self.assertTrue(repo.contribute_adaptive_evidence(ev,a.outcome_id))
            self.assertTrue(repo.contribute_adaptive_evidence(ev,b.outcome_id))
            self.assertFalse(repo.contribute_adaptive_evidence(ev,a.outcome_id))
            row=db.execute('SELECT payload FROM adaptive_evidence').fetchone()
            self.assertIsNotNone(row)
            result=json.loads(row[0]); self.assertEqual(result['sample_count'],2)
            self.assertEqual(result['wins'],2); self.assertAlmostEqual(result['mean_net_return'],.099)

    def test_marker_and_aggregate_rollback_together(self):
        for repo,db in self.repositories():
            out,ev=self.labelled(repo)
            target=repo.store if repo.backend=='sqlite' else repo
            with patch.object(target,'save_adaptive_evidence',side_effect=RuntimeError('crash')):
                with self.assertRaisesRegex(RuntimeError,'crash'):
                    repo.contribute_adaptive_evidence(ev,out.outcome_id)
            # A later unrelated successful write must not commit a stranded marker.
            repo.save_job(JobCheckpoint('j','adaptive-evidence-update',T))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM adaptive_evidence_contributions').fetchone()[0],0)
            self.assertTrue(repo.contribute_adaptive_evidence(ev,out.outcome_id))

    def test_job_checkpoint_is_updated(self):
        for repo,db in self.repositories():
            job=JobCheckpoint('j','observation-generation',T)
            repo.save_job(job)
            final=replace(job,status='COMPLETED',attempt_count=1,checkpoint={'offset':2},last_updated=END)
            repo.save_job(final)
            self.assertEqual(repo.get_job('j'),final.to_dict())

    def test_conflicting_immutable_identity_is_rejected(self):
        for repo,db in self.repositories():
            obs=ObservationRecord('o','TEST',T,'1',{})
            repo.save_observation(obs); repo.save_observation(obs)
            for changed in (replace(obs,observation_id='other'),replace(obs,market_data={'close':123})):
                with self.assertRaises(ValueError): repo.save_observation(changed)

    def test_equivalent_timestamp_and_alias_share_identity(self):
        for repo,db in self.repositories():
            obs=ObservationRecord('o','NPN',T,'1',{})
            alias=ObservationRecord('o','npn.jo','2026-01-01T02:00:00+02:00','1',{})
            repo.save_observation(obs); repo.save_observation(alias)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM observations').fetchone()[0],1)

    def test_evidence_dimensions_cannot_collide(self):
        for repo,db in self.repositories():
            out,ev=self.labelled(repo)
            a=replace(ev,evidence_id='ea',regime='r|x',profile='p')
            b=replace(ev,evidence_id='eb',regime='r',profile='x|p')
            self.assertTrue(repo.contribute_adaptive_evidence(a,out.outcome_id))
            self.assertTrue(repo.contribute_adaptive_evidence(b,out.outcome_id))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM adaptive_evidence').fetchone()[0],2)

    def test_nested_failure_does_not_discard_outer_work(self):
        for repo,db in self.repositories():
            with repo.transaction():
                repo.save_observation(ObservationRecord('a','TEST',T,'1',{}))
                with self.assertRaises(RuntimeError):
                    with repo.transaction():
                        repo.save_job(JobCheckpoint('j','observation-generation',T))
                        raise RuntimeError('crash')
                self.assertIsNone(repo.get_job('j'))
            self.assertIsNotNone(repo.get_observation('a'))

    def test_outcome_and_status_rollback_together(self):
        for repo,db in self.repositories():
            repo.save_observation(ObservationRecord('o','TEST',T,'1',{}))
            dec=decision('d','o','TEST',T,'1','BUY',{})
            repo.save_shadow_decision(dec)
            out=complete_label(dec,now=END,entry_price=100,exit_price=110)
            # Database fault after the outcome insert, before status update.
            db.execute("CREATE TRIGGER fail_status BEFORE UPDATE ON shadow_decisions BEGIN SELECT RAISE(ABORT,'injected status failure'); END")
            db.commit()
            with self.assertRaises(Exception): repo.save_outcome(out)
            self.assertIsNone(repo.get_outcome(out.outcome_id))
            self.assertEqual(repo.get_shadow_decision('d')['outcome_status'],'PENDING_OUTCOME')
            db.execute('DROP TRIGGER fail_status'); db.commit()
            repo.save_outcome(out)
            self.assertEqual(repo.get_shadow_decision('d')['outcome_status'],'LABELLED')

    def test_two_sqlite_connections_cannot_duplicate_contribution(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'race.db'
            repo=SQLiteRepository(path); out,ev=self.labelled(repo); repo.close()
            def contribute(_):
                import sqlite3
                connection=SQLiteRepository(path)
                try:
                    for attempt in range(3):
                        try: return connection.contribute_adaptive_evidence(ev,out.outcome_id)
                        except sqlite3.OperationalError:
                            if attempt==2: raise
                finally: connection.close()
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(contribute,range(2)))
            self.assertEqual(sorted(results),[False,True])
            repo=SQLiteRepository(path)
            try: self.assertEqual(repo.counts()['adaptive_updates'],1)
            finally: repo.close()
