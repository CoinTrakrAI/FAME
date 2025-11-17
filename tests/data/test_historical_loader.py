from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from data.historical.loader import FAMEHistoricalDataLoader


@pytest.fixture
def sample_dataset(tmp_path: Path):
    data_dir = tmp_path / "historical"
    data_dir.mkdir(parents=True, exist_ok=True)

    consolidated = {
        "AAPL": pd.DataFrame(
            {
                "Close": [100, 101, 102, 103],
                "Volume": [1_000, 1_050, 980, 1_020],
            },
            index=pd.date_range("2022-01-01", periods=4, freq="D"),
        ),
        "BTC-USD": pd.DataFrame(
            {
                "Close": [40_000, 41_000, 39_500, 40_500],
                "Volume": [5_000, 5_500, 4_800, 5_100],
            },
            index=pd.date_range("2022-01-01", periods=4, freq="D"),
        ),
    }
    metadata = {
        "collection_date": datetime.now().isoformat(),
        "total_instruments": len(consolidated),
        "date_range": {"start": "2022-01-01T00:00:00", "end": "2022-01-04T00:00:00"},
        "asset_classes": {"test": 2},
    }
    pd.to_pickle(consolidated, data_dir / "consolidated_market_data.pkl")
    pd.Series(metadata).to_json(data_dir / "dataset_metadata.json")
    return data_dir


def test_loader_loads_consolidated_data(sample_dataset: Path):
    loader = FAMEHistoricalDataLoader(data_path=sample_dataset)
    data = loader.load_consolidated_data()
    assert data is not None
    assert len(data) == 2
    assert loader.info()["total_instruments"] == 2


def test_loader_period_subset(sample_dataset: Path):
    loader = FAMEHistoricalDataLoader(data_path=sample_dataset)
    loader.load_consolidated_data()
    subset = loader.get_data_for_period("2022-01-02", "2022-01-03")
    assert subset
    assert all(len(df) == 2 for df in subset.values())


def test_loader_prepares_training_data(sample_dataset: Path):
    loader = FAMEHistoricalDataLoader(data_path=sample_dataset)
    training = loader.prepare_training_data(lookback_days=1, forecast_days=1)
    assert "AAPL" in training
    assert "Returns" in training["AAPL"].columns
    assert "Volatility" in training["AAPL"].columns


def test_correlation_matrix(sample_dataset: Path):
    loader = FAMEHistoricalDataLoader(data_path=sample_dataset)
    corr = loader.get_correlation_matrix()
    assert corr.shape[0] >= 1

