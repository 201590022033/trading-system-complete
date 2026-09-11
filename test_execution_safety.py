import inspect,unittest
from dataclasses import FrozenInstanceError,replace
from datetime import datetime,timezone
from types import MappingProxyType

from domain.broker.execution_safety import *
from domain.broker.reconciliation import AccountComparison,BrokerReconciliationResult
from domain.broker.state import BrokerAccountState,BrokerPositionState,BrokerStateSnapshot,Freshness
from domain.risk import RiskStatus

NOW=datetime(2026,9,11,12,tzinfo=timezone.utc)
def snapshot(*,enabled=True,available=True,fresh=Freshness.FRESH,positions=()):
    a=BrokerAccountState("IG","DEMO","ACC",None,"CFD",True,"USD",1000,None,700,None,None,None,None,None,None,"ENABLED" if enabled else "DISABLED",enabled,NOW,fresh)
    return BrokerStateSnapshot("IG","DEMO",a,tuple(positions),available,len(positions),NOW,fresh)
def position(direction="LONG",mapping="RESOLVED"):
    return BrokerPositionState("IG","DEMO","ACC","D1","BRENT" if mapping=="RESOLVED" else None,mapping,"EPIC","EPIC",direction,1,75,76,70,85,None,"USD",NOW,NOW,1,"USD","TRADEABLE")
def reconciliation(critical=0,warning=0):
    return BrokerReconciliationResult("R","broker-reconciliation-v1",NOW,"IG:DEMO","PAPER:PAPER",AccountComparison((),()),(),(),MappingProxyType({"INFO":0,"WARNING":warning,"CRITICAL":critical}),not critical and not warning,(),"read-only")
def context(**changes):
    values=dict(broker="IG",environment="DEMO",account_id="ACC",order_intent_id="OI",intent_id="TI",instrument_id="BRENT",execution_symbol="EPIC",epic="EPIC",direction="LONG",opportunity_id="OPP",policy_id="POL",policy_opportunity_id="OPP",policy_instrument_id="BRENT",policy_status="READY_FOR_RISK_REVIEW",stop_price=70.,stop_distance=5.,risk_evaluation_id="RISK",risk_policy_id="POL",risk_instrument_id="BRENT",risk_status=RiskStatus.APPROVED,approved_size=1.,approved_loss_budget=5.,account_state=snapshot(),reconciliation=reconciliation(),market_status="TRADEABLE",market_data_fresh=True,broker_submission_capability=True,duplicate_intent=False,kill_switch_active=False,account_currency="USD",price_currency="USD",fx_available=None,margin_required=False,margin_metadata_available=False,provenance_versions=("opp-v1","policy-v1","risk-v1","intent-v1"),expected_provenance_versions=("opp-v1","policy-v1","risk-v1","intent-v1"));values.update(changes);return ExecutionSafetyContext(**values)
def config(**changes):
    values=dict(execution_enabled=True,human_permission=True,warning_discrepancies_block=True,same_direction_position_blocks=True);values.update(changes);return ExecutionSafetyConfig(**values)

