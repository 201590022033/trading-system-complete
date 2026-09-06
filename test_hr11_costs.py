import unittest
from dataclasses import replace
from intraday_instruments import DEFAULT_REGISTRY
from intraday_costs import CostSchedule,transition_cost
INSTRUMENT=replace(DEFAULT_REGISTRY.get('SOL_CASH'),tick_size=.01,lot_size=1,minimum_trade_size=1,supports_short=True)
SCHEDULE=CostSchedule('fixture','SOL_CASH','ZAR',10,2,20,1,0.1,1,.1,.2,('TEST FIXTURE ONLY',))
class CostTests(unittest.TestCase):
    def test_entry_hold_exit_reversal(self):
        entry=transition_cost(INSTRUMENT,SCHEDULE,0,10,100)
        self.assertEqual(entry.turnover_units,10);self.assertAlmostEqual(entry.total,5.1)
        self.assertEqual(transition_cost(INSTRUMENT,SCHEDULE,10,10,100).total,0)
        self.assertEqual(transition_cost(INSTRUMENT,SCHEDULE,10,0,100).total,entry.total)
        reversal=transition_cost(INSTRUMENT,SCHEDULE,10,-10,100)
        self.assertEqual(reversal.turnover_units,20);self.assertAlmostEqual(reversal.total,7.2)
    def test_contract_ticks_and_financing(self):
        instrument=replace(INSTRUMENT,contract_multiplier=10,financing_applicable=True)
        held=transition_cost(instrument,SCHEDULE,10,10,100,365*86400)
        self.assertEqual(held.total,1000)
        self.assertEqual(transition_cost(instrument,SCHEDULE,-10,-10,100,365*86400).total,2000)
        self.assertEqual(transition_cost(instrument,SCHEDULE,0,10,100).components['slippage'],1)
    def test_unknowns_and_mismatches(self):
        self.assertFalse(transition_cost(DEFAULT_REGISTRY.get('GOLD_PROXY'),None,0,1,100).available)
        self.assertIn('COST_CURRENCY_MISMATCH',transition_cost(INSTRUMENT,replace(SCHEDULE,currency='USD'),0,1,100).reasons)
        self.assertIn('INVALID_LOT_SIZE',transition_cost(INSTRUMENT,SCHEDULE,0,.5,100).reasons)
        with self.assertRaises(ValueError):replace(SCHEDULE,spread_bps=float('nan'))
        with self.assertRaises(ValueError):replace(SCHEDULE,assumptions=())
    def test_minimum_zero_costs_and_rounding(self):
        self.assertEqual(transition_cost(INSTRUMENT,SCHEDULE,0,1,100).components['commission'],2)
        self.assertEqual(transition_cost(INSTRUMENT,replace(SCHEDULE,slippage_ticks=.1),0,1,100).components['slippage'],.01)
