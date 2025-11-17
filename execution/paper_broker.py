"""
In-memory paper broker implementation for testing and Stage 2 execution.
"""

from __future__ import annotations

import math
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from .broker_base import BrokerAdapter, OrderRequest, OrderResult, OrderSide, OrderStatus


@dataclass(slots=True)
class PaperOrder:
    order_id: str
    request: OrderRequest
    status: OrderStatus = OrderStatus.NEW
    filled_qty: float = 0.0
    avg_price: float = 0.0
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PaperBroker(BrokerAdapter):
    """
    Simple deterministic execution engine with optional slippage.
    """

    def __init__(
        self,
        starting_cash: float = 1_000_000.0,
        default_price: float = 100.0,
        slippage_bps: float = 5.0,
    ) -> None:
        self._positions: Dict[str, float] = {}
        self._cash = starting_cash
        self._default_price = default_price
        self._slippage_bps = slippage_bps
        self._prices: Dict[str, float] = {}
        self._orders: Dict[str, PaperOrder] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    def get_positions(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._positions)

    def get_cash_balance(self) -> float:
        with self._lock:
            return float(self._cash)

    def current_price(self, symbol: str) -> Optional[float]:
        return self._prices.get(symbol, self._default_price)

    def update_market_price(self, symbol: str, price: float) -> None:
        with self._lock:
            self._prices[symbol] = float(price)

    def submit_order(self, order: OrderRequest) -> OrderResult:
        with self._lock:
            order_id = order.ensure_id()
            price = self._determine_price(order)
            filled_qty = float(abs(order.quantity))
            notional = filled_qty * price

            side_multiplier = 1.0 if order.side == OrderSide.BUY else -1.0
            if order.side == OrderSide.BUY and self._cash < notional:
                status = OrderStatus.REJECTED
                filled_qty = 0.0
                notional = 0.0
            else:
                status = OrderStatus.FILLED
                self._positions[order.symbol] = self._positions.get(order.symbol, 0.0) + (
                    side_multiplier * filled_qty
                )
                self._cash -= side_multiplier * notional

            now = datetime.now(timezone.utc)
            paper_order = PaperOrder(
                order_id=order_id,
                request=order,
                status=status,
                filled_qty=filled_qty,
                avg_price=price if filled_qty else 0.0,
                submitted_at=now,
                completed_at=now,
            )
            self._orders[order_id] = paper_order

            return OrderResult(
                order_id=order_id,
                symbol=order.symbol,
                side=order.side,
                status=status,
                quantity=order.quantity,
                filled_qty=filled_qty,
                avg_fill_price=paper_order.avg_price,
                notional=notional,
                submitted_at=paper_order.submitted_at,
                completed_at=paper_order.completed_at,
                metadata={"slippage_bps": self._slippage_bps if filled_qty else 0.0},
            )

    def cancel_order(self, order_id: str) -> None:
        with self._lock:
            order = self._orders.get(order_id)
            if order and order.status not in {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}:
                order.status = OrderStatus.CANCELLED
                order.completed_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------ #
    def _determine_price(self, order: OrderRequest) -> float:
        base_price = order.metadata.get("price")
        if base_price is None:
            base_price = self._prices.get(order.symbol, order.limit_price or self._default_price)

        base_price = max(0.01, float(base_price))
        slippage = base_price * (self._slippage_bps / 10_000.0)
        return base_price + slippage if order.side == OrderSide.BUY else base_price - slippage

