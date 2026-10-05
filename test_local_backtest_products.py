"""Separate FX/gold hand arithmetic; price-only fixtures never inherit volume."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D, localcontext
import unittest
from domain.backtest.engine import replay, Signal, Costs
from domain.backtest.products import Forex, Gold, Conversion, reciprocal_bid_ask, theoretical_rand_gold
from research.fixtures.daily_oracle import fixture


def adapter(cls,m,**kw):
    values=dict(account_currency=m.currency,quote_currency=m.currency,calendar_id=m.calendar_id,sessions=m.sessions,
                conversions=(),long_financing_bps_per_day=D(0),short_financing_bps_per_day=D(0),
                multiplier=D(1),lot=D(1),margin_fraction=D('.1'))
    values.update(kw)
    return cls(**values)


def run(m,s,a,initial=2000):
    return replay((m,),(s,),as_of=m.sessions[len(m.bars)-1].close_at,initial_cash=initial,
                  account_currency=a.account_currency,adapters={m.instrument:a},costs=Costs(minimum_fee=2))

class ForexTests(unittest.TestCase):
    def test_long_short_margin_and_calendar_day_financing(self):
        for side,stop,last,carry,cash in ((1,17,18.5,1,'2045.28'),(-1,19,17.5,2,'2044.56')):
            prices=[(18,18.1,17.9,18),(18,18.2,17.9,18)]
            prices += [(18,18.8,17.2,last)]*3
            m=fixture(prices,'FX'); m=replace(m,bars=tuple(replace(b,activity=None) for b in m.bars))
            a=adapter(Forex,m,long_financing_bps_per_day=D(1),short_financing_bps_per_day=D(2))
            s=Signal('fx',m.instrument,'0',m.sessions[0].close_at,D(stop),D(1000),D(100),side=side)
            r=run(m,s,a); t=r['trades'][0]
            self.assertEqual(D(t['quantity']),100); self.assertEqual(D(r['cash']),D(cash))
            self.assertEqual(D(t['financing']),D('.72') if side==1 else D('1.44'))
            self.assertEqual(t['held'],3)

    def test_short_stop_gaps_target_and_no_share_activity_gate(self):
        for row,price,reason in (((20,21,17,19),20,'GAP_STOP'),((16,20,15,17),16,'GAP_TARGET_LIMIT'),((18,20,15,17),19,'AMBIGUOUS_STOP_FIRST')):
            m=fixture([(18,18.1,17.9,18),(18,18.2,17.9,18),row,(18,18.1,17.9,18),(18,18.1,17.9,18)],'FX')
            a=adapter(Forex,m); s=Signal('fx','TOY','0',m.sessions[0].close_at,D(19),D(1000),D(100),side=-1)
            t=run(m,s,a)['trades'][0]; self.assertEqual((D(t['exit']),t['reason']),(price,reason))
        with self.assertRaises(ValueError): run(replace(m,activity_basis='TRADED_SHARES'),s,a)
        with self.assertRaises(ValueError): run(m,s,replace(a,pair='ZAR/USD'))
        bid,ask=reciprocal_bid_ask(18,20); self.assertEqual(bid,D('.05')); self.assertEqual(ask,D(1)/18)

class GoldTests(unittest.TestCase):
    def test_multiplier_account_conversion_settlement_and_costs(self):
        m=fixture(product='GOLD',currency='USD'); m=replace(m,instrument='XAU/USD')
        conversions=tuple(Conversion(s.key,s.open_at,D(18) if s.key!='4' else D(19)) for s in m.sessions)
        a=adapter(Gold,m,account_currency='ZAR',multiplier=D(10),conversions=conversions)
        s=Signal('gold',m.instrument,'0',m.sessions[0].close_at,D(90),D(20000),D(21600))
        r=run(m,s,a,20000); t=r['trades'][0]
        self.assertEqual(D(t['quantity']),10); self.assertEqual(D(t['net_pnl']),7596)
        self.assertEqual(D(r['cash']),27596)
        self.assertEqual(sum(D(x['amount']) for x in r['ledger'])+20000,D(r['cash']))
        with self.assertRaises(ValueError): run(m,s,replace(a,conversions=()))
        with self.assertRaises(ValueError): replace(a,conversions=(replace(conversions[0],available_at=m.sessions[0].close_at),))
        changed=replace(a,long_financing_bps_per_day=D(1))
        self.assertNotEqual(r['config_hash'],run(m,s,changed,20000)['config_hash'])

    def test_short_gold_and_explicit_future_contract_roll_boundary(self):
        m=fixture([(100,101,99,100),(100,103,99,102),(100,102,97,99),(99,100,96,98),(98,99,95,97)],'GOLD','USD')
        m=replace(m,instrument='GC-TOY-DEC'); a=adapter(Gold,m,vehicle='FUTURE_CONTRACT',contract_id=m.instrument,multiplier=D(10))
        s=Signal('gold',m.instrument,'0',m.sessions[0].close_at,D(114),D(1100),D(1200),side=-1)
        t=run(m,s,a)['trades'][0]; self.assertEqual(D(t['net_pnl']),496)
        with self.assertRaises(ValueError): run(replace(m,instrument='CONTINUOUS_GC'),replace(s,instrument='CONTINUOUS_GC'),a)
        with self.assertRaises(ValueError): run(m,s,replace(a,vehicle='ROLLED_CONTINUOUS'))
        with self.assertRaises(ValueError): run(m,s,replace(a,calendar_id='OTHER_ETF_CALENDAR'))

    def test_theoretical_gold_alignment_and_nonexecution(self):
        m=fixture(); at=m.sessions[0].close_at
        result=theoretical_rand_gold(2000,18,gold_at=at,fx_at=at)
        self.assertEqual(D(result['value']),36000); self.assertFalse(result['executable'])
        with self.assertRaises(ValueError): theoretical_rand_gold(2000,18,gold_at=at,fx_at=at+timedelta(hours=1))
        m=fixture(product='XAU_ZAR_THEORETICAL',currency='USD')
        with self.assertRaises(ValueError): adapter(Gold,m).validate(m)

    def test_replay_decimal_context_is_reproducible(self):
        from test_local_backtest_engine import run as cash_run
        baseline=cash_run()
        with localcontext() as c:
            c.prec=12
            self.assertEqual(baseline,cash_run())

if __name__=='__main__': unittest.main()
