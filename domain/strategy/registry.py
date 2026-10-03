"""Exact-version registry with explicitly selected current versions, never overwrite."""
from types import MappingProxyType
from .profile import CapabilityState as C, StrategyCapability as Capability
from .profile import StrategyLifecycle as L, StrategyProfile, StrategyProfileRef


class StrategyProfileRegistry:
    def __init__(self, profiles, *, current_versions):
        index = {}
        for profile in profiles:
            if not isinstance(profile, StrategyProfile):
                raise TypeError("typed strategy profile required")
            key = (profile.reference.strategy_profile_id, profile.reference.strategy_profile_version)
            if key in index:
                raise ValueError("strategy profile versions cannot be overwritten")
            index[key] = profile
        current = dict(current_versions)
        if set(current) != {key[0] for key in index} or any((key, version) not in index for key, version in current.items()):
            raise ValueError("every strategy must pin an existing current version")
        self._profiles = MappingProxyType(index)
        self._current = MappingProxyType(current)

    def resolve(self, strategy_profile_id, strategy_profile_version=None):
        version = strategy_profile_version if strategy_profile_version is not None else self._current[strategy_profile_id]
        return self._profiles[(strategy_profile_id, version)]

    def current_profiles(self):
        return tuple(self.resolve(key) for key in self._current)

    def versions(self, strategy_profile_id):
        if strategy_profile_id not in self._current:
            raise KeyError(strategy_profile_id)
        return tuple(profile for (key, _), profile in self._profiles.items() if key == strategy_profile_id)


def default_profiles():
    return (
        StrategyProfile(StrategyProfileRef("jse_swing_3_5d", "1.0.0"), "JSE Swing Trader — 3–5 Day",
            "Swing Trader", "3–5 Day", L.ACTIVE_RESEARCH_PAPER, "jse_cash_swing",
            ("JSE_CASH_EQUITIES",), "1d", ("3_sessions", "4_sessions", "5_sessions"),
            ("RESEARCH", "SHADOW", "PAPER"), (
                Capability("canonical_research", C.IMPLEMENTED_REUSABLE,
                    "Existing daily canonical screening and ranking; no new strategy ranker.",
                    ("application.opportunities.public_research", "domain.evaluation.opportunity")),
                Capability("context_and_news", C.IMPLEMENTED_REUSABLE,
                    "Existing technical, regime, divergence and causal news inputs; sentiment is opinion, not a validated catalyst model.",
                    ("domain.registry.feature", "domain.features.regime", "domain.features.divergence", "application.opportunities.news_ingestion")),
                Capability("paper_and_risk", C.IMPLEMENTED_REUSABLE,
                    "Existing daily-close, long-only, three-session paper simulator and risk veto; not actual OST account sizing.",
                    ("domain.policy.paper_geometry", "domain.risk.paper_sizing", "application.opportunities.paper_loop", "domain.broker.paper")),
                Capability("profile_attribution", C.PLANNED,
                    "Exact profile attribution through opportunity, policy, risk, paper and learning records is not yet wired."),
                Capability("swing_evidence", C.IMPLEMENTED_REUSABLE,
                    "Compact three/four-session Yahoo setup context and M11 learner; descriptive shadow evidence only.",
                    ("application.opportunities.swing_history", "domain.evaluation.effectiveness")),
                Capability("entry_refinement_30m", C.BLOCKED,
                    "30-minute chart display exists; validated session/data/cost contracts for swing entry refinement remain missing.",
                    ("domain.market_data.horizons", "jse_adapter")),
            ), ("Foundation links an existing workflow; its records are not yet produced by this StrategyProfile.",
                "Current ranking evidence is one-day; paper holding is three sessions. The intended 3–5-session scope does not change either.",
                "Curated cash universe is not certified liquid; explicit liquidity admission remains required.",
                "Actual OST fees, cash and spread remain unconfigured. Research rank is separate from account feasibility.",
                "ETFs retain their existing separate research path; this initial profile targets cash equities.",
                "No validated profitability, automatic promotion or broker execution."), "canonical-opportunities"),
        StrategyProfile(StrategyProfileRef("intraday_cfd", "1.0.0"), "Intraday CFD", "Intraday CFD", "5–60 min",
            L.DEVELOPMENT_DATA_VALIDATION_REQUIRED, "intraday_cfd", ("CFD_CONTRACTS",),
            "INTRADAY_NOT_CONFIGURED", ("intraday_5m", "intraday_15m", "intraday_30m", "intraday_60m", "intraday_eod"),
            ("RESEARCH",), (
                Capability("hr11_causal_core", C.IMPLEMENTED_REUSABLE,
                    "HR11 horizon/session/aggregation/evaluation infrastructure exists; it is not an admitted intraday strategy.",
                    ("domain.market_data.horizons", "intraday_evaluation", "hr11_research")),
                Capability("broker_data_boundary", C.IMPLEMENTED_REUSABLE,
                    "Read-only IG discovery/history and gated Demo safety components exist; this profile activates none.",
                    ("domain.broker.ig", "domain.broker.ig_history", "domain.broker.execution_safety")),
                Capability("intraday_strategy", C.BLOCKED,
                    "Verified real-data depth, contract/session/cost evidence, walk-forward validation and attribution are required."),
            ), ("No validated intraday strategy, profile ranking or execution workflow.",
                "Public CFD reference charts are not broker contract prices.",
                "IG Demo submission remains disabled and requires separate explicit permission; LIVE is prohibited.")),
        StrategyProfile(StrategyProfileRef("long_term_investment", "1.0.0"), "Long-Term Investment",
            "Long-Term Investment", "Weeks–Months", L.DEVELOPMENT, "long_term_investment",
            ("INVESTMENT_UNIVERSE_NOT_CONFIGURED",), "NOT_CONFIGURED", ("weeks", "months", "longer"),
            ("RESEARCH",), (
                Capability("market_intelligence", C.IMPLEMENTED_REUSABLE,
                    "Existing source/provenance and market-intelligence boundaries can be reused for investigation.",
                    ("domain.registry.source", "market_intelligence")),
                Capability("investment_model", C.PLANNED,
                    "Fundamentals, valuation, balance sheet/earnings, macro/sector context and slower trends need separate data and evaluation contracts."),
            ), ("No investment ranking, validated model, account sizing or execution workflow.",
                "Weeks/months are intended horizons, not executable horizon contracts.",
                "Swing technical rules are not reused as an investment strategy.")),
    )


_defaults = default_profiles()
DEFAULT_STRATEGY_REGISTRY = StrategyProfileRegistry(_defaults, current_versions={
    profile.reference.strategy_profile_id: profile.reference.strategy_profile_version for profile in _defaults})
