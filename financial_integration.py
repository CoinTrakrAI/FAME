#!/usr/bin/env python3
"""
F.A.M.E Financial Data Integration
Real-time market data, backtesting, and sentiment analysis
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

# Load API keys from config
try:
    from fame_config import (
        ALPHA_VANTAGE_API_KEY,
        COINGECKO_API_KEY,
        FINNHUB_API_KEY,
        setup_environment
    )
    setup_environment()
except ImportError:
    pass  # Use environment variables if config not available

# Try importing financial libraries
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    np = None


def get_price_for_ticker(ticker: str) -> float:
    """
    Simple wrapper to get current stock price for a ticker.
    Used by assistant action router.
    """
    try:
        aggregator = FinancialDataAggregator()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data = loop.run_until_complete(aggregator.get_stock_data(ticker))
            if data and 'close' in data:
                return float(data['close'])
            # Fallback to yfinance
            if YFINANCE_AVAILABLE:
                stock = yf.Ticker(ticker)
                info = stock.info
                if 'currentPrice' in info:
                    return float(info['currentPrice'])
                elif 'regularMarketPrice' in info:
                    return float(info['regularMarketPrice'])
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"Error getting price for {ticker}: {e}")
    
    # Last resort: return 0.0 if all fails
    return 0.0


class FinancialDataAggregator:
    """Aggregate financial data from multiple sources"""
    
    def __init__(self):
        self.data_cache = {}
        self.cache_duration = timedelta(minutes=5)
        
    async def get_stock_data(self, symbol: str, period: str = "1d", interval: str = "1m") -> Optional[Dict]:
        """Get OHLCV data for a stock symbol - tries Alpha Vantage first, then yfinance, then Finnhub"""
        # Try Alpha Vantage first (has API key)
        alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if alpha_key and REQUESTS_AVAILABLE:
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'TIME_SERIES_INTRADAY',
                    'symbol': symbol,
                    'interval': '1min',
                    'apikey': alpha_key
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'Time Series (1min)' in data:
                        time_series = data['Time Series (1min)']
                        latest_time = max(time_series.keys())
                        latest_data = time_series[latest_time]
                        return {
                            "symbol": symbol,
                            "open": float(latest_data['1. open']),
                            "high": float(latest_data['2. high']),
                            "low": float(latest_data['3. low']),
                            "close": float(latest_data['4. close']),
                            "volume": int(latest_data['5. volume']),
                            "timestamp": latest_time,
                            "source": "Alpha Vantage"
                        }
            except Exception as e:
                logging.debug(f"Alpha Vantage error: {e}")
        
        # Try Finnhub as backup
        finnhub_key = os.getenv('FINNHUB_API_KEY')
        if finnhub_key and REQUESTS_AVAILABLE:
            try:
                url = f"https://finnhub.io/api/v1/quote"
                params = {'symbol': symbol, 'token': finnhub_key}
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'c' in data:  # 'c' is current price
                        return {
                            "symbol": symbol,
                            "close": float(data.get('c', 0)),
                            "high": float(data.get('h', 0)),
                            "low": float(data.get('l', 0)),
                            "open": float(data.get('o', 0)),
                            "volume": int(data.get('v', 0)),
                            "timestamp": datetime.now().isoformat(),
                            "source": "Finnhub"
                        }
            except Exception as e:
                logging.debug(f"Finnhub error: {e}")
        
        # Fallback to yfinance
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval=interval)
                
                if data.empty:
                    return None
                
                # Convert to dictionary with latest values
                latest = data.iloc[-1]
                
                return {
                    "symbol": symbol,
                    "open": float(latest['Open']),
                    "high": float(latest['High']),
                    "low": float(latest['Low']),
                    "close": float(latest['Close']),
                    "volume": int(latest['Volume']),
                    "timestamp": latest.name.isoformat() if hasattr(latest.name, 'isoformat') else str(latest.name),
                    "data_points": len(data),
                    "source": "Yahoo Finance"
                }
            except Exception as e:
                logging.error(f"Error fetching stock data for {symbol}: {e}")
        
        return None
    
    async def get_crypto_data(self, symbol: str, vs_currency: str = "usd") -> Optional[Dict]:
        """Get cryptocurrency data using CoinGecko API"""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            # Use CoinGecko API (with API key if available)
            api_key = os.getenv('COINGECKO_API_KEY')
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': symbol.lower(),
                'vs_currencies': vs_currency,
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            
            headers = {}
            if api_key:
                headers['x-cg-demo-api-key'] = api_key
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if symbol.lower() in data:
                    return data[symbol.lower()]
            return None
        except Exception as e:
            logging.error(f"Error fetching crypto data for {symbol}: {e}")
            return None
    
    async def get_multiple_assets(self, symbols: List[str], asset_type: str = "stock") -> Dict[str, Any]:
        """Get data for multiple assets in parallel"""
        tasks = []
        
        for symbol in symbols:
            if asset_type == "stock":
                tasks.append(self.get_stock_data(symbol))
            elif asset_type == "crypto":
                tasks.append(self.get_crypto_data(symbol))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        aggregated = {}
        for symbol, result in zip(symbols, results):
            if not isinstance(result, Exception) and result:
                aggregated[symbol] = result
        
        return aggregated


class TradingStrategyBacktester:
    """Backtest trading strategies on historical data"""
    
    def __init__(self):
        if not PANDAS_AVAILABLE:
            logging.warning("pandas/numpy not available for backtesting")
    
    async def backtest_strategy(self, symbol: str, strategy_func, period: str = "1y") -> Optional[Dict]:
        """Backtest a trading strategy"""
        if not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE:
            return None
        
        try:
            # Get historical data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                return None
            
            # Simple moving average crossover strategy (example)
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            
            # Generate signals
            data['Signal'] = 0
            data.loc[data['SMA_50'] > data['SMA_200'], 'Signal'] = 1  # Buy signal
            data.loc[data['SMA_50'] < data['SMA_200'], 'Signal'] = -1  # Sell signal
            
            # Calculate returns
            data['Returns'] = data['Close'].pct_change()
            data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
            
            # Calculate metrics
            total_return = data['Strategy_Returns'].sum()
            sharpe_ratio = self._calculate_sharpe_ratio(data['Strategy_Returns'])
            max_drawdown = self._calculate_max_drawdown(data['Close'])
            
            return {
                "symbol": symbol,
                "period": period,
                "total_return": float(total_return),
                "sharpe_ratio": float(sharpe_ratio),
                "max_drawdown": float(max_drawdown),
                "win_rate": float((data['Strategy_Returns'] > 0).sum() / len(data['Strategy_Returns'].dropna())),
                "trades": int((data['Signal'].diff() != 0).sum())
            }
        except Exception as e:
            logging.error(f"Error backtesting strategy for {symbol}: {e}")
            return None
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns.mean() * 252 - risk_free_rate  # Annualized
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        if volatility == 0:
            return 0.0
        
        return excess_returns / volatility
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        if len(prices) == 0:
            return 0.0
        
        peak = prices.expanding().max()
        drawdown = (prices - peak) / peak
        return float(drawdown.min())


class FinancialSentimentAnalyzer:
    """Analyze sentiment from financial news"""
    
    def __init__(self):
        if SENTIMENT_AVAILABLE:
            self.analyzer = SentimentIntensityAnalyzer()
        else:
            self.analyzer = None
            logging.warning("VADER sentiment analyzer not available. Install with: pip install vaderSentiment")
    
    async def analyze_news_sentiment(self, articles: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment from news articles"""
        if not self.analyzer or not articles:
            return {"sentiment": "neutral", "score": 0.0, "article_count": 0}
        
        sentiments = []
        
        for article in articles:
            text = article.get('title', '') + ' ' + article.get('description', '')
            if text:
                scores = self.analyzer.polarity_scores(text)
                sentiments.append(scores)
        
        if not sentiments:
            return {"sentiment": "neutral", "score": 0.0, "article_count": 0}
        
        # Aggregate sentiments
        avg_compound = sum(s['compound'] for s in sentiments) / len(sentiments)
        
        if avg_compound >= 0.05:
            sentiment_label = "positive"
        elif avg_compound <= -0.05:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        return {
            "sentiment": sentiment_label,
            "score": float(avg_compound),
            "article_count": len(articles),
            "positive_count": sum(1 for s in sentiments if s['compound'] > 0.05),
            "negative_count": sum(1 for s in sentiments if s['compound'] < -0.05),
            "neutral_count": sum(1 for s in sentiments if -0.05 <= s['compound'] <= 0.05)
        }
    
    async def get_financial_news(self, query: str = "stock market", max_results: int = 10) -> List[Dict]:
        """Get financial news articles"""
        if not REQUESTS_AVAILABLE:
            return []
        
        try:
            # Use NewsAPI (requires API key) or GNews
            # For now, return empty list - would integrate with actual news API
            # This would use the existing news fetching from F.A.M.E system
            
            return []
        except Exception as e:
            logging.error(f"Error fetching financial news: {e}")
            return []


