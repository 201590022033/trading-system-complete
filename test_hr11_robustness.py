import unittest
from dataclasses import replace
from datetime import timedelta
from intraday_robustness import prepare_cell,admit_cells,RobustnessPolicy
import test_hr11_evaluation as fixtures
CELL=fixtures.CELL
class RobustnessTests(unittest.TestCase):
    def trades(self,negative=False):
        first=fixtures.EvaluationTests().run_eval().trades[0]
        return tuple(replace(first,decision_time=first.decision_time+timedelta(days=i),entry_time=first.entry_time+timedelta(days=i),exit_time=first.exit_time+timedelta(days=i),
            outcome_available_time=first.outcome_available_time+timedelta(days=i),fold_id=str(i//10),net_return=(-1 if negative else 1)*(.01+.0001*i),cost_fraction=.001) for i in range(40))
    def test_empty_is_null_and_insufficient(self):
        result=admit_cells([prepare_cell(CELL,())])[0]
        self.assertEqual(result['admission_state'],'INSUFFICIENT_EVIDENCE');self.assertIsNone(result['ci_low']);self.assertIsNone(result['metrics']['mean_net_return'])
    def test_reproducible_shadow_only_and_negative_rejection(self):
        for negative in (False,True):
            trades=self.trades(negative);baseline=tuple(replace(t,net_return=0) for t in trades)
            a=prepare_cell(CELL,trades,baseline=baseline,sensitivity=(trades,trades))
            self.assertEqual(a,prepare_cell(CELL,trades,baseline=baseline,sensitivity=(trades,trades)))
            result=admit_cells([a])[0]
            self.assertEqual(result['admission_state'],'REJECT' if negative else 'ADMIT_FOR_CONTINUED_SHADOW')
            self.assertFalse(result['live_execution_allowed'])
    def test_small_folds_unknown_regime_and_cell_separation(self):
        trades=self.trades();a=prepare_cell(CELL,trades[:10]);b=prepare_cell(('OTHER',),())
        self.assertTrue(all(x['admission_state']=='INSUFFICIENT_EVIDENCE' for x in admit_cells([a,b])))
        self.assertEqual(b['metrics']['trade_count'],0)
        unknown=[replace(t,cell=(*CELL[:5],'unknown','stable','normal')) for t in trades]
        self.assertIn('REGIME_EVIDENCE',prepare_cell(CELL[:5],unknown)['insufficient_reasons'])
    def test_multiple_testing_adjustment(self):
        cells=[prepare_cell((str(i),),()) for i in range(3)]
        for c,p in zip(cells,(.01,.04,.9)):c['raw_p_value']=p
        self.assertEqual(admit_cells(cells)[0]['adjusted_p_value'],.03)
