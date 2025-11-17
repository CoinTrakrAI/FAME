"""
Shared schemas for market data collection.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Dict

import pandas as pd


@dataclass(slots=True)
class MarketDataBatch:
    symbol: str
    asset_class: str
    source: str
    timeframe: str
    frame: pd.DataFrame
    metadata: Dict[str, Any]

    @property
    def start(self) -> datetime:
        return pd.Timestamp(self.frame.index[0]).to_pydatetime()

    @property
    def end(self) -> datetime:
        return pd.Timestamp(self.frame.index[-1]).to_pydatetime()

    def replace_frame(self, new_frame: pd.DataFrame) -> "MarketDataBatch":
        return replace(self, frame=new_frame)

