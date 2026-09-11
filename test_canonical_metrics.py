import json,unittest
from dataclasses import replace
from datetime import datetime,timezone
from domain.contracts.trade import MetricContext
from domain.evaluation.metrics import *
from domain.evaluation.target import MetricIdentity,TargetCriterion,RequirementLevel,Comparison,EvidenceStage
from domain.evaluation.experiment import ExperimentResult,ExperimentStage
from provider_interfaces import PaperExecutionProvider,LiveExecutionDisabled

class CanonicalMetricTests(unittest.TestCase):
 def setUp(self):
  self.ctx=MetricContext('PERIODIC_CALENDAR','1d','JSE',252,'DECIMAL_RETURN','NET','MODELED_BASE','daily_1d','STRATEGY',False,.08,'X',VERSION,None,'ZAR','REALIZED')
 def c(self,mid,**kw): return replace(self.ctx,metric_id=mid,**kw)
 def test_context_and_unavailable_not_zero(self):
  with self.assertRaises(ValueError): replace(self.ctx,currency='zar')
  r=profit_factor((.1,.2),self.c('PROFIT_FACTOR'));self.assertEqual(r.status,'UNAVAILABLE');self.assertIsNone(r.value)
 def test_gross_and_net_expectancy(self):
  self.assertAlmostEqual(expectancy((.1,.2),self.c('NET_EXPECTANCY')).value,.15)
  gross=self.c('GROSS_EXPECTANCY',return_basis='GROSS',cost_basis='ZERO_COST');self.assertAlmostEqual(expectancy((.2,.3),gross,gross=True).value,.25)
 def test_hit_rate_neutral_and_unresolved(self):
  r=hit_rate((1,0,-1,None),self.c('HIT_RATE',return_unit='FRACTION'));self.assertEqual(r.value,1/3);self.assertIn('UNRESOLVED_EXCLUDED:1',r.warnings)
 def test_payoff_edge(self): self.assertEqual(payoff_metrics((1,2),self.ctx)[2].status,'UNAVAILABLE')
 def test_sharpe_formula_context_overlap_and_zero_vol(self):
  r=canonical_sharpe((.01,.02,-.01),self.c('CANONICAL_ANNUALIZED_SHARPE'));self.assertEqual(r.status,'VALID')
  self.assertEqual(canonical_sharpe((.01,.02),self.c('CANONICAL_ANNUALIZED_SHARPE',annualization_factor=None)).status,'INVALID_CONTEXT')
  self.assertEqual(canonical_sharpe((.01,.02),self.c('CANONICAL_ANNUALIZED_SHARPE',is_overlapping=True)).status,'INVALID_CONTEXT')
  self.assertEqual(canonical_sharpe((.01,.01),self.c('CANONICAL_ANNUALIZED_SHARPE')).status,'UNAVAILABLE')
 def test_legacy_distinct(self):
  r=legacy_tstat_like_v1((.1,.2,-.1),self.c('LEGACY_TSTAT_LIKE_V1',metric_version=LEGACY_VERSION));self.assertEqual(r.metric_version,LEGACY_VERSION);self.assertNotEqual(r.metric_id,'CANONICAL_ANNUALIZED_SHARPE')
 def test_sortino_requires_target(self): self.assertEqual(sortino((.1,-.1),self.c('CANONICAL_ANNUALIZED_SORTINO')).status,'INVALID_CONTEXT')
 def test_drawdown_and_duration(self):
  r=drawdown((100,120,90,100),self.c('MAX_DRAWDOWN',return_unit='FRACTION'));self.assertEqual(r.value,.25);self.assertIn('MAX_DRAWDOWN_DURATION_PERIODS:2',r.warnings)
 def test_volatility_turnover_costs(self):
  self.assertEqual(volatility((.1,.2),self.c('PERIODIC_VOLATILITY')).status,'VALID')
  self.assertEqual(turnover((1,1,0,-1),self.c('POSITION_STATE_TURNOVER')).value,3)
  self.assertEqual(cost_decomposition(.1,.01,.02,self.ctx)['net_return'],.07)
 def test_profit_factor_calmar_exposure(self):
  self.assertEqual(profit_factor((2,-1),self.c('PROFIT_FACTOR')).value,2)
  self.assertEqual(calmar(.2,.1,self.c('CALMAR')).value,2)
  self.assertEqual(exposure((0,1,-1),self.ctx)['time_in_market'],2/3)
 def test_samples_weighting_registry_and_serialization(self):
  r=expectancy((1,2),self.c('WEIGHTED_NET_EXPECTANCY'),weights=(1,2));self.assertEqual(r.metric_version,'weighted-expectancy-v1');self.assertLess(r.effective_sample_count,r.sample_count)
  self.assertEqual(METRIC_REGISTRY.get('HIT_RATE').output_unit,'FRACTION');json.dumps(r.to_dict(),sort_keys=True)
 def test_target_and_experiment_integration(self):
  criterion=TargetCriterion('c',MetricIdentity.NET_EXPECTANCY,RequirementLevel.HARD,Comparison.MINIMUM,0,self.c('NET_EXPECTANCY'),EvidenceStage.OUT_OF_SAMPLE,metric_version=VERSION);self.assertEqual(criterion.metric_version,VERSION)
  metric=expectancy((.1,),self.c('NET_EXPECTANCY'))
  result=ExperimentResult('r','run',datetime.now(timezone.utc),{'net':.1},{'net':self.c('NET_EXPECTANCY')},'t','v',None,{'n':1},{},{},{},ExperimentStage.OUT_OF_SAMPLE,(),(),(),(),(metric,));self.assertEqual(result.canonical_metrics,(metric,))
 def test_runtime_and_broker_unchanged(self):
  self.assertFalse(hasattr(METRIC_REGISTRY,'optimize'))
  with self.assertRaises(LiveExecutionDisabled):PaperExecutionProvider().submit_order({})
if __name__=='__main__':unittest.main()
