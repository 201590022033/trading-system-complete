"""Independent fee/accounting oracles; no external account or provider access."""
from dataclasses import replace
from decimal import Decimal as D
import unittest

from domain.backtest.costs import OSTCashShareCosts
from domain.backtest.engine import replay, Signal
from research.fixtures.daily_oracle import fixture


class OSTReplayCostsTests(unittest.TestCase):
    def test_asymmetric_fixed_notional_arithmetic(self):
        c=OSTCashShareCosts()
        # 110 + 6.29 + .03 + (16.50 + .94 + .00) + purchase-only 25.
        self.assertEqual(c.fee(10000,1),D('158.76'))
        self.assertEqual(c.fee(10000,-1),D('133.76'))
        self.assertEqual(c.breakdown(10000,-1)['components']['purchase_tax'],'0.00')

    def test_replay_cash_oracle_and_fee_aware_quantity(self):
        m=fixture(); s=Signal('ost-oracle','TOY','0',m.sessions[0].close_at,D(90),D(1100),D(120))
        r=replay((m,),(s,),as_of=m.sessions[4].close_at,initial_cash=2000,costs=OSTCashShareCosts())
        # Nine shares: 918 + (110+6.29+0+2.30+17.44) fits 1100;
        # ten shares: 1020+136.28 exceeds it. Exit 954 -133.73.
        self.assertEqual(r['trades'][0]['quantity'],'9')
        self.assertEqual(r['trades'][0]['fees'],'269.76')
        self.assertEqual(r['cash'],'1766.24')
        self.assertEqual(r['trades'][0]['net_pnl'],'-233.76')
        self.assertEqual(sum(D(x['amount']) for x in r['ledger'])+2000,D(r['cash']))
        self.assertEqual(D(r['equity'][-1]['equity']),D(r['cash']))
        self.assertEqual(r['semantic_hash'],replay((m,),(s,),as_of=m.sessions[4].close_at,initial_cash=2000,costs=OSTCashShareCosts())['semantic_hash'])

    def test_schedule_and_stress_parameters_change_config_hash(self):
        m=fixture(); s=Signal('hash','TOY','0',m.sessions[0].close_at,D(90),D(1100),D(120))
        def run(c): return replay((m,),(s,),as_of=m.sessions[4].close_at,initial_cash=2000,costs=c)
        a=run(OSTCashShareCosts())
        for c in (OSTCashShareCosts(brokerage_rate='.004'),OSTCashShareCosts(spread_bps=10),OSTCashShareCosts(schedule_version='alternative')):
            self.assertNotEqual(a['config_hash'],run(c)['config_hash'])

    def test_product_and_configuration_refusal(self):
        m=fixture()
        for bad in (replace(m,product='FX'),replace(m,currency='USD')):
            with self.assertRaises(ValueError): OSTCashShareCosts().validate((bad,))
        for kwargs in ({'fee_bps':1},{'minimum_fee':1},{'vat_rate':-1},{'strate_maximum':1},{'schedule_version':''}):
            with self.assertRaises(ValueError): OSTCashShareCosts(**kwargs)
        for side in (0,True,2):
            with self.assertRaises(ValueError): OSTCashShareCosts().fee(1000,side)

if __name__=='__main__': unittest.main()
