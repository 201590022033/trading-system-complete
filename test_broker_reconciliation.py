import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from domain.broker.reconciliation import *
from domain.broker.state import BrokerAccountState,BrokerPositionState,BrokerStateSnapshot,Freshness

NOW=datetime(2026,9,11,12,tzinfo=timezone.utc)
def broker_position(**changes):
    values=dict(broker="IG",environment="DEMO",account_id="ACC",broker_position_id="D1",instrument_id="BRENT",mapping_status="RESOLVED",epic="EPIC.BRENT",execution_symbol="EPIC.BRENT",direction="LONG",quantity=2.,open_level=75.,current_level=76.,stop_level=70.,limit_level=85.,unrealized_pnl=2.,pnl_currency="USD",opened_at=NOW,retrieved_at=NOW,contract_size=1.,currency="USD",market_status="TRADEABLE");values.update(changes);return BrokerPositionState(**values)
def broker(positions=(),fresh=Freshness.FRESH,available=True):
    account=BrokerAccountState("IG","DEMO","ACC","Demo","CFD",True,"USD",1000.,None,700.,250.,-50.,None,None,None,None,"ENABLED",True,NOW,fresh)
    return BrokerStateSnapshot("IG","DEMO",account,tuple(positions),available,len(positions),NOW,fresh)
def internal_position(**changes):
    values=dict(internal_position_id="I1",broker_position_id="D1",instrument_id="BRENT",epic="EPIC.BRENT",direction="LONG",quantity=2.,quantity_unit="CONTRACT",open_level=75.,stop_level=70.,limit_level=85.,unrealized_pnl=2.,pnl_currency="USD");values.update(changes);return InternalPositionSnapshot(**values)
def internal(positions=(),fresh=Freshness.FRESH,available=True,currency="USD"):
    account=InternalAccountSnapshot("PAPER","PAPER","PAPER",currency,None,None,None,NOW,fresh,"paper-broker-v1")
    return ReconciliationSnapshot("PAPER","PAPER",account,tuple(positions),available,NOW,fresh,"paper-broker-v1")
def config(**changes):
    values=dict(quantity_tolerance=0.,entry_level_tolerance=0.,account_value_tolerance=0.,pnl_tolerance=0.,max_snapshot_skew_seconds=0.,quantity_units={"EPIC.BRENT":"CONTRACT"});values.update(changes);return ReconciliationConfig(**values)

