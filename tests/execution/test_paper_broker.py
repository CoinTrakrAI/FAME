from execution.paper_broker import PaperBroker
from execution.broker_base import OrderRequest, OrderSide, OrderStatus


def test_paper_broker_executes_buy_order():
    broker = PaperBroker(starting_cash=1_000.0, default_price=10.0, slippage_bps=0.0)
    broker.update_market_price("AAPL", 10.0)
    request = OrderRequest(symbol="AAPL", side=OrderSide.BUY, quantity=10)
    result = broker.submit_order(request)

    assert result.status == OrderStatus.FILLED
    assert broker.get_positions()["AAPL"] == 10
    assert abs(broker.get_cash_balance() - (1_000.0 - 100.0)) < 1e-6


def test_paper_broker_rejects_when_insufficient_cash():
    broker = PaperBroker(starting_cash=50.0, default_price=10.0, slippage_bps=0.0)
    request = OrderRequest(symbol="MSFT", side=OrderSide.BUY, quantity=10)
    result = broker.submit_order(request)
    assert result.status == OrderStatus.REJECTED
    assert broker.get_positions().get("MSFT", 0.0) == 0.0

