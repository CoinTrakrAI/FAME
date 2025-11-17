"""
Abstract broker adapter definitions for execution services.
"""

from __future__ import annotations

import abc
import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, enum.Enum):
    NEW = "new"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(slots=True)
class OrderRequest:
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    time_in_force: str = "GTC"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def ensure_id(self) -> str:
        request_id = self.metadata.get("request_id")
        if not request_id:
            request_id = uuid.uuid4().hex
            self.metadata["request_id"] = request_id
        return request_id


@dataclass(slots=True)
class OrderResult:
    order_id: str
    symbol: str
    side: OrderSide
    status: OrderStatus
    quantity: float
    filled_qty: float
    avg_fill_price: float
    notional: float
    submitted_at: datetime
    completed_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PositionSnapshot:
    symbol: str
    quantity: float
    price: float
    timestamp: datetime


class BrokerAdapter(abc.ABC):
    """
    Interface for broker implementations.
    """

    @abc.abstractmethod
    def get_positions(self) -> Dict[str, float]:
        """Return current positions map symbol -> quantity."""

    @abc.abstractmethod
    def get_cash_balance(self) -> float:
        """Return current cash balance."""

    @abc.abstractmethod
    def submit_order(self, order: OrderRequest) -> OrderResult:
        """Submit an order and return execution result."""

    @abc.abstractmethod
    def cancel_order(self, order_id: str) -> None:
        """Cancel an active order if possible."""

    def update_market_price(self, symbol: str, price: float) -> None:
        """Optional hint to update internal price marks."""

    def current_price(self, symbol: str) -> Optional[float]:
        """Optional helper for mark price lookup."""
        return None

    def snapshot(self) -> Iterable[PositionSnapshot]:
        now = datetime.now(timezone.utc)
        for symbol, qty in self.get_positions().items():
            yield PositionSnapshot(
                symbol=symbol,
                quantity=qty,
                price=self.current_price(symbol) or 0.0,
                timestamp=now,
            )

