"""Versioned candidate trade-policy and geometry contracts."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Optional

from .market import finite, utc_timestamp


class EntryPolicyType(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    MARKET = "MARKET"
    PULLBACK_LIMIT = "PULLBACK_LIMIT"
    BREAKOUT_STOP = "BREAKOUT_STOP"
    CONFIRMATION_ENTRY = "CONFIRMATION_ENTRY"
    SCALE_IN = "SCALE_IN"


class StopPolicyType(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    STRUCTURAL_INVALIDATION = "STRUCTURAL_INVALIDATION"
    ATR_VOLATILITY = "ATR_VOLATILITY"
    FIXED_DISTANCE = "FIXED_DISTANCE"
    SWING_LEVEL = "SWING_LEVEL"
    TIME_STOP = "TIME_STOP"


class ExitPolicyType(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    FIXED_TARGET = "FIXED_TARGET"
    RISK_REWARD_TARGET = "RISK_REWARD_TARGET"
    TRAILING = "TRAILING"
    TIME_EXPIRY = "TIME_EXPIRY"
    SIGNAL_REVERSAL = "SIGNAL_REVERSAL"
    REGIME_CHANGE = "REGIME_CHANGE"


@dataclass(frozen=True)
class CandidateTradePolicy:
    policy_id: str
    policy_version: str
    entry_policy: EntryPolicyType
    stop_policy: StopPolicyType
    exit_policy: ExitPolicyType
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.policy_id or not self.policy_version:
            raise ValueError("policy identity and version are required")
        if not all(isinstance(value, Enum) for value in (self.entry_policy, self.stop_policy, self.exit_policy)):
            raise ValueError("policy types must use canonical enums")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))

    def to_dict(self) -> dict[str, Any]:
        return {"policy_id": self.policy_id, "policy_version": self.policy_version,
                "entry_policy": self.entry_policy.value, "stop_policy": self.stop_policy.value,
                "exit_policy": self.exit_policy.value, "parameters": dict(self.parameters)}


@dataclass(frozen=True)
class TradeGeometry:
    policy_snapshot: CandidateTradePolicy
    entry_price: float
    invalidation_price: float
    stop_loss_price: float
    take_profit_price: float
    expected_holding_seconds: int
    trailing_stop_activation: Optional[float]
    trailing_stop_distance: Optional[float]
    time_exit_cutoff: datetime

    def __post_init__(self) -> None:
        for name in ("entry_price", "invalidation_price", "stop_loss_price", "take_profit_price"):
            finite(getattr(self, name), name, minimum=0.0)
        if self.expected_holding_seconds <= 0:
            raise ValueError("expected holding time must be positive")
        for name in ("trailing_stop_activation", "trailing_stop_distance"):
            value = getattr(self, name)
            if value is not None:
                finite(value, name, minimum=0.0)
        object.__setattr__(self, "time_exit_cutoff", utc_timestamp(self.time_exit_cutoff))

    def to_dict(self) -> dict[str, Any]:
        return {"policy_snapshot": self.policy_snapshot.to_dict(), "entry_price": self.entry_price,
                "invalidation_price": self.invalidation_price, "stop_loss_price": self.stop_loss_price,
                "take_profit_price": self.take_profit_price, "expected_holding_seconds": self.expected_holding_seconds,
                "trailing_stop_activation": self.trailing_stop_activation,
                "trailing_stop_distance": self.trailing_stop_distance,
                "time_exit_cutoff": self.time_exit_cutoff.isoformat()}
