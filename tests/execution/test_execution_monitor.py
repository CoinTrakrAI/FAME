from datetime import datetime, timezone

from execution.execution_monitor import ExecutionMonitor
from execution.broker_base import OrderRequest, OrderResult, OrderSide, OrderStatus


def test_execution_monitor_tracks_slippage_and_latency():
    monitor = ExecutionMonitor()
    order = OrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=10)
    monitor.record_submission(order)

    submitted_at = datetime.now(timezone.utc)
    result = OrderResult(
        order_id=order.ensure_id(),
        symbol="AAPL",
        side=OrderSide.BUY,
        status=OrderStatus.FILLED,
        quantity=10,
        filled_qty=10,
        avg_fill_price=10.5,
        notional=105.0,
        submitted_at=submitted_at,
        completed_at=submitted_at,
        metadata={"slippage_bps": 5.0},
    )

    monitor.record_result(result)
    summary = monitor.metrics_summary()
    assert summary["orders_submitted"] == 1
    assert summary["orders_filled"] == 1
    assert summary["execution_notional"] == 105.0
    assert summary["execution_slippage_bps_avg"] == 5.0

