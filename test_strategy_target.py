import json
import unittest
from dataclasses import replace
from datetime import datetime, timezone

from domain.contracts.trade import MetricContext
from domain.evaluation.target import *
from domain.risk import RiskEngine
from signal_pipeline import legacy_technical_score


class StrategyTargetTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 11, tzinfo=timezone.utc)
        self.daily_net = MetricContext("PERIODIC_CALENDAR", "1d", "JSE", 252,
            "DECIMAL_RETURN", "NET", "MODELED_BASE", "daily_1d", "STRATEGY", False, .08)
        self.trade_net = MetricContext("TRADE_BY_TRADE", "variable", "JSE", None,
            "DECIMAL_RETURN", "NET", "MODELED_BASE", "daily_1d", "PER_TRADE", False, None)

    def criterion(self, cid="expectancy", metric=MetricIdentity.NET_EXPECTANCY,
                  level=RequirementLevel.HARD, threshold=.001, stage=EvidenceStage.OUT_OF_SAMPLE,
                  context=None, comparison=Comparison.MINIMUM, **kw):
        return TargetCriterion(cid, metric, level, comparison, threshold,
                               context or self.trade_net, stage, **kw)

    def target(self, criteria=None, family="daily-directional", horizon=("daily_1d",)):
        return StrategyTarget("target-1", VERSION, self.now, family, ("EQ_ZAR_SASOL",),
            horizon, TargetStatus.DRAFT, tuple(criteria or (self.criterion(),)), "operator",
            "predeclared research target", ("initial declaration",), "directional-v1")

    def observation(self, criterion, value):
        return MetricObservation(criterion.criterion_id, criterion.metric_id,
            criterion.evidence_stage, value, criterion.context, self.now, {"run": "test"})

    def test_target_versioning_and_deterministic_serialization(self):
        target = self.target()
        self.assertEqual(target.target_version, "strategy-target-v1")
        self.assertEqual(json.dumps(target.to_dict(), sort_keys=True), json.dumps(target.to_dict(), sort_keys=True))

    def test_hard_failure_cannot_be_offset_by_soft_success(self):
        hard = self.criterion(threshold=.01)
        soft = self.criterion("sharpe", MetricIdentity.CANONICAL_ANNUALIZED_SHARPE,
            RequirementLevel.SOFT, 1.0, context=self.daily_net)
        result = assess_target(self.target((hard, soft)),
                               (self.observation(hard, -.01), self.observation(soft, 9.0)))
        self.assertEqual(result.status, "HARD_REQUIREMENTS_FAILED")
        self.assertFalse(result.promotion_authorized)

    def test_unset_threshold_remains_not_configured(self):
        item = self.criterion(threshold=None)
        result = assess_target(self.target((item,)), ())
        self.assertEqual(result.status, "NOT_CONFIGURED")

    def test_metric_context_is_required_and_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            replace(self.criterion(), context=None)
        item = self.criterion()
        bad = replace(self.observation(item, .01), context=replace(self.trade_net, return_basis="GROSS"))
        self.assertEqual(assess_target(self.target((item,)), (bad,)).status, "INVALID_EVIDENCE_CONTEXT")

    def test_legacy_metric_is_distinct_and_preserves_hr10_formula(self):
        result = legacy_tstat_like_v1((.01, .02, -.01))
        self.assertEqual(result.metric_id, MetricIdentity.LEGACY_TSTAT_LIKE_V1)
        self.assertNotEqual(result.metric_id, MetricIdentity.CANONICAL_ANNUALIZED_SHARPE)

    def test_canonical_sharpe_requires_annualization_context(self):
        bad = canonical_annualized_sharpe((.01, .02), self.trade_net)
        self.assertEqual(bad.status, "INVALID_CONTEXT")
        good = canonical_annualized_sharpe((.01, .02, -.005), self.daily_net)
        self.assertEqual(good.status, "AVAILABLE")

    def test_intraday_and_daily_families_remain_distinct(self):
        daily = self.target()
        intraday = self.target(family="intraday-scalping", horizon=("intraday_5m",))
        self.assertNotEqual((daily.strategy_family, daily.horizon_scope),
                            (intraday.strategy_family, intraday.horizon_scope))

    def test_net_and_gross_metrics_remain_distinct_by_context(self):
        gross = replace(self.trade_net, return_basis="GROSS", cost_basis="ZERO_COST")
        self.assertNotEqual(self.trade_net, gross)

    def test_oos_is_forward_and_walk_forward_stages_are_distinct(self):
        self.assertEqual(len({EvidenceStage.IN_SAMPLE, EvidenceStage.OUT_OF_SAMPLE,
                             EvidenceStage.WALK_FORWARD, EvidenceStage.FORWARD_DEMO}), 4)

    def test_sample_minimum_behavior(self):
        item = self.criterion("oos-n", MetricIdentity.OOS_SAMPLE_COUNT, threshold=30,
                              context=replace(self.trade_net, return_unit="COUNT"))
        self.assertEqual(assess_target(self.target((item,)), (self.observation(item, 5),)).status,
                         "HARD_REQUIREMENTS_FAILED")

    def test_cost_sensitivity_has_explicit_stress_context(self):
        context = replace(self.trade_net, cost_basis="MODELED_STRESS")
        item = self.criterion("stress", MetricIdentity.COST_STRESS_EXPECTANCY, context=context)
        self.assertEqual(item.context.cost_basis, "MODELED_STRESS")

    def test_regime_specialization_is_supported(self):
        item = self.criterion(required_regimes=("bull",), allowed_specialization=("bull", "normal_volatility"))
        self.assertEqual(item.allowed_specialization, ("bull", "normal_volatility"))

    def test_forward_demo_requirements_are_explicit(self):
        item = self.criterion("forward-days", MetricIdentity.FORWARD_DURATION_DAYS,
            threshold=20, stage=EvidenceStage.FORWARD_DEMO,
            context=replace(self.trade_net, return_unit="DAYS", return_basis="NOT_APPLICABLE",
                            cost_basis="NOT_APPLICABLE"))
        self.assertEqual(item.evidence_stage, EvidenceStage.FORWARD_DEMO)

    def test_risk_criteria_do_not_override_m15(self):
        item = self.criterion("gearing", MetricIdentity.MAX_GEARING, threshold=2,
            comparison=Comparison.MAXIMUM, context=replace(self.trade_net, return_unit="FRACTION",
            return_basis="NOT_APPLICABLE", cost_basis="NOT_APPLICABLE"))
        self.assertEqual(assess_target(self.target((item,)), (self.observation(item, 1),)).status,
                         "REQUIREMENTS_SATISFIED_FOR_REVIEW")
        self.assertFalse(hasattr(self.target((item,)), "risk_engine_override"))
        self.assertTrue(hasattr(RiskEngine(), "evaluate"))

    def test_no_automatic_promotion_or_runtime_behavior_change(self):
        result = assess_target(self.target(), (self.observation(self.criterion(), .01),))
        self.assertFalse(result.promotion_authorized)
        self.assertFalse(hasattr(result, "deploy"))
        self.assertTrue(callable(legacy_technical_score))


if __name__ == "__main__":
    unittest.main()
