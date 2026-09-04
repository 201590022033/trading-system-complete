import unittest
from datetime import datetime, timedelta, timezone

from provider_interfaces import (
    BrokerAccount, LiveExecutionDisabled, PaperExecutionProvider, Quote,
    SuggestionState, TradeSuggestion,
)


class ProviderBoundaryTests(unittest.TestCase):
    def suggestion(self, state=SuggestionState.ADMISSIBLE, stale=False):
        now = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)
        return TradeSuggestion("id", "SOL", now, now, "mock", "buy", "3 sessions",
            100, 95, 110, 2, 10, .6, "demo", ("reason",), "test-v1", state,
            now - timedelta(seconds=1) if stale else now + timedelta(minutes=5))

    def test_preview_is_paper_and_submit_hard_fails(self):
        provider = PaperExecutionProvider()
        preview = provider.preview_order({"instrument": "NPN", "side": "buy",
            "quantity": 2, "order_type": "limit", "estimated_price": 100})
        self.assertEqual(preview.mode, "paper")
        with self.assertRaises(LiveExecutionDisabled):
            provider.submit_order({})

    def test_canonical_serialization_includes_provenance_and_safety(self):
        now = datetime(2026, 9, 4, 12, tzinfo=timezone.utc)
        result = self.suggestion().to_dict(now)
        self.assertEqual(result["state"], "admissible")
        self.assertTrue(result["safety"]["actionable"])
        self.assertFalse(result["safety"]["live_execution_available"])
        self.assertEqual(result["data_source"], "mock")

    def test_rejected_strategy_cannot_be_previewed(self):
        with self.assertRaisesRegex(LiveExecutionDisabled, "strategy_state_rejected"):
            PaperExecutionProvider().preview_suggestion(
                self.suggestion(SuggestionState.REJECTED),
                datetime(2026, 9, 4, 12, tzinfo=timezone.utc))

    def test_stale_suggestion_cannot_be_previewed(self):
        suggestion = self.suggestion()
        with self.assertRaisesRegex(LiveExecutionDisabled, "stale"):
            PaperExecutionProvider().preview_suggestion(
                suggestion, suggestion.stale_after + timedelta(seconds=1))

    def test_invalid_chronology_and_naive_timestamps_are_rejected(self):
        with self.assertRaises(ValueError):
            TradeSuggestion("id", "SOL", datetime.now(), datetime.now(), "mock",
                "buy", "1", 1, 1, 1, 1, 1, .5, "x", (), "v",
                SuggestionState.RESEARCH, datetime.now() + timedelta(minutes=1))

    def test_provider_value_objects_reject_live_account_and_bad_quote(self):
        now = datetime(2026, 9, 4, tzinfo=timezone.utc)
        self.assertEqual(Quote("SOL", 100, now, "simulated", "mock").state, "simulated")
        with self.assertRaises(ValueError):
            Quote("SOL", 0, now, "live", "feed")
        with self.assertRaises(ValueError):
            BrokerAccount("broker", "masked", "live", "ZAR")


if __name__ == "__main__":
    unittest.main()
