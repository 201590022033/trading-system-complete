import unittest
from dataclasses import replace
from datetime import timedelta
from intraday_features import compute_features
from intraday_profiles import get_profile
from intraday_signals import ensemble,cell_key,regimes,EvidenceOutcome
from intraday_gates import evaluate_gates
from intraday_cross_asset import CrossAssetSnapshot
from test_hr11_data import bar,T
from test_hr11_costs import INSTRUMENT,SCHEDULE
from intraday_sessions import SessionWindow
class SignalGateTests(unittest.TestCase):
    def setUp(self):
        self.bars=[bar(i) for i in range(90)];self.now=self.bars[-1].event_time
        self.session=SessionWindow('s1','2026-01-05',T,T+timedelta(hours=8),'fixture')
        self.snapshot=compute_features(self.bars,self.now,[self.session]);self.profile=get_profile(INSTRUMENT)
        self.cell=cell_key(INSTRUMENT,'5m','intraday_30m',regimes(self.snapshot))
        self.decision=ensemble(self.snapshot,self.bars[-1].close,self.cell)
        self.cross=CrossAssetSnapshot(self.now,{f:0.01 for f in self.profile.factors},{},{})
    def gate(self,**kw):
        args=dict(instrument=INSTRUMENT,bar=self.bars[-1],session=self.session,profile=self.profile,snapshot=self.snapshot,
            decision=self.decision,cross_asset=self.cross,schedule=SCHEDULE,units=10);args.update(kw)
        return evaluate_gates(**args)
    def test_missing_signals_are_not_neutral(self):
        snap=replace(self.snapshot,values={'macd':1})
        result=ensemble(snap,100,self.cell)
        self.assertEqual(result.score,1);self.assertIsNone(result.signals['rsi'])
        self.assertIsNone(ensemble(replace(snap,values={}),100,self.cell).score)
    def test_evidence_future_and_cell_isolation(self):
        evidence=[EvidenceOutcome(self.cell,'macd',T-timedelta(days=i+2),T-timedelta(days=i+1,hours=1),T-timedelta(days=i+1),.01,.02) for i in range(35)]
        result=ensemble(self.snapshot,100,self.cell,evidence)
        self.assertGreater(result.explanations['macd']['weight'],1)
        future=replace(evidence[0],available_time=self.now+timedelta(minutes=1),net_return=-9)
        self.assertEqual(result,ensemble(self.snapshot,100,self.cell,evidence+[future]))
        other=tuple('other' if i==0 else x for i,x in enumerate(self.cell))
        self.assertEqual(ensemble(self.snapshot,100,other,evidence).explanations['macd']['weight'],1)
    def test_small_sample_and_overlap(self):
        e=EvidenceOutcome(self.cell,'macd',T-timedelta(days=2),T-timedelta(days=1),T-timedelta(days=1),.01,.01)
        result=ensemble(self.snapshot,100,self.cell,[e]*50)
        self.assertEqual(result.explanations['macd']['evidence_sample_count'],1)
        self.assertEqual(result.explanations['macd']['weight'],1)
    def test_research_pass_never_execution_grade(self):
        self.assertTrue(self.gate().research_pass)
        self.assertFalse(self.gate(execution=True).research_pass)
        self.assertFalse(self.gate().execution_grade)
    def test_refusal_matrix(self):
        for args in (dict(schedule=None),dict(cross_asset=None),dict(bar=replace(self.bars[-1],stale=True)),dict(session=None),dict(instrument=replace(INSTRUMENT,enabled=False)),dict(bar=replace(self.bars[-1],bid=100,ask=110))):
            self.assertFalse(self.gate(**args).research_pass,args)
