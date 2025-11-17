from execution import ExecutionMonitor, OrderRouter, PaperBroker
from execution.broker_base import OrderResult, OrderSide


def test_order_router_builds_plan_with_deltas():
    router = OrderRouter()
    plan = router.build_plan({"AAPL": 10.0}, {"AAPL": 4.0})
    assert len(plan.orders) == 1
    order = plan.orders[0]
    assert order.symbol == "AAPL"
    assert order.side == OrderSide.BUY
    assert order.quantity == 6.0


def test_order_router_executes_plan_with_paper_broker():
    monitor = ExecutionMonitor()
    router = OrderRouter(monitor=monitor)
    broker = PaperBroker(starting_cash=1_000.0, default_price=10.0, slippage_bps=0.0)
    plan = router.build_plan({"AAPL": 5.0}, {})
    results = router.execute_plan(plan, broker, price_map={"AAPL": 10.0})
    assert isinstance(results, list) and results
    assert isinstance(results[0], OrderResult)
    metrics = monitor.metrics_summary()
    assert metrics["orders_submitted"] == 1
    assert metrics["orders_filled"] == 1

