"""
CLI entry point for the market data collector.
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path

from data.historical.collectors.feature_builder import FeatureAugmentor
from data.historical.collectors.orchestrator import CollectorOrchestrator

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FAME Market Data Collector")
    parser.add_argument("--manifest", type=Path, required=True, help="Path to symbol manifest YAML")
    parser.add_argument("--output", type=Path, required=True, help="Directory for raw output")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--augment", action="store_true", help="Augment batches with technical features")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_args()

    start = datetime.fromisoformat(args.start) if args.start else None
    end = datetime.fromisoformat(args.end) if args.end else None

    orchestrator = CollectorOrchestrator()
    result = orchestrator.collect(args.manifest, start=start, end=end)

    batches = result.batches
    if args.augment:
        augmentor = FeatureAugmentor()
        batches = augmentor.augment(batches)

    orchestrator.persist_batches(batches, args.output)

    meta_frame = orchestrator.create_metadata_frame(result.metadata)
    meta_frame.to_csv(args.output / "collection_summary.csv", index=False)

    LOGGER.info("Collected %d batches across %d sources.", len(batches), len(result.metadata))


if __name__ == "__main__":
    main()

