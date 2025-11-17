"""
Execution service facade coordinating broker, router and monitoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.production_logger import get_production_logger

from execution import (
    ExecutionMonitor,
    ExecutionPlan,
    OrderRequest,
    OrderResult,
    OrderRouter,
    PaperBroker,
    BrokerAdapter,
    OrderStatus,
)
from monitoring.tracing import span


@dataclass(slots=True)
class ExecutionService:
    broker: BrokerAdapter = field(default_factory=PaperBroker)
    monitor: ExecutionMonitor = field(default_factory=ExecutionMonitor)
    router: OrderRouter = field(init=False)
    logger = get_production_logger().get_logger()

    def __post_init__(self) -> None:
        self.router = OrderRouter(self.monitor)

    # ------------------------------------------------------------------ #
    def update_price_marks(self, price_map: Dict[str, float]) -> None:
        for symbol, price in price_map.items():
            self.broker.update_market_price(symbol, price)

    def plan_execution(
        self,
        portfolio_payload: Dict[str, Dict],
        price_map: Optional[Dict[str, float]] = None,
    ) -> ExecutionPlan:
        target_positions = portfolio_payload.get("positions") or {}
        current_positions = self.broker.get_positions()
        return self.router.build_plan(target_positions, current_positions, price_map=price_map)

    def execute_portfolio(
        self,
        portfolio_payload: Dict[str, Dict],
        price_map: Optional[Dict[str, float]] = None,
    ) -> Dict[str, any]:
        with span(
            "ExecutionService.execute_portfolio",
            {"orders_planned": len(portfolio_payload.get("positions") or {})},
        ):
            plan = self.plan_execution(portfolio_payload, price_map=price_map)
            results: List[OrderResult] = []
            if not plan.is_empty():
                results = self.router.execute_plan(plan, self.broker, price_map=price_map)
                self._log_execution(results, plan)
            return {
                "plan": plan,
                "orders": results,
                "metrics": self.monitor.metrics_summary(),
                "positions": self.broker.get_positions(),
                "cash": self.broker.get_cash_balance(),
            }

    def metrics(self) -> Dict[str, float]:
        return self.monitor.metrics_summary()

    def _log_execution(self, orders: List[OrderResult], plan: ExecutionPlan) -> None:
        if not orders:
            return
        summary = {
            "submitted": len(orders),
            "filled": sum(1 for o in orders if o.status == OrderStatus.FILLED),
            "rejected": sum(1 for o in orders if o.status == OrderStatus.REJECTED),
        }
        payload = {
            "plan_target_positions": plan.target_positions,
            "current_positions": plan.current_positions,
            "orders": [
                {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "status": order.status.value,
                    "quantity": order.quantity,
                    "filled_qty": order.filled_qty,
                    "avg_fill_price": order.avg_fill_price,
                }
                for order in orders
            ],
            "summary": summary,
        }
        self.logger.info("Execution plan processed", extra={"execution_event": payload})


__all__ = ["ExecutionService"]

