"""
Collector providers for historical market data ingestion.

This package exposes concrete provider implementations that the
collector orchestrator uses to download raw market data from
different sources (Yahoo Finance, crypto exchanges, macro APIs, etc.).
"""

from . import base, yahoo_finance, crypto_exchange, macro_data, orchestrator

__all__ = [
    "base",
    "yahoo_finance",
    "crypto_exchange",
    "macro_data",
    "orchestrator",
]

