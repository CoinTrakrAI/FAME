"""
Historical data collection utilities.

NOTE: Network access is required to fetch live market data. The provided
collector is designed for production use but will not succeed inside the
offline test environment. Consumers should run the collector in an
environment with internet access and the necessary API quotas.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

try:  # pragma: no cover - optional dependency
    import yfinance as yf
except ImportError:  # pragma: no cover
    yf = None  # type: ignore

LOGGER = logging.getLogger(__name__)


DEFAULT_CRYPTO = [
    "BTC-USD",
    "ETH-USD",
    "ADA-USD",
    "DOT-USD",
    "LINK-USD",
    "LTC-USD",
    "BCH-USD",
    "XLM-USD",
    "XRP-USD",
    "EOS-USD",
    "TRX-USD",
    "XTZ-USD",
    "ATOM-USD",
    "ALGO-USD",
    "SOL-USD",
    "AVAX-USD",
    "MATIC-USD",
    "NEAR-USD",
    "FTM-USD",
    "SAND-USD",
]

DEFAULT_FOREX = [
    "EURUSD=X",
    "GBPUSD=X",
    "USDJPY=X",
    "USDCHF=X",
    "AUDUSD=X",
    "USDCAD=X",
    "NZDUSD=X",
    "EURGBP=X",
    "EURJPY=X",
    "GBPJPY=X",
    "EURCHF=X",
    "AUDJPY=X",
    "NZDJPY=X",
    "CADJPY=X",
    "CHFJPY=X",
]

DEFAULT_COMMODITIES = [
    "GC=F",
    "SI=F",
    "CL=F",
    "NG=F",
    "PL=F",
    "PA=F",
    "HG=F",
    "ZC=F",
    "ZW=F",
    "ZS=F",
]

DEFAULT_INDICES = [
    "^GSPC",
    "^DJI",
    "^IXIC",
    "^RUT",
    "^FTSE",
    "^GDAXI",
    "^FCHI",
    "^STOXX50E",
    "^N225",
    "^HSI",
    "^AXJO",
    "^BSESN",
    "^MXX",
    "^BVSP",
]

DEFAULT_ETFS = [
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
    "VGK",
    "EWJ",
    "EEM",
    "GLD",
    "SLV",
    "USO",
    "TLT",
    "HYG",
    "LQD",
    "VNQ",
    "XLF",
    "XLK",
    "XLV",
    "XLE",
    "XLI",
    "XLP",
]

DEFAULT_STOCKS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "TSLA",
    "META",
    "NVDA",
    "JPM",
    "JNJ",
    "V",
    "PG",
    "UNH",
    "HD",
    "DIS",
    "PYPL",
    "NFLX",
    "ADBE",
    "CRM",
    "INTC",
    "CSCO",
    "PEP",
    "T",
    "ABT",
    "TMO",
    "COST",
    "AVGO",
    "TXN",
    "LLY",
    "WMT",
    "XOM",
]

DEFAULT_VOLATILITY = ["^VIX", "VXX", "UVXY", "SVXY"]

DEFAULT_MACRO = ["DGS10", "DTWEXB", "DCOILWTICO", "GOLDAMGBD228NLBM"]


@dataclass(slots=True)
class HistoricalDataCollector:
    """
    Collects and stores multi-asset historical market data.

    The collector relies on `yfinance` for convenience. For production usage,
    replace with dedicated data vendors or extend the provider interface.
    """

    data_dir: Path = field(default_factory=lambda: Path("data/historical"))
    period: str = "5y"
    interval: str = "1d"

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if yf is None:
            LOGGER.warning("yfinance is not available; data collection cannot run.")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def save_all_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Collect data across asset classes and persist to disk.

        Returns:
            Dictionary mapping asset class -> symbol -> DataFrame.
        """
        LOGGER.info("Starting historical data collection.")

        assets = {
            "crypto": self._collect(DEFAULT_CRYPTO),
            "forex": self._collect(DEFAULT_FOREX),
            "commodities": self._collect(DEFAULT_COMMODITIES),
            "indices": self._collect(DEFAULT_INDICES),
            "etfs": self._collect(DEFAULT_ETFS),
            "stocks": self._collect(DEFAULT_STOCKS),
            "volatility": self._collect(DEFAULT_VOLATILITY),
            "macro": self._collect(DEFAULT_MACRO),
        }

        for asset_class, dataset in assets.items():
            if dataset:
                self._save_asset_bundle(asset_class, dataset)

        self.create_consolidated_dataset(assets)
        LOGGER.info("Historical data collection complete.")
        return assets

    def create_consolidated_dataset(self, all_data: Dict[str, Dict[str, pd.DataFrame]]) -> None:
        """
        Consolidate all collected data into a single pickle + metadata file.
        """
        consolidated: Dict[str, pd.DataFrame] = {}
        earliest: Optional[pd.Timestamp] = None
        latest: Optional[pd.Timestamp] = None
        instruments = 0

        for data_dict in all_data.values():
            for symbol, df in data_dict.items():
                if df.empty:
                    continue
                instruments += 1
                consolidated[symbol] = df.sort_index()
                start = df.index.min()
                end = df.index.max()
                earliest = start if earliest is None else min(earliest, start)
                latest = end if latest is None else max(latest, end)

        consolidated_path = self.data_dir / "consolidated_market_data.pkl"
        pd.to_pickle(consolidated, consolidated_path)

        metadata = {
            "collection_date": datetime.now().isoformat(),
            "total_instruments": instruments,
            "date_range": {
                "start": earliest.isoformat() if earliest is not None else None,
                "end": latest.isoformat() if latest is not None else None,
            },
            "asset_classes": {k: len(v) for k, v in all_data.items()},
        }

        metadata_path = self.data_dir / "dataset_metadata.json"
        pd.Series(metadata).to_json(metadata_path)
        LOGGER.info(
            "Consolidated dataset saved: %d instruments (%s -> %s)",
            instruments,
            metadata["date_range"]["start"],
            metadata["date_range"]["end"],
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _collect(self, tickers: Iterable[str]) -> Dict[str, pd.DataFrame]:
        if yf is None:  # pragma: no cover - requires network
            LOGGER.error("yfinance not available; skipping ticker collection.")
            return {}

        results: Dict[str, pd.DataFrame] = {}
        for symbol in tickers:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=self.period, interval=self.interval)
                if not data.empty:
                    results[symbol] = data
                    LOGGER.debug("Fetched %s (%d rows)", symbol, len(data))
                else:
                    LOGGER.warning("No data for %s", symbol)
            except Exception as exc:  # pragma: no cover - network failure
                LOGGER.exception("Failed to fetch %s: %s", symbol, exc)
        return results

    def _save_asset_bundle(self, asset_class: str, data_dict: Dict[str, pd.DataFrame]) -> Path:
        path = self.data_dir / f"{asset_class}_data.pkl"
        pd.to_pickle(data_dict, path)
        LOGGER.info("Saved %s data bundle (%d instruments)", asset_class, len(data_dict))
        return path

