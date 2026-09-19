import unittest
from datetime import timedelta
from dataclasses import replace
from test_opportunity_ranking import OpportunityRankingTests
from domain.policy.paper_geometry import resolve_paper_policy


class PaperGeometryTests(unittest.TestCase):
    def setUp(self):
        helper = OpportunityRankingTests()
        helper.setUp()
        self.o = helper.rank_one()
        self.now = helper.now + timedelta(days=1)
        self.rows = tuple((helper.now - timedelta(days=20-i), 90+i*.1) for i in range(20))

    def resolve(self, **changes):
        args = dict(now=self.now, observed_at=self.now, observed_price=100.,
                    prior_closes=self.rows, slippage=.1)
        args.update(changes)
        return resolve_paper_policy(self.o, **args)

    def test_long_geometry_has_loss_side_stop_target_and_no_execution_authority(self):
        p = self.resolve()
        self.assertEqual(p.status, "READY_FOR_RISK_REVIEW")
        self.assertEqual(p.stop_price, 90)
        self.assertGreater(p.target_levels[0], p.entry_price)
        self.assertEqual(p.risk_approval_status, "NOT_EVALUATED")
        self.assertEqual(p.actionability, "NON_EXECUTABLE_RESEARCH_PLAN")
        self.assertTrue(p.provenance["paper_only"])

    def test_short_geometry_and_future_gap_stale_missing_rejected(self):
        self.o = replace(self.o, direction="SHORT")
        rows = tuple((at, price+30) for at, price in self.rows)
        p = self.resolve(prior_closes=rows)
        self.assertGreater(p.stop_price, p.entry_price)
        self.assertLess(p.target_levels[0], p.entry_price)
        for changes in ({"observed_at": self.o.evaluated_at},
                        {"observed_at": self.now + timedelta(seconds=1)},
                        {"prior_closes": rows+((self.now, 500),)},
                        {"prior_closes": ()}, {"observed_price": 150},
                        {"now": self.now+timedelta(days=9)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.resolve(**changes)
