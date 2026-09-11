import unittest
from pathlib import Path
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from domain.broker.paper import *
from domain.broker.adapter import UnsupportedBrokerCapability
from domain.risk import RiskEvaluation,RiskStatus,ApprovedRiskIntent

class PaperBrokerTests(unittest.TestCase):
 def setUp(self):
  self.t=datetime(2026,9,11,tzinfo=timezone.utc);self.config=PaperExecutionConfig('test',.1,2.,'USD')
  self.b=PaperBroker(10000,self.config)
  ai=ApprovedRiskIntent('policy','SOL',10,1000,0.1,0,100,'USD')
  self.r=RiskEvaluation('risk','v1',self.t,'policy','SOL',RiskStatus.APPROVED,100,.01,None,10,90,'OBSERVED',100,10,1000,.1,0,100,(),(),(),{}, {},ai)
 def intent(self,i='i1',direction='LONG',qty=10,at=None):return CanonicalOrderIntent(i,at or self.t,'PAPER','SOL','SOL.P',direction,qty,'MARKET',None,90,None,'DAY','risk',False,{'fixture':'synthetic'})
 def obs(self,p=100,at=None):return MarketObservation('SOL',p,at or self.t,'synthetic-causal-quote')
 def test_identity_mode_capabilities_and_unsupported(self):
  self.assertEqual((self.b.broker,self.b.mode),('PAPER','PAPER'));self.assertTrue(self.b.capabilities['order_submission']);self.assertFalse(self.b.capabilities['streaming'])
  with self.assertRaises(UnsupportedBrokerCapability):self.b.authenticate()
 def test_risk_gate_missing_size_and_unresolved_current_state(self):
  bad=replace(self.r,status=RiskStatus.UNRESOLVED,approved_loss_budget=None,approved_position_size=None,approved_notional=None,approved_gearing=None,estimated_margin=None,estimated_loss_at_stop=None,approved_intent=None)
  self.assertEqual(self.b.place_order(self.intent(),risk=bad).state,OrderState.REJECTED)
  missing=replace(self.r,approved_position_size=None,approved_intent=replace(self.r.approved_intent,position_size=0))
  # Contract itself prevents approved status from silently carrying missing size.
  self.assertIsNone(missing.approved_position_size);self.assertEqual(self.b.place_order(self.intent('i2'),risk=missing).state,OrderState.REJECTED)
 def test_duplicate_and_no_market_data_pending_cancel(self):
  o=self.b.place_order(self.intent(),risk=self.r);self.assertEqual(o.state,OrderState.PENDING)
  with self.assertRaises(PaperBrokerError):self.b.place_order(self.intent(),risk=self.r)
  self.assertEqual(self.b.cancel_order(o.order_id,self.t).state,OrderState.CANCELLED)
 def test_deterministic_fill_slippage_cost_provenance_and_long(self):
  o=self.b.place_order(self.intent(),risk=self.r,observation=self.obs());f=self.b.fills()[0];self.assertEqual(o.state,OrderState.FILLED);self.assertEqual(f.fill_price,100.1);self.assertEqual(f.slippage,1);self.assertEqual(f.transaction_cost,2);self.assertEqual(f.fill_model_version,'paper-supplied-observation-v1');self.assertEqual(self.b.get_positions()[0].state,PositionState.LONG)
  with self.assertRaises(PaperBrokerError):self.b.cancel_order(o.order_id,self.t)
 def test_short_open_same_direction_increase_and_mark(self):
  b=PaperBroker(10000,self.config);b.place_order(self.intent(direction='SHORT'),risk=self.r,observation=self.obs());b.place_order(self.intent('i2','SHORT',5,self.t+timedelta(minutes=1)),risk=self.r,observation=self.obs(90,self.t+timedelta(minutes=1)));p=b.get_positions()[0];self.assertEqual((p.state,p.quantity),(PositionState.SHORT,15));b.mark(self.obs(80,self.t+timedelta(minutes=2)));self.assertGreater(b.get_account().unrealized_pnl,0)
 def test_partial_reduction_close_realized_and_no_auto_reverse(self):
  self.b.place_order(self.intent(),risk=self.r,observation=self.obs());self.b.place_order(self.intent('reduce','SHORT',4,self.t+timedelta(minutes=1)),risk=self.r,observation=self.obs(110,self.t+timedelta(minutes=1)));self.assertEqual(self.b.get_positions()[0].quantity,6);self.assertGreater(self.b.realized,0)
  rejected=self.b.place_order(self.intent('reverse','SHORT',10,self.t+timedelta(minutes=2)),risk=self.r,observation=self.obs(110,self.t+timedelta(minutes=2)));self.assertEqual(rejected.state,OrderState.REJECTED)
  p=self.b.get_positions()[0];self.b.close_position(p.position_id,observation=self.obs(120,self.t+timedelta(minutes=3)),risk=self.r);self.assertEqual(self.b.get_positions(),());self.assertGreater(self.b.get_account().realized_pnl,0)
 def test_no_observation_no_fill_and_unconfigured_costs_fail(self):
  b=PaperBroker(10000,PaperExecutionConfig('unconfigured',None,None,'USD'));b.place_order(self.intent(),risk=self.r)
  with self.assertRaises(PaperBrokerError):b._fill(next(iter(b._orders.values())),self.intent(),self.obs())
 def test_reconciliation_audit_append_only_and_detects_inconsistency(self):
  self.b.place_order(self.intent(),risk=self.r,observation=self.obs());before=self.b.audit_trail();self.assertTrue(self.b.reconcile(self.t).clean);self.assertEqual(self.b.audit_trail()[:len(before)],before);self.b.cash+=1;self.assertFalse(self.b.reconcile(self.t).clean)
 def test_no_external_adapters_or_gui_controls(self):
  self.assertNotIn('IG',str(self.b.capabilities));html=Path('templates/dashboard.html').read_text(encoding='utf-8').split('canonical-opportunities',1)[1].split('</section>',1)[0].upper();self.assertNotIn('PLACE ORDER',html);self.assertNotIn('TAKE TRADE',html)

if __name__=='__main__':unittest.main()
