"""
Historical market data utilities for FAME.

This package provides tools to collect, persist, and load multi-asset
historical datasets used by the intelligence, risk, and training subsystems.
"""

from .data_collector import HistoricalDataCollector
from .loader import FAMEHistoricalDataLoader

__all__ = ["HistoricalDataCollector", "FAMEHistoricalDataLoader"]

