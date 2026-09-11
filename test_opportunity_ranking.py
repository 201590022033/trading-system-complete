import unittest
from dataclasses import fields, replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from domain.broker.ig import IGMapping
from domain.evaluation.effectiveness import FeatureEffectiveness
from domain.evaluation.opportunity import (
    OpportunityCandidate, OpportunityRanker, RankingConfig, ResearchOpportunity,
    SCORE_SEMANTICS, rank_opportunities,
)
from domain.evaluation.suitability import CostEvidence, LiquidityEvidence, SuitabilityEvidence, evaluate_suitability
from domain.features.divergence import DivergenceConfig, SignalEvidence, summarize
from domain.features.regime import MarketRegime
from domain.registry.instrument import DEFAULT_INSTRUMENT_REGISTRY
from intraday_instruments import DEFAULT_REGISTRY, DataGrade
from signal_pipeline import legacy_technical_score


class OpportunityRankingTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)

    def effectiveness(self, instrument="SOL_CASH", value=.01, *, fallback="instrument+horizon+regime",
                      status="LEARNED", evaluated_at=None, feature="rsi"):
        count = 30 if status == "LEARNED" else 5
        return FeatureEffectiveness(
            feature, "feature-v1", "technical", instrument, "1d", "regime-candidate-v2", "bull",
            evaluated_at or self.now, self.now - timedelta(days=1), count, float(count),
            20 if value > 0 else 10, 10 if value > 0 else 20, 0, value, value, .66, .01, .01, .8,
            "SUFFICIENT" if status == "LEARNED" else "INSUFFICIENT", status, fallback,
            value, 0.0, 20.0, None, "contextual-effectiveness-v1", ("outcome-1",),
        )

    def divergence(self, instrument="SOL_CASH", states=(1, 1), *, evaluated_at=None):
        at = evaluated_at or self.now
        signals = tuple(SignalEvidence(f"f{i}", "signal-v1", state, at - timedelta(minutes=1),
                                       instrument_id=instrument, horizon_id="1d")
                        for i, state in enumerate(states))
        return summarize(signals, at, DivergenceConfig(len(signals), 1),
                         instrument_id=instrument, horizon_id="1d")

    def candidate(self, instrument="SOL_CASH", *, values=(.01, .02), states=(1, 1),
                  fallback="instrument+horizon+regime", blocked=False, mapping=False,
                  liquidity="UNKNOWN", regime_trend="bull", effectiveness=None):
        canonical = DEFAULT_INSTRUMENT_REGISTRY.get(instrument)
        legacy = DEFAULT_REGISTRY.get(instrument)
        records = tuple(effectiveness if effectiveness is not None else
                        (self.effectiveness(instrument, value, fallback=fallback,
                                            feature=f"feature-{index}")
                         for index, value in enumerate(values)))
        suitability = evaluate_suitability(
            legacy, "1d", self.now,
            data=SuitabilityEvidence("AVAILABLE", DataGrade.RESEARCH, "IG REST v3", "1d", 457, 0.0,
                                     "IG_UTC_SOURCE_TIMESTAMP"),
            features=records, costs=CostEvidence("ASSUMED", 10.0, "research assumption"),
            liquidity=LiquidityEvidence(liquidity, liquidity == "OBSERVED"),
            manually_blocked=blocked, regime_coverage="SUPPORTED")
        regime = MarketRegime(self.now, "regime-candidate-v2", trend_state=regime_trend,
                              volatility_state="normal", availability="AVAILABLE")
        broker = (IGMapping(instrument, "IG", "CC.D.LCO.BMU.IP", "DEMO", "COMMODITIES", "Brent")
                  if mapping else None)
        return OpportunityCandidate(canonical, suitability, self.divergence(instrument, states),
                                    records, regime, "RESEARCH_DATA", broker)

    def rank_one(self, candidate=None):
        return rank_opportunities((candidate or self.candidate(),), evaluated_at=self.now).opportunities[0]

    def test_blocked_and_unsupported_instruments_cannot_rank(self):
        blocked = self.rank_one(self.candidate(blocked=True))
        self.assertEqual(blocked.eligibility_status, "BLOCKED")
        self.assertIsNone(blocked.rank)
        unsupported_candidate = self.candidate()
        unsupported = replace(unsupported_candidate.suitability, overall_status="UNSUPPORTED",
                              hard_eligible=False, blockers=("UNSUPPORTED_HORIZON",))
        result = self.rank_one(replace(unsupported_candidate, suitability=unsupported))
        self.assertEqual(result.eligibility_status, "UNSUPPORTED")
        self.assertIsNone(result.ranking_score)

    def test_insufficient_evidence_is_retained_but_not_ranked(self):
        sparse = self.effectiveness(status="INSUFFICIENT_EVIDENCE")
        result = self.rank_one(self.candidate(effectiveness=(sparse,)))
        self.assertEqual(result.eligibility_status, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result.evidence_status, "INSUFFICIENT")
        self.assertIsNone(result.rank)

    def test_negative_effectiveness_lowers_support_without_being_discarded(self):
        positive = self.rank_one(self.candidate(values=(.01, .02)))
        negative = self.rank_one(self.candidate(values=(-.01, -.02)))
        self.assertLess(negative.ranking_score, positive.ranking_score)
        self.assertEqual(negative.feature_evidence_summary.negative_count, 2)
        self.assertIn("NEGATIVE_EFFECTIVENESS_REDUCES_SUPPORT", negative.reasons)

    def test_agreement_conflict_and_dominance_with_conflict_remain_distinct(self):
        agreement = self.rank_one(self.candidate(states=(1, 1, 1)))
        conflict = self.rank_one(self.candidate(states=(1, -1)))
        dominance = self.rank_one(self.candidate(states=(1, 1, -1)))
        self.assertEqual(agreement.divergence_summary["state"], "HIGH_AGREEMENT")
        self.assertEqual(conflict.divergence_summary["state"], "HIGH_DISAGREEMENT")
        self.assertEqual(dominance.divergence_summary["state"], "DOMINANT_WITH_CONFLICT")
        self.assertEqual(dominance.direction, "LONG")
        self.assertGreater(dominance.divergence_summary["disagreement_ratio"], 0)

    def test_regime_changes_only_documented_component(self):
        matching = self.rank_one(self.candidate(regime_trend="bull"))
        other = self.rank_one(self.candidate(regime_trend="bear"))
        differing = {name for name in matching.ranking_components
                     if matching.ranking_components[name] != other.ranking_components[name]}
        self.assertEqual(differing, {"regime_context"})

    def test_fallback_and_unknown_liquidity_uncertainty_are_preserved(self):
        result = self.rank_one(self.candidate(fallback="global", liquidity="UNKNOWN"))
        self.assertIn("BROADER_EFFECTIVENESS_FALLBACK", result.uncertainty)
        self.assertEqual(result.liquidity_status, "UNKNOWN")
        self.assertIn("LIQUIDITY_UNKNOWN", result.uncertainty)

    def test_research_suitable_execution_unsuitable_remains_research_opportunity(self):
        result = self.rank_one(self.candidate(mapping=False))
        self.assertIn(result.eligibility_status, {"ELIGIBLE", "WATCH"})
        self.assertEqual(result.execution_suitability, "RESEARCH-ONLY")
        self.assertEqual(result.market_mapping_status, "UNAVAILABLE")
        self.assertIsNotNone(result.rank)

    def test_deterministic_ranking_ties_and_top_n_retain_all_candidates(self):
        sol = self.candidate("SOL_CASH")
        bhp = self.candidate("BHP_CASH")
        first = rank_opportunities((sol, bhp), evaluated_at=self.now, top_n=1)
        second = rank_opportunities((bhp, sol), evaluated_at=self.now, top_n=1)
        self.assertEqual(first, second)
        self.assertEqual(len(first.top_opportunities), 1)
        self.assertEqual(len(first.opportunities), 2)
        self.assertEqual(first.top_opportunities[0].instrument_id, "BHP_CASH")

    def test_provenance_score_semantics_and_contract_exclude_trade_policy(self):
        result = self.rank_one(self.candidate(mapping=True))
        rendered = result.to_dict()
        self.assertEqual(result.ranking_score_semantics, SCORE_SEMANTICS)
        self.assertFalse(any("probability" in key.lower() for key in rendered))
        self.assertEqual(result.ig_epic, "CC.D.LCO.BMU.IP")
        self.assertEqual(result.suitability_version, "instrument-suitability-v1")
        self.assertEqual(result.regime_version, "regime-candidate-v2")
        self.assertEqual(result.feature_evidence_summary.evidence_confidence, .8)
        names = {item.name for item in fields(ResearchOpportunity)}
        for forbidden in ("trade_policy", "entry_price", "stop_loss", "take_profit",
                          "position_size", "quantity", "requested_units", "order_type"):
            self.assertNotIn(forbidden, names)

    def test_future_inputs_cannot_alter_earlier_ranking(self):
        base = self.candidate()
        future = self.effectiveness(value=-1.0, evaluated_at=self.now + timedelta(days=1), feature="future")
        changed = replace(base, effectiveness=base.effectiveness + (future,))
        self.assertEqual(self.rank_one(base), self.rank_one(changed))

    def test_watch_is_not_forced_to_trade_direction(self):
        result = self.rank_one(self.candidate(states=(1, -1)))
        self.assertEqual(result.direction, "WATCH")
        self.assertEqual(result.eligibility_status, "WATCH")

    def test_configuration_is_explicit_and_legacy_runtime_is_unchanged(self):
        self.assertEqual(RankingConfig().version, "opportunity-ranking-v1")
        observation = SimpleNamespace(indicators=SimpleNamespace(
            rsi_signal=1, sma_signal=1, breakout_signal=0, stochastic_signal=0))
        self.assertAlmostEqual(legacy_technical_score(observation), .65)
        self.assertFalse(hasattr(OpportunityRanker(), "place_order"))


if __name__ == "__main__":
    unittest.main()
