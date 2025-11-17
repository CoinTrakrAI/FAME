import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from data.historical.collectors.orchestrator import CollectorOrchestrator, register_provider
from data.historical.feature_builder import FeatureAugmentor
from data.historical.collectors.base import ManifestEntry, MarketDataProvider
from services.market_data.schemas import MarketDataBatch


class DummyProvider(MarketDataProvider):
    name = "dummy"

    def bootstrap(self) -> None:
        return

    def fetch(self, entry: ManifestEntry, start=None, end=None):
        index = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame(
            {
                "open": [1.0, 1.1, 1.2],
                "high": [1.2, 1.3, 1.4],
                "low": [0.9, 1.0, 1.1],
                "close": [1.1, 1.2, 1.3],
                "volume": [100, 110, 120],
            },
            index=index,
        )
        yield MarketDataBatch(
            symbol=entry.symbol,
            asset_class=entry.asset_class,
            source=self.name,
            timeframe="1d",
            frame=df,
            metadata={"provider": "dummy"},
        )


def test_orchestrator_collects_dummy_provider(tmp_path: Path):
    register_provider("dummy", DummyProvider)
    manifest = {
        "providers": {
            "dummy": {
                "timeframes": ["1d"],
                "assets": [
                    {"class": "test_asset", "symbols": ["TEST1"]},
                ],
            }
        }
    }
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    orchestrator = CollectorOrchestrator(providers={"dummy": DummyProvider})
    result = orchestrator.collect(manifest_path)

    assert len(result.batches) == 1
    batch = result.batches[0]
    assert batch.symbol == "TEST1"
    assert "close" in batch.frame.columns


def test_feature_augmentor_adds_expected_columns():
    index = pd.date_range("2024-01-01", periods=40, freq="D")
    df = pd.DataFrame(
        {
            "open": 1.0,
            "high": 1.2,
            "low": 0.8,
            "close": 1.1,
            "volume": 100,
        },
        index=index,
    )
    batch = MarketDataBatch(
        symbol="TEST",
        asset_class="test",
        source="dummy",
        timeframe="1d",
        frame=df,
        metadata={},
    )
    augmentor = FeatureAugmentor()
    augmented = augmentor.augment_batch(batch)
    assert "rsi" in augmented.frame.columns
    assert "sma_20" in augmented.frame.columns

