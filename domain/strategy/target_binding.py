"""Optional exact target binding. No default thresholds or admission are created."""
from dataclasses import dataclass
from domain.evaluation.target import StrategyTarget
from .profile import StrategyProfile
from .attribution import StrategyAttributed, fields, same_strategy


@dataclass(frozen=True)
class StrategyTargetBinding(StrategyAttributed):
    strategy_target_id: str
    strategy_target_version: str
    strategy_family: str
    instrument_scope: tuple[str, ...]
    horizon_scope: tuple[str, ...]

    def __post_init__(self):
        super().__post_init__()
        if not self.strategy_profile_id or not self.strategy_target_id or not self.strategy_target_version:
            raise ValueError("binding requires exact profile and target versions")
        for name in ("instrument_scope", "horizon_scope"):
            object.__setattr__(self, name, tuple(getattr(self, name)))

    @classmethod
    def create(cls, profile: StrategyProfile, target: StrategyTarget):
        same_strategy(profile.reference, target)
        if profile.strategy_family != target.strategy_family:
            raise ValueError("target family differs from strategy profile")
        if not set(target.horizon_scope) <= set(profile.intended_horizon_ids):
            raise ValueError("target horizon is outside the declared strategy intent")
        # Explicit shared universe-scope tags, not guessed ticker membership.
        if not set(target.instrument_scope) <= set(profile.universe_scope):
            raise ValueError("target requires explicit matching universe-scope tags")
        return cls(target.target_id, target.target_version, target.strategy_family,
                   target.instrument_scope, target.horizon_scope, **fields(target))
