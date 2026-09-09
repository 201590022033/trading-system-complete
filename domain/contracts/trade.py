"""Canonical trade, risk, order and metric contracts."""

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from .market import Direction, finite, utc_timestamp
from .policy import TradeGeometry


def _mapping(value: Mapping[str, Any], field: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")


@dataclass(frozen=True)
class TradeIntent:
    intent_id: str
    strategy_version: str
    instrument_id: str
    execution_symbol: str
    generated_at: datetime
    direction: Direction
    opportunity_score: float
    opportunity_rank: int
    regime_snapshot: Mapping[str, Any]
    geometry: TradeGeometry
    requested_units: float
    requested_notional: float
    estimated_cost: float
    contributing_feature_ids: Tuple[str, ...]
    evidence_provenance_ids: Tuple[str, ...]
    expires_at: datetime

    def __post_init__(self) -> None:
        for name in ("generated_at", "expires_at"):
            object.__setattr__(self, name, utc_timestamp(getattr(self, name)))
        if not self.intent_id or not self.strategy_version or not self.instrument_id or not self.execution_symbol:
            raise ValueError("trade intent identity is required")
        if not isinstance(self.direction, Direction) or not -1.0 <= self.opportunity_score <= 1.0:
            raise ValueError("direction and bounded opportunity score are required")
        if not 1 <= self.opportunity_rank <= 5 or self.expires_at <= self.generated_at:
            raise ValueError("rank must be 1..5 and expiry must follow generation")
        _mapping(self.regime_snapshot, "regime_snapshot")
        for name in ("requested_units", "requested_notional", "estimated_cost"):
            finite(getattr(self, name), name, minimum=0.0)
        object.__setattr__(self, "regime_snapshot", MappingProxyType(dict(self.regime_snapshot)))
        if not isinstance(self.contributing_feature_ids, tuple) or not isinstance(self.evidence_provenance_ids, tuple):
            raise ValueError("provenance identifiers must be tuples")

    def to_dict(self) -> dict[str, Any]:
        return {"intent_id": self.intent_id, "strategy_version": self.strategy_version,
                "instrument_id": self.instrument_id, "execution_symbol": self.execution_symbol,
                "generated_at": self.generated_at.isoformat(), "direction": self.direction.value,
                "opportunity_score": self.opportunity_score, "opportunity_rank": self.opportunity_rank,
                "regime_snapshot": dict(self.regime_snapshot), "geometry": self.geometry.to_dict(),
                "requested_units": self.requested_units, "requested_notional": self.requested_notional,
                "estimated_cost": self.estimated_cost, "contributing_feature_ids": list(self.contributing_feature_ids),
                "evidence_provenance_ids": list(self.evidence_provenance_ids), "expires_at": self.expires_at.isoformat()}


@dataclass(frozen=True)
class RiskDecision:
    intent_id: str
    evaluated_at: datetime
    approved: bool
    reduced_size: bool
    authorized_units: float
    authorized_notional: float
    maximum_loss_monetary: float
    committed_margin: float
    remaining_portfolio_risk_budget: float
    hard_limit_checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "evaluated_at", utc_timestamp(self.evaluated_at))
        if not self.intent_id:
            raise ValueError("intent identity is required")
        for name in ("authorized_units", "authorized_notional", "maximum_loss_monetary", "committed_margin", "remaining_portfolio_risk_budget"):
            finite(getattr(self, name), name, minimum=0.0)
        _mapping(self.hard_limit_checks, "hard_limit_checks")
        if not all(isinstance(key, str) and isinstance(value, bool) for key, value in self.hard_limit_checks.items()):
            raise ValueError("hard-limit checks must map names to booleans")
        object.__setattr__(self, "hard_limit_checks", MappingProxyType(dict(self.hard_limit_checks)))
        if self.approved and self.rejection_reasons:
            raise ValueError("approved risk decisions cannot have rejection reasons")

    def to_dict(self) -> dict[str, Any]:
        return {"intent_id": self.intent_id, "evaluated_at": self.evaluated_at.isoformat(),
                "approved": self.approved, "reduced_size": self.reduced_size,
                "authorized_units": self.authorized_units, "authorized_notional": self.authorized_notional,
                "maximum_loss_monetary": self.maximum_loss_monetary, "committed_margin": self.committed_margin,
                "remaining_portfolio_risk_budget": self.remaining_portfolio_risk_budget,
                "hard_limit_checks": dict(self.hard_limit_checks), "rejection_reasons": list(self.rejection_reasons)}


@dataclass(frozen=True)
class OrderIntent:
    order_intent_id: str
    intent_id: str
    instrument_id: str
    broker_symbol: str
    side: str
    order_type: str
    price: float
    quantity: float
    time_in_force: str
    client_order_id: str
    mode: str
    dispatched_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "dispatched_at", utc_timestamp(self.dispatched_at))
        if not all((self.order_intent_id, self.intent_id, self.instrument_id, self.broker_symbol, self.client_order_id)):
            raise ValueError("order identity is required")
        if self.side not in {"BUY", "SELL"} or self.order_type not in {"MARKET", "LIMIT", "STOP"}:
            raise ValueError("unsupported order side or type")
        if self.time_in_force not in {"GTC", "IOC", "DAY"} or self.mode not in {"PAPER", "DEMO", "LIVE"}:
            raise ValueError("unsupported order time-in-force or mode")
        finite(self.price, "price", minimum=0.0)
        finite(self.quantity, "quantity", minimum=0.0)

    def to_dict(self) -> dict[str, Any]:
        result = {"order_intent_id": self.order_intent_id, "intent_id": self.intent_id,
                  "instrument_id": self.instrument_id, "broker_symbol": self.broker_symbol,
                  "side": self.side, "order_type": self.order_type, "price": self.price,
                  "quantity": self.quantity, "time_in_force": self.time_in_force,
                  "client_order_id": self.client_order_id, "mode": self.mode,
                  "dispatched_at": self.dispatched_at.isoformat()}
        return result


@dataclass(frozen=True)
class MetricContext:
    sampling_basis: str
    period_duration: str
    trading_calendar: str
    annualization_factor: Optional[float]

    def __post_init__(self) -> None:
        if self.sampling_basis not in {"TRADE_BY_TRADE", "PERIODIC_CALENDAR"}:
            raise ValueError("unsupported metric sampling basis")
        if not self.period_duration or not self.trading_calendar:
            raise ValueError("metric period and calendar are required")
        if self.annualization_factor is not None:
            finite(self.annualization_factor, "annualization_factor", minimum=0.0)

    def to_dict(self) -> dict[str, Any]:
        return {"sampling_basis": self.sampling_basis, "period_duration": self.period_duration,
                "trading_calendar": self.trading_calendar, "annualization_factor": self.annualization_factor}
