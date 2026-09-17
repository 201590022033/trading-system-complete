"""Identical rolling-count and safe read-model contracts on both adapters."""
import unittest
from dataclasses import replace
import test_shadow_transactions as transactions
from test_shadow_transactions import T, END
from shadow_learning import ObservationRecord
from shadow_test_fixtures import decision,complete_label

class LearningStatusBehavior(unittest.TestCase):
    repositories=transactions.TransactionContracts.repositories
    labelled=transactions.TransactionContracts.labelled

    def test_counts_timestamps_events_and_unavailable_are_distinct(self):
        for repo,db in self.repositories():
            a,ev=self.labelled(repo,'a'); b,_=self.labelled(repo,'b')
            repo.contribute_adaptive_evidence(ev,a.outcome_id)
            repo.contribute_adaptive_evidence(ev,b.outcome_id)
            repo.contribute_adaptive_evidence(ev,a.outcome_id)
            obs=ObservationRecord('u','TEST',T,'1',{},source_version='unavailable')
            dec=decision('du','u','TEST',T,'1','BUY',{})
            repo.save_observation(obs); repo.save_shadow_decision(dec)
            repo.save_outcome(complete_label(dec,now=END,entry_price=None,exit_price=None))
            repo.save_observation(ObservationRecord('f','TEST','2099-01-01T00:00:00Z','1',{}))
            state=repo.learning_status(now=END)
            self.assertEqual(state['observations']['24h'],3)
            self.assertEqual(state['labelled_outcomes']['24h'],2)
            self.assertEqual(state['unavailable_outcomes']['24h'],1)
            self.assertEqual(state['adaptive_updates']['24h'],2)
            self.assertEqual(state['latest_timestamps']['observations'],T)
            self.assertEqual(state['latest_timestamps']['adaptive_updates'],END)
            self.assertEqual(state['pending_outcomes'],0)
            older=repo.learning_status(now='2026-01-06T00:00:00Z')
            self.assertEqual(older['labelled_outcomes']['3d'],0)
            self.assertEqual(older['labelled_outcomes']['7d'],2)

    def test_persisted_heartbeat_safe_projection_and_staleness(self):
        for repo,db in self.repositories():
            repo.save_worker_status({'worker_id':'w','status':'RUNNING','last_heartbeat_at':END,
                'started_at':T,'processed':2,'private':'SYNTHETIC_SECRET_SENTINEL'})
            state=repo.learning_status(now=END)
            self.assertEqual(state['worker_status']['last_heartbeat_at'],END)
            self.assertEqual(state['worker_status']['status'],'RUNNING')
            self.assertNotIn('SYNTHETIC_SECRET_SENTINEL',str(state))
            self.assertEqual(repo.learning_status(now='2026-01-02T00:06:00Z')['worker_status']['status'],'STALE')
