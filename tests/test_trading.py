"""Tests for the trading service integration."""

from __future__ import annotations

import asyncio
import pathlib
import sys
from typing import Dict

import pytest
from unittest.mock import AsyncMock

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.trading_service import (
    TradingConfig,
    TradingService,
    TradingSignalType,
    TradingStrategyEngine,
    talib,
)


@pytest.fixture
def trading_config() -> TradingConfig:
    return TradingConfig(
        finnhub_key="test",
        serpapi_key="test",
        coingecko_key="test",
        alpha_vantage_key="test",
    )


@pytest.mark.asyncio
async def test_momentum_strategy_buy_signal():
    if talib is None:
        pytest.skip("TA-Lib not installed")
    engine = TradingStrategyEngine()
    market_data: Dict = {
        "symbol": "AAPL",
        "current_price": 150.0,
        "indicators": {
            "rsi_14": 55.0,
            "macd_hist": 0.5,
            "sma_20": 148.0,
            "sma_50": 145.0,
            "atr_14": 2.0,
        },
    }
    signals = await engine.generate_signals(market_data)
    assert any(signal.signal_type in {TradingSignalType.BUY, TradingSignalType.STRONG_BUY} for signal in signals)


@pytest.mark.asyncio
async def test_trading_service_handles_missing_symbol(trading_config: TradingConfig):
    service = TradingService(trading_config)
    service.data_service.get_real_time_data = AsyncMock(return_value={})
    try:
        result = await service.get_signals("UNKNOWN")
        assert "error" in result
    finally:
        await service.shutdown()


@pytest.mark.asyncio
async def test_trade_intent_requires_symbol(trading_config: TradingConfig):
    service = TradingService(trading_config)
    service.data_service.get_real_time_data = AsyncMock(return_value={})
    try:
        result = await service.execute_trade({"action": "buy"})
        assert result["status"] == "error"
    finally:
        await service.shutdown()


