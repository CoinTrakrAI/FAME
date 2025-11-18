#!/usr/bin/env python3
"""
FAME Real-Time Data Enhancer
Provides real-time market data for advanced trading handlers
Currently mocked, but designed to connect to actual data sources
"""

import logging
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

# Try to import real data sources
try:
    from core.investment_brain.data_aggregator import get_market_data
    from core.enhanced_market_oracle import EnhancedMarketOracle
    from utils.market_data import get_crypto_price
    REAL_DATA_AVAILABLE = True
except ImportError:
    REAL_DATA_AVAILABLE = False
    logger.warning("Real data sources not available, using mock data")


# Known tickers for validation
KNOWN_TICKERS = {
    # Major stocks
    'SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD',
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C',
    'JNJ', 'PG', 'KO', 'PEP', 'WMT', 'HD',
    'XOM', 'CVX', 'COP', 'SLB',
    # Crypto
    'BTC', 'ETH', 'XRP', 'SOL', 'ADA', 'DOT', 'MATIC', 'LINK', 'AVAX', 'ATOM'
}


def _extract_symbol(text: str) -> Optional[str]:
    """
    Extract stock/crypto symbol from text
    
    Args:
        text: Question text
        
    Returns:
        Symbol (uppercase) if found, None otherwise
    """
    import re
    
    # Look for known tickers (uppercase, 1-5 chars, word boundaries)
    text_upper = text.upper()
    
    # Find all potential tickers
    ticker_pattern = r'\b([A-Z]{1,5})\b'
    matches = re.findall(ticker_pattern, text_upper)
    
    # Return first known ticker found
    for match in matches:
        if match in KNOWN_TICKERS:
            return match
    
    return None


def get_options_chain(symbol: str, expiration_days: int = 30) -> Optional[Dict[str, Any]]:
    """
    Get options chain data for a symbol
    
    Args:
        symbol: Stock symbol
        expiration_days: Target expiration in days
        
    Returns:
        Options chain data or None
    """
    if not REAL_DATA_AVAILABLE:
        # Mock options data
        return _mock_options_chain(symbol, expiration_days)
    
    try:
        # TODO: Connect to real options data source (CBOE, Interactive Brokers, etc.)
        # For now, return mock
        return _mock_options_chain(symbol, expiration_days)
    except Exception as e:
        logger.error(f"Error fetching options chain for {symbol}: {e}")
        return None


def _mock_options_chain(symbol: str, expiration_days: int) -> Dict[str, Any]:
    """Generate mock options chain data"""
    import random
    
    # Mock ATM price
    base_price = 100.0 if symbol != 'SPY' else 450.0
    
    # Mock IVs
    atm_iv = 0.20 + random.uniform(-0.05, 0.05)  # 15-25%
    put_iv = atm_iv + random.uniform(0.02, 0.08)  # Higher for puts (skew)
    call_iv = atm_iv - random.uniform(0.01, 0.03)  # Lower for calls
    
    # Mock Greeks
    delta_put = random.uniform(-0.45, -0.35)  # OTM put delta
    delta_call = random.uniform(0.35, 0.45)  # OTM call delta
    gamma = random.uniform(0.01, 0.02)
    theta = random.uniform(-0.05, -0.02)  # Negative (time decay)
    vega = random.uniform(0.10, 0.20)
    
    # Calculate skew
    skew = (put_iv - call_iv) / atm_iv
    
    return {
        'symbol': symbol,
        'underlying_price': base_price,
        'expiration_days': expiration_days,
        'atm_iv': atm_iv,
        'put_iv': put_iv,
        'call_iv': call_iv,
        'skew': skew,
        'greeks': {
            'delta_put': delta_put,
            'delta_call': delta_call,
            'gamma': gamma,
            'theta': theta,
            'vega': vega
        },
        'timestamp': time.time(),
        'data_source': 'mock'  # Will be 'real' when connected to actual source
    }


def get_risk_metrics(portfolio: Dict[str, float]) -> Optional[Dict[str, Any]]:
    """
    Calculate risk metrics for a portfolio
    
    Args:
        portfolio: Dict of {symbol: weight} e.g., {'SPY': 0.6, 'QQQ': 0.3, 'TLT': 0.1}
        
    Returns:
        Risk metrics dict or None
    """
    if not REAL_DATA_AVAILABLE:
        return _mock_risk_metrics(portfolio)
    
    try:
        # TODO: Connect to real risk calculation service
        # For now, return mock
        return _mock_risk_metrics(portfolio)
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}")
        return None


