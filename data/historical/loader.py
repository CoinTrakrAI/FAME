"""
Historical data loader utilities for FAME components.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class FAMEHistoricalDataLoader:
    """
    Loads consolidated historical data produced by HistoricalDataCollector.
    """

    data_path: Path = Path("data/historical")
    consolidated_filename: str = "consolidated_market_data.pkl"
    metadata_filename: str = "dataset_metadata.json"

    consolidated_data: Optional[Dict[str, pd.DataFrame]] = None
    metadata: Optional[Dict[str, any]] = None

    # ------------------------------------------------------------------ #
    def load_consolidated_data(self) -> Optional[Dict[str, pd.DataFrame]]:
        consolidated_file = self.data_path / self.consolidated_filename
        if not consolidated_file.exists():
            LOGGER.error("Consolidated dataset not found at %s", consolidated_file)
            return None
        self.consolidated_data = pd.read_pickle(consolidated_file)
        LOGGER.info("Loaded consolidated dataset with %d instruments.", len(self.consolidated_data))
        metadata_path = self.data_path / self.metadata_filename
        if metadata_path.exists():
            self.metadata = pd.read_json(metadata_path, typ="series").to_dict()
        return self.consolidated_data

    def get_data_for_period(self, start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        if self.consolidated_data is None:
            self.load_consolidated_data()
        if not self.consolidated_data:
            return {}

        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)
        result: Dict[str, pd.DataFrame] = {}
        for symbol, df in self.consolidated_data.items():
            mask = (df.index >= start) & (df.index <= end)
            sliced = df.loc[mask]
            if not sliced.empty:
                result[symbol] = sliced
        return result

    def get_correlation_matrix(self, symbols: Optional[Iterable[str]] = None) -> pd.DataFrame:
        if self.consolidated_data is None:
            self.load_consolidated_data()
        if not self.consolidated_data:
            return pd.DataFrame()

        selected = list(symbols) if symbols else list(self.consolidated_data.keys())[:50]
        closes = {}
        for symbol in selected:
            df = self.consolidated_data.get(symbol)
            if df is None or "Close" not in df.columns:
                LOGGER.debug("Symbol %s missing Close prices.", symbol)
                continue
            closes[symbol] = df["Close"]

        if not closes:
            LOGGER.warning("No instruments with Close prices available for correlation matrix.")
            return pd.DataFrame()

        price_df = pd.DataFrame(closes).dropna(how="all")
        return price_df.pct_change().dropna().corr()

    def prepare_training_data(self, lookback_days: int = 30, forecast_days: int = 5) -> Dict[str, pd.DataFrame]:
        if self.consolidated_data is None:
            self.load_consolidated_data()
        if not self.consolidated_data:
            return {}

        prepared: Dict[str, pd.DataFrame] = {}
        for symbol, df in self.consolidated_data.items():
            if len(df) < lookback_days + forecast_days:
                continue
            dataset = df.copy()
            if "Close" not in dataset.columns:
                continue
            dataset["Returns"] = dataset["Close"].pct_change()
            window_20 = max(1, min(20, len(dataset)))
            window_50 = max(1, min(50, len(dataset)))
            dataset["Volatility"] = dataset["Returns"].rolling(window=window_20, min_periods=1).std()
            dataset["MA_20"] = dataset["Close"].rolling(window=window_20, min_periods=1).mean()
            dataset["MA_50"] = dataset["Close"].rolling(window=window_50, min_periods=1).mean()
            dataset = dataset.dropna()
            if len(dataset) >= lookback_days + forecast_days:
                prepared[symbol] = dataset
        LOGGER.info("Prepared training data for %d instruments.", len(prepared))
        return prepared

    def load_enhanced_dataset(self, filename: str = "enhanced_consolidated_market_data.pkl") -> Optional[Dict[str, pd.DataFrame]]:
        path = self.data_path / filename
        if not path.exists():
            LOGGER.warning("Enhanced dataset not found at %s", path)
            return None
        return pd.read_pickle(path)

    def load_feature_set(
        self,
        feature_set_name: str,
        features_manifest: Path,
        *,
        dataset: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, pd.DataFrame]:
        if dataset is None:
            dataset = self.load_enhanced_dataset() or self.load_consolidated_data() or {}

        with features_manifest.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        feature_sets = manifest.get("feature_sets", {})
        if feature_set_name not in feature_sets:
            raise KeyError(f"Feature set {feature_set_name!r} not defined.")

        selected_features = set(feature_sets[feature_set_name])
        result: Dict[str, pd.DataFrame] = {}
        for symbol, frame in dataset.items():
            matching = [col for col in frame.columns if col in selected_features]
            if matching:
                result[symbol] = frame[matching].copy()
        return result

    # ------------------------------------------------------------------ #
    def info(self) -> Dict[str, any]:
        """Return metadata summary."""
        if self.metadata is None:
            metadata_path = self.data_path / self.metadata_filename
            if metadata_path.exists():
                self.metadata = pd.read_json(metadata_path, typ="series").to_dict()
        return self.metadata or {}