class FAMEFinancialEngine:
    """Main financial data engine for F.A.M.E"""
    
    def __init__(self):
        self.aggregator = FinancialDataAggregator()
        self.backtester = TradingStrategyBacktester()
        self.sentiment_analyzer = FinancialSentimentAnalyzer()
        
        # Learning rules and strategies
        self.learned_patterns = []
        self.strategy_performance = {}
    
    async def get_market_overview(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get comprehensive market overview"""
        if not symbols:
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]  # Default stocks
        
        # Get data for all symbols in parallel
        stock_data = await self.aggregator.get_multiple_assets(symbols, asset_type="stock")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "symbols_analyzed": len(stock_data),
            "data": stock_data,
            "market_summary": self._generate_market_summary(stock_data)
        }
    
    def _generate_market_summary(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market summary from aggregated data"""
        if not stock_data:
            return {"status": "no_data"}
        
        prices = [d.get('close', 0) for d in stock_data.values() if d.get('close')]
        volumes = [d.get('volume', 0) for d in stock_data.values() if d.get('volume')]
        
        if not prices:
            return {"status": "insufficient_data"}
        
        return {
            "average_price": float(sum(prices) / len(prices)),
            "total_volume": int(sum(volumes)),
            "price_range": {
                "min": float(min(prices)),
                "max": float(max(prices))
            },
            "market_status": "active" if volumes else "inactive"
        }
    
    async def learn_from_data(self, symbol: str, days: int = 30):
        """Learn patterns from historical data"""
        if not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE:
            return
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f"{days}d")
            
            if data.empty:
                return
            
            # Extract patterns (simplified example)
            price_trend = "up" if data['Close'].iloc[-1] > data['Close'].iloc[0] else "down"
            volatility = float(data['Close'].pct_change().std())
            
            pattern = {
                "symbol": symbol,
                "trend": price_trend,
                "volatility": volatility,
                "learned_at": datetime.now().isoformat(),
                "data_points": len(data)
            }
            
            self.learned_patterns.append(pattern)
            
            logging.info(f"Learned pattern for {symbol}: {pattern}")
        except Exception as e:
            logging.error(f"Error learning from data for {symbol}: {e}")


