"""Hand arithmetic and adversarial execution tests for isolated local replay."""
from dataclasses import replace
from decimal import Decimal as D
from itertools import product
import unittest
from domain.backtest.engine import replay, Signal, Costs, Action, atr
from research.fixtures.daily_oracle import fixture, ORACLE


def signal(m, **kw):
    return Signal('s1',m.instrument,'0',m.sessions[0].close_at,D(90),D(1100),D(120),**kw)


def run(m=None, s=None, **kw):
    m=m or fixture()
    return replay((m,), (s or signal(m),), as_of=m.sessions[len(m.bars)-1].close_at,
                  initial_cash=2000, costs=Costs(minimum_fee=2), **kw)

class LocalReplayTests(unittest.TestCase):
    def test_independent_cash_oracle_and_reconciliation(self):
        r=run(); t=r['trades'][0]
        self.assertEqual(D(t['entry']),ORACLE['entry']); self.assertEqual(D(t['exit']),ORACLE['exit'])
        self.assertEqual(D(t['quantity']),ORACLE['quantity']); self.assertEqual(t['held'],ORACLE['held'])
        self.assertEqual(D(r['cash']),ORACLE['final_cash']); self.assertEqual(D(t['net_pnl']),36)
        self.assertEqual(sum(D(x['amount']) for x in r['ledger'])+2000,D(r['cash']))
        self.assertEqual(r,run()); self.assertFalse(r['execution_enabled'])

    def test_stop_target_gap_and_daily_ambiguity(self):
        for row,price,reason in [((102,130,89,100),90,'AMBIGUOUS_STOP_FIRST'),
                                ((85,95,80,90),85,'GAP_STOP'),((130,132,80,100),126,'GAP_TARGET_LIMIT'),
                                ((102,127,100,104),126,'TARGET')]:
            m=fixture(); m=replace(m,bars=m.bars[:2]+(replace(m.bars[2],open=D(row[0]),high=D(row[1]),low=D(row[2]),close=D(row[3])),)+m.bars[3:])
            t=run(m)['trades'][0]; self.assertEqual((D(t['exit']),t['reason']),(price,reason))

    def test_no_pre_entry_fill_and_invalid_geometry(self):
        m=fixture(); m=replace(m,bars=(m.bars[0],replace(m.bars[1],high=D(500)))+m.bars[2:])
        self.assertEqual(run(m)['trades'][0]['reason'],'HORIZON_CLOSE')
        m=replace(m,bars=(m.bars[0],replace(m.bars[1],low=D(89)))+m.bars[2:])
        self.assertEqual(run(m)['trades'],[])
        self.assertIn('INVALIDATED_BEFORE_CLOSE',[x['state'] for x in run(m)['decisions']])
        with self.assertRaises(ValueError): run(m, replace(signal(m),decision_at=m.sessions[0].open_at))

    def test_trail_next_session_and_only_close_activation(self):
        m=fixture([(100,101,99,100),(100,103,99,102),(102,130,91,115),(116,117,108,110),(110,111,100,105)])
        s=signal(m,trail='ATR',atr_period=1,trail_k=D('.1'),target_r=None)
        r=run(m,s); self.assertEqual(r['trades'][0]['exit_session'],'3')
        self.assertEqual(D(r['trades'][0]['exit']),D('111.1'))
        # Day 2 low 91 predates its close-computed stop 111.1, so no same-day fill.
        m=replace(m,bars=m.bars[:2]+(replace(m.bars[2],close=D(110)),)+m.bars[3:])
        self.assertNotIn('TRAIL_NEXT_SESSION',[x['state'] for x in run(m,s)['decisions']])

    def test_competing_reservations_wider_stop_and_cost_components(self):
        m=fixture(); s=signal(m); s2=replace(s,id='s2')
        r=replay((m,),(s2,s),as_of=m.sessions[4].close_at,initial_cash=2000,costs=Costs(minimum_fee=2))
        self.assertEqual([x['state'] for x in r['decisions'][:2]],['RESERVED','CAPITAL_REJECTED'])
        self.assertEqual(r['trades'][0]['id'],'s1')
        wider=replace(s,stop=D(80)); self.assertLess(D(run(m,wider)['trades'][0]['quantity']),D(run(m,s)['trades'][0]['quantity']))
        cost=Costs(fee_bps=10,spread_bps=20,slippage_bps=5)
        r=replay((m,),(s,),as_of=m.sessions[4].close_at,initial_cash=2000,costs=cost)
        self.assertEqual(D(r['trades'][0]['entry']),D('102.1530'))
        self.assertEqual(D(r['trades'][0]['exit']),D('105.8410'))
        self.assertEqual(D(r['trades'][0]['fees']),D('1.87')) # nine units, .92 + .95

    def test_horizons_censoring_future_invariance_and_missing_session(self):
        prices=[(100,101,99,100)]+[(102+i,104+i,101+i,102+i) for i in range(8)]
        m=fixture(prices)
        for h in (3,4,5): self.assertEqual(run(m,signal(m,horizon=h))['trades'][0]['held'],h)
        now=m.sessions[2].close_at
        r=replay((m,),(signal(m),),as_of=now,initial_cash=2000)
        self.assertEqual(r['open_positions'],['TOY']); self.assertEqual(r['trades'],[])
        changed=replace(m,bars=m.bars[:3]+tuple(replace(b,close=D(-1)) for b in m.bars[3:]))
        r2=replay((changed,),(signal(m),),as_of=now,initial_cash=2000)
        for key in ('ledger','decisions','equity','trades'): self.assertEqual(r[key],r2[key])
        with self.assertRaises(ValueError): run(replace(m,bars=m.bars[:2]+m.bars[3:]))

    def test_split_dividend_raw_prices_no_double_counting(self):
        m=fixture([(100,101,99,100),(100,103,99,102),(51,53,50,52),(52,54,51,53),(53,55,52,54)])
        m=replace(m,action_basis='EXPLICIT'); a=Action('TOY','2',D(2),D(1))
        r=run(m,actions=(a,)); t=r['trades'][0]
        self.assertEqual(D(t['quantity']),20); self.assertEqual(D(t['entry']),51)
        self.assertEqual(D(t['distributions']),20); self.assertEqual(D(t['net_pnl']),76)
        self.assertEqual(D(r['cash']),2076)
        with self.assertRaises(ValueError): run(replace(m,price_basis='ADJUSTED'),actions=(a,))

    def test_bounded_toy_paths_cash_and_no_duplicate_fills(self):
        for opens,lows,highs in product((85,102,130),(80,99),(105,135)):
            if not lows<=opens<=highs: continue
            m=fixture(); m=replace(m,bars=m.bars[:2]+(replace(m.bars[2],open=D(opens),low=D(lows),high=D(highs),close=D(opens)),)+m.bars[3:])
            r=run(m)
            self.assertEqual(sum(x['kind']=='ENTRY' for x in r['ledger']),1)
            self.assertEqual(sum(x['kind']=='EXIT' for x in r['ledger']),1)
            self.assertEqual(D(r['cash']),2000+sum(D(x['amount']) for x in r['ledger']))

    def test_atr_fixed_numeric_seeds(self):
        m=fixture(); self.assertEqual(atr(m.bars[:3],2),D(4))
        self.assertEqual(atr(m.bars[:4],2),D('3.5'))
        self.assertIsNone(atr(m.bars[:2],2))

if __name__=='__main__': unittest.main()
