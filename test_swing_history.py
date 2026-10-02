import unittest
from datetime import datetime, timedelta, timezone

from application.opportunities.swing_history import (
    VERSION, current_evidence, market_state, metrics, setup, summarize_history, usable_bars,
)
from application.opportunities.public_research import candidate_from_chart
from test_public_research_refresh import NOW, chart


class SwingHistoryTests(unittest.TestCase):
    def test_setup_uses_only_supplied_prefix(self):
        self.assertEqual(setup(list(range(100, 121))), "BREAKOUT")
        self.assertEqual(setup([100]*20+[99]), "NO_LONG_SETUP")
        self.assertEqual(setup([100]*15+[110]*5+[105]), "TREND_PULLBACK")
        self.assertEqual(setup([100]*15+[110]*5+[110]), "TREND")
        self.assertEqual(setup([100]*20), "UNAVAILABLE")

    def test_next_close_entry_exact_horizons_nonoverlap_and_round_trip_cost(self):
        first = datetime(2025, 1, 1, tzinfo=timezone.utc)
        data = {"bars": [{"timestamp": (first+timedelta(days=i)).isoformat(), "close": 100+i}
                         for i in range(42)]}
        result = summarize_history(data, data, cutoff=first+timedelta(days=42))
        for horizon in (3, 4):
            values = result["cells"][f"BREAKOUT|ALL|{horizon}"]["all_history"]
            entries = list(range(21, 42-horizon, horizon+1))
            expected = sum(horizon/(100+i) for i in entries)/len(entries)
            self.assertEqual(values["sample_count"], len(entries))
            self.assertAlmostEqual(values["mean_gross_return"], expected)
            self.assertAlmostEqual(values["mean_net_return"], expected-.002)
            self.assertAlmostEqual(values["mean_net_50bps_stress"], expected-.005)
            self.assertAlmostEqual(values["mean_etf_excess"], 0)
            self.assertEqual(values["mean_close_mae"], 0)

    def test_future_bar_does_not_change_replay_and_dates_must_be_unique(self):
        base = chart("TFG.JO")
        future = {**base, "bars": base["bars"]+[{"timestamp": "2026-09-18", "close": 1}]}
        self.assertEqual(summarize_history(base, base, cutoff=NOW),
                         summarize_history(future, future, cutoff=NOW))
        future["bars"][-1]["close"] = -1
        self.assertEqual(usable_bars(base, NOW), usable_bars(future, NOW))
        with self.assertRaises(ValueError):
            usable_bars({"bars": base["bars"]+[base["bars"][-1]]}, NOW)

    def test_market_needs_exact_session_not_stale_substitution(self):
        rows = [(f"2026-01-{i:02d}", 100+i) for i in range(1, 22)]
        self.assertEqual(market_state(rows, "2026-01-21"), "SUPPORTIVE")
        self.assertEqual(market_state(rows, "2026-01-22"), "UNKNOWN")

    def report(self):
        data = chart("TFG.JO")
        return {"version": VERSION, "available_at": (NOW-timedelta(days=1)).isoformat(),
                "limitations": ["SHADOW_ONLY"], "instruments": {"TFMJ": {
                    "symbol": "TFG.JO", "source_sha256": "a"*64,
                    **summarize_history(data, data, cutoff=NOW)}}}

    def test_report_clocks_identity_missing_data_and_exact_horizons(self):
        data, report = chart("TFG.JO"), self.report()
        evidence = current_evidence("TFMJ", data, data, evaluated_at=NOW, report=report)
        self.assertEqual(evidence["state"], "HISTORICAL_RESEARCH_CONTEXT")
        self.assertEqual(set(evidence["horizons"]), {"3_sessions", "4_sessions"})
        self.assertEqual(evidence["governance"], "SHADOW_ONLY_NO_RANKING_EFFECT")
        report["available_at"] = (NOW+timedelta(seconds=1)).isoformat()
        self.assertEqual(current_evidence("TFMJ", data, data, evaluated_at=NOW,
                                         report=report)["state"], "UNAVAILABLE")
        self.assertEqual(current_evidence("MISSING", data, None, evaluated_at=NOW,
                                         report={})["state"], "UNAVAILABLE")

    def test_attachment_does_not_change_legacy_or_canonical_effectiveness(self):
        data = chart("TFG.JO")
        before = candidate_from_chart("TFMJ", data, evaluated_at=NOW, swing_history={})
        after = candidate_from_chart("TFMJ", data, evaluated_at=NOW,
                                     swing_history=self.report(), benchmark_chart=data)
        self.assertEqual(before.effectiveness, after.effectiveness)
        self.assertEqual(before.suitability, after.suitability)
        self.assertEqual(before.divergence, after.divergence)
        self.assertIn("swing_history", after.input_evidence)

    def test_empty_metrics_are_unavailable_not_zero_returns(self):
        self.assertNotIn("mean_net_return", metrics([]))

    def test_unit_glitch_is_quarantined_not_repaired_or_learnt_as_profit(self):
        base = chart("TFG.JO")
        benchmark = {**base, "bars": [dict(x) for x in base["bars"]]}
        benchmark["bars"][80]["close"] /= 100
        result = summarize_history(base, benchmark, cutoff=NOW)
        self.assertEqual(len(result["data_quality"]["benchmark_discontinuity_sessions"]), 2)
        for cell in result["cells"].values():
            if cell["all_history"].get("mean_etf_excess") is not None:
                self.assertAlmostEqual(cell["all_history"]["mean_etf_excess"], 0)
        self.assertEqual(setup([100]*20+[1]), "UNAVAILABLE")

    def test_runtime_benchmark_requires_identity_and_bad_context_does_not_remove_candidate(self):
        data = chart("TFG.JO")
        wrong = current_evidence("TFMJ", data, data, evaluated_at=NOW, report=self.report())
        self.assertEqual(wrong["market_state"], "UNKNOWN")
        benchmark = {**data, "symbol": "STX40.JO"}
        good = current_evidence("TFMJ", data, benchmark, evaluated_at=NOW, report=self.report())
        self.assertEqual(good["market_state"], "SUPPORTIVE")
        benchmark["bars"] = [{"timestamp": "2026-09-17", "close": None}]
        bad = current_evidence("TFMJ", data, benchmark, evaluated_at=NOW, report=self.report())
        self.assertEqual(bad["market_state"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
