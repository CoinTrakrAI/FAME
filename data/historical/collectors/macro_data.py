"""
Macroeconomic data provider using Yahoo Finance/FRED accessible series.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Iterable, Optional

import pandas as pd

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None  # type: ignore

from .base import ManifestEntry, MarketDataProvider, ProviderUnavailable
from services.market_data.schemas import MarketDataBatch

LOGGER = logging.getLogger(__name__)


class MacroDataProvider(MarketDataProvider):
    name = "macro"

    def bootstrap(self) -> None:
        if yf is None:
            raise ProviderUnavailable("yfinance is required for macro provider.")
        if os.getenv("FAME_COLLECTOR_OFFLINE") == "1":
            raise ProviderUnavailable("Offline mode enabled.")

    def fetch(
        self,
        entry: ManifestEntry,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Iterable[MarketDataBatch]:
        if yf is None:
            return []

        batches = []
        for _timeframe in entry.timeframes:
            try:
                ticker = yf.Ticker(entry.symbol)
                df = ticker.history(period="max", interval="1d", start=start, end=end)
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Macro fetch failed for %s: %s", entry.symbol, exc)
                continue

            if df.empty:
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

            batches.append(
                MarketDataBatch(
                    symbol=entry.symbol,
                    asset_class=entry.asset_class,
                    source=self.name,
                    timeframe="1d",
                    frame=df,
                    metadata={"provider": "yfinance", "series": entry.symbol},
                )
            )

        return batches

