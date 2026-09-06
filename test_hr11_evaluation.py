import unittest
from dataclasses import replace
from datetime import timedelta
from intraday_evaluation import evaluate,EvaluationPolicy,training_evidence
from intraday_signals import EnsembleDecision,EvidenceOutcome
from intraday_gates import GateResult
from intraday_horizons import get_horizon
from test_hr11_data import bar,T
from test_hr11_costs import INSTRUMENT,SCHEDULE
from test_hr11_sessions import SESSION

CELL=('SOL_CASH','cash_equity','5m','intraday_15m','energy_sasol','up','stable','normal')
def builder(current,prefix,evidence):
    assert all(b.available_time<=current.decision_time for b in prefix)
    return EnsembleDecision(current.decision_time,CELL,1,{'macd':1},{'macd':{'value':1}}),GateResult({'fixture':'PASS'},(),True,False,.001)
class EvaluationTests(unittest.TestCase):
    def run_eval(self,bars=None,cutoff=None,builder_=builder):
        bars=bars or [bar(i) for i in range(24)]
        return evaluate(INSTRUMENT,bars,bars,[SESSION],get_horizon('intraday_15m'),SCHEDULE,builder_,cutoff or bars[-1].event_time,EvaluationPolicy(units=10))
    def test_nonoverlap_entry_costs_mfe_and_holding(self):
        result=self.run_eval();self.assertGreater(len(result.trades),1)
        first=result.trades[0]
        self.assertEqual(first.entry_price,101);self.assertEqual(first.exit_price,103)
        self.assertEqual(first.holding_seconds,900);self.assertEqual(first.turnover_units,20)
        self.assertLess(first.net_return,first.gross_return);self.assertGreater(first.mfe,first.gross_return);self.assertLess(first.mae,0)
        self.assertTrue(all(a.exit_time<=b.entry_time for a,b in zip(result.trades,result.trades[1:])))
    def test_future_changes_cannot_change_prior_decisions_or_matured_trades(self):
        bars=[bar(i) for i in range(24)];cutoff=bar(11).event_time
        changed=[b if i<12 else replace(b,open=b.open+100,high=b.high+100,low=b.low+100,close=b.close+100) for i,b in enumerate(bars)]
        self.assertEqual(self.run_eval(bars,cutoff),self.run_eval(changed,cutoff))
    def test_purge_embargo_and_fixed_folds(self):
        policy=EvaluationPolicy();e=EvidenceOutcome(CELL,'macd',T-timedelta(hours=2),T-timedelta(minutes=59),T-timedelta(minutes=59),.1,.1)
        self.assertEqual(training_evidence([e],T,policy),())
        delayed=replace(e,label_end=T-timedelta(hours=1,minutes=1),available_time=T-timedelta(minutes=4))
        self.assertEqual(training_evidence([delayed],T,policy),())
        valid=replace(delayed,available_time=T-timedelta(minutes=6))
        self.assertEqual(training_evidence([valid],T,policy),(valid,))
        self.assertEqual(policy.fold(T),policy.fold(T+timedelta(minutes=5)))
    def test_missing_bars_and_delayed_outcomes(self):
        bars=[bar(i) for i in range(24) if i!=2]
        result=self.run_eval(bars)
        self.assertIn('INCOMPLETE_OR_UNALIGNED_EXECUTION_WINDOW',result.warnings)
        bars=[bar(0),bar(1),bar(2),replace(bar(3),available_time=T+timedelta(hours=3),decision_time=T+timedelta(hours=3))]
        self.assertFalse(self.run_eval(bars,bar(3).event_time).trades)
    def test_gate_failure_and_short_refusal(self):
        def failed(c,p,e):
            d,g=builder(c,p,e);return d,replace(g,research_pass=False)
        self.assertEqual(self.run_eval(builder_=failed).metrics['trade_count'],0)
        self.assertIsNone(self.run_eval(builder_=failed).metrics['mean_net_return'])
