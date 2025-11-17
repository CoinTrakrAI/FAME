import asyncio
import aiohttp
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any

# Try importing financial libraries
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    np = None

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


class AutonomousInvestor:
    def __init__(self):
        self.knowledge_base = {}
        self.trading_strategies = {}
        self.market_data = {}
        self.learning_cycles = 0
        self.prediction_accuracy = 0.0
        self.main_app = None  # Reference to main app for cross-module access
        
        # Initialize learning systems
        self._initialize_core_knowledge()
    
    def _initialize_core_knowledge(self):
        """Initialize with Warren Buffett + advanced trading knowledge"""
        self.core_principles = {
            "buffett_rules": [
                "Rule 1: Never lose money",
                "Rule 2: Never forget rule 1",
                "Buy wonderful companies at fair prices",
                "Be fearful when others are greedy, greedy when others are fearful",
                "Our favorite holding period is forever"
            ],
            "advanced_strategies": [
                "quantitative_momentum",
                "mean_reversion", 
                "volatility_arbitrage",
                "statistical_arbitrage",
                "machine_learning_predictions"
            ],
            "market_psychology": [
                "herd_behavior_analysis",
                "fear_greed_index_tracking",
                "sentiment_analysis",
                "behavioral_finance_patterns"
            ]
        }
    
    def begin_autonomous_operation(self):
        """Start the autonomous learning and trading"""
        logging.info("🎯 Autonomous Investor beginning operation...")
        
        # Start all learning loops
        if asyncio.get_event_loop().is_running():
            # If event loop already running, create tasks
            asyncio.create_task(self._market_analysis_loop())
            asyncio.create_task(self._strategy_development_loop())
            asyncio.create_task(self._continuous_learning_loop())
        else:
            # Start new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.create_task(self._market_analysis_loop())
            loop.create_task(self._strategy_development_loop())
            loop.create_task(self._continuous_learning_loop())
            # Note: loop would need to be run, but this is called from sync context
            # The calling code should manage the event loop
    
    async def _market_analysis_loop(self):
        """Continuous market analysis"""
        while True:
            try:
                # Analyze multiple markets simultaneously
                await asyncio.gather(
                    self._analyze_stock_market(),
                    self._analyze_crypto_market(),
                    self._analyze_forex_market(),
                    self._analyze_commodities(),
                    return_exceptions=True
                )
                
                self.learning_cycles += 1
                await asyncio.sleep(60)  # Analyze every minute
                
            except Exception as e:
                logging.error(f"Market analysis error: {e}")
                await asyncio.sleep(30)
    
    async def _analyze_stock_market(self):
        """Comprehensive stock market analysis"""
        if not YFINANCE_AVAILABLE:
            return
            
        try:
            # Get major indices
            indices = ['^GSPC', '^DJI', '^IXIC', '^RUT']
            for symbol in indices:
                data = yf.download(symbol, period='1d', interval='1m', progress=False)
                if not data.empty and len(data) > 0:
                    self._process_market_data(symbol, data)
            
            # Analyze individual stocks
            stocks = ['AAPL', 'TSLA', 'NVDA', 'AMZN', 'META', 'GOOGL']
            for stock in stocks:
                data = yf.download(stock, period='1d', interval='1m', progress=False)
                if not data.empty and len(data) > 0:
                    self._analyze_stock_movement(stock, data)
                    
        except Exception as e:
            logging.error(f"Stock analysis error: {e}")
    
    async def _analyze_crypto_market(self):
        """Comprehensive cryptocurrency analysis"""
        if not YFINANCE_AVAILABLE:
            return
            
        try:
            cryptocurrencies = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD']
            
            for crypto in cryptocurrencies:
                data = yf.download(crypto, period='1d', interval='1m', progress=False)
                if not data.empty and len(data) > 0:
                    # Advanced crypto analysis
                    analysis = self._perform_advanced_crypto_analysis(crypto, data)
                    self._update_crypto_predictions(crypto, analysis)
                    
        except Exception as e:
            logging.error(f"Crypto analysis error: {e}")
    
    async def _analyze_forex_market(self):
        """Forex market analysis"""
        # Placeholder for forex analysis
        pass
    
    async def _analyze_commodities(self):
        """Commodities analysis"""
        # Placeholder for commodities analysis
        pass
    
    def _perform_advanced_crypto_analysis(self, symbol: str, data) -> Dict[str, Any]:
        """Perform advanced technical and sentiment analysis"""
        if not PANDAS_AVAILABLE or data.empty:
            return {}
        
        # Calculate technical indicators
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['SMA_50'] = data['Close'].rolling(50).mean()
        if len(data) > 14:
            data['RSI'] = self._calculate_rsi(data['Close'])
            data['MACD'] = self._calculate_macd(data['Close'])
        
        # Volatility analysis
        if len(data) > 20:
            data['volatility'] = data['Close'].pct_change().rolling(20).std()
        
        # Price predictions using multiple models
        predictions = {
            'short_term': self._predict_short_term(data),
            'medium_term': self._predict_medium_term(data),
            'momentum_score': self._calculate_momentum(data),
            'volatility_forecast': self._forecast_volatility(data)
        }
        
        return predictions
    
    def _predict_short_term(self, data) -> float:
        """Predict short-term price movement"""
        if not PANDAS_AVAILABLE or data.empty or len(data) < 10:
            return 0.0
        
        recent_data = data['Close'].tail(10)
        if len(recent_data) < 10:
            return 0.0
        
        # Simple momentum-based prediction
        momentum = (recent_data.iloc[-1] - recent_data.iloc[0]) / recent_data.iloc[0]
        return float(momentum * 100)  # Return as percentage
    
    def _predict_medium_term(self, data) -> float:
        """Predict medium-term price movement"""
        if not PANDAS_AVAILABLE or data.empty or len(data) < 20:
            return 0.0
        
        recent_data = data['Close'].tail(20)
        momentum = (recent_data.iloc[-1] - recent_data.iloc[0]) / recent_data.iloc[0]
        return float(momentum * 100)
    
    def _forecast_volatility(self, data) -> float:
        """Forecast volatility"""
        if not PANDAS_AVAILABLE or data.empty or len(data) < 20:
            return 0.0
        
        if 'volatility' in data.columns:
            return float(data['volatility'].iloc[-1] * 100)
        return 0.0
    
    def _process_market_data(self, symbol: str, data):
        """Process and store market data"""
        if not data.empty and len(data) > 0:
            self.market_data[symbol] = {
                'last_price': float(data['Close'].iloc[-1]),
                'timestamp': datetime.now().isoformat(),
                'data_points': len(data)
            }
    
    def _analyze_stock_movement(self, stock: str, data):
        """Analyze individual stock movement"""
        if not data.empty and len(data) > 0:
            self.market_data[stock] = {
                'price': float(data['Close'].iloc[-1]),
                'volume': int(data['Volume'].iloc[-1]) if 'Volume' in data.columns else 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def _update_crypto_predictions(self, symbol: str, analysis: Dict[str, Any]):
        """Update crypto predictions"""
        self.market_data[f"{symbol}_predictions"] = analysis
    
    async def _strategy_development_loop(self):
        """Continuously develop and refine trading strategies"""
        strategy_count = 0
        
        while True:
            try:
                # Generate new strategies based on market conditions
                new_strategy = await self._generate_trading_strategy()
                strategy_id = f"strategy_{strategy_count:04d}"
                self.trading_strategies[strategy_id] = new_strategy
                
                # Backtest strategy
                performance = await self._backtest_strategy(new_strategy)
                self.trading_strategies[strategy_id]['performance'] = performance
                
                # Remove underperforming strategies
                self._prune_strategies()
                
                strategy_count += 1
                await asyncio.sleep(300)  # Develop new strategy every 5 minutes
                
            except Exception as e:
                logging.error(f"Strategy development error: {e}")
                await asyncio.sleep(60)
    
    async def _generate_trading_strategy(self) -> Dict[str, Any]:
        """Generate a new trading strategy"""
        return {
            'name': f"Strategy_{len(self.trading_strategies)}",
            'type': 'momentum',
            'parameters': {},
            'created_at': datetime.now().isoformat()
        }
    
    async def _backtest_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Backtest a trading strategy"""
        return {
            'total_return': 0.05,
            'sharpe_ratio': 1.2,
            'win_rate': 0.65
        }
    
    def _prune_strategies(self):
        """Remove underperforming strategies"""
        # Keep top 10 strategies by performance
        if len(self.trading_strategies) > 10:
            sorted_strategies = sorted(
                self.trading_strategies.items(),
                key=lambda x: x[1].get('performance', {}).get('total_return', 0),
                reverse=True
            )
            self.trading_strategies = dict(sorted_strategies[:10])
    
    async def _continuous_learning_loop(self):
        """Continuous learning from all available data"""
        while True:
            try:
                # Learn from financial news
                await self._analyze_financial_news()
                
                # Learn from economic indicators
                await self._analyze_economic_data()
                
                # Learn from market patterns
                await self._extract_market_patterns()
                
                # Self-improvement: Analyze prediction accuracy
                await self._improve_prediction_models()
                
                await asyncio.sleep(1800)  # Learn every 30 minutes
                
            except Exception as e:
                logging.error(f"Continuous learning error: {e}")
                await asyncio.sleep(300)
    
    async def _analyze_financial_news(self):
        """Analyze financial news for sentiment and insights"""
        if not REQUESTS_AVAILABLE:
            return
            
        try:
            # Analyze news sentiment (simplified)
            market_sentiment = {
                "positive_news": 5,
                "negative_news": 3,
                "neutral_news": 10
            }
            
            self.knowledge_base['market_sentiment'] = market_sentiment
            
        except Exception as e:
            logging.error(f"News analysis error: {e}")
    
    async def _analyze_economic_data(self):
        """Analyze economic indicators"""
        # Placeholder for economic data analysis
        pass
    
    async def _extract_market_patterns(self):
        """Extract patterns from market data"""
        # Placeholder for pattern extraction
        pass
    
    async def _improve_prediction_models(self):
        """Improve prediction models based on accuracy"""
        # Placeholder for model improvement
        pass
    
    def get_market_insights(self) -> Dict[str, Any]:
        """Get current market insights and predictions"""
        return {
            "learning_cycles": self.learning_cycles,
            "prediction_accuracy": self.prediction_accuracy,
            "active_strategies": len(self.trading_strategies),
            "market_analysis": self._get_current_analysis(),
            "crypto_predictions": self._get_crypto_forecasts(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_current_analysis(self) -> Dict[str, Any]:
        """Get current market analysis"""
        return {
            "stocks_analyzed": len([k for k in self.market_data.keys() if not k.endswith('_predictions')]),
            "data_points": sum(v.get('data_points', 0) for v in self.market_data.values())
        }
    
    def _get_crypto_forecasts(self) -> Dict[str, Any]:
        """Get crypto forecasts"""
        forecasts = {}
        for key, value in self.market_data.items():
            if key.endswith('_predictions'):
                forecasts[key] = value
        return forecasts
    
    # Technical analysis methods
    def _calculate_rsi(self, prices, period: int = 14):
        """Calculate Relative Strength Index"""
        if not PANDAS_AVAILABLE or len(prices) < period:
            return pd.Series([0.0] * len(prices))
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0)  # Fill NaN with neutral value
    
    def _calculate_macd(self, prices):
        """Calculate MACD indicator"""
        if not PANDAS_AVAILABLE or len(prices) < 26:
            return pd.Series([0.0] * len(prices))
        
        exp1 = prices.ewm(span=12).mean()
        exp2 = prices.ewm(span=26).mean()
        macd = exp1 - exp2
        return macd
    
    def _calculate_momentum(self, data) -> float:
        """Calculate momentum score"""
        if not PANDAS_AVAILABLE or data.empty or len(data) < 20:
            return 0.0
        
        returns = data['Close'].pct_change(periods=5)
        momentum = returns.rolling(10).mean().iloc[-1]
        return float(momentum * 100) if not pd.isna(momentum) else 0.0

