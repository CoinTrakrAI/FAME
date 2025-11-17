"""Historical market data utilities for the trading service."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import httpx
import numpy as np
import pandas as pd

try:
    import aiofiles
except ImportError:  # pragma: no cover - optional dependency
    aiofiles = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class HistoricalDataConfig:
    finnhub_key: str
    alpha_vantage_key: str
    cache_dir: Path = Path("data/cache/historical")
    cache_ttl_seconds: int = 3600  # 1 hour
    rate_limit_interval_seconds: int = 1


class HistoricalDataService:
    """Production-oriented historical data client with caching and fallbacks."""

    def __init__(self, config: HistoricalDataConfig) -> None:
        self.config = config
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        self._cache: Dict[str, tuple[pd.DataFrame, float]] = {}
        self._rate_limits: Dict[str, float] = {}

    async def get_historical_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Fetch historical OHLCV data with caching and fallbacks."""

        cache_key = f"{symbol.upper()}_{days}"
        cached = await self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        await self._respect_rate_limit("finnhub")
        try:
            data = await self._fetch_finnhub(symbol, days)
            if not data.empty:
                await self._store_cache(cache_key, data)
                return data
        except Exception as exc:
            logger.warning("Finnhub historical fetch failed for %s: %s", symbol, exc)

        await self._respect_rate_limit("alpha_vantage")
        try:
            data = await self._fetch_alpha_vantage(symbol)
            if not data.empty:
                await self._store_cache(cache_key, data)
                return data
        except Exception as exc:
            logger.warning("Alpha Vantage historical fetch failed for %s: %s", symbol, exc)

        logger.warning("Falling back to synthetic historical data for %s", symbol)
        synthetic = self._generate_synthetic(symbol, days)
        await self._store_cache(cache_key, synthetic, persist=False)
        return synthetic

    async def shutdown(self) -> None:
        await self._client.aclose()

    # Internal helpers -------------------------------------------------

    async def _fetch_finnhub(self, symbol: str, days: int) -> pd.DataFrame:
        end_ts = int(datetime.now().timestamp())
        start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
        params = {
            "symbol": symbol,
            "resolution": "D",
            "from": start_ts,
            "to": end_ts,
            "token": self.config.finnhub_key,
        }
        response = await self._client.get("https://finnhub.io/api/v1/stock/candle", params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("s") != "ok":
            raise RuntimeError(f"Finnhub returned status {data.get('s')}")
        timestamps = data.get("t", [])
        frame = pd.DataFrame(
            {
                "date": [datetime.fromtimestamp(ts) for ts in timestamps],
                "open": data.get("o", []),
                "high": data.get("h", []),
                "low": data.get("l", []),
                "close": data.get("c", []),
                "volume": data.get("v", []),
            }
        )
        frame.set_index("date", inplace=True)
        return frame

    async def _fetch_alpha_vantage(self, symbol: str) -> pd.DataFrame:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.config.alpha_vantage_key,
            "outputsize": "compact",
        }
        response = await self._client.get("https://www.alphavantage.co/query", params=params)
        response.raise_for_status()
        data = response.json().get("Time Series (Daily)", {})
        if not data:
            raise RuntimeError("Alpha Vantage returned empty data set")
        records = []
        for date_str, values in data.items():
            records.append(
                {
                    "date": datetime.strptime(date_str, "%Y-%m-%d"),
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": float(values["5. volume"]),
                }
            )
        frame = pd.DataFrame(records)
        frame.set_index("date", inplace=True)
        return frame.sort_index()

    async def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        in_memory = self._cache.get(cache_key)
        if in_memory:
            frame, ts = in_memory
            if time.time() - ts < self.config.cache_ttl_seconds:
                return frame

        cache_file = self.config.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None
        if time.time() - cache_file.stat().st_mtime > self.config.cache_ttl_seconds:
            return None

        if aiofiles:
            async with aiofiles.open(cache_file, "r", encoding="utf-8") as handle:
                raw = json.loads(await handle.read())
        else:
            raw = json.loads(cache_file.read_text(encoding="utf-8"))
        frame = pd.DataFrame(raw["values"])
        frame["date"] = pd.to_datetime(frame["date"])
        frame.set_index("date", inplace=True)
        self._cache[cache_key] = (frame, time.time())
        return frame

    async def _store_cache(self, cache_key: str, frame: pd.DataFrame, persist: bool = True) -> None:
        self._cache[cache_key] = (frame, time.time())
        if not persist:
            return
        cache_file = self.config.cache_dir / f"{cache_key}.json"
        serialisable = {
            "values": [
                {
                    "date": index.isoformat(),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                }
                for index, row in frame.iterrows()
            ]
        }
        if aiofiles:
            async with aiofiles.open(cache_file, "w", encoding="utf-8") as handle:
                await handle.write(json.dumps(serialisable))
        else:
            cache_file.write_text(json.dumps(serialisable), encoding="utf-8")

    async def _respect_rate_limit(self, service: str) -> None:
        interval = self.config.rate_limit_interval_seconds
        last_call = self._rate_limits.get(service)
        now = time.time()
        if last_call and now - last_call < interval:
            await asyncio.sleep(interval - (now - last_call))
        self._rate_limits[service] = time.time()

    def _generate_synthetic(self, symbol: str, days: int) -> pd.DataFrame:
        dates = pd.date_range(end=datetime.now(), periods=days, freq="D")
        base_price = 150.0 if symbol.upper() != "BTC" else 40_000.0
        prices = [base_price]
        for _ in range(1, days):
            change = np.random.normal(0, 0.02)
            prices.append(prices[-1] * (1 + change))
        frame = pd.DataFrame(index=dates)
        frame["close"] = prices
        frame["open"] = frame["close"] * (1 + np.random.normal(0, 0.01, size=len(frame)))
        frame["high"] = frame[["open", "close"]].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.005, size=len(frame))))
        frame["low"] = frame[["open", "close"]].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.005, size=len(frame))))
        frame["volume"] = np.random.randint(1_000_000, 5_000_000, size=len(frame))
        return frame


__all__ = ["HistoricalDataService", "HistoricalDataConfig"]


