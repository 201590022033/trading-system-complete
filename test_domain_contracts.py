import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

from domain.contracts import (CanonicalBar, CandidateTradePolicy, DataGrade,
                              Direction, EntryPolicyType, ExitPolicyType,
                              MetricContext, StopPolicyType, SourcePolicy,
                              TradeGeometry, TradeIntent)


UTC = timezone.utc


def source():
    return SourcePolicy("fixture", 2, "licensed", DataGrade.RESEARCH, 300, "RESEARCH")


def bar():
    start = datetime(2026, 1, 1, 9, tzinfo=UTC)
    return CanonicalBar("NPN", "1d", start, start + timedelta(days=1),
                        start + timedelta(days=1, minutes=1), 10, 12, 9, 11,
                        100, 10.9, 11.1, source(), ("row-1",))


class DomainContractTests(unittest.TestCase):
    def test_bar_serialization_round_trip_and_enum_serialization(self):
        restored = CanonicalBar.from_dict(bar().to_dict())
        self.assertEqual(restored, bar())
        self.assertEqual(bar().to_dict()["source_policy"]["data_grade"], "RESEARCH_DATA")

    def test_naive_canonical_bar_timestamp_rejected(self):
        with self.assertRaises(ValueError):
            replace(bar(), interval_start=datetime(2026, 1, 1, 9))

    def test_bar_causal_order_rejected(self):
        with self.assertRaises(ValueError):
            replace(bar(), available_time=bar().event_time - timedelta(seconds=1))

    def test_contracts_are_frozen(self):
        with self.assertRaises(FrozenInstanceError):
            bar().close = 12

    def test_policy_parameters_and_regime_are_defensively_immutable(self):
        policy = CandidateTradePolicy("p1", "v1", EntryPolicyType.MARKET,
                                      StopPolicyType.FIXED_DISTANCE,
                                      ExitPolicyType.FIXED_TARGET, {"risk": 1})
        with self.assertRaises(TypeError):
            policy.parameters["risk"] = 2
        geometry = TradeGeometry(policy, 10, 9, 9, 12, 3600, None, None,
                                 datetime(2026, 1, 2, tzinfo=UTC))
        intent = TradeIntent("i1", "legacy-v1", "NPN", "NPN", datetime.now(UTC),
                             Direction.LONG, .5, 1, {"trend": "bull"}, geometry,
                             1, 10, .1, ("rsi",), ("e1",), datetime.now(UTC) + timedelta(hours=1))
        with self.assertRaises(TypeError):
            intent.regime_snapshot["trend"] = "bear"

    def test_trade_intent_bounds_and_expiry(self):
        policy = CandidateTradePolicy("p1", "v1", EntryPolicyType.MARKET,
                                      StopPolicyType.FIXED_DISTANCE,
                                      ExitPolicyType.FIXED_TARGET, {})
        geometry = TradeGeometry(policy, 10, 9, 9, 12, 3600, None, None,
                                 datetime(2026, 1, 2, tzinfo=UTC))
        with self.assertRaises(ValueError):
            TradeIntent("i1", "v1", "NPN", "NPN", datetime(2026, 1, 1, tzinfo=UTC),
                        Direction.LONG, 1.1, 1, {}, geometry, 1, 10, 0, (), (),
                        datetime(2026, 1, 1, tzinfo=UTC))

    def test_metric_context_validation(self):
        self.assertEqual(MetricContext("PERIODIC_CALENDAR", "1d", "JSE", 252).annualization_factor, 252)
        with self.assertRaises(ValueError):
            MetricContext("invalid", "1d", "JSE", 252)


if __name__ == "__main__":
    unittest.main()
