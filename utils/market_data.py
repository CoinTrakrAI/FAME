#!/usr/bin/env python3
"""
FAME Market Data Utility - Real-time price fetching for cryptocurrencies and stocks
Supports CoinGecko, Alpha Vantage, and Finnhub APIs
"""

import requests
import time
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL = int(os.getenv("PRICE_CACHE_TTL_SECONDS", "60"))  # 1 minute default
_price_cache = {}

# API Keys
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "CG-PwNH6eV5PhUhFMhHspq3nqoz")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "3GEY3XZMBLJGQ099")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "d3vpeq1r01qhm1tedo10d3vpeq1r01qhm1tedo1g")


def _cache_set(key: str, value: Dict[str, Any]):
    """Set cache entry with timestamp"""
    _price_cache[key] = {"ts": time.time(), "value": value}


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    """Get cache entry if valid, None if expired or missing"""
    v = _price_cache.get(key)
    if not v:
        return None
    if time.time() - v["ts"] > CACHE_TTL:
        return None
    return v["value"]


def get_current_price_coingecko(coin_id: str = "ripple", vs_currency: str = "usd", use_cache: bool = True) -> Dict[str, Any]:
    """
    Fetch current price from CoinGecko API
    
    Args:
        coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'ripple' for XRP)
        vs_currency: Currency to compare against (default: 'usd')
        use_cache: Whether to use cached results (default: True)
    
    Returns:
        dict: {'price': float, 'timestamp': int, 'provider': 'coingecko'}
    
    Raises:
        requests.HTTPError: On API fetch failure
        ValueError: If coin not found in response
    """
    cache_key = f"coingecko:{coin_id}:{vs_currency}"
    
    if use_cache:
        cached = _cache_get(cache_key)
        if cached:
            logger.debug(f"Using cached price for {coin_id}")
            return cached
    
    try:
        # CoinGecko API endpoint
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": vs_currency,
            "include_last_updated_at": "true"
        }
        
        # Add API key if available (for higher rate limits)
        headers = {}
        if COINGECKO_API_KEY:
            headers["CG-Demo-API-Key"] = COINGECKO_API_KEY
        
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        
        if coin_id not in data:
            raise ValueError(f"Coin '{coin_id}' not found in CoinGecko response")
        
        price = float(data[coin_id][vs_currency])
        ts = int(data[coin_id].get("last_updated_at", time.time()))
        
        result = {
            "price": price,
            "timestamp": ts,
            "provider": "coingecko",
            "coin_id": coin_id,
            "currency": vs_currency
        }
        
        _cache_set(cache_key, result)
        logger.info(f"Fetched {coin_id} price: ${price:.6f} from CoinGecko")
        return result
        
    except requests.RequestException as e:
        logger.error(f"CoinGecko API error: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"CoinGecko response parsing error: {e}")
        raise


def get_current_price_alphavantage(symbol: str = "XRP") -> Dict[str, Any]:
    """
    Fetch current price from Alpha Vantage (for stocks, can also handle crypto if available)
    
    Args:
        symbol: Stock or crypto symbol (e.g., 'AAPL', 'XRP')
    
    Returns:
        dict: {'price': float, 'timestamp': int, 'provider': 'alphavantage'}
    
    Raises:
        requests.HTTPError: On API fetch failure
    """
    cache_key = f"alphavantage:{symbol}"
    
    cached = _cache_get(cache_key)
    if cached:
        return cached
    
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": symbol,
            "to_currency": "USD",
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        
        if "Error Message" in data:
            raise ValueError(data["Error Message"])
        
        if "Realtime Currency Exchange Rate" not in data:
            raise ValueError("Invalid Alpha Vantage response format")
        
        exchange_data = data["Realtime Currency Exchange Rate"]
        price = float(exchange_data["5. Exchange Rate"])
        ts = int(time.time())  # Alpha Vantage doesn't provide timestamp
        
        result = {
            "price": price,
            "timestamp": ts,
            "provider": "alphavantage",
            "symbol": symbol
        }
        
        _cache_set(cache_key, result)
        return result
        
    except requests.RequestException as e:
        logger.error(f"Alpha Vantage API error: {e}")
        raise


def get_current_price_finnhub(symbol: str = "XRP") -> Dict[str, Any]:
    """
    Fetch current price from Finnhub (primarily for stocks, but can handle crypto quotes)
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
    
    Returns:
        dict: {'price': float, 'timestamp': int, 'provider': 'finnhub'}
    
    Raises:
        requests.HTTPError: On API fetch failure
    """
    cache_key = f"finnhub:{symbol}"
    
    cached = _cache_get(cache_key)
    if cached:
        return cached
    
    try:
        url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol,
            "token": FINNHUB_API_KEY
        }
        
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        
        if "c" not in data or data["c"] == 0:
            raise ValueError(f"No valid price data for {symbol}")
        
        price = float(data["c"])  # Current price
        ts = int(time.time())  # Finnhub doesn't provide explicit timestamp in quote
        
        result = {
            "price": price,
            "timestamp": ts,
            "provider": "finnhub",
            "symbol": symbol
        }
        
        _cache_set(cache_key, result)
        return result
        
    except requests.RequestException as e:
        logger.error(f"Finnhub API error: {e}")
        raise