# Integration function for F.A.M.E desktop
async def get_financial_insight(query: str) -> str:
    """Generate financial insight based on query"""
    engine = FAMEFinancialEngine()
    
    query_lower = query.lower()
    
    # Detect what user is asking for
    if "stock" in query_lower or "price" in query_lower:
        # Extract stock symbol (simple detection)
        symbols_to_check = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA"]
        detected_symbol = None
        
        for symbol in symbols_to_check:
            if symbol.lower() in query_lower or symbol in query:
                detected_symbol = symbol
                break
        
        if detected_symbol:
            data = await engine.aggregator.get_stock_data(detected_symbol)
            if data:
                return f"{detected_symbol}: ${data['close']:.2f} (Open: ${data['open']:.2f}, High: ${data['high']:.2f}, Low: ${data['low']:.2f}, Volume: {data['volume']:,})"
        else:
            # Get market overview
            overview = await engine.get_market_overview()
            return f"Market Overview: {overview['market_summary']}"
    
    elif "crypto" in query_lower or "bitcoin" in query_lower:
        crypto_data = await engine.aggregator.get_crypto_data("bitcoin")
        if crypto_data:
            return f"Bitcoin: ${crypto_data.get('usd', 'N/A'):,.2f}"
    
    elif "sentiment" in query_lower or "news" in query_lower:
        news = await engine.sentiment_analyzer.get_financial_news()
        sentiment = await engine.sentiment_analyzer.analyze_news_sentiment(news)
        return f"Financial News Sentiment: {sentiment['sentiment']} (Score: {sentiment['score']:.2f})"
    
    return "I can help with stock prices, crypto data, sentiment analysis, and market overviews. Try asking about a specific stock or market conditions."

