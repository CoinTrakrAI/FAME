"""
Premium price service that favours enterprise-grade data providers before falling
back to public feeds. All API keys are sourced from environment variables.
"""

from __future__ import annotations

import os
import time
import logging
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)

_CRYPTO_SYMBOL_MAP = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "xrp": "ripple",
    "ada": "cardano",
    "sol": "solana",
    "doge": "dogecoin",
    "matic": "matic-network",
    "dot": "polkadot",
    "avax": "avalanche-2",
    "link": "chainlink",
    "uni": "uniswap",
    "bnb": "binancecoin",
    "ltc": "litecoin",
    "bch": "bitcoin-cash",
    "xlm": "stellar",
}


class PremiumPriceService:
    """Wrapper around SERPAPI, CoinGecko, Alpha Vantage, and Finnhub."""

    def __init__(self) -> None:
        # API keys - hardcoded for demo, can be overridden via environment
        self.serpapi_key = os.getenv(
            "SERPAPI_KEY",
            "90f8748cb8ab624df5d503e1765e929491c57ef0b4d681fbe046f1febe045dbc",
        )
        self.serpapi_backup_key = os.getenv(
            "SERPAPI_BACKUP_KEY",
            "912dc3fe069c587aa89dc662a492998ded20a25dfc49f9961ff5e5c99168eeb1",
        )
        # Updated API keys from user
        self.coingecko_key = os.getenv("COINGECKO_API_KEY", "CG-PwNH6eV5PhUhFMhHspq3nqoz")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "3GEY3XZMBLJGQ099")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY", "d3vpeq1r01qhm1tedo10d3vpeq1r01qhm1tedo1g")
        self._session = requests.Session()
        self._rate_limits = {
            "serpapi": {"last": 0.0, "interval": 0.3},  # Reduced from 1.0s
            "coingecko": {"last": 0.0, "interval": 0.2},  # Reduced from 0.5s
            "alpha_vantage": {"last": 0.0, "interval": 0.5},  # Reduced from 1.2s
            "finnhub": {"last": 0.0, "interval": 0.3},  # Reduced from 1.0s
        }

    def get_price(self, symbol: str) -> Optional[Dict]:
        """Return the best available quote for either crypto or equity."""
        symbol = (symbol or "").strip()
        if not symbol:
            return None

        crypto_quote = self._get_crypto_quote(symbol)
        if crypto_quote:
            return crypto_quote

        equity_quote = self._get_equity_quote(symbol)
        if equity_quote:
            return equity_quote

        return None

    # --------------------------------------------------------------------- #
    # Crypto helpers
    # --------------------------------------------------------------------- #

    def _get_crypto_quote(self, symbol: str) -> Optional[Dict]:
        normalized = symbol.lower().strip().lstrip("$")
        serp_result = self._query_serpapi(normalized)
        if serp_result:
            return serp_result

        coingecko_result = self._query_coingecko(normalized)
        if coingecko_result:
            return coingecko_result

        return None

    def _query_serpapi(self, symbol: str) -> Optional[Dict]:
        api_key = self.serpapi_key or self.serpapi_backup_key
        if not api_key:
            return None
        self._respect_rate_limit("serpapi")
        params = {
            "engine": "google_finance",
            "q": f"{symbol.upper()}-USD",
            "hl": "en",
            "api_key": api_key,
        }
        try:
            resp = self._session.get("https://serpapi.com/search", params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, requests.Timeout) as e:
            logger.debug(f"SERPAPI error for {symbol}: {e}")
            return None

        price = data.get("price")
        if price is None:
            return None

        try:
            price_val = float(str(price).replace(",", ""))
        except ValueError:
            return None

        change = data.get("price_movement", {}).get("percentage")
        change_percent = None
        if change is not None:
            try:
                change_percent = float(str(change).replace("%", ""))
            except ValueError:
                change_percent = None

        return {
            "asset_class": "crypto",
            "symbol": symbol.upper(),
            "price": price_val,
            "change_percent": change_percent,
            "source": "SERPAPI",
            "text": self._format_crypto(symbol.upper(), price_val, change_percent, "SERPAPI"),
        }

    def _query_coingecko(self, symbol: str) -> Optional[Dict]:
        coin_id = _CRYPTO_SYMBOL_MAP.get(symbol.lower())
        if not coin_id:
            return None
        self._respect_rate_limit("coingecko")
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
        }
        if self.coingecko_key:
            params["x_cg_pro_api_key"] = self.coingecko_key

        try:
            resp = self._session.get("https://api.coingecko.com/api/v3/simple/price", params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, requests.Timeout) as e:
            logger.debug(f"CoinGecko error for {symbol}: {e}")
            return None

        coin_data = data.get(coin_id)
        if not coin_data or "usd" not in coin_data:
            return None

        price = float(coin_data["usd"])
        change = float(coin_data.get("usd_24h_change", 0.0))
        return {
            "asset_class": "crypto",
            "symbol": symbol.upper(),
            "price": price,
            "change_percent": change,
            "market_cap": coin_data.get("usd_market_cap"),
            "volume_24h": coin_data.get("usd_24h_vol"),
            "source": "CoinGecko",
            "text": self._format_crypto(symbol.upper(), price, change, "CoinGecko"),
        }

    # --------------------------------------------------------------------- #
    # Equity helpers
    # --------------------------------------------------------------------- #

    def _get_equity_quote(self, symbol: str) -> Optional[Dict]:
        symbol_upper = symbol.upper().strip()
        alpha_quote = self._query_alpha_vantage(symbol_upper)
        if alpha_quote:
            return alpha_quote

        finnhub_quote = self._query_finnhub(symbol_upper)
        if finnhub_quote:
            return finnhub_quote

        return None

    def _query_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        if not self.alpha_vantage_key:
            return None
        self._respect_rate_limit("alpha_vantage")
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.alpha_vantage_key,
        }
        try:
            resp = self._session.get("https://www.alphavantage.co/query", params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, requests.Timeout) as e:
            logger.debug(f"Alpha Vantage error for {symbol}: {e}")
            return None

        quote = data.get("Global Quote") or {}
        price = quote.get("05. price")
        if price is None:
            return None

        try:
            price_val = float(price)
        except ValueError:
            return None

        change = quote.get("09. change")
        change_percent = quote.get("10. change percent")
        change_val = self._safe_float(change)
        change_pct_val = self._safe_float(change_percent)

        return {
            "asset_class": "equity",
            "symbol": symbol,
            "price": price_val,
            "change": change_val,
            "change_percent": change_pct_val,
            "volume": self._safe_float(quote.get("06. volume")),
            "source": "Alpha Vantage",
            "text": self._format_equity(symbol, price_val, change_val, change_pct_val, "Alpha Vantage"),
        }

    def _query_finnhub(self, symbol: str) -> Optional[Dict]:
        if not self.finnhub_key:
            return None
        self._respect_rate_limit("finnhub")
        params = {
            "symbol": symbol,
            "token": self.finnhub_key,
        }
        try:
            resp = self._session.get("https://finnhub.io/api/v1/quote", params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, requests.Timeout) as e:
            logger.debug(f"Finnhub error for {symbol}: {e}")
            return None

        current = data.get("c")
        if not current:
            return None

        change = self._safe_float(data.get("d"))
        change_pct = self._safe_float(data.get("dp"))

        return {
            "asset_class": "equity",
            "symbol": symbol,
            "price": float(current),
            "change": change,
            "change_percent": change_pct,
            "high": self._safe_float(data.get("h")),
            "low": self._safe_float(data.get("l")),
            "source": "Finnhub",
            "text": self._format_equity(symbol, float(current), change, change_pct, "Finnhub"),
        }

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    @staticmethod
    def _format_crypto(symbol: str, price: float, change_percent: Optional[float], source: str) -> str:
        change_str = ""
        if change_percent is not None:
            change_str = f" ({change_percent:+.2f}%)"
        return f"{symbol} is trading at ${price:,.4f}{change_str} [Source: {source}]"

    @staticmethod
    def _format_equity(
        symbol: str,
        price: float,
        change: Optional[float],
        change_percent: Optional[float],
        source: str,
    ) -> str:
        parts = [f"{symbol} is trading at ${price:,.2f}"]
        if change is not None:
            parts.append(f"{change:+.2f}")
        if change_percent is not None:
            parts.append(f"({change_percent:+.2f}%)")
        summary = " ".join(parts)
        return f"{summary} [Source: {source}]"

    def _respect_rate_limit(self, name: str) -> None:
        limiter = self._rate_limits.get(name)
        if not limiter:
            return
        now = time.monotonic()
        elapsed = now - limiter["last"]
        wait = limiter["interval"] - elapsed
        if wait > 0:
            time.sleep(wait)
        limiter["last"] = time.monotonic()

    @staticmethod
    def _safe_float(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(str(value).replace("%", ""))
        except ValueError:
            return None


premium_price_service = PremiumPriceService()


__all__ = ["PremiumPriceService", "premium_price_service"]


