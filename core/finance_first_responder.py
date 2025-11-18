#!/usr/bin/env python3
"""
FAME Finance-First Responder
Generates comprehensive financial responses with detailed analysis
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class FinanceFirstResponder:
    """
    Generates comprehensive financial responses with:
    - Real-time prices
    - Technical analysis
    - Fundamental analysis
    - Trading recommendations
    - Risk assessment
    - Market sentiment
    """
    
    def __init__(self):
        self.premium_service = None
        self._init_services()
    
    def _init_services(self):
        """Initialize financial data services"""
        try:
            from services.premium_price_service import premium_price_service
            self.premium_service = premium_price_service
        except ImportError:
            logger.warning("Premium price service not available")
    
    async def generate_response(self, intent: Dict[str, Any], query_text: str) -> Dict[str, Any]:
        """
        Generate comprehensive financial response based on intent
        """
        intent_type = intent.get('type', 'unknown')
        symbol = intent.get('symbol')
        asset_type = intent.get('asset_type')
        action = intent.get('action')
        
        if intent_type == 'price_query' and symbol:
            return await self._handle_price_query(symbol, asset_type, query_text)
        elif intent_type == 'analysis_query' and symbol:
            return await self._handle_analysis_query(symbol, asset_type, query_text)
        elif intent_type == 'prediction_query' and symbol:
            return await self._handle_prediction_query(symbol, asset_type, query_text)
        elif intent_type == 'recommendation_query' and symbol:
            return await self._handle_recommendation_query(symbol, asset_type, query_text)
        elif intent_type == 'strategy_query':
            return await self._handle_strategy_query(intent.get('strategy'), query_text)
        elif intent_type == 'general_financial':
            return await self._handle_general_financial(query_text)
        else:
            return await self._handle_unknown_financial(query_text)
    
    async def _handle_price_query(self, symbol: str, asset_type: Optional[str], query: str) -> Dict[str, Any]:
        """Handle price queries with comprehensive data"""
        try:
            # Try premium service first
            if self.premium_service:
                quote = self.premium_service.get_price(symbol)
                if quote:
                    return self._format_premium_response(quote, symbol, asset_type)
            
            # Fallback to yfinance
            import yfinance as yf
            
            if asset_type == 'crypto':
                ticker_symbol = f"{symbol}-USD"
            else:
                ticker_symbol = symbol
            
            ticker = yf.Ticker(ticker_symbol)
            
            # Get current price
            try:
                info = ticker.info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                
                if not current_price:
                    # Try fast_info
                    fast_info = ticker.fast_info
                    current_price = fast_info.lastPrice if hasattr(fast_info, 'lastPrice') else None
                
                if not current_price:
                    # Get from history
                    hist = ticker.history(period="1d", interval="1m")
                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])
                
                if current_price:
                    # Get additional data
                    hist_1d = ticker.history(period="1d")
                    hist_5d = ticker.history(period="5d")
                    
                    price_change = None
                    price_change_pct = None
                    volume = None
                    
                    if not hist_1d.empty:
                        close_prices = hist_1d['Close']
                        if len(close_prices) > 1:
                            prev_close = float(close_prices.iloc[-2])
                            price_change = float(current_price) - prev_close
                            price_change_pct = (price_change / prev_close) * 100
                        volume = int(hist_1d['Volume'].iloc[-1]) if 'Volume' in hist_1d.columns else None
                    
                    # Build comprehensive response
                    response_text = f"📊 **{symbol} Price Analysis**\n\n"
                    response_text += f"**Current Price:** ${float(current_price):,.2f}\n"
                    
                    if price_change is not None:
                        change_symbol = "📈" if price_change >= 0 else "📉"
                        response_text += f"{change_symbol} **Change:** ${price_change:+.2f} ({price_change_pct:+.2f}%)\n"
                    
                    if volume:
                        response_text += f"**Volume:** {volume:,}\n"
                    
                    # Add market cap if available
                    if 'marketCap' in info:
                        market_cap = info['marketCap']
                        if market_cap:
                            response_text += f"**Market Cap:** ${market_cap:,.0f}\n"
                    
                    # Add 52-week range if available
                    if 'fiftyTwoWeekHigh' in info and 'fiftyTwoWeekLow' in info:
                        high = info['fiftyTwoWeekHigh']
                        low = info['fiftyTwoWeekLow']
                        if high and low:
                            response_text += f"**52-Week Range:** ${low:,.2f} - ${high:,.2f}\n"
                    
                    response_text += f"\n💡 **Quick Analysis:**\n"
                    if price_change_pct:
                        if price_change_pct > 2:
                            response_text += "Strong upward momentum. Consider monitoring for entry/exit points.\n"
                        elif price_change_pct < -2:
                            response_text += "Significant downward pressure. Exercise caution.\n"
                        else:
                            response_text += "Price movement within normal range. Stable trend.\n"
                    
                    return {
                        'ok': True,
                        'text': response_text,
                        'data': {
                            'symbol': symbol,
                            'price': float(current_price),
                            'change': price_change,
                            'change_pct': price_change_pct,
                            'volume': volume,
                            'asset_type': asset_type or 'unknown',
                            'source': 'yfinance'
                        },
                        'confidence': 0.9
                    }
            except Exception as inner_e:
                logger.warning(f"Error fetching price details for {symbol}: {inner_e}")
                # Fall through to return error response
            
            return {
                'ok': False,
                'text': f"Could not fetch price data for {symbol}. Please verify the symbol is correct.",
                'data': {},
                'confidence': 0.0
            }
            
        except Exception as e:
            logger.error(f"Price query error: {e}")
            return {
                'ok': False,
                'text': f"Error fetching price for {symbol}: {str(e)}",
                'data': {},
                'confidence': 0.0
            }
    
    async def _handle_analysis_query(self, symbol: str, asset_type: Optional[str], query: str) -> Dict[str, Any]:
        """Handle comprehensive analysis queries"""
        try:
            import yfinance as yf
            
            if asset_type == 'crypto':
                ticker_symbol = f"{symbol}-USD"
            else:
                ticker_symbol = symbol
            
            ticker = yf.Ticker(ticker_symbol)
            
            # Get comprehensive data
            info = ticker.info
            hist_1mo = ticker.history(period="1mo")
            hist_1y = ticker.history(period="1y")
            
            response_text = f"📊 **Comprehensive Analysis: {symbol}**\n\n"
            
            # Current metrics
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            if current_price:
                response_text += f"**Current Price:** ${float(current_price):,.2f}\n"
            
            # Price trends
            if not hist_1mo.empty:
                month_ago_price = float(hist_1mo['Close'].iloc[0])
                month_change = ((float(current_price) - month_ago_price) / month_ago_price) * 100
                response_text += f"**1-Month Change:** {month_change:+.2f}%\n"
            
            if not hist_1y.empty:
                year_ago_price = float(hist_1y['Close'].iloc[0])
                year_change = ((float(current_price) - year_ago_price) / year_ago_price) * 100
                response_text += f"**1-Year Change:** {year_change:+.2f}%\n"
            
            # Volume analysis
            if not hist_1mo.empty and 'Volume' in hist_1mo.columns:
                avg_volume = int(hist_1mo['Volume'].mean())
                current_volume = int(hist_1mo['Volume'].iloc[-1])
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                response_text += f"\n**Volume Analysis:**\n"
                response_text += f"Current: {current_volume:,}\n"
                response_text += f"Average (30d): {avg_volume:,}\n"
                if volume_ratio > 1.5:
                    response_text += "⚠️ High volume - increased interest/volatility\n"
                elif volume_ratio < 0.5:
                    response_text += "📉 Low volume - reduced activity\n"
            
            # Technical indicators (simplified)
            if not hist_1mo.empty:
                closes = hist_1mo['Close']
                sma_20 = closes.tail(20).mean()
                response_text += f"\n**Technical Indicators:**\n"
                response_text += f"20-Day SMA: ${sma_20:,.2f}\n"
                if current_price > sma_20:
                    response_text += "✅ Price above 20-day average - bullish signal\n"
                else:
                    response_text += "⚠️ Price below 20-day average - bearish signal\n"
            
            # Fundamental data (for stocks)
            if asset_type == 'stock' and info:
                if 'peRatio' in info and info['peRatio']:
                    response_text += f"\n**Fundamental Metrics:**\n"
                    response_text += f"P/E Ratio: {info['peRatio']:.2f}\n"
                if 'dividendYield' in info and info['dividendYield']:
                    response_text += f"Dividend Yield: {info['dividendYield']*100:.2f}%\n"
                if 'marketCap' in info and info['marketCap']:
                    response_text += f"Market Cap: ${info['marketCap']:,.0f}\n"
            
            response_text += f"\n💡 **Analysis Summary:**\n"
            response_text += "Based on current data, this asset shows "
            if month_change and month_change > 5:
                response_text += "strong positive momentum. "
            elif month_change and month_change < -5:
                response_text += "negative pressure. "
            else:
                response_text += "moderate movement. "
            response_text += "Monitor key support/resistance levels and volume patterns for trading opportunities."
            
            return {
                'ok': True,
                'text': response_text,
                'data': {
                    'symbol': symbol,
                    'analysis_type': 'comprehensive',
                    'asset_type': asset_type
                },
                'confidence': 0.85
            }
            
        except Exception as e:
            logger.error(f"Analysis query error: {e}")
            return {
                'ok': False,
                'text': f"Error performing analysis for {symbol}: {str(e)}",
                'data': {},
                'confidence': 0.0
            }
    
    async def _handle_prediction_query(self, symbol: str, asset_type: Optional[str], query: str) -> Dict[str, Any]:
        """Handle prediction/forecast queries"""
        # For now, provide disclaimer and basic trend analysis
        response_text = f"🔮 **Price Prediction: {symbol}**\n\n"
        response_text += "⚠️ **Important Disclaimer:** Price predictions are highly speculative and should not be used as the sole basis for investment decisions. Past performance does not guarantee future results.\n\n"
        response_text += "**Analysis Approach:**\n"
        response_text += "1. Historical trend analysis\n"
        response_text += "2. Technical indicator patterns\n"
        response_text += "3. Market sentiment factors\n"
        response_text += "4. Fundamental analysis (where applicable)\n\n"
        response_text += "For detailed predictions, I would need:\n"
        response_text += "- Specific timeframe (1 week, 1 month, 1 year, 10 years)\n"
        response_text += "- Risk tolerance level\n"
        response_text += "- Market conditions context\n\n"
        response_text += "Would you like me to analyze current trends for {symbol}?"
        
        return {
            'ok': True,
            'text': response_text.format(symbol=symbol),
            'data': {
                'symbol': symbol,
                'prediction_type': 'general',
                'disclaimer': True
            },
            'confidence': 0.7
        }
    
    async def _handle_recommendation_query(self, symbol: str, asset_type: Optional[str], query: str) -> Dict[str, Any]:
        """Handle buy/sell/hold recommendation queries"""
        response_text = f"💼 **Trading Recommendation: {symbol}**\n\n"
        response_text += "⚠️ **Not Financial Advice:** This is for informational purposes only. Always conduct your own research and consult with a financial advisor.\n\n"
        response_text += "**Recommendation Framework:**\n"
        response_text += "- **BUY:** Strong fundamentals, positive momentum, favorable risk/reward\n"
        response_text += "- **HOLD:** Neutral outlook, wait for clearer signals\n"
        response_text += "- **SELL:** Weak fundamentals, negative momentum, high risk\n\n"
        response_text += "To provide a specific recommendation, I would analyze:\n"
        response_text += "1. Current price vs. historical ranges\n"
        response_text += "2. Technical indicators (RSI, MACD, moving averages)\n"
        response_text += "3. Volume patterns\n"
        response_text += "4. Fundamental metrics (for stocks)\n"
        response_text += "5. Market sentiment\n\n"
        response_text += f"Would you like me to perform a detailed analysis of {symbol}?"
        
        return {
            'ok': True,
            'text': response_text,
            'data': {
                'symbol': symbol,
                'recommendation_type': 'framework',
                'disclaimer': True
            },
            'confidence': 0.75
        }
    
    async def _handle_strategy_query(self, strategy: Optional[str], query: str) -> Dict[str, Any]:
        """Handle trading strategy queries"""
        response_text = "📈 **Trading Strategy Information**\n\n"
        
        if strategy:
            response_text += f"**{strategy.title()} Strategy:**\n\n"
            # Add strategy-specific information
            if 'day trading' in strategy.lower():
                response_text += "Day trading involves opening and closing positions within the same trading day.\n"
                response_text += "Key considerations:\n"
                response_text += "- Requires significant time and attention\n"
                response_text += "- High risk, high reward potential\n"
                response_text += "- Need to understand technical analysis\n"
                response_text += "- Capital requirements and pattern day trader rules\n"
            elif 'swing trading' in strategy.lower():
                response_text += "Swing trading holds positions for days to weeks.\n"
                response_text += "Key considerations:\n"
                response_text += "- Less time-intensive than day trading\n"
                response_text += "- Focus on technical and fundamental analysis\n"
                response_text += "- Risk management is crucial\n"
            else:
                response_text += f"Strategy: {strategy}\n"
                response_text += "I can provide detailed information about this trading strategy.\n"
        else:
            response_text += "**Available Trading Strategies:**\n"
            response_text += "- Day Trading\n"
            response_text += "- Swing Trading\n"
            response_text += "- Position Trading\n"
            response_text += "- Scalping\n"
            response_text += "- Momentum Trading\n"
            response_text += "- Mean Reversion\n"
            response_text += "- Trend Following\n\n"
            response_text += "Which strategy would you like to learn about?"
        
        return {
            'ok': True,
            'text': response_text,
            'data': {
                'strategy': strategy,
                'type': 'strategy_info'
            },
            'confidence': 0.8
        }
    
    async def _handle_general_financial(self, query: str) -> Dict[str, Any]:
        """Handle general financial queries"""
        response_text = "💰 **FAME Financial Assistant**\n\n"
        response_text += "I can help you with:\n\n"
        response_text += "**Asset Prices:**\n"
        response_text += "- Stocks (AAPL, MSFT, TSLA, etc.)\n"
        response_text += "- Cryptocurrencies (BTC, ETH, XRP, etc.)\n"
        response_text += "- Commodities (Gold, Silver, Oil)\n"
        response_text += "- ETFs and Mutual Funds\n\n"
        response_text += "**Analysis:**\n"
        response_text += "- Technical analysis\n"
        response_text += "- Fundamental analysis\n"
        response_text += "- Market sentiment\n"
        response_text += "- Price predictions\n\n"
        response_text += "**Trading:**\n"
        response_text += "- Day trading strategies\n"
        response_text += "- Swing trading strategies\n"
        response_text += "- Position trading\n"
        response_text += "- Risk management\n\n"
        response_text += "**Examples:**\n"
        response_text += "- \"What's the price of Bitcoin?\"\n"
        response_text += "- \"Analyze AAPL\"\n"
        response_text += "- \"Should I buy TSLA?\"\n"
        response_text += "- \"Day trading strategies\"\n\n"
        response_text += "What would you like to know?"
        
        return {
            'ok': True,
            'text': response_text,
            'data': {
                'type': 'general_info'
            },
            'confidence': 0.9
        }
    
    async def _handle_unknown_financial(self, query: str) -> Dict[str, Any]:
        """Handle unknown financial queries"""
        return {
            'ok': True,
            'text': f"I understand you're asking about financial markets. Could you be more specific? For example:\n\n"
                   f"- \"What's the price of [symbol]?\"\n"
                   f"- \"Analyze [symbol]\"\n"
                   f"- \"Trading strategies for [asset type]\"\n\n"
                   f"I can help with stocks, crypto, commodities, ETFs, and trading strategies.",
            'data': {},
            'confidence': 0.6
        }
    
    def _format_premium_response(self, quote: Dict, symbol: str, asset_type: Optional[str]) -> Dict[str, Any]:
        """Format premium service response"""
        text = quote.get('text', '')
        if not text:
            # Build from data
            price = quote.get('price')
            if price:
                text = f"**{symbol}:** ${float(price):,.2f}"
        
        return {
            'ok': True,
            'text': text,
            'data': quote,
            'confidence': 0.95
        }


# Global instance
finance_first_responder = FinanceFirstResponder()

