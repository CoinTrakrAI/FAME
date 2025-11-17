#!/usr/bin/env python3
"""
FAME Finance-First Router
Prioritizes financial queries and routes to comprehensive financial analysis
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Comprehensive financial asset types
STOCK_TICKERS = {
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'INTC', 'AMD',
    'SPY', 'QQQ', 'DIA', 'IWM', 'VTI', 'VOO', 'VEA', 'VWO', 'BND', 'GLD', 'SLV',
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'XOM', 'CVX', 'COP', 'SLB'
}

CRYPTO_TICKERS = {
    'BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'DOGE', 'MATIC', 'DOT', 'AVAX',
    'LINK', 'UNI', 'BNB', 'LTC', 'BCH', 'XLM', 'ATOM', 'ALGO', 'VET', 'TRX'
}

CRYPTO_NAME_MAP = {
    'bitcoin': 'BTC', 'ethereum': 'ETH', 'ripple': 'XRP', 'xrp': 'XRP',
    'cardano': 'ADA', 'solana': 'SOL', 'dogecoin': 'DOGE', 'doge': 'DOGE',
    'polygon': 'MATIC', 'matic': 'MATIC', 'polkadot': 'DOT', 'avalanche': 'AVAX',
    'chainlink': 'LINK', 'uniswap': 'UNI', 'binance coin': 'BNB', 'bnb': 'BNB',
    'litecoin': 'LTC', 'bitcoin cash': 'BCH', 'stellar': 'XLM'
}

COMPANY_NAME_MAP = {
    'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL',
    'amazon': 'AMZN', 'tesla': 'TSLA', 'meta': 'META', 'facebook': 'META',
    'netflix': 'NFLX', 'nvidia': 'NVDA', 'intel': 'INTC', 'amd': 'AMD',
    'jpmorgan': 'JPM', 'bank of america': 'BAC', 'wells fargo': 'WFC',
    'goldman sachs': 'GS', 'morgan stanley': 'MS', 'exxon': 'XOM', 'chevron': 'CVX'
}

# Trading strategy keywords
TRADING_STRATEGIES = {
    'day trading', 'swing trading', 'position trading', 'scalping',
    'momentum trading', 'mean reversion', 'trend following', 'breakout',
    'support resistance', 'technical analysis', 'fundamental analysis',
    'options trading', 'futures trading', 'forex trading', 'crypto trading'
}

# Asset class keywords
ASSET_CLASSES = {
    'stocks', 'equities', 'crypto', 'cryptocurrency', 'commodities',
    'precious metals', 'gold', 'silver', 'platinum', 'palladium',
    'etf', 'etfs', 'mutual funds', 'bonds', 'treasuries', 'forex',
    'currencies', 'nft', 'nfts', 'options', 'futures', 'derivatives'
}


class FinanceFirstRouter:
    """
    Finance-first router that prioritizes financial queries
    and provides comprehensive financial analysis
    """
    
    def __init__(self):
        self.financial_keywords = {
            'price', 'trading', 'market', 'stock', 'crypto', 'bitcoin', 'ethereum',
            'analyze', 'analysis', 'forecast', 'prediction', 'trend', 'chart',
            'volume', 'volatility', 'sentiment', 'news', 'earnings', 'dividend',
            'buy', 'sell', 'hold', 'recommendation', 'target', 'support', 'resistance',
            'rsi', 'macd', 'moving average', 'bollinger', 'stochastic', 'indicator',
            'portfolio', 'allocation', 'risk', 'return', 'sharpe', 'beta', 'alpha',
            'day trade', 'swing trade', 'position trade', 'scalp', 'momentum',
            'commodity', 'precious metal', 'gold', 'silver', 'oil', 'gas',
            'etf', 'mutual fund', 'bond', 'treasury', 'forex', 'currency',
            'nft', 'token', 'coin', 'blockchain', 'defi', 'staking', 'yield'
        }
    
    def is_financial_query(self, text: str) -> Tuple[bool, float]:
        """
        Determine if query is financial and return confidence
        Returns: (is_financial, confidence)
        """
        if not text:
            return False, 0.0
        
        text_lower = text.lower()
        
        # Check for explicit financial keywords
        keyword_matches = sum(1 for kw in self.financial_keywords if kw in text_lower)
        keyword_confidence = min(1.0, keyword_matches / 3.0)  # At least 3 keywords = high confidence
        
        # Check for ticker symbols
        ticker_confidence = 0.0
        potential_tickers = re.findall(r'\b([A-Z]{2,5})\b', text.upper())
        for ticker in potential_tickers:
            if ticker in STOCK_TICKERS or ticker in CRYPTO_TICKERS:
                ticker_confidence = 0.9
                break
        
        # Check for company/crypto names
        name_confidence = 0.0
        for name, ticker in {**COMPANY_NAME_MAP, **CRYPTO_NAME_MAP}.items():
            if name in text_lower:
                name_confidence = 0.85
                break
        
        # Check for trading strategy terms
        strategy_confidence = 0.0
        for strategy in TRADING_STRATEGIES:
            if strategy in text_lower:
                strategy_confidence = 0.8
                break
        
        # Check for asset class terms
        asset_confidence = 0.0
        for asset in ASSET_CLASSES:
            if asset in text_lower:
                asset_confidence = 0.75
                break
        
        # Combine confidences
        max_confidence = max(keyword_confidence, ticker_confidence, name_confidence, 
                           strategy_confidence, asset_confidence)
        
        # If any confidence > 0.5, it's likely financial
        is_financial = max_confidence > 0.5 or keyword_matches >= 2
        
        return is_financial, max_confidence
    
    def extract_financial_intent(self, text: str) -> Dict[str, Any]:
        """
        Extract detailed financial intent from query
        """
        text_lower = text.lower()
        intent = {
            'type': 'unknown',
            'asset_type': None,
            'symbol': None,
            'action': None,
            'timeframe': None,
            'strategy': None,
            'confidence': 0.0
        }
        
        # Extract symbol
        symbol = self._extract_symbol(text)
        if symbol:
            intent['symbol'] = symbol
            intent['asset_type'] = 'stock' if symbol in STOCK_TICKERS else 'crypto'
            intent['confidence'] += 0.3
        
        # Extract asset type
        if any(term in text_lower for term in ['stock', 'equity', 'share']):
            intent['asset_type'] = 'stock'
            intent['confidence'] += 0.2
        elif any(term in text_lower for term in ['crypto', 'cryptocurrency', 'coin', 'token']):
            intent['asset_type'] = 'crypto'
            intent['confidence'] += 0.2
        elif any(term in text_lower for term in ['commodity', 'gold', 'silver', 'oil']):
            intent['asset_type'] = 'commodity'
            intent['confidence'] += 0.2
        elif any(term in text_lower for term in ['etf', 'mutual fund']):
            intent['asset_type'] = 'etf'
            intent['confidence'] += 0.2
        
        # Extract action
        if any(term in text_lower for term in ['price', 'what is', "what's", 'how much']):
            intent['action'] = 'get_price'
            intent['confidence'] += 0.2
        elif any(term in text_lower for term in ['analyze', 'analysis', 'analyze']):
            intent['action'] = 'analyze'
            intent['confidence'] += 0.25
        elif any(term in text_lower for term in ['predict', 'forecast', 'projection', 'target']):
            intent['action'] = 'predict'
            intent['confidence'] += 0.25
        elif any(term in text_lower for term in ['buy', 'sell', 'hold', 'recommend']):
            intent['action'] = 'recommendation'
            intent['confidence'] += 0.3
        elif any(term in text_lower for term in ['trade', 'trading', 'strategy']):
            intent['action'] = 'trading_strategy'
            intent['confidence'] += 0.25
        
        # Extract timeframe
        if any(term in text_lower for term in ['today', 'current', 'now', 'live']):
            intent['timeframe'] = 'intraday'
        elif any(term in text_lower for term in ['week', 'weekly']):
            intent['timeframe'] = 'weekly'
        elif any(term in text_lower for term in ['month', 'monthly']):
            intent['timeframe'] = 'monthly'
        elif any(term in text_lower for term in ['year', 'yearly', 'annual']):
            intent['timeframe'] = 'yearly'
        elif any(term in text_lower for term in ['10 years', 'long term']):
            intent['timeframe'] = 'long_term'
        
        # Extract trading strategy
        for strategy in TRADING_STRATEGIES:
            if strategy in text_lower:
                intent['strategy'] = strategy
                intent['confidence'] += 0.15
                break
        
        # Determine intent type
        if intent['action'] == 'get_price':
            intent['type'] = 'price_query'
        elif intent['action'] == 'analyze':
            intent['type'] = 'analysis_query'
        elif intent['action'] == 'predict':
            intent['type'] = 'prediction_query'
        elif intent['action'] == 'recommendation':
            intent['type'] = 'recommendation_query'
        elif intent['action'] == 'trading_strategy':
            intent['type'] = 'strategy_query'
        elif symbol:
            intent['type'] = 'price_query'  # Default to price if symbol found
        else:
            intent['type'] = 'general_financial'
        
        return intent
    
    def _extract_symbol(self, text: str) -> Optional[str]:
        """Extract stock or crypto symbol from text"""
        # Check for $SYMBOL format
        dollar_match = re.search(r'\$([A-Z]{2,5})\b', text.upper())
        if dollar_match:
            symbol = dollar_match.group(1)
            if symbol in STOCK_TICKERS or symbol in CRYPTO_TICKERS:
                return symbol
        
        # Check for standalone tickers
        potential_tickers = re.findall(r'\b([A-Z]{2,5})\b', text.upper())
        for ticker in potential_tickers:
            if ticker in STOCK_TICKERS or ticker in CRYPTO_TICKERS:
                return ticker
        
        # Check for company/crypto names
        text_lower = text.lower()
        for name, ticker in {**COMPANY_NAME_MAP, **CRYPTO_NAME_MAP}.items():
            if name in text_lower:
                return ticker
        
        return None


# Global instance
finance_first_router = FinanceFirstRouter()

