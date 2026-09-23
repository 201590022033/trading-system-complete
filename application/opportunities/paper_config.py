"""Explicit simulation configuration. Never reads broker credentials."""
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from math import isfinite
from domain.risk import RiskLimits
from .public_research import public_share_catalog


@dataclass(frozen=True)
class PaperLoopConfig:
    account_id: str
    mode: str
    starting_cash: float
    currency: str
    universe: tuple[str, ...]
    slippage_per_unit: float
    commission_per_fill: float
    risk_fraction: float
    aggression: str
    max_volume_fraction: float
    limits: dict
    interval_seconds: int = 300
    max_price_age_seconds: int = 86400
    max_holding_seconds: int = 604800
    reward_multiple: float = 2.

    def __post_init__(self):
        if self.mode != "PAPER" or self.currency != "ZAR" or not self.account_id:
            raise ValueError("only explicit ZAR PAPER accounts supported")
        object.__setattr__(self, "universe", tuple(self.universe))
        if not 1 <= len(self.universe) <= 30 or len(set(self.universe)) != len(self.universe):
            raise ValueError("bounded unique universe required")
        # Existing durable accounts may retain an explicitly inactive legacy
        # identity. Runtime loaders use the active catalog and skip it without
        # issuing a provider request or relabelling historical records.
        if any(key not in public_share_catalog(include_inactive=True) for key in self.universe):
            raise ValueError("unknown public cash equity")
        for name in ("starting_cash", "slippage_per_unit", "commission_per_fill",
                     "risk_fraction", "max_volume_fraction", "reward_multiple"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isfinite(value) or value <= 0:
                raise ValueError("explicit positive finite paper assumptions required")
        if self.risk_fraction > 1 or self.max_volume_fraction > .01 or self.reward_multiple < 1:
            raise ValueError("invalid paper risk/participation/reward bounds")
        if self.aggression not in {"conservative", "balanced", "aggressive"}:
            raise ValueError("unknown aggression")
        if not 60 <= self.interval_seconds <= 86400 or not 1 <= self.max_price_age_seconds <= 86400:
            raise ValueError("invalid bounded scheduling/freshness")
        if not 86400 <= self.max_holding_seconds <= 604800:
            raise ValueError("invalid paper holding expiry")
        limits = self.risk_limits()
        if limits.missing or limits.max_gearing > 1:
            raise ValueError("all paper limits must be explicit; no borrowing")

    def risk_limits(self):
        values = dict(self.limits)
        values["effective_at"] = datetime.fromisoformat(values["effective_at"])
        return RiskLimits(**values)

    def to_dict(self):
        return {**asdict(self), "universe": list(self.universe)}

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as handle:
            return cls(**json.load(handle))
