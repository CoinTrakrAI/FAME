"""
Order routing and plan execution utilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from .broker_base import BrokerAdapter, OrderRequest, OrderResult, OrderSide
from .execution_monitor import ExecutionMonitor


@dataclass(slots=True)
class ExecutionPlan:
    target_positions: Dict[str, float]
    current_positions: Dict[str, float]
    orders: List[OrderRequest] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.orders


class OrderRouter:
    """
    Converts position deltas into executable orders and routes them through a broker.
    """

    def __init__(self, monitor: Optional[ExecutionMonitor] = None) -> None:
        self.monitor = monitor or ExecutionMonitor()

    # ------------------------------------------------------------------ #
    def build_plan(
        self,
        target_positions: Dict[str, float],
        current_positions: Optional[Dict[str, float]] = None,
        price_map: Optional[Dict[str, float]] = None,
    ) -> ExecutionPlan:
        current_positions = current_positions or {}
        price_map = price_map or {}

        orders: List[OrderRequest] = []
        for symbol, target in target_positions.items():
            current = current_positions.get(symbol, 0.0)
            delta = target - current
            if abs(delta) < 1e-6:
                continue
            side = OrderSide.BUY if delta > 0 else OrderSide.SELL
            orders.append(
                OrderRequest(
                    symbol=symbol,
                    side=side,
                    quantity=abs(delta),
                    metadata={"price": price_map.get(symbol)},
                )
            )

        for symbol, current in current_positions.items():
            if symbol not in target_positions and abs(current) > 1e-6:
                side = OrderSide.SELL if current > 0 else OrderSide.BUY
                orders.append(
                    OrderRequest(
                        symbol=symbol,
                        side=side,
                        quantity=abs(current),
                        metadata={"price": price_map.get(symbol)},
                    )
                )

        return ExecutionPlan(
            target_positions=dict(target_positions),
            current_positions=dict(current_positions),
            orders=orders,
        )

    # ------------------------------------------------------------------ #
    def execute_plan(
        self,
        plan: ExecutionPlan,
        broker: BrokerAdapter,
        price_map: Optional[Dict[str, float]] = None,
    ) -> List[OrderResult]:
        price_map = price_map or {}
        results: List[OrderResult] = []
        if plan.is_empty():
            return results

        for request in plan.orders:
            price_hint = price_map.get(request.symbol)
            if price_hint is not None:
                request.metadata.setdefault("price", price_hint)

            self.monitor.record_submission(request)
            result = broker.submit_order(request)
            self.monitor.record_result(result)
            results.append(result)
        return results

    def metrics(self) -> Dict[str, float]:
        return self.monitor.metrics_summary()

