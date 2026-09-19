import unittest
from dataclasses import replace
from domain.broker.paper import PaperBroker, PaperExecutionConfig
from domain.risk import RiskStatus
from domain.risk.paper_sizing import size_paper_policy
from application.opportunities.paper_config import PaperLoopConfig
import test_paper_geometry


class PaperSizingTests(unittest.TestCase):
    def setUp(self):
        helper = test_paper_geometry.PaperGeometryTests()
        helper.setUp()
        self.policy, self.now = helper.resolve(), helper.now
        self.config = PaperLoopConfig.load("config/paper.example.json")
        self.broker = PaperBroker(100000, PaperExecutionConfig("test", .1, 5., "ZAR"))

    def size(self, **changes):
        args = dict(now=self.now, broker=self.broker, book={}, config=self.config,
                    peak_equity=100000., daily_loss=0., volume=1e6, sector="TEST")
        args.update(changes)
        return size_paper_policy(self.policy, **args)[1]

    def test_aggression_cost_cash_volume_and_m15_pause(self):
        low = self.size()
        high = self.size(config=replace(self.config, aggression="aggressive"))
        self.assertGreater(high.approved_position_size, low.approved_position_size)
        self.assertLessEqual(high.estimated_loss_at_stop, 500.)
        self.assertLessEqual(high.approved_notional+10, self.broker.cash)
        volume_limited = self.size(volume=2000)
        self.assertLessEqual(volume_limited.approved_position_size, 2)
        self.assertEqual(self.size(paused=True).status, RiskStatus.BLOCKED)
        self.assertEqual(self.size(volume=None).status, RiskStatus.UNRESOLVED)
        self.assertEqual(self.size(daily_loss=1000).status, RiskStatus.REJECTED)
        self.assertEqual(self.size(daily_loss=999).status, RiskStatus.REJECTED)
        self.broker.cash = 1
        self.assertNotIn(self.size().status, {RiskStatus.APPROVED, RiskStatus.REDUCED})

    def test_real_modes_unset_limits_and_unbounded_aggression_rejected(self):
        for changes in ({"mode": "LIVE"}, {"mode": "DEMO"}, {"aggression": "unlimited"},
                        {"limits": {**self.config.limits, "max_gearing": None}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.config, **changes)
