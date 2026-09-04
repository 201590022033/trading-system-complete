"""Vendor-neutral market-data and paper-execution contracts.

There is deliberately no live execution implementation in HR10.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol


class LiveExecutionDisabled(RuntimeError):
    pass


class SuggestionState(str, Enum):
    RESEARCH = "research"
    SHADOW = "shadow"
    ADMISSIBLE = "admissible"
    REJECTED = "rejected"


@dataclass(frozen=True)
class TradeSuggestion:
    suggestion_id: str
    instrument: str
    timestamp: datetime
    data_timestamp: datetime
    data_source: str
    direction: str
    horizon: str
    entry: float
    stop: float
    target: float
    position_size: float
    defined_risk: float
    confidence: float
    evidence: str
    rationale: tuple[str, ...]
    strategy_version: str
    state: SuggestionState
    stale_after: datetime

    def __post_init__(self):
        if any(value.tzinfo is None or value.utcoffset() is None
               for value in (self.timestamp, self.data_timestamp, self.stale_after)):
            raise ValueError("suggestion timestamps must be timezone-aware")
        if self.direction not in {"buy", "sell", "no_trade"}:
            raise ValueError("direction must be buy, sell or no_trade")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between zero and one")
        if self.data_timestamp > self.timestamp or self.stale_after <= self.timestamp:
            raise ValueError("invalid data or expiry chronology")
        if min(self.entry, self.stop, self.target, self.position_size, self.defined_risk) < 0:
            raise ValueError("price, size and risk fields cannot be negative")

    def safety(self, now: datetime | None = None) -> dict:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("safety clock must be timezone-aware")
        stale = now >= self.stale_after
        admitted = self.state is SuggestionState.ADMISSIBLE
        actionable = admitted and not stale and self.direction in {"buy", "sell"}
        reasons = []
        if not admitted:
            reasons.append(f"strategy_state_{self.state.value}")
        if stale:
            reasons.append("stale")
        if self.direction == "no_trade":
            reasons.append("no_trade")
        return {"stale": stale, "admitted": admitted, "actionable": actionable,
                "reasons": reasons, "live_execution_available": False}

    def to_dict(self, now: datetime | None = None) -> dict:
        result = asdict(self)
        result["state"] = self.state.value
        for name in ("timestamp", "data_timestamp", "stale_after"):
            result[name] = result[name].isoformat()
        result["rationale"] = list(self.rationale)
        result["safety"] = self.safety(now)
        return result


@dataclass(frozen=True)
class Quote:
    instrument: str
    price: float
    timestamp: datetime
    state: str
    source: str

    def __post_init__(self):
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("quote timestamp must be timezone-aware")
        if self.price <= 0 or not self.instrument or not self.source:
            raise ValueError("quote requires positive price, instrument and source")
        if self.state not in {"historical", "research", "shadow", "delayed", "live", "simulated"}:
            raise ValueError("unsupported quote data state")


@dataclass(frozen=True)
class BrokerAccount:
    provider: str
    account_reference: str
    mode: str
    currency: str

    def __post_init__(self):
        if self.mode not in {"paper", "read_only"}:
            raise ValueError("OI1 broker accounts must be paper or read-only")


@dataclass(frozen=True)
class OrderPreview:
    instrument: str
    side: str
    quantity: float
    order_type: str
    estimated_price: float
    estimated_cost: float
    mode: str = "paper"


class MarketDataProvider(Protocol):
    def get_quote(self, instrument: str) -> Quote: ...
    def get_bars(self, instrument: str, timeframe: str, start: datetime, end: datetime): ...
    def get_order_book(self, instrument: str): ...
    def get_market_status(self, instrument: str) -> str: ...
    def get_data_timestamp(self) -> datetime: ...


class ResearchDataProvider(Protocol):
    def get_point_in_time_dataset(self, dataset_id: str, as_of: datetime): ...
    def get_provenance(self, dataset_id: str) -> dict: ...


class SignalEngine(Protocol):
    def suggest(self, research_data) -> TradeSuggestion: ...


class ExecutionProvider(Protocol):
    def get_account_state(self) -> BrokerAccount | dict: ...
    def get_positions(self) -> dict: ...
    def preview_order(self, order: dict) -> OrderPreview: ...
    def submit_order(self, order: dict): ...
    def cancel_order(self, order_id: str): ...
    def get_order_status(self, order_id: str): ...


class PaperExecutionProvider:
    """Preview-only boundary: all state-changing methods hard-fail."""

    def get_account_state(self) -> dict:
        return {"mode": "paper", "currency": "ZAR", "cash": 0.0}

    def get_positions(self) -> dict:
        return {"mode": "paper", "positions": []}

    def preview_order(self, order: dict) -> OrderPreview:
        required = {"instrument", "side", "quantity", "order_type", "estimated_price"}
        missing = required - order.keys()
        if missing:
            raise ValueError(f"missing order fields: {sorted(missing)}")
        if order["side"] not in {"buy", "sell"} or float(order["quantity"]) <= 0:
            raise ValueError("paper preview requires buy/sell and positive quantity")
        price, quantity = float(order["estimated_price"]), float(order["quantity"])
        return OrderPreview(order["instrument"], order["side"], quantity,
                            order["order_type"], price, price * quantity)

    def preview_suggestion(self, suggestion: TradeSuggestion,
                           now: datetime | None = None) -> OrderPreview:
        safety = suggestion.safety(now)
        if not safety["actionable"]:
            raise LiveExecutionDisabled(
                "suggestion is not eligible for preview: " + ", ".join(safety["reasons"])
            )
        return self.preview_order({"instrument": suggestion.instrument,
            "side": suggestion.direction, "quantity": suggestion.position_size,
            "order_type": "limit", "estimated_price": suggestion.entry})

    def submit_order(self, order: dict):
        raise LiveExecutionDisabled("HR10 is preview-only; live order submission is disabled")

    def cancel_order(self, order_id: str):
        raise LiveExecutionDisabled("HR10 has no live orders to cancel")

    def get_order_status(self, order_id: str):
        return {"order_id": order_id, "status": "NOT_SUBMITTED", "mode": "paper",
                "timestamp": datetime.now(timezone.utc).isoformat()}
