"""
Execution monitoring and telemetry helpers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict

from .broker_base import OrderRequest, OrderResult, OrderStatus


@dataclass(slots=True)
class ExecutionMetrics:
    orders_submitted: int = 0
    orders_filled: int = 0
    orders_rejected: int = 0
    notional_traded: float = 0.0
    slippage_bps_accumulated: float = 0.0
    slippage_events: int = 0
    last_latency_ms: float = 0.0
    total_latency_ms: float = 0.0


class ExecutionMonitor:
    def __init__(self) -> None:
        self._metrics = ExecutionMetrics()
        self._open_orders: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}

    def record_submission(self, order: OrderRequest) -> None:
        request_id = order.ensure_id()
        self._metrics.orders_submitted += 1
        self._open_orders[request_id] = order.quantity
        self._start_times[request_id] = time.time()

    def record_result(self, result: OrderResult) -> None:
        self._open_orders.pop(result.order_id, None)
        start = self._start_times.pop(result.order_id, None)
        if start is not None:
            latency = max(0.0, (time.time() - start) * 1000.0)
            self._metrics.last_latency_ms = latency
            self._metrics.total_latency_ms += latency

        if result.status == OrderStatus.FILLED:
            self._metrics.orders_filled += 1
            self._metrics.notional_traded += result.notional
        elif result.status in {OrderStatus.REJECTED, OrderStatus.CANCELLED}:
            self._metrics.orders_rejected += 1

        slippage_bps = float(result.metadata.get("slippage_bps", 0.0))
        if slippage_bps:
            self._metrics.slippage_bps_accumulated += slippage_bps
            self._metrics.slippage_events += 1

    def metrics_summary(self) -> Dict[str, float]:
        metrics = self._metrics
        avg_slippage = (
            metrics.slippage_bps_accumulated / metrics.slippage_events
            if metrics.slippage_events
            else 0.0
        )
        avg_latency = (
            metrics.total_latency_ms / max(metrics.orders_filled + metrics.orders_rejected, 1)
        )
        return {
            "orders_submitted": metrics.orders_submitted,
            "orders_filled": metrics.orders_filled,
            "orders_rejected": metrics.orders_rejected,
            "execution_notional": metrics.notional_traded,
            "execution_slippage_bps_avg": avg_slippage,
            "execution_latency_ms_avg": avg_latency,
            "execution_latency_ms_last": metrics.last_latency_ms,
        }

