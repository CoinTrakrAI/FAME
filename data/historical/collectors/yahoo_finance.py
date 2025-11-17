"""
Yahoo Finance provider using yfinance for multi-asset coverage.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Iterable, Optional

import pandas as pd

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - optional dependency
    yf = None  # type: ignore

from .base import ManifestEntry, MarketDataProvider, ProviderUnavailable
from services.market_data.schemas import MarketDataBatch

LOGGER = logging.getLogger(__name__)


class YahooFinanceProvider(MarketDataProvider):
    name = "yahoo"

    def bootstrap(self) -> None:
        if yf is None:
            raise ProviderUnavailable("yfinance is not installed.")
        if os.getenv("FAME_COLLECTOR_OFFLINE") == "1":
            raise ProviderUnavailable("Offline mode enabled.")

    def fetch(
        self,
        entry: ManifestEntry,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Iterable[MarketDataBatch]:
        if yf is None:
            LOGGER.debug("Skipping %s: yfinance not available.", entry.symbol)
            return []

        results = []
        for timeframe in entry.timeframes:
            if not self.supports(timeframe):
                LOGGER.debug("Skipping timeframe %s for %s.", timeframe, entry.symbol)
                continue

            interval = "1d"
            period = "max"
            if start or end:
                period = None

            try:
                ticker = yf.Ticker(entry.symbol)
                df = ticker.history(
                    period=period,
                    interval=interval,
                    start=start,
                    end=end,
                )
            except Exception as exc:  # pragma: no cover - network failure
                LOGGER.warning("Failed to fetch %s: %s", entry.symbol, exc)
                continue

            if df.empty:
                LOGGER.debug("No data returned for %s.", entry.symbol)
                continue

            df = df.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                }
            )
            df.index = pd.to_datetime(df.index)

            results.append(
                MarketDataBatch(
                    symbol=entry.symbol,
                    asset_class=entry.asset_class,
                    source=self.name,
                    timeframe=timeframe,
                    frame=df,
                    metadata={"provider": "yfinance"},
                )
            )

            if self.rate_limit_sleep > 0:
                time.sleep(self.rate_limit_sleep)

        return results

