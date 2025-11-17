#!/usr/bin/env python3
"""
FAME Configuration
Stores API keys and settings
"""

import os

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class APISettings:
    """Container for API credentials loaded from environment variables."""

    openai_api_key: Optional[str]
    serpapi_key: Optional[str]
    serpapi_key_backup: Optional[str]
    coingecko_api_key: Optional[str]
    alpha_vantage_api_key: Optional[str]
    finnhub_api_key: Optional[str]


def load_api_settings(require_all: bool = False) -> APISettings:
    """
    Load API credentials from environment variables.

    Args:
        require_all: If True, raise RuntimeError when any value is missing.
    """

    settings = APISettings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        serpapi_key=os.getenv("SERPAPI_KEY"),
        serpapi_key_backup=os.getenv("SERPAPI_KEY_BACKUP"),
        coingecko_api_key=os.getenv("COINGECKO_API_KEY"),
        alpha_vantage_api_key=os.getenv("ALPHA_VANTAGE_API_KEY"),
        finnhub_api_key=os.getenv("FINNHUB_API_KEY"),
    )

    if require_all:
        missing = [
            name
            for name, value in {
                "OPENAI_API_KEY": settings.openai_api_key,
                "SERPAPI_KEY": settings.serpapi_key,
                "SERPAPI_KEY_BACKUP": settings.serpapi_key_backup,
                "COINGECKO_API_KEY": settings.coingecko_api_key,
                "ALPHA_VANTAGE_API_KEY": settings.alpha_vantage_api_key,
                "FINNHUB_API_KEY": settings.finnhub_api_key,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required API keys: {', '.join(missing)}")

    return settings


def as_dict(settings: Optional[APISettings] = None) -> Dict[str, Optional[str]]:
    """Return settings as a dictionary."""
    settings = settings or load_api_settings()
    return {
        "OPENAI_API_KEY": settings.openai_api_key,
        "SERPAPI_KEY": settings.serpapi_key,
        "SERPAPI_KEY_BACKUP": settings.serpapi_key_backup,
        "COINGECKO_API_KEY": settings.coingecko_api_key,
        "ALPHA_VANTAGE_API_KEY": settings.alpha_vantage_api_key,
        "FINNHUB_API_KEY": settings.finnhub_api_key,
    }
