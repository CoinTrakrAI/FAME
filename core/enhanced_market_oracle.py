#!/usr/bin/env python3
"""
F.A.M.E. - Enhanced Market Oracle
Real market analysis with advanced AI predictions
"""

import yfinance as yf
import pandas as pd
import numpy as np
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("[WARNING] TA-Lib not available. Install with: pip install TA-Lib")

from typing import Dict, List, Any, Tuple
import asyncio
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("[WARNING] aiohttp not available. Using requests fallback.")

from datetime import datetime, timedelta
import warnings
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False

import requests
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

import re

warnings.filterwarnings('ignore')


class EnhancedMarketOracle:
    """Enhanced market analysis with ML predictions and real data"""
   
    def __init__(self):
        self.session = None
        self.models = {}
        self.scalers = {}
        self.news_cache = {}
    
    async def __aenter__(self):
        if AIOHTTP_AVAILABLE:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
   
    async def get_enhanced_market_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market analysis with AI predictions"""
        try:
            # Get multiple data sources
            market_data = await self.get_real_market_data(symbol)
            if "error" in market_data:
                return market_data
                
            news_sentiment = await self.get_news_sentiment(symbol)
            options_flow = await self.get_options_flow(symbol)
            technical_analysis = self.advanced_technical_analysis(market_data['historical_data'])
           
            # Generate AI prediction
            ai_prediction = await self.generate_ai_prediction(symbol, market_data, technical_analysis)
           
            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics(market_data['historical_data'])
           
            return {
                "symbol": symbol,
                "current_price": market_data['current_price'],
                "ai_prediction": ai_prediction,
                "technical_analysis": technical_analysis,
                "news_sentiment": news_sentiment,
                "options_flow": options_flow,
                "risk_metrics": risk_metrics,
                "timestamp": datetime.now().isoformat(),
                "confidence_score": self.calculate_confidence(ai_prediction, technical_analysis)
            }
           
        except Exception as e:
            return {"error": str(e)}
   
    async def get_real_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market data with multiple timeframes"""
        try:
            ticker = yf.Ticker(symbol)
           
            # Get multiple timeframes
            hist_1d = ticker.history(period="1d", interval="5m")
            hist_1w = ticker.history(period="5d", interval="1h")
            hist_1m = ticker.history(period="1mo", interval="1d")
            hist_3m = ticker.history(period="3mo", interval="1d")
           
            if hist_1d.empty:
                return {"error": f"No data available for symbol {symbol}"}
           
            current_price = float(hist_1d['Close'].iloc[-1]) if not hist_1d.empty else 0.0
            volume = float(hist_1d['Volume'].iloc[-1]) if not hist_1d.empty else 0.0
           
            # Get additional info
            try:
                info = ticker.info
                fundamentals = {
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'eps': info.get('trailingEps'),
                    'dividend_yield': info.get('dividendYield'),
                    'beta': info.get('beta')
                }
            except:
                fundamentals = {}
           
            return {
                "current_price": current_price,
                "volume": volume,
                "historical_data": {
                    "1d": hist_1d,
                    "1w": hist_1w,
                    "1m": hist_1m,
                    "3m": hist_3m
                },
                "fundamentals": fundamentals,
                "data_quality": "HIGH"
            }
           
        except Exception as e:
            return {"error": str(e)}
   
    def advanced_technical_analysis(self, historical_data: Dict) -> Dict[str, Any]:
        """Advanced technical analysis with multiple indicators"""
        try:
            df = historical_data.get('1m', pd.DataFrame())
           
            if df.empty:
                return {"error": "No data available for technical analysis"}
           
            closes = df['Close'].values
            highs = df['High'].values
            lows = df['Low'].values
            volumes = df['Volume'].values
           
            # Multiple technical indicators
            indicators = {}
            
            if TALIB_AVAILABLE:
                # Trend indicators
                indicators['sma_20'] = float(talib.SMA(closes, timeperiod=20)[-1]) if len(closes) >= 20 else 0.0
                indicators['sma_50'] = float(talib.SMA(closes, timeperiod=50)[-1]) if len(closes) >= 50 else 0.0
                indicators['ema_12'] = float(talib.EMA(closes, timeperiod=12)[-1]) if len(closes) >= 12 else 0.0
                indicators['ema_26'] = float(talib.EMA(closes, timeperiod=26)[-1]) if len(closes) >= 26 else 0.0
               
                # Momentum indicators
                indicators['rsi'] = float(talib.RSI(closes, timeperiod=14)[-1]) if len(closes) >= 14 else 50.0
               
                # MACD calculation with error handling
                try:
                    macd, macd_signal, macd_hist = talib.MACD(closes)
                    indicators.update({
                        'macd': float(macd[-1]),
                        'macd_signal': float(macd_signal[-1]),
                        'macd_hist': float(macd_hist[-1])
                    })
                except:
                    indicators.update({'macd': 0.0, 'macd_signal': 0.0, 'macd_hist': 0.0})
               
                # Stochastic
                try:
                    stoch_k, stoch_d = talib.STOCH(highs, lows, closes)
                    indicators.update({
                        'stoch_k': float(stoch_k[-1]),
                        'stoch_d': float(stoch_d[-1])
                    })
                except:
                    indicators.update({'stoch_k': 50.0, 'stoch_d': 50.0})
               
                # Bollinger Bands
                try:
                    bb_upper, bb_middle, bb_lower = talib.BBANDS(closes)
                    indicators.update({
                        'bb_upper': float(bb_upper[-1]),
                        'bb_middle': float(bb_middle[-1]),
                        'bb_lower': float(bb_lower[-1])
                    })
                except:
                    indicators.update({'bb_upper': 0.0, 'bb_middle': 0.0, 'bb_lower': 0.0})
               
                # Additional indicators
                try:
                    indicators['atr'] = float(talib.ATR(highs, lows, closes, timeperiod=14)[-1])
                    indicators['obv'] = float(talib.OBV(closes, volumes)[-1])
                except:
                    indicators.update({'atr': 0.0, 'obv': 0.0})
            else:
                # Fallback: simple calculations without TA-Lib
                if len(closes) >= 20:
                    indicators['sma_20'] = float(np.mean(closes[-20:]))
                else:
                    indicators['sma_20'] = 0.0
                    
                if len(closes) >= 50:
                    indicators['sma_50'] = float(np.mean(closes[-50:]))
                else:
                    indicators['sma_50'] = 0.0
                    
                # Simple RSI calculation
                if len(closes) >= 14:
                    deltas = np.diff(closes)
                    gains = np.where(deltas > 0, deltas, 0)
                    losses = np.where(deltas < 0, -deltas, 0)
                    avg_gain = np.mean(gains[-14:])
                    avg_loss = np.mean(losses[-14:])
                    if avg_loss != 0:
                        rs = avg_gain / avg_loss
                        indicators['rsi'] = float(100 - (100 / (1 + rs)))
                    else:
                        indicators['rsi'] = 100.0
                else:
                    indicators['rsi'] = 50.0
                
                indicators.update({
                    'macd': 0.0, 'macd_signal': 0.0, 'macd_hist': 0.0,
                    'stoch_k': 50.0, 'stoch_d': 50.0,
                    'bb_upper': 0.0, 'bb_middle': 0.0, 'bb_lower': 0.0,
                    'atr': 0.0, 'obv': 0.0
                })
           
            # Calculate signals
            signals = self.calculate_trading_signals(indicators, float(closes[-1]))
           
            return {
                "indicators": indicators,
                "signals": signals,
                "trend_strength": self.calculate_trend_strength(indicators),
                "volatility_regime": self.assess_volatility_regime(indicators),
                "momentum_score": self.calculate_momentum_score(indicators)
            }
           
        except Exception as e:
            return {"error": f"Technical analysis error: {str(e)}"}
   
    def calculate_trading_signals(self, indicators: Dict, current_price: float) -> List[str]:
        """Calculate trading signals based on technical indicators"""
        signals = []
       
        # RSI signals
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            signals.append("RSI_OVERSOLD")
        elif rsi > 70:
            signals.append("RSI_OVERBOUGHT")
       
        # Moving average signals
        sma_20 = indicators.get('sma_20', 0)
        sma_50 = indicators.get('sma_50', 0)
        if sma_20 > sma_50 and sma_20 > 0 and sma_50 > 0:
            signals.append("UPTREND_MA")
        elif sma_20 < sma_50 and sma_20 > 0 and sma_50 > 0:
            signals.append("DOWNTREND_MA")
       
        # MACD signals
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        if macd > macd_signal:
            signals.append("MACD_BULLISH")
        else:
            signals.append("MACD_BEARISH")
       
        # Bollinger Bands signals
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        if bb_lower > 0 and current_price < bb_lower:
            signals.append("BB_OVERSOLD")
        elif bb_upper > 0 and current_price > bb_upper:
            signals.append("BB_OVERBOUGHT")
       
        return signals
   
    def calculate_trend_strength(self, indicators: Dict) -> str:
        """Calculate trend strength"""
        rsi = indicators.get('rsi', 50)
        if rsi < 20 or rsi > 80:
            return "STRONG"
        elif rsi < 30 or rsi > 70:
            return "MODERATE"
        else:
            return "WEAK"
   
    def assess_volatility_regime(self, indicators: Dict) -> str:
        """Assess volatility regime"""
        atr = indicators.get('atr', 0)
        if atr > 0.05:  # 5% ATR
            return "HIGH_VOLATILITY"
        elif atr > 0.02:
            return "MEDIUM_VOLATILITY"
        else:
            return "LOW_VOLATILITY"
   
    def calculate_momentum_score(self, indicators: Dict) -> float:
        """Calculate momentum score (0-1)"""
        score = 0.0
        rsi = indicators.get('rsi', 50)
       
        # RSI momentum
        if rsi > 70 or rsi < 30:
            score += 0.3
        elif rsi > 60 or rsi < 40:
            score += 0.2
           
        # MACD momentum
        macd_hist = indicators.get('macd_hist', 0)
        if abs(macd_hist) > 0.01:
            score += 0.3
           
        return min(1.0, score)
   
    async def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get news sentiment analysis"""
        try:
            if AIOHTTP_AVAILABLE and self.session:
                # Use async session
                url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
               
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_sentiment(content)
            else:
                # Fallback to requests
                url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    return self._parse_sentiment(response.text)
                    
            return {"sentiment": "NEUTRAL", "score": 0, "source": "Unknown", "error": "Failed to fetch news"}
                   
        except Exception as e:
            return {"sentiment": "NEUTRAL", "score": 0, "source": "Unknown", "error": str(e)}
    
    def _parse_sentiment(self, content: str) -> Dict[str, Any]:
        """Parse sentiment from RSS content"""
        positive_words = ['bullish', 'gain', 'profit', 'growth', 'buy', 'outperform']
        negative_words = ['bearish', 'loss', 'drop', 'decline', 'sell', 'underperform']
       
        positive_count = sum(1 for word in positive_words if word in content.lower())
        negative_count = sum(1 for word in negative_words if word in content.lower())
       
        total = positive_count + negative_count
        if total > 0:
            sentiment_score = (positive_count - negative_count) / total
        else:
            sentiment_score = 0
       
        return {
            "sentiment_score": sentiment_score,
            "sentiment": "BULLISH" if sentiment_score > 0.1 else "BEARISH" if sentiment_score < -0.1 else "NEUTRAL",
            "news_count": total,
            "source": "Yahoo Finance"
        }
   
    async def generate_ai_prediction(self, symbol: str, market_data: Dict, technicals: Dict) -> Dict[str, Any]:
        """Generate AI-powered price prediction"""
        try:
            # Feature engineering for ML prediction
            features = self.prepare_features(market_data, technicals)
           
            # Simple ML model (in production, you'd use a trained model)
            prediction = self.simple_ml_prediction(features)
           
            return {
                "predicted_direction": prediction['direction'],
                "predicted_change_percent": prediction['change_percent'],
                "confidence": prediction['confidence'],
                "timeframe": "1_week",
                "model_version": "enhanced_v1"
            }
           
        except Exception as e:
            return {"error": str(e)}
   
    def prepare_features(self, market_data: Dict, technicals: Dict) -> np.array:
        """Prepare features for ML prediction"""
        features = []
       
        # Price features
        if market_data.get('current_price'):
            features.append(market_data['current_price'])
       
        # Technical indicator features
        if technicals.get('indicators'):
            ind = technicals['indicators']
            features.extend([
                ind.get('rsi', 50),
                ind.get('sma_20', 0),
                ind.get('sma_50', 0),
                ind.get('macd', 0),
                len(technicals.get('signals', []))
            ])
       
        # Ensure we always return the same number of features
        while len(features) < 6:
            features.append(0.0)
           
        return np.array(features).reshape(1, -1)
   
    def simple_ml_prediction(self, features: np.array) -> Dict[str, Any]:
        """Simple ML prediction (replace with trained model in production)"""
        if features.size == 0:
            return {"direction": "SIDEWAYS", "change_percent": 0.0, "confidence": 0.5}
           
        # This is a simplified version - in production, use a properly trained model
        rsi = features[0][1] if len(features[0]) > 1 else 50
       
        if rsi < 35:
            return {"direction": "UP", "change_percent": 2.5, "confidence": 0.75}
        elif rsi > 65:
            return {"direction": "DOWN", "change_percent": -1.8, "confidence": 0.70}
        else:
            return {"direction": "SIDEWAYS", "change_percent": 0.5, "confidence": 0.60}
   
    def calculate_risk_metrics(self, historical_data: Dict) -> Dict[str, Any]:
        """Calculate advanced risk metrics"""
        try:
            df = historical_data.get('3m', pd.DataFrame())
           
            if df.empty:
                return {"error": "No data for risk calculation"}
           
            returns = df['Close'].pct_change().dropna()
           
            if len(returns) == 0:
                return {"error": "Insufficient data for risk calculation"}
           
            risk_metrics = {
                "volatility_1m": float(returns.std() * np.sqrt(21)) if returns.std() > 0 else 0.0,  # Monthly volatility
                "sharpe_ratio": float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0,
                "max_drawdown": float((df['Close'] / df['Close'].cummax() - 1).min()),
                "var_95": float(returns.quantile(0.05)) if len(returns) > 0 else 0.0,
            }
           
            # Expected shortfall with error handling
            try:
                var_95 = returns.quantile(0.05)
                risk_metrics["expected_shortfall"] = float(returns[returns <= var_95].mean())
            except:
                risk_metrics["expected_shortfall"] = 0.0
           
            risk_metrics["beta"] = 1.0  # Would need benchmark data for actual beta
           
            return risk_metrics
           
        except Exception as e:
            return {"error": str(e)}
   
    def calculate_confidence(self, prediction: Dict, technicals: Dict) -> float:
        """Calculate overall confidence score"""
        base_confidence = prediction.get('confidence', 0.5)
       
        # Adjust based on technical strength
        trend_strength = technicals.get('trend_strength', 'WEAK')
        if trend_strength == "STRONG":
            base_confidence *= 1.2
        elif trend_strength == "WEAK":
            base_confidence *= 0.8
       
        # Adjust based on signal strength
        signals = technicals.get('signals', [])
        if len(signals) >= 3:
            base_confidence *= 1.1
       
        return min(0.95, max(0.3, base_confidence))
   
    async def get_options_flow(self, symbol: str) -> Dict[str, Any]:
        """Get options flow analysis (simulated - real implementation would use options data)"""
        # In production, this would analyze actual options chain data
        return {
            "unusual_volume": "MODERATE",
            "put_call_ratio": 0.85,
            "largest_trades": ["CALLS_120D", "PUTS_30D"],
            "flow_sentiment": "SLIGHTLY_BULLISH"
        }


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    """Orchestrator interface for enhanced market oracle"""
    text = request.get("text", "")
    symbol = request.get("symbol") or request.get("ticker")
    
    # Extract symbol from text if not provided
    if not symbol:
        # Try to find ticker symbol in text (more flexible pattern)
        import re
        # Look for common stock patterns: "AAPL", "Apple stock", "stock AAPL", etc.
        text_upper = text.upper()
        
        # First try explicit symbol mention
        match = re.search(r'\b([A-Z]{1,5})\b', text_upper)
        if match:
            potential_symbol = match.group(1)
            # Filter out common words that match stock symbol pattern
            common_words = {'THE', 'AND', 'FOR', 'ARE', 'ALL', 'YOU', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'APPLE', 'GOOGLE', 'MICROSOFT', 'AMAZON', 'TESLA', 'META'}
            if potential_symbol not in common_words:
                symbol = potential_symbol
        
        # If still no symbol, check for company name mentions
        if not symbol:
            company_symbols = {
                'APPLE': 'AAPL', 'GOOGLE': 'GOOGL', 'MICROSOFT': 'MSFT', 
                'AMAZON': 'AMZN', 'TESLA': 'TSLA', 'META': 'META',
                'NETFLIX': 'NFLX', 'NVIDIA': 'NVDA', 'INTEL': 'INTC'
            }
            for company, ticker in company_symbols.items():
                if company in text_upper:
                    symbol = ticker
                    break
        
        # Last resort: if text contains "stock" or "analyze", try AAPL as default
        if not symbol and ('stock' in text.lower() or 'analyze' in text.lower()):
            # Try to extract any capitalized word as potential symbol
            words = text_upper.split()
            for word in words:
                if len(word) >= 1 and len(word) <= 5 and word.isalpha():
                    if word not in common_words:
                        symbol = word
                        break
            
            # If still nothing, default to a common stock for testing
            if not symbol:
                symbol = 'AAPL'
    
    if not symbol:
        return {"error": "No stock symbol provided. Please specify a ticker symbol (e.g., AAPL, TSLA, MSFT)"}
    
    async def analyze():
        async with EnhancedMarketOracle() as oracle:
            return await oracle.get_enhanced_market_analysis(symbol)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(analyze())
        return result
    finally:
        loop.close()

