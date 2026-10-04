"""Display estimates preserve actual inputs and cannot resolve shadow outcomes."""
from copy import deepcopy
import unittest

from application.opportunities.swing_data_quality import diagnostics
from application.opportunities.swing_technical import snapshot
from domain.policy.swing_shadow import build_policy
from test_swing_technical import chart, clock


class SwingDataQualityTests(unittest.TestCase):
    def test_missing_close_has_flagged_display_average_only(self):
        data = chart()
        data["bars"][-1]["close"] = None
        result = snapshot(data, evaluated_at=clock(data))
        self.assertEqual(result["state"], "UNAVAILABLE")
        self.assertIsNotNone(result["data_quality"]["issues"][0]["display_ohlc"])
        self.assertNotIn("values", result)

    def test_estimated_path_cannot_resolve_stop_or_target(self):
        from test_swing_policy import fixture
        from domain.policy.swing_shadow import simulate
        features, data, now = fixture()
        data["bars"][81]["price_quality"] = "ESTIMATED"
        result = simulate(build_policy(features, decision_at=now.isoformat()), data,
                          evaluated_at=clock(data).isoformat(), horizon_sessions=3)
        self.assertEqual(result["state"], "DATA_UNAVAILABLE")
        self.assertEqual(result["reason"], "REAL_VALID_OHLC_REQUIRED")
        self.assertNotIn("gross_return", result)

    def test_causal_average_dated_flags_no_mutation_or_volume(self):
        data = chart()
        data["bars"][40]["high"] = None
        before = deepcopy(data)
        quality = diagnostics(data["bars"])
        issue = quality["issues"][0]
        self.assertEqual(issue["display_ohlc"]["close"], 137)
        self.assertEqual(issue["basis_sessions"], [r["timestamp"] for r in data["bars"][35:40]])
        self.assertIsNone(issue["volume"])
        self.assertEqual(data, before)
        later = deepcopy(data)
        later["bars"][41]["close"] += 100
        self.assertEqual(diagnostics(later["bars"])["issues"][0], issue)

    def test_no_recursive_estimates_or_initial_fabrication(self):
        data = chart()
        for i in (0, 40, 41):
            data["bars"][i]["open"] = None
        issues = diagnostics(data["bars"])["issues"]
        self.assertIsNone(issues[0]["display_ohlc"])
        self.assertIsNotNone(issues[1]["display_ohlc"])
        self.assertIsNone(issues[2]["display_ohlc"])

    def test_old_bad_bar_does_not_hide_independent_real_structure(self):
        data = chart()
        data["bars"][1]["low"] = 9999
        evidence = snapshot(data, evaluated_at=clock(data), benchmark_chart=chart())
        self.assertIsNotNone(evidence["values"]["ema50"])
        self.assertIsNone(evidence["values"]["atr14_wilder"])
        self.assertEqual(evidence["data_quality"]["indicator_checks"]["prior_structure"]["20"]["state"], "REAL_DATA_AVAILABLE")
        self.assertEqual(build_policy(evidence, decision_at=clock(data).isoformat())["state"], "BLOCKED")

    def test_recent_bad_bar_blocks_only_affected_diagnostic_windows(self):
        data = chart()
        data["bars"][-15]["high"] = None
        windows = diagnostics(data["bars"])["indicator_checks"]["prior_structure"]
        self.assertEqual(windows["10"]["state"], "REAL_DATA_AVAILABLE")
        self.assertEqual(windows["20"]["state"], "REAL_DATA_REQUIRED")

    def test_flagged_plausible_estimate_never_supplies_atr(self):
        data = chart()
        data["bars"][-2]["estimated"] = True
        evidence = snapshot(data, evaluated_at=clock(data), benchmark_chart=chart())
        self.assertIsNone(evidence["values"]["atr14_wilder"])
        self.assertEqual(build_policy(evidence, decision_at=clock(data).isoformat())["state"], "BLOCKED")

    def test_no_invented_calendar_sessions_and_bounded_report(self):
        data = chart()
        del data["bars"][20]
        self.assertEqual(diagnostics(data["bars"])["invalid_ohlc_count"], 0)
        for row in data["bars"]:
            row["high"] = None
        quality = diagnostics(data["bars"])
        self.assertEqual(quality["invalid_ohlc_count"], 79)
        self.assertEqual(len(quality["issues"]), 10)
        self.assertTrue(quality["issues_truncated"])
