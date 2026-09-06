"""Fail-closed Standard Bank ViewPoint broker boundary.

ViewPoint payloads and selectors are intentionally not assumed here.  The
adapter accepts only verified/supplied payloads and never submits an order.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from provider_interfaces import LiveExecutionDisabled


class Availability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_AUTHENTICATED = "not_authenticated"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BrokerAccountState:
    broker: str
    account_id: str
    display_name: str | None = None
    account_type: str | None = None
    currency: str | None = None
    status: str = "unknown"
    observed_at: datetime | None = None
    provenance: str = "unavailable"


@dataclass(frozen=True)
class CashBalance:
    account_id: str
    currency: str | None = None
    available: float | None = None
    buying_power: float | None = None
    margin_available: float | None = None
    reserved: float | None = None
    observed_at: datetime | None = None
    provenance: str = "unavailable"


@dataclass(frozen=True)
class BrokerPosition:
    account_id: str
    instrument: str
    broker_instrument_id: str | None = None
    quantity: float | None = None
    average_price: float | None = None
    current_price: float | None = None
    market_value: float | None = None
    unrealised_pnl: float | None = None
    currency: str | None = None
    observed_at: datetime | None = None
    provenance: str = "unavailable"


@dataclass(frozen=True)
class BrokerOrder:
    broker_order_id: str | None
    account_id: str
    instrument: str
    side: str
    quantity: float
    filled_quantity: float = 0
    remaining_quantity: float | None = None
    order_type: str | None = None
    limit_price: float | None = None
    average_fill_price: float | None = None
    status: str = "UNKNOWN"
    created_at: datetime | None = None
    last_observed_at: datetime | None = None


@dataclass(frozen=True)
class BrokerInstrumentMapping:
    research_instrument: str
    broker: str
    broker_instrument_id: str
    asset_class: str | None = None


@dataclass(frozen=True)
class PreparedOrder:
    intent_id: str
    account_id: str
    instrument: str
    side: str
    quantity: float
    order_type: str
    limit_price: float | None
    status: str = "PREPARED"
    execution_mode: str = "PREPARE_ONLY"


class ViewPointAdapter:
    """Transport-neutral scaffold; live payload transport is not verified."""
    broker = "standard_bank_viewpoint"

    def __init__(self, payload: dict[str, Any] | None = None,
                 availability: Availability = Availability.UNKNOWN):
        self.availability = availability
        self.payload = payload or {}

    def _guard(self):
        if self.availability is not Availability.AVAILABLE:
            raise RuntimeError(f"ViewPoint unavailable: {self.availability.value}")

    def get_accounts(self) -> list[BrokerAccountState]:
        self._guard()
        return list(self.payload.get("accounts", []))

    def get_cash(self, account_id: str) -> CashBalance:
        self._guard()
        value = self.payload.get("cash", {}).get(account_id)
        if value is None:
            return CashBalance(account_id=account_id)
        return value if isinstance(value, CashBalance) else CashBalance(account_id, **value)

    def get_positions(self, account_id: str) -> list[BrokerPosition]:
        self._guard()
        return list(self.payload.get("positions", {}).get(account_id, []))

    def get_open_orders(self, account_id: str) -> list[BrokerOrder]:
        self._guard()
        return list(self.payload.get("open_orders", {}).get(account_id, []))

    def prepare_order(self, intent: dict[str, Any], *, mapping: BrokerInstrumentMapping | None,
                      cash: CashBalance | None, positions: list[BrokerPosition] | None = None,
                      open_orders: list[BrokerOrder] | None = None) -> PreparedOrder:
        self._guard()
        if mapping is None:
            raise ValueError("broker instrument mapping is required")
        if cash is None or cash.available is None:
            raise ValueError("authoritative available cash is required")
        qty = float(intent["quantity"]); price = intent.get("limit_price")
        if qty <= 0 or intent.get("side") not in {"BUY", "SELL"}:
            raise ValueError("invalid order intent")
        if intent["side"] == "BUY" and price is not None and qty * float(price) > cash.available:
            raise ValueError("insufficient broker-observed cash")
        for order in open_orders or []:
            if order.instrument == intent["instrument"] and order.side == intent["side"] and order.remaining_quantity:
                raise ValueError("duplicate/pending order protection")
        return PreparedOrder(intent["intent_id"], intent["account_id"], mapping.broker_instrument_id,
                             intent["side"], qty, intent.get("order_type", "LIMIT"), price)

    def submit_order(self, prepared: PreparedOrder):
        raise LiveExecutionDisabled("ViewPoint is prepare-only; final submission remains human controlled")

    def reconcile_order(self, broker_order_id: str) -> BrokerOrder:
        self._guard()
        for order in self.payload.get("order_history", []):
            if order.broker_order_id == broker_order_id:
                return order
        return BrokerOrder(broker_order_id, "unknown", "unknown", "UNKNOWN", 0, status="UNKNOWN")
