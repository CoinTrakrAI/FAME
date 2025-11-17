"""
Collector orchestrator that loads manifest definitions and runs providers.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Type

import pandas as pd
import yaml

from .base import ManifestEntry, MarketDataProvider, ProviderUnavailable
from .crypto_exchange import CryptoExchangeProvider
from .macro_data import MacroDataProvider
from .yahoo_finance import YahooFinanceProvider
from services.market_data.schemas import MarketDataBatch

LOGGER = logging.getLogger(__name__)

PROVIDER_REGISTRY: Dict[str, Type[MarketDataProvider]] = {
    "yahoo": YahooFinanceProvider,
    "crypto_exchange": CryptoExchangeProvider,
    "macro": MacroDataProvider,
}


def register_provider(name: str, provider_cls: Type[MarketDataProvider]) -> None:
    PROVIDER_REGISTRY[name] = provider_cls


@dataclass
class CollectorResult:
    batches: List[MarketDataBatch]
    metadata: Dict[str, int]


class CollectorOrchestrator:
    """
    High-level interface for running data collection jobs.
    """

    def __init__(self, providers: Optional[Dict[str, Type[MarketDataProvider]]] = None) -> None:
        self.providers = providers or PROVIDER_REGISTRY

    def load_manifest(self, manifest_path: Path) -> List[ManifestEntry]:
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = yaml.safe_load(handle)

        entries: List[ManifestEntry] = []
        for provider_name, cfg in manifest.get("providers", {}).items():
            timeframes = cfg.get("timeframes", ["1d"])
            for asset in cfg.get("assets", []):
                asset_class = asset.get("class", "unknown")
                symbols = asset.get("symbols", [])
                options = {k: v for k, v in asset.items() if k not in {"class", "symbols"}}
                for symbol in symbols:
                    entries.append(
                        ManifestEntry(
                            provider=provider_name,
                            symbol=symbol,
                            asset_class=asset_class,
                            timeframes=list(timeframes),
                            options=options,
                        )
                    )
        return entries

    async def _run_provider(
        self,
        provider_name: str,
        provider_cls: Type[MarketDataProvider],
        entries: Iterable[ManifestEntry],
        start: Optional[datetime],
        end: Optional[datetime],
    ) -> List[MarketDataBatch]:
        provider = provider_cls()
        try:
            provider.bootstrap()
        except ProviderUnavailable as exc:
            LOGGER.info("Provider %s unavailable: %s", provider_name, exc)
            return []

        batches: List[MarketDataBatch] = []
        for entry in entries:
            try:
                result = provider.fetch(entry, start=start, end=end)
                batches.extend(result)
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("Provider %s failed for %s: %s", provider_name, entry.symbol, exc)
        return batches

    async def collect_async(
        self,
        manifest_path: Path,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> CollectorResult:
        entries = self.load_manifest(manifest_path)
        batches: List[MarketDataBatch] = []
        metadata: Dict[str, int] = {}

        grouped: Dict[str, List[ManifestEntry]] = {}
        for entry in entries:
            grouped.setdefault(entry.provider, []).append(entry)

        tasks = []
        for provider_name, provider_entries in grouped.items():
            provider_cls = self.providers.get(provider_name)
            if provider_cls is None:
                LOGGER.warning("No provider registered for %s; skipping.", provider_name)
                continue
            tasks.append(
                asyncio.create_task(
                    self._run_provider(provider_name, provider_cls, provider_entries, start, end)
                )
            )

        if tasks:
            results = await asyncio.gather(*tasks)
            for provider_batches in results:
                for batch in provider_batches:
                    batches.append(batch)
                    metadata_key = f"{batch.source}:{batch.symbol}"
                    metadata[metadata_key] = metadata.get(metadata_key, 0) + len(batch.frame)

        return CollectorResult(batches=batches, metadata=metadata)

    def collect(
        self,
        manifest_path: Path,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> CollectorResult:
        return asyncio.run(self.collect_async(manifest_path, start=start, end=end))

    def persist_batches(self, batches: Iterable[MarketDataBatch], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        for batch in batches:
            dest = output_dir / batch.source / batch.symbol.replace("/", "_") / batch.timeframe
            dest.mkdir(parents=True, exist_ok=True)
            filename = dest / f"{batch.start:%Y%m%d}_{batch.end:%Y%m%d}.parquet"
            batch.frame.to_parquet(filename)
            metadata_path = dest / "metadata.json"
            if not metadata_path.exists():
                metadata_path.write_text(json.dumps(batch.metadata, indent=2), encoding="utf-8")

    def create_metadata_frame(self, metadata: Dict[str, int]) -> pd.DataFrame:
        rows = []
        for key, count in metadata.items():
            source, symbol = key.split(":", maxsplit=1)
            rows.append({"source": source, "symbol": symbol, "rows": count})
        return pd.DataFrame(rows)

