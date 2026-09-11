import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from domain.contracts.trade import MetricContext
from domain.evaluation.experiment import *
from provider_interfaces import PaperExecutionProvider,LiveExecutionDisabled

class ExperimentRegistryTests(unittest.TestCase):
 def setUp(self):
  self.t=datetime(2026,9,11,tzinfo=timezone.utc); self.repo=InMemoryExperimentRepository()
  self.bound=DataBoundary('ds','v1','RESEARCH_DATA',self.t+timedelta(days=30),self.t-timedelta(days=30),self.t-timedelta(days=10),oos_start=self.t,oos_end=self.t+timedelta(days=20),provenance='frozen artifact')
  self.definition=ExperimentDefinition('e1','v1',self.t,'operator',ExperimentMode.CONFIRMATORY,'daily',('SOL',),('daily_1d',),'base-a','v1','abc',(),('metric:a',),'weak net return',('report:a',),'adding divergence improves OOS net return','independent disagreement evidence','OOS net expectancy rises','add divergence feature',('divergence',),'div-v1',configuration_hash({'weight':.1}),('signal threshold','cost model'),'base-a','target-a','v1',('NET_EXPECTANCY',),(self.bound,))
  self.run=ExperimentRun('run1','e1','v1',self.t+timedelta(hours=1),self.t+timedelta(hours=2),'abc','code-v1','local',{'ds':'v1'},('f1',),'r1','c1',7,configuration_hash({'weight':.1}),self.t+timedelta(days=30),ExperimentStage.OUT_OF_SAMPLE)
  self.ctx=MetricContext('TRADE_BY_TRADE','variable','JSE',None,'DECIMAL_RETURN','NET','MODELED_BASE','daily_1d','STRATEGY',False,None)
  self.result=ExperimentResult('res1','run1',self.t+timedelta(hours=3),{'net':-.01},{'net':self.ctx},'target-a','v1','assessment-1',{'trades':20},{'ci':'wide'},{'bull':-.01},{'stress':-.02},ExperimentStage.OUT_OF_SAMPLE,(),('negative expectancy',),('small sample',),('research data',))
 def ready(self): self.repo.register_definition(self.definition); self.repo.record_run(self.run); self.repo.record_result(self.result)
 def test_definition_registration_identity_baseline_and_preregistration(self):
  self.assertEqual(self.repo.register_definition(self.definition),self.definition); self.assertEqual(self.repo.list_experiments()[0].baseline_id,'base-a')
  with self.assertRaises(ValueError): self.repo.register_definition(self.definition)
  with self.assertRaises(ValueError): self.repo.record_run(replace(self.run,started_at=self.t-timedelta(seconds=1)))
 def test_one_treatment_and_factorial_rules(self):
  with self.assertRaises(ValueError): replace(self.definition,changed_components=('a','b'))
  design=FactorialDesign((Factor('a',('off','on')),Factor('b',('low','high'))),'estimate interactions','balanced cells')
  self.assertEqual(len(replace(self.definition,changed_components=('a','b'),factorial_design=design).changed_components),2)
 def test_retrospective_label_allows_historical_run(self):
  d=replace(self.definition,mode=ExperimentMode.RETROSPECTIVE); self.repo.register_definition(d)
  self.repo.record_run(replace(self.run,started_at=self.t-timedelta(days=2),completed_at=self.t-timedelta(days=1)))
 def test_run_provenance_hash_and_secrets(self):
  self.repo.register_definition(self.definition); self.repo.record_run(self.run); self.assertEqual(self.run.dataset_versions['ds'],'v1')
  self.assertEqual(configuration_hash({'a':1}),configuration_hash({'a':1}))
  with self.assertRaises(ValueError): configuration_hash({'password':'x'})
 def test_result_context_target_and_append_only(self):
  self.ready(); self.assertEqual(self.repo.get_experiment('e1','v1')['results'][0].metric_contexts['net'],self.ctx)
  with self.assertRaises(ValueError): self.repo.record_result(self.result)
  with self.assertRaises(ValueError): self.repo.record_result(replace(self.result,result_id='r2',strategy_target_version='v2'))
 def test_negative_rejected_and_inconclusive_evidence_retained(self):
  self.ready(); reject=ExperimentDecision('d1','e1','v1',self.t+timedelta(hours=4),DecisionType.REJECT,'operator','failed target',('res1',),('expectancy',),(),None)
  self.repo.record_decision(reject); self.assertEqual(self.repo.find(decision=DecisionType.REJECT),(self.definition,)); self.assertEqual(self.repo.get_experiment('e1','v1')['results'][0].negative_evidence,('negative expectancy',))
  inc=replace(reject,decision_id='d2',decision=DecisionType.INCONCLUSIVE,rationale='wide interval'); self.repo.record_decision(inc); self.assertEqual(len(self.repo.get_experiment('e1','v1')['decisions']),2)
 def test_accept_next_stage_does_not_promote_and_baseline_requires_decision(self):
  self.ready(); d=ExperimentDecision('d','e1','v1',self.t+timedelta(hours=4),DecisionType.ACCEPT_FOR_NEXT_STAGE,'operator','more validation',('res1',),(),(),ExperimentStage.FORWARD_DEMO,'base-b'); self.repo.record_decision(d)
  self.assertEqual(self.repo.get_lineage('base-b'),(d,)); self.assertFalse(hasattr(self.repo,'promote_runtime'))
  with self.assertRaises(ValueError): replace(d,decision=DecisionType.INCONCLUSIVE)
 def test_changed_scientific_meaning_requires_new_version(self):
  self.repo.register_definition(self.definition)
  with self.assertRaises(ValueError): self.repo.register_definition(replace(self.definition,primary_hypothesis='changed'))
  self.assertEqual(self.repo.register_definition(replace(self.definition,experiment_version='v2',primary_hypothesis='changed')).experiment_version,'v2')
 def test_causal_boundary_and_oos_overlap_validation(self):
  with self.assertRaises(ValueError): replace(self.bound,oos_start=self.bound.train_end)
  d=replace(self.definition,data_boundaries=(replace(self.bound,oos_start=None,oos_end=None),)); self.repo.register_definition(d); self.repo.record_run(self.run)
  with self.assertRaises(ValueError): self.repo.record_result(self.result)
 def test_query_support_and_no_execution(self):
  self.ready(); self.assertEqual(self.repo.find(component='divergence',dataset_version='v1',stage=ExperimentStage.OUT_OF_SAMPLE),(self.definition,))
  with self.assertRaises(LiveExecutionDisabled): PaperExecutionProvider().submit_order({})

if __name__=='__main__': unittest.main()
