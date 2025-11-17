"""
Base provider definitions for historical market data collection.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from services.market_data.schemas import MarketDataBatch

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ManifestEntry:
    """
    Small helper representing a row in the symbol manifest.
    """

    provider: str
    symbol: str
    asset_class: str
    timeframes: List[str] = field(default_factory=lambda: ["1d"])
    options: Dict[str, Any] = field(default_factory=dict)


class ProviderUnavailable(RuntimeError):
    """Raised when a provider cannot run in the current environment."""


class MarketDataProvider(abc.ABC):
    """
    Abstract base class for data providers.
    """

    name: str = "base"

    def __init__(self, *, rate_limit_sleep: float = 0.0) -> None:
        self.rate_limit_sleep = rate_limit_sleep

    def bootstrap(self) -> None:
        """
        Optional hook invoked before any fetches.
        Providers should raise ProviderUnavailable if dependencies or
        credentials are missing.
        """

    @abc.abstractmethod
    def fetch(
        self,
        entry: ManifestEntry,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Iterable[MarketDataBatch]:
        """
        Download data for the provided manifest entry.
        """

    def supports(self, timeframe: str) -> bool:
        """Return True if the provider supports the requested timeframe."""
        return timeframe in ("1d",)

    def _warn_offline(self, message: str) -> None:
        LOGGER.warning("[%s] %s", self.name, message)

