"""
CCXT-powered crypto exchange provider (Binance by default).
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Iterable, Optional

import pandas as pd

try:
    import ccxt  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    ccxt = None  # type: ignore

from .base import ManifestEntry, MarketDataProvider, ProviderUnavailable
from services.market_data.schemas import MarketDataBatch

LOGGER = logging.getLogger(__name__)


class CryptoExchangeProvider(MarketDataProvider):
    name = "crypto_exchange"

    def __init__(self, *, exchange_id: str = "binance", rate_limit_sleep: float = 0.5) -> None:
        super().__init__(rate_limit_sleep=rate_limit_sleep)
        self.exchange_id = exchange_id
        self._exchange = None

    def bootstrap(self) -> None:
        if ccxt is None:
            raise ProviderUnavailable("ccxt is not installed.")
        if os.getenv("FAME_COLLECTOR_OFFLINE") == "1":
            raise ProviderUnavailable("Offline mode enabled.")

        try:
            exchange_class = getattr(ccxt, self.exchange_id)
        except AttributeError as exc:  # pragma: no cover
            raise ProviderUnavailable(f"Exchange {self.exchange_id} not supported by ccxt.") from exc

        self._exchange = exchange_class({"enableRateLimit": True})

    def supports(self, timeframe: str) -> bool:
        return timeframe in {"1d"}

    def fetch(
        self,
        entry: ManifestEntry,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Iterable[MarketDataBatch]:
        if self._exchange is None or ccxt is None:
            LOGGER.debug("Exchange not initialised; skipping %s.", entry.symbol)
            return []

        results = []
        for timeframe in entry.timeframes:
            if not self.supports(timeframe):
                continue

            since = None
            if start:
                since = int(start.timestamp() * 1000)

            all_rows = []
            while True:
                try:
                    candles = self._exchange.fetch_ohlcv(entry.symbol, timeframe="1d", since=since, limit=1000)
                except Exception as exc:  # pragma: no cover - network
                    LOGGER.warning("Failed to fetch %s from %s: %s", entry.symbol, self.exchange_id, exc)
                    break

                if not candles:
                    break

                all_rows.extend(candles)
                last_ts = candles[-1][0]
                if since is not None and last_ts == since:
                    break
                since = last_ts + 1

                if end and datetime.utcfromtimestamp(last_ts / 1000) >= end:
                    break

                if len(all_rows) >= 2000:
                    break

                time.sleep(self.rate_limit_sleep)

            if not all_rows:
                continue

            df = pd.DataFrame(
                all_rows,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.set_index("timestamp").sort_index()

            results.append(
                MarketDataBatch(
                    symbol=entry.symbol,
                    asset_class=entry.asset_class,
                    source=self.exchange_id,
                    timeframe=timeframe,
                    frame=df,
                    metadata={"provider": "ccxt", "exchange": self.exchange_id},
                )
            )

        return results

