import unittest
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from application.opportunities.market_brief import (
    BENCHMARK_DECISION_KIND, BENCHMARK_OUTCOME_KIND,
    benchmark_learning_summary, build_decision_brief, build_market_context,
    label_benchmark_decisions, record_benchmark_decisions)
from persistence.sqlite_repository import SQLiteRepository


T = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)


def etf_chart(symbol, direction=1, *, future_jump=False):
    start = T.date() - timedelta(days=42)
    bars = [{"timestamp": (start + timedelta(days=i)).isoformat(),
             "close": 100 + direction * i} for i in range(42)]
    if future_jump:
        bars.append({"timestamp": (T.date() + timedelta(days=1)).isoformat(),
                     "close": 1_000_000})
    return {"symbol": symbol, "currency": "ZAR", "interval": "1d", "bars": bars}


def shares(direction=1):
    start = T.replace(hour=0) - timedelta(days=30)
    return {key: [(start + timedelta(days=i), 100 + direction * i, 10000)
                  for i in range(31)] for key in ("NPN", "SASOL", "BHP", "IMPJ", "SHPJ", "TFMJ")}


class MarketBriefTests(unittest.TestCase):
    def test_market_level_learning_labels_only_after_four_later_closes(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRepository(Path(directory) / "brief.db")
            try:
                repository.create_paper_account("a", {"mode": "PAPER"})
                initial = {"ETF_STX40": etf_chart("STX40.JO")}
                context = build_market_context(initial, shares(), evaluated_at=T)
                self.assertEqual(record_benchmark_decisions(
                    repository, "a", initial, context, evaluated_at=T), 1)
                self.assertEqual(record_benchmark_decisions(
                    repository, "a", initial, context, evaluated_at=T), 0)
                decisions = repository.paper_records("a", BENCHMARK_DECISION_KIND,
                                                     as_of=T.isoformat(), limit=10)
                self.assertEqual(len(decisions), 1)
                self.assertNotIn("bars", decisions[0])
                future = etf_chart("STX40.JO")
                future["bars"].extend({"timestamp": (T.date() + timedelta(days=i)).isoformat(),
                                       "close": 142 + i} for i in range(4))
                self.assertEqual(label_benchmark_decisions(
                    repository, "a", {"ETF_STX40": future},
                    evaluated_at=T + timedelta(days=3)), 0)
                self.assertEqual(label_benchmark_decisions(
                    repository, "a", {"ETF_STX40": future},
                    evaluated_at=T + timedelta(days=4)), 1)
                outcomes = repository.paper_records("a", BENCHMARK_OUTCOME_KIND,
                                                    as_of=(T + timedelta(days=4)).isoformat(), limit=10)
                self.assertEqual(len(outcomes), 1)
                self.assertGreater(outcomes[0]["gross_return"], 0)
                summary = benchmark_learning_summary(
                    repository, "a", evaluated_at=T + timedelta(days=4))
                self.assertEqual(summary["by_benchmark_and_market_state"]["ETF_STX40"]
                                 ["SUPPORTIVE"]["nonoverlapping_sessions"], 1)
            finally:
                repository.close()

    def test_cross_market_context_is_causal_and_requires_independent_benchmark(self):
        benchmark = {"ETF_STX40": etf_chart("STX40.JO", future_jump=True),
                     "ETF_STXFIN": etf_chart("STXFIN.JO")}
        context = build_market_context(benchmark, shares(), evaluated_at=T)
        self.assertEqual(context["state"], "SUPPORTIVE")
        self.assertEqual(context["sampled_share_count"], 6)
        self.assertLess(context["benchmarks"]["ETF_STX40"]["return_20_sessions"], 1)
        defensive = build_market_context(
            {"ETF_STX40": etf_chart("STX40.JO", -1)}, shares(-1), evaluated_at=T)
        self.assertEqual(defensive["state"], "DEFENSIVE")
        unknown = build_market_context(
            {"ETF_STX40": etf_chart("WRONG.JO")}, shares(), evaluated_at=T)
        self.assertEqual(unknown["state"], "INSUFFICIENT_CONTEXT")

    def test_brief_is_human_review_only_and_cash_is_explicitly_simulated(self):
        rows = {"TFMJ": {"instrument_id": "EQ_ZAR_TFMJ",
                         "bars": [(T, 120.0, 10000)]}}
        opportunity = SimpleNamespace(rank=1, instrument_id="EQ_ZAR_TFMJ",
                                      direction="LONG", eligibility_status="ELIGIBLE",
                                      ranking_score=61.0)
        context = {"state": "SUPPORTIVE"}
        brief = build_decision_brief((opportunity,), rows, context,
                                     available_cash=1000, evaluated_at=T)
        self.assertEqual(brief["ideas"][0]["state"], "REVIEW")
        self.assertFalse(brief["live_execution"])
        self.assertEqual(brief["simulated_available_cash"], 1000)
        self.assertEqual(build_decision_brief((opportunity,), rows, {"state": "DEFENSIVE"},
                                              available_cash=1000, evaluated_at=T)["ideas"][0]["state"],
                         "WAIT_MARKET")
        self.assertEqual(build_decision_brief((opportunity,), rows, context,
                                              available_cash=100, evaluated_at=T)["ideas"][0]["state"],
                         "PAPER_CASH_LIMIT")
