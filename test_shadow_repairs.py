"""Forensic regressions: use explicit clocks, factual sessions and isolated storage."""
import unittest
from datetime import datetime, timezone
from dataclasses import replace

from operational_intelligence import OperationalIntelligence
from shadow_learning import ShadowDecision
from shadow_learning_pipeline import production_shadow_decision, matured, label_decision, aggregate_evidence
from persistence.sqlite_repository import SQLiteRepository
from shadow_learning import ObservationRecord, OutcomeLabel, AdaptiveEvidence

T = '2026-01-02T16:00:00+00:00'  # Friday close
END = '2026-01-05T16:00:00+00:00'  # next supplied session, Monday
SESSIONS = [dict(session_id='fri', session_date='2026-01-02', open_time='2026-01-02T08:00:00+00:00', close_time=T, calendar_version='fixture-v1'),
            dict(session_id='mon', session_date='2026-01-05', open_time='2026-01-05T08:00:00+00:00', close_time=END, calendar_version='fixture-v1')]

class CausalRepairs(unittest.TestCase):
    def test_future_rows_cannot_change_decision(self):
        service = OperationalIntelligence()
        service._load_rows()
        first = production_shadow_decision(service,'NPN',horizon='1',observation_id='o',decided_at=T)
        for i, row in enumerate(service._rows['NPN'][-50:]):
            self.assertGreater(row['event_time'], T)
            row['close'] = str(100000 * (i+1))
        second = production_shadow_decision(service,'NPN',horizon='1',observation_id='o',decided_at=T)
        self.assertEqual(first.production_assessment, second.production_assessment)

    def test_eod_without_session_is_unresolved(self):
        decision = ShadowDecision('d','o','NPN',T,'intraday_eod','BUY',{})
        self.assertFalse(matured(decision,'2026-01-02T16:00:01+00:00'))

    def test_sell_uses_raw_return_once(self):
        decision = ShadowDecision('d','o','NPN',T,'1','SELL',{})
        # The corrected API requires explicit session and price availability context.
        decision = replace(decision, horizon_context={'sessions': SESSIONS})
        label = label_decision(decision,now=END,entry_price=100,exit_price=90,
                               entry_at=T,exit_at=END,entry_available_at=T,exit_available_at=END)
        self.assertAlmostEqual(label.net_return,.099)

    def test_orphan_outcome_rejected(self):
        repo = SQLiteRepository(':memory:')
        try:
            with self.assertRaises(ValueError):
                repo.save_outcome(OutcomeLabel('x','missing',END,'WIN',100,110,.1,.099))
        finally:
            repo.close()

    def test_orphan_decision_rejected(self):
        repo = SQLiteRepository(':memory:')
        try:
            with self.assertRaises(ValueError):
                repo.save_shadow_decision(ShadowDecision('d','missing','NPN',T,'1','BUY',{}))
        finally:
            repo.close()

    def test_unpersisted_contribution_rejected(self):
        repo = SQLiteRepository(':memory:')
        try:
            evidence = AdaptiveEvidence('e','NPN','1','UNKNOWN','production',1,1,0,.099,'OBSERVED',updated_at=END)
            with self.assertRaises(ValueError):
                repo.contribute_adaptive_evidence(evidence,'missing')
        finally:
            repo.close()

    def test_cost_direction_and_transition_matrix(self):
        for action, exit_price, previous, gross, net in (
            ('BUY',110,0,.1,.099), ('BUY',90,0,-.1,-.101),
            ('SELL',90,0,.1,.099), ('SELL',110,0,-.1,-.101),
            ('SELL',90,-1,.1,.1), ('SELL',90,1,.1,.098),
            ('BUY',110,-1,.1,.098), ('HOLD',110,0,0,0), ('HOLD',110,1,0,-.001)):
            with self.subTest(action=action, previous=previous, price=exit_price):
                d = ShadowDecision('d','o','NPN',T,'1',action,{},
                    horizon_context={'sessions':SESSIONS}, previous_signal=previous)
                out = label_decision(d,now=END,entry_price=100,exit_price=exit_price,
                    entry_at=T,exit_at=END,entry_available_at=T,exit_available_at=END)
                self.assertAlmostEqual(out.gross_return,gross)
                self.assertAlmostEqual(out.net_return,net)
                self.assertEqual(out.label,'HOLD' if action=='HOLD' else 'WIN' if gross>0 else 'LOSS')

    def test_sessions_weekend_timezone_and_unsupported(self):
        d = ShadowDecision('d','o','NPN',T,'1','BUY',{},horizon_context={'sessions':SESSIONS})
        self.assertFalse(matured(d,'2026-01-03T16:00:00Z'))
        self.assertTrue(matured(d,'2026-01-05T18:00:00+02:00'))
        self.assertFalse(matured(d,T))
        for horizon in ('0','2','swing','intraday_7m'):
            self.assertFalse(matured(replace(d,horizon=horizon),END))
        # No inferred holiday/session: only the supplied next trading close is used.
        holiday = [SESSIONS[0],{**SESSIONS[1],'session_date':'2026-01-06',
            'open_time':'2026-01-06T08:00:00Z','close_time':'2026-01-06T16:00:00Z'}]
        self.assertFalse(matured(replace(d,horizon_context={'sessions':holiday}),END))

    def test_intraday_eod_break_and_session_close(self):
        d=ShadowDecision('d','o','NPN','2026-01-02T08:00:00Z','intraday_5m','BUY',{},horizon_context={'sessions':SESSIONS})
        self.assertFalse(matured(d,'2026-01-02T08:04:59Z'))
        self.assertTrue(matured(d,'2026-01-02T08:05:00Z'))
        eod=replace(d,horizon='intraday_eod')
        self.assertFalse(matured(eod,'2026-01-02T15:59:59Z'))
        self.assertTrue(matured(eod,T))
        broken=[{**SESSIONS[0],'breaks':[['2026-01-02T08:02:00Z','2026-01-02T08:10:00Z']]}]
        self.assertFalse(matured(replace(d,horizon_context={'sessions':broken}),END))
        self.assertFalse(matured(replace(d,decided_at=T),END))

    def test_missing_stale_future_and_invalid_prices_fail_closed(self):
        d=ShadowDecision('d','o','NPN',T,'1','BUY',{},horizon_context={'sessions':SESSIONS})
        for args in ({}, {'entry_at':T,'exit_at':T,'entry_available_at':T,'exit_available_at':END},
                     {'entry_at':T,'exit_at':END,'entry_available_at':T,'exit_available_at':'2026-01-06T16:00:00Z'}):
            out=label_decision(d,now=END,entry_price=100,exit_price=110,**args)
            self.assertEqual(out.label,'OUTCOME_DATA_UNAVAILABLE')
            self.assertIsNone(out.net_return)
        for price in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):
                label_decision(d,now=END,entry_price=price,exit_price=110,
                    entry_at=T,exit_at=END,entry_available_at=T,exit_available_at=END)

    def test_ledger_rejects_forged_incomplete_future_and_cross_instrument(self):
        repo=SQLiteRepository(':memory:')
        self.addCleanup(repo.close)
        o=ObservationRecord('o','NPN',T,'1',{})
        d=ShadowDecision('d','o','NPN',T,'1','BUY',{},horizon_context={'sessions':SESSIONS})
        repo.save_observation(o); repo.save_shadow_decision(d)
        out=label_decision(d,now=END,entry_price=100,exit_price=110,
            entry_at=T,exit_at=END,entry_available_at=T,exit_available_at=END)
        for field, value in (('net_return',123),('matured_at',T),('evaluated_at','2099-01-01T00:00:00Z')):
            with self.assertRaises(ValueError): repo.save_outcome(replace(out,**{field:value}))
        with self.assertRaises(ValueError):
            repo.save_shadow_decision(replace(d,decision_id='foreign',instrument='SHP'))
        with self.assertRaises(ValueError): replace(out,data_quality='INCOMPLETE')
        repo.save_outcome(out)
        with self.assertRaises(ValueError): aggregate_evidence(repo,out,instrument='SHP',horizon='1')
        self.assertTrue(aggregate_evidence(repo,out,instrument='NPN',horizon='1'))

    def test_observation_available_boundary_and_research_metadata(self):
        with self.assertRaises(ValueError):
            ObservationRecord('o','NPN',T,'1',{},research_context={'available_time':END})
        with self.assertRaises(ValueError):
            ObservationRecord('o','NPN',T,'1',{'forward_return':.1})
        self.assertEqual(ObservationRecord('o','NPN','2026-01-02T18:00:00+02:00','1',{}).observed_at,T)
        with self.assertRaises(ValueError): ObservationRecord('o','NPN','nonsenseZ','1',{})

if __name__ == '__main__': unittest.main()
