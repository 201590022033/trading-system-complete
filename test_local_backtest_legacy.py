"""Frozen replay comparison: entry/exit agree; account costs have distinct units."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import unittest
from test_swing_policy import fixture, clock
from domain.policy.swing_shadow import build_policy, simulate
from domain.backtest.data import Manifest, Session, Bar
from domain.backtest.legacy import from_frozen_policy
from domain.backtest.engine import replay, Costs

class LocalLegacyTests(unittest.TestCase):
    def test_frozen_long_geometry_and_horizons_reconcile(self):
        features,chart,decision=fixture()
        policy=build_policy(features,decision_at=decision.isoformat())
        sessions=[]; bars=[]
        for row in chart['bars']:
            day=datetime.fromisoformat(row['timestamp']).replace(tzinfo=timezone.utc)
            # Synthetic times mirror the old helper; this is not a JSE calendar.
            available=clock({'bars':[row]})
            sessions.append(Session(row['timestamp'],day+timedelta(hours=7),day+timedelta(hours=15)))
            bars.append(Bar(row['timestamp'],available,*(D(str(row[k])) for k in ('open','high','low','close')),D(1000)))
        m=Manifest(chart['symbol'],'EQUITY','ZAR','SYNTHETIC_LEGACY_FIXTURE',clock(chart),'RAW','TRADED_SHARES',
                   'TOY',True,'SYNTHETIC','FIXED_TOY','NONE_VERIFIED','1',tuple(sessions),tuple(bars))
        for h in (3,4,5):
            legacy=simulate(policy,chart,evaluated_at=clock(chart).isoformat(),horizon_sessions=h)
            s=from_frozen_policy(policy,m,max_notional=2000,risk_budget=100,horizon=h)
            r=replay((m,),(s,),as_of=clock(chart),initial_cash=5000,costs=Costs())
            trade=r['trades'][0]
            self.assertEqual(D(trade['entry']),D(legacy['entry_price']))
            self.assertEqual(D(trade['exit']),D(legacy['exit_price']))
            self.assertEqual(trade['held'],legacy['held_observed_sessions'])
            self.assertEqual(trade['reason'],legacy['reason'])
        with self.assertRaises(ValueError): from_frozen_policy({**policy,'policy_version':'changed'},m,max_notional=100,risk_budget=10)

if __name__=='__main__': unittest.main()