def _mock_risk_metrics(portfolio: Dict[str, float]) -> Dict[str, Any]:
    """Generate mock risk metrics"""
    import random
    import numpy as np
    
    # Mock volatilities and correlations
    symbols = list(portfolio.keys())
    weights = list(portfolio.values())
    
    # Mock volatilities (annualized)
    volatilities = {sym: random.uniform(0.15, 0.35) for sym in symbols}
    
    # Mock correlations (positive for equity, negative for bonds)
    correlations = {}
    for i, sym1 in enumerate(symbols):
        for j, sym2 in enumerate(symbols):
            if i == j:
                corr = 1.0
            elif 'TLT' in [sym1, sym2] and 'TLT' not in [sym1, sym2]:
                corr = random.uniform(-0.3, 0.1)  # Bonds negatively correlated with stocks
            else:
                corr = random.uniform(0.5, 0.9)  # Stocks positively correlated
            correlations[(sym1, sym2)] = corr
    
    # Calculate portfolio volatility (simplified)
    portfolio_vol = 0.0
    for i, sym1 in enumerate(symbols):
        for j, sym2 in enumerate(symbols):
            portfolio_vol += weights[i] * weights[j] * volatilities[sym1] * volatilities[sym2] * correlations[(sym1, sym2)]
    portfolio_vol = np.sqrt(portfolio_vol)
    
    # Mock VaR (95% confidence, 1-day)
    var_95_daily = portfolio_vol / np.sqrt(252) * 1.645  # Approximate
    
    # Mock Sharpe (assume 8% annual return, 2% risk-free)
    sharpe = (0.08 - 0.02) / portfolio_vol
    
    # Mock Sortino (assume same return, but only downside volatility)
    downside_vol = portfolio_vol * 0.7  # Rough estimate
    sortino = (0.08 - 0.02) / downside_vol
    
    return {
        'portfolio': portfolio,
        'volatilities': volatilities,
        'correlations': correlations,
        'portfolio_volatility': portfolio_vol,
        'var_95_daily': var_95_daily,
        'var_95_monthly': var_95_daily * np.sqrt(21),
        'var_95_annual': var_95_daily * np.sqrt(252),
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'timestamp': time.time(),
        'data_source': 'mock'
    }


def get_market_regime() -> Optional[Dict[str, Any]]:
    """
    Get current market regime classification
    
    Returns:
        Market regime dict or None
    """
    if not REAL_DATA_AVAILABLE:
        return _mock_market_regime()
    
    try:
        # TODO: Connect to real market regime detection
        # For now, return mock
        return _mock_market_regime()
    except Exception as e:
        logger.error(f"Error detecting market regime: {e}")
        return None


def _mock_market_regime() -> Dict[str, Any]:
    """Generate mock market regime"""
    import random
    
    # Mock VIX-based regime
    vix = random.uniform(12, 25)
    
    if vix < 15:
        regime = 'bull'
        volatility_regime = 'low'
    elif vix < 20:
        regime = 'neutral'
        volatility_regime = 'moderate'
    else:
        regime = 'bear'
        volatility_regime = 'high'
    
    return {
        'regime': regime,
        'volatility_regime': volatility_regime,
        'vix': vix,
        'confidence': random.uniform(0.7, 0.9),
        'timestamp': time.time(),
        'data_source': 'mock'
    }


def get_real_time_price(symbol: str, asset_type: str = "stock") -> Optional[Dict[str, Any]]:
    """
    Get real-time price data for a symbol
    
    Args:
        symbol: Asset symbol
        asset_type: "stock", "crypto", etc.
        
    Returns:
        Price data dict or None
    """
    if not REAL_DATA_AVAILABLE:
        return _mock_price_data(symbol, asset_type)
    
    try:
        # Try Investment Brain data aggregator
        from core.investment_brain.data_aggregator import get_market_data_sync
        data = get_market_data_sync(symbol, asset_type)
        if data:
            return {
                'symbol': symbol,
                'price': data.get('price_usd') or data.get('price'),
                'timestamp': time.time(),
                'data_source': 'data_aggregator'
            }
        
        # Try Enhanced Market Oracle
        try:
            oracle = EnhancedMarketOracle()
            import asyncio
            loop = asyncio.get_event_loop()
            market_data = loop.run_until_complete(oracle.get_real_market_data(symbol))
            if market_data and 'current_price' in market_data:
                return {
                    'symbol': symbol,
                    'price': market_data['current_price'],
                    'volume': market_data.get('volume'),
                    'timestamp': time.time(),
                    'data_source': 'market_oracle'
                }
        except Exception:
            pass
        
        # Try crypto price
        if asset_type == "crypto":
            try:
                crypto_data = get_crypto_price(symbol)
                if crypto_data and 'price' in crypto_data:
                    return {
                        'symbol': symbol,
                        'price': crypto_data['price'],
                        'timestamp': time.time(),
                        'data_source': 'crypto_api'
                    }
            except Exception:
                pass
        
        # Fallback to mock
        return _mock_price_data(symbol, asset_type)
    except Exception as e:
        logger.error(f"Error fetching real-time price for {symbol}: {e}")
        return _mock_price_data(symbol, asset_type)


def _mock_price_data(symbol: str, asset_type: str) -> Dict[str, Any]:
    """Generate mock price data"""
    import random
    
    # Mock prices based on symbol
    base_prices = {
        'SPY': 450.0,
        'QQQ': 380.0,
        'AAPL': 175.0,
        'MSFT': 380.0,
        'TSLA': 250.0,
        'BTC': 43000.0,
        'ETH': 2500.0,
        'XRP': 0.60
    }
    
    base_price = base_prices.get(symbol, 100.0)
    price = base_price * random.uniform(0.95, 1.05)  # ±5% variation
    
    return {
        'symbol': symbol,
        'price': price,
        'timestamp': time.time(),
        'data_source': 'mock'
    }


def extract_symbol(text: str) -> Optional[str]:
    """
    Extract symbol from text (public wrapper)
    
    Args:
        text: Question text
        
    Returns:
        Symbol (uppercase) if found, None otherwise
    """
    return _extract_symbol(text)


__all__ = [
    'get_options_chain',
    'get_risk_metrics',
    'get_market_regime',
    'get_real_time_price',
    'extract_symbol',
    'KNOWN_TICKERS'
]