class ReconciliationTests(unittest.TestCase):
    def kinds(self,result):return {d.discrepancy_type for d in result.discrepancies}
    def test_clean_and_zero_positions(self):
        self.assertTrue(reconcile(broker(),internal(),config(),NOW).clean)
        result=reconcile(broker((broker_position(),)),internal((internal_position(),)),config(),NOW);self.assertTrue(result.clean);self.assertEqual(result.position_comparisons[0].match_basis,"DEAL_ID")
    def test_broker_and_internal_only_positions(self):
        self.assertIn(DiscrepancyType.BROKER_ONLY_POSITION,self.kinds(reconcile(broker((broker_position(),)),internal(),config(),NOW)))
        self.assertIn(DiscrepancyType.INTERNAL_ONLY_POSITION,self.kinds(reconcile(broker(),internal((internal_position(),)),config(),NOW)))
    def test_direction_quantity_and_entry_mismatches(self):
        local=internal_position(direction="SHORT",quantity=3,open_level=74)
        kinds=self.kinds(reconcile(broker((broker_position(),)),internal((local,)),config(),NOW));self.assertTrue({DiscrepancyType.DIRECTION_MISMATCH,DiscrepancyType.QUANTITY_MISMATCH,DiscrepancyType.ENTRY_LEVEL_MISMATCH}<=kinds)
    def test_unresolved_mapping_is_retained(self):
        bp=broker_position(instrument_id=None,mapping_status="UNRESOLVED_INSTRUMENT_MAPPING")
        self.assertIn(DiscrepancyType.INSTRUMENT_MAPPING_UNRESOLVED,self.kinds(reconcile(broker((bp,)),internal((internal_position(),)),config(),NOW)))
    def test_currency_mismatch_and_only_explicit_account_semantics(self):
        result=reconcile(broker(),internal(currency="ZAR"),config(),NOW);self.assertIn(DiscrepancyType.ACCOUNT_CURRENCY_MISMATCH,self.kinds(result));self.assertNotIn("balance",result.account_comparison.compared_fields)
        aligned=config(account_comparisons=(("account_currency","currency"),("available_funds","available_funds")))
        self.assertIn(DiscrepancyType.FIELD_UNAVAILABLE,self.kinds(reconcile(broker(),internal(),aligned,NOW)))
    def test_unavailable_is_not_flat(self):
        self.assertIn(DiscrepancyType.BROKER_UNAVAILABLE,self.kinds(reconcile(None,internal(),config(),NOW)))
        self.assertIn(DiscrepancyType.BROKER_UNAVAILABLE,self.kinds(reconcile(broker(available=False),internal(),config(),NOW)))
    def test_stale_states(self):
        self.assertIn(DiscrepancyType.STALE_BROKER_SNAPSHOT,self.kinds(reconcile(broker(fresh=Freshness.STALE),internal(),config(),NOW)))
        self.assertIn(DiscrepancyType.STALE_INTERNAL_SNAPSHOT,self.kinds(reconcile(broker(),internal(fresh=Freshness.STALE),config(),NOW)))
    def test_epic_fallback_is_exact_and_fuzzy_matching_absent(self):
        local=internal_position(broker_position_id=None);result=reconcile(broker((broker_position(),)),internal((local,)),config(),NOW);self.assertEqual(result.position_comparisons[0].match_basis,"EPIC_ACCOUNT_DIRECTION")
        fuzzy=internal_position(broker_position_id=None,epic="EPIC.BREN",instrument_id="OTHER");self.assertIn(DiscrepancyType.BROKER_ONLY_POSITION,self.kinds(reconcile(broker((broker_position(),)),internal((fuzzy,)),config(),NOW)))
    def test_units_required_and_tolerances_are_configurable(self):
        no_units=config(quantity_units={});result=reconcile(broker((broker_position(),)),internal((internal_position(quantity=99),)),no_units,NOW);self.assertIn(DiscrepancyType.SEMANTICALLY_NOT_COMPARABLE,self.kinds(result));self.assertNotIn(DiscrepancyType.QUANTITY_MISMATCH,self.kinds(result))
        tolerant=config(quantity_tolerance=1.1,entry_level_tolerance=2.);self.assertTrue(reconcile(broker((broker_position(),)),internal((internal_position(quantity=3,open_level=76),)),tolerant,NOW).clean)
    def test_pnl_requires_aligned_currency(self):
        result=reconcile(broker((broker_position(),)),internal((internal_position(pnl_currency="ZAR"),)),config(),NOW);self.assertIn(DiscrepancyType.SEMANTICALLY_NOT_COMPARABLE,self.kinds(result))
    def test_result_is_immutable_and_sources_are_retained(self):
        result=reconcile(broker(),internal(),config(),NOW);self.assertIn("IG:DEMO",result.broker_snapshot_reference);self.assertIn("PAPER:PAPER",result.internal_snapshot_reference)
        with self.assertRaises(FrozenInstanceError):result.clean=False
    def test_inputs_not_mutated_and_no_execution_surface(self):
        b=broker((broker_position(),));i=internal((internal_position(),));before=(b,i);reconcile(b,i,config(),NOW);self.assertEqual(before,(b,i))
        for name in ("place_order","close_position","amend_order","repair","sync"):self.assertFalse(hasattr(__import__("domain.broker.reconciliation",fromlist=[name]),name))

if __name__=="__main__":unittest.main()
