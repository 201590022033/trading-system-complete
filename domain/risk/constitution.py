"""Immutable, broker-neutral inputs and outputs for canonical risk evaluation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Mapping


VERSION = "risk-exposure-v1"


class RiskStatus(str, Enum):
    APPROVED = "APPROVED"
    REDUCED = "REDUCED"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    BLOCKED = "BLOCKED"


def _utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _number(value: float | None, name: str, *, positive: bool = False) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{name} must be {'positive' if positive else 'nonnegative'} and finite")


@dataclass(frozen=True)
class RiskLimits:
    """Operator controls. None means explicitly NOT_CONFIGURED, never unlimited."""

    limits_id: str
    effective_at: datetime
    max_risk_per_trade_fraction: float | None = None
    max_daily_loss_monetary: float | None = None
    max_portfolio_open_risk_fraction: float | None = None
    max_notional_exposure_fraction: float | None = None
    max_gearing: float | None = None
    max_margin_utilization_fraction: float | None = None
    max_instrument_exposure_fraction: float | None = None
    max_sector_exposure_fraction: float | None = None
    max_correlated_exposure_fraction: float | None = None
    max_drawdown_fraction: float | None = None
    emergency_trading_pause: bool | None = None
    version: str = VERSION

    def __post_init__(self):
        if not self.limits_id:
            raise ValueError("limits identity is required")
        object.__setattr__(self, "effective_at", _utc(self.effective_at, "effective_at"))
        for name in self.__dataclass_fields__:
            if name.endswith("fraction"):
                value = getattr(self, name)
                _number(value, name)
                if value is not None and value > 1:
                    raise ValueError(f"{name} cannot exceed one")
        _number(self.max_daily_loss_monetary, "max_daily_loss_monetary")
        _number(self.max_gearing, "max_gearing", positive=True)
        if self.emergency_trading_pause not in {None, True, False}:
            raise ValueError("emergency pause must be configured boolean or None")

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(name for name in self.__dataclass_fields__
                     if name.startswith("max_") and getattr(self, name) is None) + (() if self.emergency_trading_pause is not None else ("emergency_trading_pause",))


@dataclass(frozen=True)
class PortfolioRiskState:
    state_id: str
    as_of: datetime
    account_currency: str
    equity: float | None
    cash: float | None
    margin_available: float | None
    margin_used: float | None
    current_open_risk: float | None
    daily_realised_loss: float | None
    daily_unrealised_loss: float | None
    current_drawdown_fraction: float | None
    gross_notional: float | None
    instrument_exposure: Mapping[str, float] = field(default_factory=dict)
    sector_exposure: Mapping[str, float] = field(default_factory=dict)
    correlated_exposure: Mapping[str, float] = field(default_factory=dict)
    kill_switch_active: bool = False

    def __post_init__(self):
        if not self.state_id or len(self.account_currency) != 3 or not self.account_currency.isupper():
            raise ValueError("portfolio identity and uppercase account currency are required")
        object.__setattr__(self, "as_of", _utc(self.as_of, "as_of"))
        for name in ("equity", "cash", "margin_available", "margin_used", "current_open_risk",
                     "daily_realised_loss", "daily_unrealised_loss", "current_drawdown_fraction", "gross_notional"):
            _number(getattr(self, name), name)
        for name in ("instrument_exposure", "sector_exposure", "correlated_exposure"):
            values = dict(getattr(self, name))
            for key, value in values.items():
                if not key:
                    raise ValueError(f"{name} keys cannot be empty")
                _number(value, name)
            object.__setattr__(self, name, MappingProxyType(values))


@dataclass(frozen=True)
class InstrumentRiskMetadata:
    instrument_id: str
    as_of: datetime
    price_currency: str | None
    contract_multiplier: float | None
    lot_size: float | None
    minimum_deal_size: float | None
    margin_factor: float | None
    sector: str | None = None
    correlation_buckets: tuple[str, ...] = ()
    source: str = "UNAVAILABLE"

    def __post_init__(self):
        if not self.instrument_id:
            raise ValueError("instrument identity is required")
        object.__setattr__(self, "as_of", _utc(self.as_of, "as_of"))
        if self.price_currency is not None and (len(self.price_currency) != 3 or not self.price_currency.isupper()):
            raise ValueError("price currency must be uppercase ISO-style code")
        for name in ("contract_multiplier", "lot_size", "minimum_deal_size"):
            _number(getattr(self, name), name, positive=True)
        _number(self.margin_factor, "margin_factor")
        if self.margin_factor is not None and self.margin_factor > 1:
            raise ValueError("margin factor must be a fraction")


@dataclass(frozen=True)
class FXConversion:
    base_currency: str
    quote_currency: str
    rate: float
    as_of: datetime
    source: str

    def __post_init__(self):
        if any(len(value) != 3 or not value.isupper() for value in (self.base_currency, self.quote_currency)):
            raise ValueError("FX currencies must be uppercase ISO-style codes")
        _number(self.rate, "rate", positive=True)
        object.__setattr__(self, "as_of", _utc(self.as_of, "as_of"))
        if not self.source:
            raise ValueError("FX provenance is required")


@dataclass(frozen=True)
class ApprovedRiskIntent:
    policy_id: str
    instrument_id: str
    position_size: float
    notional: float
    gearing: float
    estimated_margin: float
    estimated_loss_at_stop: float
    currency: str


@dataclass(frozen=True)
class RiskEvaluation:
    evaluation_id: str
    risk_version: str
    evaluated_at: datetime
    policy_id: str
    instrument_id: str
    status: RiskStatus
    requested_loss_budget: float | None
    requested_risk_fraction: float | None
    requested_gearing: float | None
    stop_distance: float | None
    stop_price: float | None
    entry_reference: str
    approved_loss_budget: float | None
    approved_position_size: float | None
    approved_notional: float | None
    approved_gearing: float | None
    estimated_margin: float | None
    estimated_loss_at_stop: float | None
    reduction_reasons: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    hard_limit_checks: Mapping[str, str]
    provenance: Mapping[str, object]
    approved_intent: ApprovedRiskIntent | None = None

    def __post_init__(self):
        object.__setattr__(self, "evaluated_at", _utc(self.evaluated_at, "evaluated_at"))
        object.__setattr__(self, "hard_limit_checks", MappingProxyType(dict(self.hard_limit_checks)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))
        if self.status not in {RiskStatus.APPROVED, RiskStatus.REDUCED} and any(
                value is not None for value in (self.approved_position_size, self.approved_notional, self.approved_gearing,
                                                self.estimated_margin, self.estimated_loss_at_stop, self.approved_intent)):
            raise ValueError("non-approved evaluations cannot carry an approved size")
        if self.status in {RiskStatus.APPROVED, RiskStatus.REDUCED} and self.approved_intent is None:
            raise ValueError("approved evaluation requires an immutable approved intent")

    def to_dict(self) -> dict[str, object]:
        return {
            "evaluation_id": self.evaluation_id, "risk_version": self.risk_version,
            "evaluated_at": self.evaluated_at.isoformat(), "policy_id": self.policy_id,
            "instrument_id": self.instrument_id, "status": self.status.value,
            "requested_loss_budget": self.requested_loss_budget,
            "requested_risk_fraction": self.requested_risk_fraction,
            "requested_gearing": self.requested_gearing, "stop_distance": self.stop_distance,
            "stop_price": self.stop_price, "entry_reference": self.entry_reference,
            "approved_loss_budget": self.approved_loss_budget,
            "approved_position_size": self.approved_position_size,
            "approved_notional": self.approved_notional, "approved_gearing": self.approved_gearing,
            "estimated_margin": self.estimated_margin,
            "estimated_loss_at_stop": self.estimated_loss_at_stop,
            "reduction_reasons": list(self.reduction_reasons),
            "rejection_reasons": list(self.rejection_reasons), "blockers": list(self.blockers),
            "hard_limit_checks": dict(self.hard_limit_checks), "provenance": dict(self.provenance),
            "approved_intent": None if self.approved_intent is None else dict(self.approved_intent.__dict__),
        }