class SafetyTests(unittest.TestCase):
    def check(self,result,name):return next(x for x in result.checks if x.check_id==name)
    def test_complete_hypothetical_context_passes_but_submits_nothing(self):
        result=evaluate_safety(context(),config(),NOW);self.assertTrue(result.eligible_for_submission);self.assertEqual(result.status,CheckStatus.PASS);self.assertIn("never an order",result.provenance)
    def test_live_and_non_ig_fail_demo_gate(self):
        for change in ({"environment":"LIVE"},{"broker":"PAPER"}):self.assertEqual(self.check(evaluate_safety(context(**change),config(),NOW),"demo_environment").status,CheckStatus.FAIL)
    def test_flags_and_human_permission_fail_closed(self):
        self.assertEqual(self.check(evaluate_safety(context(),config(execution_enabled=False),NOW),"execution_feature_flag").status,CheckStatus.FAIL)
        self.assertEqual(self.check(evaluate_safety(context(),config(execution_enabled=None),NOW),"execution_feature_flag").status,CheckStatus.NOT_CONFIGURED)
        self.assertEqual(self.check(evaluate_safety(context(),config(human_permission=None),NOW),"human_permission").status,CheckStatus.NOT_CONFIGURED)
    def test_risk_size_budget_policy_and_stop(self):
        cases=[("risk_approval",dict(risk_status=RiskStatus.REJECTED)),("approved_size",dict(approved_size=None)),("approved_loss_budget",dict(approved_loss_budget=None)),("policy_resolved",dict(policy_status="UNRESOLVED")),("stop_resolved",dict(stop_price=None))]
        for name,change in cases:self.assertNotEqual(self.check(evaluate_safety(context(**change),config(),NOW),name).status,CheckStatus.PASS)
    def test_account_positions_and_zero_position_semantics(self):
        self.assertNotEqual(self.check(evaluate_safety(context(account_state=None),config(),NOW),"account_enabled").status,CheckStatus.PASS)
        self.assertEqual(self.check(evaluate_safety(context(account_state=snapshot(enabled=False)),config(),NOW),"account_enabled").status,CheckStatus.FAIL)
        self.assertEqual(self.check(evaluate_safety(context(account_state=snapshot(available=False)),config(),NOW),"positions_available").status,CheckStatus.FAIL)
        self.assertEqual(self.check(evaluate_safety(context(account_state=snapshot()),config(),NOW),"positions_available").status,CheckStatus.PASS)
    def test_reconciliation_critical_warning_and_missing(self):
        self.assertEqual(self.check(evaluate_safety(context(reconciliation=reconciliation(critical=1)),config(),NOW),"reconciliation_clean").status,CheckStatus.FAIL)
        self.assertEqual(self.check(evaluate_safety(context(reconciliation=None),config(),NOW),"reconciliation_clean").status,CheckStatus.UNRESOLVED)
        self.assertEqual(self.check(evaluate_safety(context(reconciliation=reconciliation(warning=1)),config(warning_discrepancies_block=None),NOW),"reconciliation_clean").status,CheckStatus.NOT_CONFIGURED)
    def test_mapping_market_and_freshness(self):
        for name,change in [("instrument_mapping",dict(epic=None)),("market_state",dict(market_status="CLOSED")),("stale_market_data",dict(market_data_fresh=False)),("broker_state_freshness",dict(account_state=snapshot(fresh=Freshness.STALE)))]:self.assertNotEqual(self.check(evaluate_safety(context(**change),config(),NOW),name).status,CheckStatus.PASS)
    def test_duplicate_position_conflict_and_reversal(self):
        self.assertEqual(self.check(evaluate_safety(context(duplicate_intent=True),config(),NOW),"duplicate_pending").status,CheckStatus.FAIL)
        opposing=snapshot(positions=(position("SHORT"),));self.assertEqual(self.check(evaluate_safety(context(account_state=opposing),config(),NOW),"position_conflict").status,CheckStatus.FAIL)
        same=snapshot(positions=(position("LONG"),));self.assertEqual(self.check(evaluate_safety(context(account_state=same),config(same_direction_position_blocks=None),NOW),"position_conflict").status,CheckStatus.NOT_CONFIGURED)
    def test_kill_switch_fx_margin_and_provenance(self):
        cases=[("kill_switch",dict(kill_switch_active=True)),("account_currency",dict(price_currency="ZAR",fx_available=False)),("margin_metadata",dict(margin_required=True)),("provenance_integrity",dict(risk_policy_id="OTHER")),("provenance_integrity",dict(expected_provenance_versions=("other",)))]
        for name,change in cases:self.assertNotEqual(self.check(evaluate_safety(context(**change),config(),NOW),name).status,CheckStatus.PASS)
    def test_all_checks_auditable_and_decision_immutable(self):
        result=evaluate_safety(context(),config(),NOW);self.assertEqual(len({x.check_id for x in result.checks}),len(result.checks));self.assertGreaterEqual(len(result.checks),20)
        with self.assertRaises(FrozenInstanceError):result.eligible_for_submission=False
    def test_current_capability_and_unresolved_chain_remain_non_executable(self):
        from domain.broker.ig import IGConfig,IGReadOnlyAdapter
        adapter=IGReadOnlyAdapter(IGConfig("k","u","p"),lambda *x:None);self.assertFalse(adapter.capabilities()["order_submission"])
        result=evaluate_safety(context(broker_submission_capability=False,policy_status="UNRESOLVED",stop_price=None,stop_distance=None,risk_status=RiskStatus.UNRESOLVED,approved_size=None,approved_loss_budget=None),ExecutionSafetyConfig(),NOW);self.assertFalse(result.eligible_for_submission)
    def test_no_transport_payload_or_execution_route(self):
        source=inspect.getsource(__import__("domain.broker.execution_safety",fromlist=["x"]));
        for forbidden in ("_request(","urlopen","place_order","close_position","amend_order","cancel_order"):self.assertNotIn(forbidden,source)

if __name__=="__main__":unittest.main()
