import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from domain.evaluation.opportunity import FeatureEvidenceSummary, ResearchOpportunity, SCORE_SEMANTICS
from domain.policy.engine import NON_EXECUTABLE, PolicyContext, TradePolicy, TradePolicyEngine
from domain.contracts.policy import StopPolicyType
from provider_interfaces import LiveExecutionDisabled, PaperExecutionProvider
from signal_pipeline import legacy_technical_score


class TradePolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 11, 10, tzinfo=timezone.utc)
        self.engine = TradePolicyEngine()

    def opportunity(self, *, direction="LONG", status="ELIGIBLE", evaluated_at=None):
        score = None if status in {"BLOCKED", "UNSUPPORTED", "INSUFFICIENT_EVIDENCE"} else 70.0
        rank = None if score is None else 1
        blockers = ("MANUALLY_BLOCKED",) if status == "BLOCKED" else ()
        return ResearchOpportunity(
            opportunity_id="opp-1", evaluated_at=evaluated_at or self.now,
            opportunity_version="opportunity-ranking-v1", instrument_id="SOL_CASH",
            horizon_id="intraday_30m", broker=None, market_mapping_status="UNAVAILABLE",
            ig_epic=None, direction=direction,
            evidence_status="INSUFFICIENT" if status == "INSUFFICIENT_EVIDENCE" else "SUFFICIENT",
            feature_evidence_summary=FeatureEvidenceSummary(2, 0, 2, 0, 60, 60.0, .8,
                                                            ("instrument+horizon+regime",), ()),
            divergence_summary={"state": "HIGH_AGREEMENT", "dominant_direction": 1},
            regime_context={"trend": "bull", "availability": "AVAILABLE"},
            suitability_status="BLOCKED" if status == "BLOCKED" else "SUITABLE",
            research_suitability="NOT_RESEARCH-SUITABLE" if status == "BLOCKED" else "RESEARCH-SUITABLE",
            execution_suitability="RESEARCH-ONLY", data_status="AVAILABLE", cost_status="ASSUMED",
            liquidity_status="UNKNOWN", data_grade="RESEARCH_DATA", sample_count=60,
            effective_evidence_count=60.0, uncertainty=("DATA_NOT_EXECUTION_GRADE",),
            ranking_score=score, ranking_score_semantics=SCORE_SEMANTICS,
            ranking_components={"suitability": .8}, rank=rank, eligibility_status=status,
            reasons=(), blockers=blockers, input_feature_versions=("feature-v1", "divergence-v1"),
            regime_version="regime-candidate-v2", suitability_version="instrument-suitability-v1",
            effectiveness_version="contextual-effectiveness-v1", ranking_version="opportunity-ranking-v1",
            provenance={"instrument_registry_version": "canonical-instrument-registry-v1"})

    def context(self, *, position=None, available_at=None, horizon_end=True):
        return PolicyContext(
            available_at or self.now,
            self.now + timedelta(minutes=30) if horizon_end else None,
            300, position, {"status": "ASSUMED", "basis": "research cost schedule"})

    def policy(self, opportunity=None, context=None):
        return self.engine.create(opportunity or self.opportunity(), created_at=self.now,
                                  context=context or self.context())

    def test_blocked_and_insufficient_opportunities_are_nonactionable(self):
        blocked = self.policy(self.opportunity(status="BLOCKED"))
        insufficient = self.policy(self.opportunity(direction="UNKNOWN", status="INSUFFICIENT_EVIDENCE"))
        self.assertEqual(blocked.status, "BLOCKED")
        self.assertEqual(insufficient.status, "INSUFFICIENT_EVIDENCE")
        for policy in (blocked, insufficient):
            self.assertEqual(policy.entry_timing, "NO_ENTRY_INTENT")
            self.assertIsNone(policy.direction)
            self.assertEqual(policy.actionability, NON_EXECUTABLE)

    def test_watch_has_no_entry_intent(self):
        policy = self.policy(self.opportunity(direction="WATCH", status="WATCH"))
        self.assertEqual(policy.status, "WATCH")
        self.assertEqual(policy.entry_reference, "UNRESOLVED")
        self.assertIsNone(policy.entry_price)

    def test_long_and_short_directions_are_preserved(self):
        self.assertEqual(self.policy(self.opportunity(direction="LONG")).direction, "LONG")
        self.assertEqual(self.policy(self.opportunity(direction="SHORT")).direction, "SHORT")

    def test_entry_is_causal_and_future_price_remains_unresolved(self):
        policy = self.policy()
        self.assertEqual(policy.entry_reference, "NEXT_OBSERVED_CANONICAL_BAR_OPEN")
        self.assertEqual(policy.allowed_entry_window_start, self.now)
        self.assertEqual(policy.allowed_entry_window_end, self.now + timedelta(minutes=5))
        self.assertIsNone(policy.entry_price)
        self.assertIn("PRICE_UNAVAILABLE_UNTIL_OBSERVED", policy.entry_price_source)

    def test_future_inputs_and_later_state_cannot_rewrite_policy(self):
        base = self.opportunity()
        original = self.policy(base)
        later_score = self.policy(replace(base, ranking_score=99.0))
        later_regime = self.policy(replace(base, regime_context={"trend": "bear", "availability": "AVAILABLE"}))
        self.assertEqual(original, later_score)
        self.assertEqual(original, later_regime)
        future = self.policy(self.opportunity(evaluated_at=self.now + timedelta(minutes=1)))
        self.assertEqual(future.status, "BLOCKED")
        self.assertIn("FUTURE_OPPORTUNITY", future.blockers)
        future_context = self.policy(context=self.context(available_at=self.now + timedelta(minutes=1)))
        self.assertEqual(future_context.status, "BLOCKED")

    def test_stop_and_strategy_invalidation_are_distinct_and_unresolved(self):
        policy = self.policy()
        self.assertEqual(policy.stop_type.value, "UNRESOLVED")
        self.assertIsNone(policy.stop_price)
        self.assertIsNone(policy.stop_distance)
        self.assertEqual(policy.stop_provenance["status"], "UNRESOLVED")
        self.assertNotEqual(policy.stop_reference, policy.invalidation_condition)
        self.assertIn("OPPORTUNITY_BECOMES_INELIGIBLE", policy.invalidation_condition)
        self.assertEqual(policy.status, "UNRESOLVED")

    def test_contract_rejects_invented_or_wrong_side_stop_geometry(self):
        policy = self.policy()
        with self.assertRaisesRegex(ValueError, "unresolved stop"):
            replace(policy, stop_price=90.0)
        with self.assertRaisesRegex(ValueError, "loss side"):
            replace(policy, entry_price=100.0, stop_type=StopPolicyType.FIXED_DISTANCE,
                    stop_price=101.0, stop_distance=1.0)
        with self.assertRaisesRegex(ValueError, "risk review requires"):
            replace(policy, status="READY_FOR_RISK_REVIEW")

    def test_target_is_optional_and_trailing_is_not_invented(self):
        policy = self.policy()
        self.assertEqual(policy.target_type, "NONE")
        self.assertEqual(policy.target_levels, ())
        self.assertIsNone(policy.target_distance)
        self.assertFalse(policy.trailing_enabled)
        self.assertEqual(policy.trailing_rules["status"], "UNSUPPORTED")

    def test_time_exit_respects_canonical_horizon_identity(self):
        policy = self.policy()
        self.assertEqual(policy.horizon_id, "intraday_30m")
        self.assertEqual(policy.max_holding_seconds, 1800)
        self.assertEqual(policy.ttl_seconds, 1800)
        self.assertEqual(policy.time_exit_at, self.now + timedelta(minutes=30))
        noncanonical = self.policy(replace(self.opportunity(), horizon_id="1d"))
        self.assertIn("NONCANONICAL_HORIZON_ID", noncanonical.blockers)

    def test_reversal_requires_exit_and_never_auto_flips(self):
        policy = self.policy(context=self.context(position="SHORT"))
        self.assertTrue(policy.reversal_required)
        self.assertIn("EXIT_EXISTING_POSITION", policy.reversal_rule)
        self.assertIn("SEPARATE_NEW_POLICY_REVIEW", policy.reversal_rule)

    def test_requested_risk_is_not_approved_and_no_final_size_or_margin_exists(self):
        policy = self.policy()
        self.assertIsNone(policy.requested_risk_fraction)
        self.assertIsNone(policy.requested_loss_budget)
        self.assertIsNone(policy.requested_gearing)
        self.assertEqual(policy.risk_approval_status, "NOT_EVALUATED")
        names = {item.name for item in fields(TradePolicy)}
        for forbidden in ("position_size", "final_size", "approved_gearing", "approved_margin",
                          "portfolio_exposure", "order", "quantity"):
            self.assertNotIn(forbidden, names)

    def test_version_provenance_determinism_execution_and_legacy_boundaries(self):
        first, second = self.policy(), self.policy()
        self.assertEqual(first, second)
        self.assertEqual(first.policy_version, "trade-policy-v1")
        self.assertEqual(first.provenance["opportunity_version"], "opportunity-ranking-v1")
        self.assertEqual(first.opportunity_feature_versions, ("feature-v1", "divergence-v1"))
        self.assertFalse(hasattr(self.engine, "place_order"))
        with self.assertRaises(LiveExecutionDisabled):
            PaperExecutionProvider().submit_order({})
        observation = SimpleNamespace(indicators=SimpleNamespace(
            rsi_signal=1, sma_signal=1, breakout_signal=0, stochastic_signal=0))
        self.assertAlmostEqual(legacy_technical_score(observation), .65)


if __name__ == "__main__":
    unittest.main()
