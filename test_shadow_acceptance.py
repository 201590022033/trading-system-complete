"""Real production path, persisted jobs and reconstructed adapters end-to-end."""
import copy
import hashlib
import json
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from dataclasses import asdict
from unittest.mock import patch
from persistence.sqlite_repository import SQLiteRepository
from persistence.postgres_repository import PostgresRepository
from test_postgres_repository_behavior import SQLiteDBAPIForPostgres
from shadow_learning import ObservationRecord,JobCheckpoint,timestamp
from shadow_test_fixtures import decision as fixture_decision
from workers.runtime import runtime_handlers
from workers.shadow_learning import ShadowWorker
from operational_intelligence import service
from market_profiles import DEFAULT_PROFILE_REGISTRY
from test_shadow_transactions import T,END

ROOT=Path(__file__).parent

def production_fingerprint():
    manifest=json.loads((ROOT/'docs/handoffs/2026-09-06-ARTIFACT-CHECKSUMS.json').read_text())
    files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in manifest['files']}
    for name in ('signal_pipeline.py','adaptive_fusion.py','regime_engine.py','market_profiles.py','indicator_effectiveness.py'):
        files[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return {'files':files,'profiles':copy.deepcopy(vars(DEFAULT_PROFILE_REGISTRY))}

def causal_observation():
    prices=[100.]*25+[300.-n for n in range(15)]
    rows=[]
    for i,price in enumerate(prices):
        event=(timestamp(T)-timedelta(days=len(prices)-i-1)).isoformat()
        rows.append({'instrument':'NPN','event_time':event,'available_time':event,'close':str(price),'feature_version':'synthetic-v1'})
    return ObservationRecord('causal-o','NPN',T,'1',{'history':rows},
        research_context={'research_only':999},source_version='synthetic-v1',pipeline_version='acceptance-v1')

class FullAcceptance(unittest.TestCase):
    def run_loop(self,backend,restart):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'acceptance.db'
            def repository():
                if backend=='sqlite': return SQLiteRepository(path)
                result=PostgresRepository('postgresql://fixture',connection=SQLiteDBAPIForPostgres(path))
                result.initialize(); return result
            repo=repository(); clock=[T]
            jobs=[]
            def worker(): return ShadowWorker(repo,'acceptance',runtime_handlers(repo,clock=lambda:clock[0]),clock=lambda:clock[0])
            def run(job):
                jobs.append(job); self.assertEqual(worker().run_once([job]),1)
                result=repo.get_job(job.job_key)
                self.assertEqual(result['status'],'COMPLETED')
                return result['checkpoint']
            def boundary():
                nonlocal repo
                if restart: repo.close(); repo=repository()
            try:
                observation=causal_observation()
                canonical=service.analyze('NPN',horizon='1',as_of=T,observation_context={'history':observation.market_data['history']})
                self.assertEqual(canonical['decision']['action'],'buy')
                run(JobCheckpoint('observe','observation-generation',T,checkpoint={'observation':observation.to_dict()})); boundary()
                sessions=fixture_decision('d','causal-o','NPN',T,'1','BUY',{}).horizon_context
                dec_id=run(JobCheckpoint('decide','shadow-decision-generation',T,checkpoint={'observation_id':observation.observation_id,'horizon_context':sessions}))['decision_id']
                self.assertEqual(repo.get_shadow_decision(dec_id)['production_assessment'],canonical['decision'])
                self.assertEqual(repo.counts()['pending_outcomes'],1); boundary()
                label_job=JobCheckpoint('label','outcome-labelling',END,checkpoint={'decision_id':dec_id,'prices':{
                    'now':END,'entry_price':286.,'exit_price':288.86,'entry_at':T,'exit_at':END,'entry_available_at':T,'exit_available_at':END}})
                self.assertEqual(worker().run_once([label_job]),0)
                self.assertEqual(repo.counts()['pending_outcomes'],1)
                clock[0]=END
                out_id=run(label_job)['outcome_id']; boundary()
                self.assertEqual(repo.get_outcome(out_id)['label'],'WIN')
                run(JobCheckpoint('evidence','adaptive-evidence-update',END,checkpoint={'outcome_id':out_id})); boundary()
                final=repo.counts()
                self.assertEqual(final,{'observations':1,'shadow_decisions':1,'labelled_outcomes':1,'adaptive_updates':1,'pending_outcomes':0})
                for job in jobs: self.assertEqual(worker().run_once([job]),0)
                # Reconstruct both processes/adapters even in the uninterrupted variant.
                repo.close(); repo=repository()
                for job in jobs: self.assertEqual(worker().run_once([job]),0)
                self.assertEqual(repo.counts(),final)
                state=repo.learning_status(now=END)
                for key in ('observations','shadow_decisions','labelled_outcomes','adaptive_updates'):
                    self.assertEqual(state[key]['24h'],1)
                self.assertEqual(state['latest_timestamps']['adaptive_updates'],END)
                return (repo.get_observation(observation.observation_id),repo.get_shadow_decision(dec_id),repo.get_outcome(out_id),final)
            finally: repo.close()

    def test_full_pipeline_backend_and_multiple_restart_equivalence(self):
        before=production_fingerprint()
        results=[]
        for backend in ('sqlite','postgresql'):
            for restart in (False,True):
                with self.subTest(backend=backend,restart=restart): results.append(self.run_loop(backend,restart))
        self.assertTrue(all(result==results[0] for result in results))
        self.assertEqual(before,production_fingerprint())

    def test_fingerprint_detects_actual_profile_state_perturbation(self):
        before=production_fingerprint()
        with patch.dict(DEFAULT_PROFILE_REGISTRY._ticker_profiles,{'NPN':'banks_financials'}):
            self.assertNotEqual(before,production_fingerprint())
        self.assertEqual(before,production_fingerprint())
