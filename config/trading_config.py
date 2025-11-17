"""Helpers for trading configuration sourced from environment variables."""

from __future__ import annotations

import os

from services.trading_service import TradingConfig


def get_trading_config() -> TradingConfig:
    return TradingConfig(
        finnhub_key=os.getenv("FINNHUB_API_KEY", "d3vpeq1r01qhm1tedo10d3vpeq1r01qhm1tedo1g"),
        serpapi_key=os.getenv("SERPAPI_KEY", "90f8748cb8ab624df5d503e1765e929491c57ef0b4d681fbe046f1febe045dbc"),
        coingecko_key=os.getenv("COINGECKO_API_KEY", "CG-PwNH6eV5PhUhFMhHspq3nqoz"),
        alpha_vantage_key=os.getenv("ALPHA_VANTAGE_API_KEY", "3GEY3XZMBLJGQ099"),
        initial_capital=float(os.getenv("TRADING_CAPITAL", "100000")),
        max_drawdown=float(os.getenv("MAX_DRAWDOWN", "0.08")),
        max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "0.03")),
    )


__all__ = ["get_trading_config"]


