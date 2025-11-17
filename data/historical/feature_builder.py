"""
Feature augmentation for historical market data batches.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
import pandas as pd

from services.market_data.schemas import MarketDataBatch

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class FeatureAugmentor:
    windows: Iterable[int] = (5, 10, 20, 50, 100, 200)

    def augment_batch(self, batch: MarketDataBatch) -> MarketDataBatch:
        frame = batch.frame.copy()
        required_cols = {"close", "high", "low"}
        if not required_cols.issubset({c.lower() for c in frame.columns}):
            LOGGER.debug("Batch %s missing required price columns; skipping features.", batch.symbol)
            return batch

        # Normalise column names.
        mapping = {col: col.lower() for col in frame.columns}
        frame = frame.rename(columns=mapping)

        frame["return"] = frame["close"].pct_change()
        frame["log_return"] = np.log(frame["close"] / frame["close"].shift(1))
        frame["price_range"] = (frame["high"] - frame["low"]) / frame["close"].replace(0, np.nan)

        for window in self.windows:
            frame[f"sma_{window}"] = frame["close"].rolling(window=window).mean()
            frame[f"ema_{window}"] = frame["close"].ewm(span=window, adjust=False).mean()

        frame["volatility_20"] = frame["return"].rolling(window=20).std(ddof=0)
        frame["volatility_50"] = frame["return"].rolling(window=50).std(ddof=0)

        frame["bb_middle"] = frame["close"].rolling(window=20).mean()
        bb_std = frame["close"].rolling(window=20).std(ddof=0)
        frame["bb_upper"] = frame["bb_middle"] + bb_std * 2
        frame["bb_lower"] = frame["bb_middle"] - bb_std * 2
        frame["bb_position"] = (frame["close"] - frame["bb_lower"]) / (frame["bb_upper"] - frame["bb_lower"])

        delta = frame["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        frame["rsi"] = 100 - (100 / (1 + rs))

        macd_fast = frame["close"].ewm(span=12, adjust=False).mean()
        macd_slow = frame["close"].ewm(span=26, adjust=False).mean()
        frame["macd"] = macd_fast - macd_slow
        frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False).mean()
        frame["macd_histogram"] = frame["macd"] - frame["macd_signal"]

        if "volume" in frame.columns:
            frame["volume_ma20"] = frame["volume"].rolling(window=20).mean()
            frame["volume_ratio"] = frame["volume"] / frame["volume_ma20"].replace(0, np.nan)

        frame.dropna(inplace=True)
        return batch.replace_frame(frame)

    def augment(self, batches: Iterable[MarketDataBatch]) -> List[MarketDataBatch]:
        return [self.augment_batch(batch) for batch in batches]