def get_crypto_price(coin_symbol: str, preferred_provider: str = "coingecko") -> Dict[str, Any]:
    """
    Fetch cryptocurrency price with fallback providers
    
    Args:
        coin_symbol: Cryptocurrency symbol (e.g., 'XRP', 'BTC', 'ETH')
        preferred_provider: Primary provider to use ('coingecko', 'alphavantage', 'finnhub')
    
    Returns:
        dict: Price information with provider details
    
    Raises:
        Exception: If all providers fail
    """
    # CoinGecko coin ID mapping
    coin_id_map = {
        "XRP": "ripple",
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "ADA": "cardano",
        "SOL": "solana",
        "DOGE": "dogecoin",
        "MATIC": "matic-network",
        "DOT": "polkadot",
        "LINK": "chainlink"
    }
    
    coin_id = coin_id_map.get(coin_symbol.upper(), coin_symbol.lower())
    
    providers = []
    if preferred_provider == "coingecko":
        providers = [
            ("coingecko", lambda: get_current_price_coingecko(coin_id=coin_id)),
            ("alphavantage", lambda: get_current_price_alphavantage(symbol=coin_symbol)),
        ]
    elif preferred_provider == "alphavantage":
        providers = [
            ("alphavantage", lambda: get_current_price_alphavantage(symbol=coin_symbol)),
            ("coingecko", lambda: get_current_price_coingecko(coin_id=coin_id)),
        ]
    else:
        providers = [
            ("coingecko", lambda: get_current_price_coingecko(coin_id=coin_id)),
        ]
    
    last_error = None
    for provider_name, provider_func in providers:
        try:
            result = provider_func()
            logger.info(f"Successfully fetched {coin_symbol} price from {provider_name}: ${result['price']:.6f}")
            return result
        except Exception as e:
            logger.warning(f"Provider {provider_name} failed for {coin_symbol}: {e}")
            last_error = e
            continue
    
    # All providers failed
    raise Exception(f"All price providers failed for {coin_symbol}. Last error: {last_error}")


def validate_price_data(price_data: Dict[str, Any], max_age_seconds: int = 300) -> bool:
    """
    Validate price data freshness and validity
    
    Args:
        price_data: Price data dict with 'price' and 'timestamp'
        max_age_seconds: Maximum age in seconds (default: 5 minutes)
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not price_data:
        return False
    
    price = price_data.get("price")
    timestamp = price_data.get("timestamp")
    
    # Check price validity
    if price is None or price <= 0:
        logger.warning(f"Invalid price value: {price}")
        return False
    
    # Check timestamp freshness
    if timestamp is None:
        logger.warning("Missing timestamp in price data")
        return False
    
    age = time.time() - timestamp
    if age > max_age_seconds:
        logger.warning(f"Price data is stale: {age:.0f} seconds old (max: {max_age_seconds}s)")
        return False
    
    return True

