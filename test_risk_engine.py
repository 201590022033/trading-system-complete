import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from domain.contracts.policy import StopPolicyType
from domain.evaluation.opportunity import FeatureEvidenceSummary, ResearchOpportunity, SCORE_SEMANTICS
from domain.policy.engine import PolicyContext, TradePolicyEngine
from domain.risk import (FXConversion, InstrumentRiskMetadata, PortfolioRiskState,
                         RiskEngine, RiskLimits, RiskStatus)
from provider_interfaces import LiveExecutionDisabled, PaperExecutionProvider


class RiskEngineTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 11, 10, tzinfo=timezone.utc)
        self.engine = RiskEngine()
        opportunity = ResearchOpportunity(
            "opp-risk", self.now, "opportunity-ranking-v1", "SOL_CASH", "intraday_30m",
            None, "UNAVAILABLE", None, "LONG", "SUFFICIENT",
            FeatureEvidenceSummary(2, 0, 2, 0, 60, 60.0, .8, ("exact",), ()),
            {"state": "HIGH_AGREEMENT"}, {"trend": "bull"}, "SUITABLE",
            "RESEARCH-SUITABLE", "RESEARCH-ONLY", "AVAILABLE", "ASSUMED", "UNKNOWN",
            "RESEARCH_DATA", 60, 60.0, (), 70.0, SCORE_SEMANTICS, {"suitability": .8},
            1, "ELIGIBLE", (), (), ("feature-v1",), "regime-v1", "suitability-v1",
            "effectiveness-v1", "ranking-v1", {})
        base = TradePolicyEngine().create(
            opportunity, created_at=self.now,
            context=PolicyContext(self.now, self.now + timedelta(minutes=30), 300))
        self.policy = replace(
            base, status="READY_FOR_RISK_REVIEW", entry_price=100.0,
            stop_type=StopPolicyType.FIXED_DISTANCE, stop_reference="VALIDATED_CAUSAL_INPUT",
            stop_distance=10.0, stop_price=90.0, stop_provenance={"status": "AVAILABLE"},
            requested_loss_budget=100.0, requested_risk_fraction=.01, requested_gearing=2.0)
        self.limits = RiskLimits(
            "operator-limits", self.now, .02, 200.0, .10, 1.0, 3.0, .50,
            1.0, 1.0, 1.0, .20, False)
        self.portfolio = PortfolioRiskState(
            "state-1", self.now, "USD", 10_000.0, 9_000.0, 5_000.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, {}, {}, {})
        self.metadata = InstrumentRiskMetadata(
            "SOL_CASH", self.now, "USD", 1.0, 1.0, 1.0, .10,
            "energy", ("energy-beta",), "canonical-test")

    def evaluate(self, **changes):
        inputs = {"policy": self.policy, "evaluated_at": self.now, "limits": self.limits,
                  "portfolio": self.portfolio, "metadata": self.metadata}
        inputs.update(changes)
        return self.engine.evaluate(**inputs)

    def test_unresolved_stop_means_no_size(self):
        policy = replace(self.policy, status="UNRESOLVED", stop_type=StopPolicyType.UNRESOLVED,
                         stop_price=None, stop_distance=None)
        result = self.evaluate(policy=policy)
        self.assertEqual(result.status, RiskStatus.UNRESOLVED)
        self.assertIsNone(result.approved_position_size)

    def test_missing_required_limit_is_not_configured(self):
        result = self.evaluate(limits=replace(self.limits, max_gearing=None))
        self.assertEqual(result.status, RiskStatus.NOT_CONFIGURED)
        self.assertIn("NOT_CONFIGURED:max_gearing", result.blockers)

    def test_blocked_policy_is_blocked(self):
        result = self.evaluate(policy=replace(self.policy, status="BLOCKED"))
        self.assertEqual(result.status, RiskStatus.BLOCKED)
        self.assertIsNone(result.approved_position_size)

    def test_monetary_loss_formula_and_contract_multiplier(self):
        result = self.evaluate(metadata=replace(self.metadata, contract_multiplier=2.0))
        self.assertEqual(result.approved_position_size, 5.0)
        self.assertEqual(result.estimated_loss_at_stop, 100.0)

    def test_lot_rounding_only_rounds_down(self):
        policy = replace(self.policy, requested_loss_budget=105.0, requested_risk_fraction=None)
        result = self.evaluate(policy=policy, metadata=replace(self.metadata, lot_size=2.0))
        self.assertEqual(result.approved_position_size, 10.0)
        self.assertLessEqual(result.estimated_loss_at_stop, 105.0)
        self.assertIn("LOT_SIZE_ROUND_DOWN", result.reduction_reasons)

    def test_minimum_deal_size_failure(self):
        result = self.evaluate(metadata=replace(self.metadata, minimum_deal_size=20.0))
        self.assertEqual(result.status, RiskStatus.REJECTED)
        self.assertIn("BELOW_MINIMUM_DEAL_SIZE", result.rejection_reasons)

    def test_per_trade_and_portfolio_risk_caps_reduce(self):
        policy = replace(self.policy, requested_loss_budget=500.0, requested_risk_fraction=None)
        per_trade = self.evaluate(policy=policy)
        self.assertEqual(per_trade.estimated_loss_at_stop, 200.0)
        self.assertIn("MAX_RISK_PER_TRADE_CAP", per_trade.reduction_reasons)
        portfolio = replace(self.portfolio, current_open_risk=950.0)
        result = self.evaluate(policy=policy, portfolio=portfolio)
        self.assertEqual(result.estimated_loss_at_stop, 50.0)
        self.assertIn("MAX_PORTFOLIO_OPEN_RISK_CAP", result.reduction_reasons)

    def test_daily_loss_drawdown_and_open_risk_tripwires(self):
        cases = (
            (replace(self.portfolio, daily_realised_loss=200.0), "DAILY_LOSS_LIMIT_BREACHED"),
            (replace(self.portfolio, current_drawdown_fraction=.20), "DRAWDOWN_LIMIT_BREACHED"),
            (replace(self.portfolio, current_open_risk=1_000.0), "PORTFOLIO_OPEN_RISK_LIMIT_BREACHED"),
        )
        for state, reason in cases:
            with self.subTest(reason=reason):
                result = self.evaluate(portfolio=state)
                self.assertEqual(result.status, RiskStatus.REJECTED)
                self.assertIn(reason, result.rejection_reasons)

    def test_instrument_sector_and_correlated_caps_reduce(self):
        cases = (
            (replace(self.portfolio, instrument_exposure={"SOL_CASH": 9_850.0}), "MAX_INSTRUMENT_EXPOSURE_CAP"),
            (replace(self.portfolio, sector_exposure={"energy": 9_850.0}), "MAX_SECTOR_EXPOSURE_CAP"),
            (replace(self.portfolio, correlated_exposure={"energy-beta": 9_850.0}), "MAX_CORRELATED_EXPOSURE_CAP:energy-beta"),
        )
        for state, reason in cases:
            with self.subTest(reason=reason):
                result = self.evaluate(portfolio=state)
                self.assertEqual(result.approved_position_size, 1.0)
                self.assertIn(reason, result.reduction_reasons)

    def test_missing_margin_and_margin_cap(self):
        unavailable = self.evaluate(metadata=replace(self.metadata, margin_factor=None))
        self.assertEqual(unavailable.status, RiskStatus.UNRESOLVED)
        capped = self.evaluate(portfolio=replace(self.portfolio, margin_available=50.0))
        self.assertEqual(capped.approved_position_size, 5.0)
        self.assertIn("MAX_MARGIN_UTILIZATION_CAP", capped.reduction_reasons)
        cash_instrument = self.evaluate(metadata=replace(self.metadata, margin_factor=0.0))
        self.assertEqual(cash_instrument.estimated_margin, 0.0)

    def test_nonpositive_equity_rejects_without_sizing(self):
        result = self.evaluate(portfolio=replace(self.portfolio, equity=0.0))
        self.assertEqual(result.status, RiskStatus.REJECTED)
        self.assertIsNone(result.approved_position_size)
        self.assertIn("ACCOUNT_EQUITY_NOT_POSITIVE", result.rejection_reasons)

    def test_gearing_cap_and_requested_gearing_never_enlarge(self):
        result = self.evaluate(policy=replace(self.policy, requested_loss_budget=1000.0,
                                              requested_gearing=.05))
        self.assertEqual(result.approved_notional, 500.0)
        self.assertIn("MAX_GEARING_CAP", result.reduction_reasons)

    def test_currency_conversion_is_explicit(self):
        metadata = replace(self.metadata, price_currency="ZAR")
        missing = self.evaluate(metadata=metadata)
        self.assertEqual(missing.status, RiskStatus.UNRESOLVED)
        fx = FXConversion("ZAR", "USD", .05, self.now, "observed-fx")
        converted = self.evaluate(metadata=metadata, fx=fx)
        self.assertEqual(converted.estimated_loss_at_stop, 100.0)
        self.assertEqual(converted.approved_position_size, 200.0)

    def test_reduction_reasons_are_retained(self):
        result = self.evaluate(policy=replace(self.policy, requested_loss_budget=500.0,
                                              requested_risk_fraction=None),
                               metadata=replace(self.metadata, lot_size=3.0))
        self.assertEqual(result.status, RiskStatus.REDUCED)
        self.assertIn("MAX_RISK_PER_TRADE_CAP", result.reduction_reasons)
        self.assertIn("LOT_SIZE_ROUND_DOWN", result.reduction_reasons)

    def test_human_limits_override_score_and_rank(self):
        result = self.evaluate(portfolio=replace(self.portfolio, kill_switch_active=True))
        self.assertEqual(result.status, RiskStatus.BLOCKED)
        self.assertIsNone(result.approved_intent)

    def test_future_inputs_block_and_prior_evaluation_is_immutable(self):
        result = self.evaluate()
        later = replace(self.portfolio, state_id="later", as_of=self.now + timedelta(minutes=1), equity=1.0)
        blocked = self.evaluate(portfolio=later)
        self.assertEqual(blocked.status, RiskStatus.BLOCKED)
        self.assertEqual(result.approved_position_size, 10.0)
        with self.assertRaises(TypeError):
            result.provenance["later"] = True

    def test_no_broker_execution_or_order_contract_dependency(self):
        self.assertFalse(hasattr(self.engine, "place_order"))
        self.assertFalse(hasattr(self.engine, "submit_order"))
        with self.assertRaises(LiveExecutionDisabled):
            PaperExecutionProvider().submit_order({})


if __name__ == "__main__":
    unittest.main()
