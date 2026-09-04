"""Vendor-neutral market-data and paper-execution contracts.

There is deliberately no live execution implementation in HR10.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


class LiveExecutionDisabled(RuntimeError):
    pass


@dataclass(frozen=True)
class Quote:
    instrument: str
    price: float
    timestamp: datetime
    state: str
    source: str


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


class ExecutionProvider(Protocol):
    def get_account_state(self) -> dict: ...
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

    def submit_order(self, order: dict):
        raise LiveExecutionDisabled("HR10 is preview-only; live order submission is disabled")

    def cancel_order(self, order_id: str):
        raise LiveExecutionDisabled("HR10 has no live orders to cancel")

    def get_order_status(self, order_id: str):
        return {"order_id": order_id, "status": "NOT_SUBMITTED", "mode": "paper",
                "timestamp": datetime.now(timezone.utc).isoformat()}
