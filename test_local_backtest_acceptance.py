"""Final independent audit fixtures: split orders, portfolio stress and event safety."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D
import unittest
from domain.backtest.engine import replay,Costs,Action
from domain.backtest.selection import select
from research.fixtures.daily_oracle import fixture
from test_local_backtest_engine import signal,run

class LocalAcceptanceTests(unittest.TestCase):
    def test_pending_order_split_and_raw_input_preserved(self):
        m=fixture([(100,101,99,100),(50,51.5,49.5,51),(51,53,50,52),(52,54,51,53),(53,55,52,54)])
        m=replace(m,action_basis='EXPLICIT'); before=m.sha256
        r=run(m,actions=(Action('TOY','1',D(2)),)); t=r['trades'][0]
        self.assertEqual(D(t['entry']),51); self.assertEqual(D(t['quantity']),20)
        self.assertEqual(D(r['cash']),2056); self.assertEqual(m.sha256,before)

    def test_split_trail_uses_rebased_prior_history(self):
        m=fixture([(100,101,99,100),(100,103,99,102),(51,57,50,56),(56,58,55,57),(57,59,56,58)])
        m=replace(m,action_basis='EXPLICIT')
        s=signal(m,trail='ATR',atr_period=1,trail_k=D('.5'),target_r=None)
        r=run(m,s,actions=(Action('TOY','2',D(2)),))
        trail=[x for x in r['decisions'] if x['state']=='TRAIL_NEXT_SESSION'][0]
        # Prior entry close rebased 102/2=51; range=max(7,6,1)=7.
        # Activation 56-51 >= R6 is false; next close57 activates with ATR3.
        self.assertEqual(D(trail['stop']),D('55.5')); self.assertEqual(r['trades'][0]['reason'],'HORIZON_CLOSE')

    def test_expiry_censoring_and_daily_bounds(self):
        m=fixture(); s=replace(signal(m),expiry_days=1)
        self.assertEqual(run(m,s)['trades'],[])
        self.assertIn('EXPIRED',[x['state'] for x in run(m,s)['decisions']])
        r=run(); t=r['trades'][0]
        self.assertEqual(D(t['favorable_daily_range_r_bound']),D(5)/12)
        self.assertEqual(D(t['adverse_daily_range_r_bound']),D(1)/12)
        self.assertIn('ORDER_UNKNOWN',t['excursion_basis'])

    def test_equal_time_cross_asset_sale_proceeds_and_cost_stress(self):
        m=fixture(); other=replace(m,instrument='OTHER')
        s1=replace(signal(m),max_notional=D(1500))
        s2=replace(signal(other),id='later',session='4',decision_at=m.sessions[4].close_at,max_notional=D(1500))
        prices=[(100,101,99,100),(100,103,99,102),(102,105,101,104),(104,106,103,105),(105,107,104,106),
                (106,108,105,107),(107,109,106,108),(108,110,107,109),(109,111,108,110)]
        m=fixture(prices); other=replace(m,instrument='OTHER')
        r=replay((m,other),(s1,s2),as_of=m.sessions[8].close_at,initial_cash=2000,costs=Costs(minimum_fee=2))
        self.assertEqual(len(r['trades']),2); self.assertTrue(all(D(x['cash'])>=0 for x in r['ledger']))
        values=[]
        for bps in (0,25,100):
            cost=Costs(fee_bps=bps,spread_bps=bps,slippage_bps=bps)
            one=replay((m,),(replace(s1,risk_budget=D(10000),max_notional=D(1100)),),as_of=m.sessions[4].close_at,initial_cash=2000,costs=cost)
            values.append(D(one['trades'][0]['net_pnl']))
            self.assertEqual(D(one['trades'][0]['quantity']),10)
        self.assertGreater(values[0],values[1]); self.assertGreater(values[1],values[2])

    def test_selection_uses_net_expectancy_and_unresolved_is_unavailable(self):
        def report(value): return {'horizons':{'3':{'selected':{'net_expectancy':value}}}}
        self.assertEqual(select({'high_win_low_net':report(-.01),'lower_win_positive_net':report(.02)}),'lower_win_positive_net')
        self.assertIsNone(select({'empty':report(None)}))

if __name__=='__main__': unittest.main()
