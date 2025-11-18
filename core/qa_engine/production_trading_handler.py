#!/usr/bin/env python3
"""
FAME PRODUCTION Trading Question Handler
Integrates with real-time data, Decision Engine, and Portfolio context
Production-grade implementation with fallback to static handlers
"""

import logging
from typing import Dict, Any, Optional, List
import re
from datetime import datetime
import asyncio
import time

# Import FAME production engines
try:
    from core.investment_brain.decision_engine import get_investment_brain, FAMEInvestmentBrain
    from core.investment_brain.portfolio import load_portfolio_state
    from core.investment_brain.models import InvestmentContext, PortfolioState
    from core.investment_brain.data_aggregator import get_market_data_sync, get_market_data
    from core.enhanced_market_oracle import EnhancedMarketOracle
    from utils.market_data import get_crypto_price
    from services.trading_service import MarketDataService
    PRODUCTION_ENGINES_AVAILABLE = True
except ImportError as e:
    PRODUCTION_ENGINES_AVAILABLE = False
    logging.warning(f"Production engines not available: {e}")

# Import realtime enhancer
try:
    from .realtime_enhancer import (
        get_options_chain, get_risk_metrics, get_market_regime,
        get_real_time_price, extract_symbol, KNOWN_TICKERS
    )
    REALTIME_ENHANCER_AVAILABLE = True
except ImportError:
    REALTIME_ENHANCER_AVAILABLE = False

# Import degraded mode handler (Tier 2)
try:
    from .degraded_mode_handler import DegradedModeHandler
    from .cache_manager import get_cache_manager
    DEGRADED_MODE_AVAILABLE = True
except ImportError:
    DEGRADED_MODE_AVAILABLE = False
    logging.warning("Degraded mode handler not available")

logger = logging.getLogger(__name__)


class ProductionTradingHandler:
    """
    Production-grade trading question handler
    Integrates with FAME's real-time decision engine, data layer, and portfolio context
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize production engines
        if PRODUCTION_ENGINES_AVAILABLE:
            try:
                self.decision_engine = get_investment_brain()
                self.market_oracle = EnhancedMarketOracle()
                self.portfolio_state = load_portfolio_state()
                self.logger.info("Production engines initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize some production engines: {e}")
                self.decision_engine = None
                self.market_oracle = None
                self.portfolio_state = None
        else:
            self.decision_engine = None
            self.market_oracle = None
            self.portfolio_state = None
        
        # Initialize degraded mode handler (Tier 2)
        if DEGRADED_MODE_AVAILABLE:
            try:
                self.degraded_handler = DegradedModeHandler()
                self.cache_manager = get_cache_manager()
                self.logger.info("Degraded mode handler initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize degraded mode handler: {e}")
                self.degraded_handler = None
                self.cache_manager = None
        else:
            self.degraded_handler = None
            self.cache_manager = None
    
    async def handle_advanced_question(
        self, 
        text: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point with real-time data integration
        
        Args:
            text: Question text
            user_context: Optional user context (portfolio, risk_profile, session_id, etc.)
            
        Returns:
            Response dict with real-time analysis when available
        """
        try:
            text_lower = text.lower()
            user_context = user_context or {}
            
            # Load portfolio state if not provided
            if not user_context.get('portfolio') and self.portfolio_state:
                user_context['portfolio'] = self._portfolio_state_to_dict(self.portfolio_state)
            
            # Extract symbols and parameters
            symbols = await self._extract_symbols(text)
            
            # Route to appropriate real-time analyzer
            # Tier 1: Try real-time first
            try:
                if any(kw in text_lower for kw in ['option', 'iv', 'gamma', 'delta', 'iron condor', 'implied volatility']):
                    result = await self._handle_realtime_options(text, symbols, user_context)
                    if result and result.get('realtime'):
                        # Cache successful real-time result
                        self._cache_real_time_result('options', symbols[0] if symbols else None, result)
                        return result
                    # Fall through to Tier 2
                
                elif any(kw in text_lower for kw in ['var', 'value at risk', 'sharpe', 'sortino', 'risk metric', 'correlation']):
                    result = await self._handle_realtime_risk(text, symbols, user_context)
                    if result and result.get('realtime'):
                        self._cache_real_time_result('risk', None, result)
                        return result
                    # Fall through to Tier 2
                
                elif any(kw in text_lower for kw in ['kelly', 'position sizing', 'portfolio optimization', 'markowitz']):
                    result = await self._handle_realtime_portfolio(text, symbols, user_context)
                    if result and result.get('realtime'):
                        self._cache_real_time_result('portfolio', symbols[0] if symbols else None, result)
                        return result
                    # Fall through to Tier 2
                
                elif any(kw in text_lower for kw in ['invest', 'buy', 'sell', 'hold', 'analysis', 'recommendation']):
                    result = await self._handle_realtime_decision(text, symbols, user_context)
                    if result and result.get('realtime'):
                        self._cache_real_time_result('decision', symbols[0] if symbols else None, result)
                        return result
                    # Fall through to Tier 2
            except Exception as e:
                self.logger.warning(f"Tier 1 (real-time) failed: {e}, trying Tier 2")
            
            # Tier 2: Try degraded mode (cached data + deterministic calculations)
            if self.degraded_handler:
                try:
                    # Determine question type
                    question_type = None
                    if any(kw in text_lower for kw in ['option', 'iv', 'gamma', 'delta']):
                        question_type = 'options'
                    elif any(kw in text_lower for kw in ['var', 'sharpe', 'sortino', 'risk']):
                        question_type = 'risk'
                    elif any(kw in text_lower for kw in ['invest', 'buy', 'sell', 'hold']):
                        question_type = 'decision'
                    elif any(kw in text_lower for kw in ['kelly', 'position sizing', 'portfolio']):
                        question_type = 'portfolio'
                    
                    if question_type and self.degraded_handler.can_handle(text, question_type):
                        degraded_result = self.degraded_handler.handle(text, question_type, user_context)
                        if degraded_result:
                            self.logger.info(f"Using Tier 2 (degraded mode) for {question_type}")
                            return degraded_result
                except Exception as e:
                    self.logger.warning(f"Tier 2 (degraded mode) failed: {e}, falling back to Tier 3")
            
            # Tier 3: Fall back to conceptual/educational (only for theory questions)
            return await self._handle_conceptual_fallback(text)
            
        except Exception as e:
            self.logger.error(f"Error in production trading handler: {e}", exc_info=True)
            return self._error_response(str(e))
    
    async def _handle_realtime_options(
        self, 
        text: str, 
        symbols: List[str], 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Real-time options analysis using live data"""
        
        if not symbols and REALTIME_ENHANCER_AVAILABLE:
            symbol = extract_symbol(text) or 'SPY'  # Default to SPY
            symbols = [symbol]
        
        if not symbols:
            return await self._handle_static_fallback(text)
        
        symbol = symbols[0]
        
        try:
            # Get real-time options data
            options_chain = None
            if REALTIME_ENHANCER_AVAILABLE:
                options_chain = get_options_chain(symbol, expiration_days=30)
            
            if not options_chain:
                return await self._handle_static_fallback(text)
            
            # Calculate live metrics
            iv_skew = self._calculate_live_iv_skew(options_chain)
            greeks = options_chain.get('greeks', {})
            
            # Generate dynamic response based on live data
            if 'iv skew' in text.lower() or 'implied volatility' in text.lower():
                response = self._format_iv_skew_analysis(symbol, iv_skew, options_chain)
            elif 'gamma' in text.lower() or 'delta neutral' in text.lower():
                response = self._format_gamma_analysis(symbol, greeks, user_context, options_chain)
            elif 'iron condor' in text.lower():
                response = self._format_iron_condor_analysis(symbol, options_chain, user_context)
            else:
                response = self._format_general_options_analysis(symbol, options_chain, iv_skew, greeks)
            
            return {
                "response": response,
                "source": "realtime_options_data",
                "type": "options_analysis",
                "confidence": 0.92 if options_chain.get('data_source') == 'real' else 0.75,
                "realtime": True,
                "data_timestamp": datetime.utcnow().isoformat(),
                "underlying_symbol": symbol,
                "data": {
                    "iv_skew_ratio": iv_skew.get('skew_ratio'),
                    "atm_iv": iv_skew.get('atm_iv'),
                    "gamma_exposure": greeks.get('gamma'),
                    "options_data": options_chain
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Failed real-time options analysis: {e}")
            # Don't return here - let it fall through to Tier 2 degraded mode
            return None
    
    async def _handle_realtime_risk(
        self, 
        text: str, 
        symbols: List[str], 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Real-time risk metrics using portfolio context"""
        
        try:
            portfolio = user_context.get('portfolio', {})
            
            # Convert portfolio weights if needed
            if portfolio and isinstance(portfolio, dict):
                portfolio_weights = portfolio.get('asset_weights', {})
                if not portfolio_weights:
                    # Try to extract from portfolio dict directly
                    portfolio_weights = {k: v for k, v in portfolio.items() if isinstance(v, (int, float))}
            else:
                portfolio_weights = {}
            
            if not portfolio_weights and self.portfolio_state:
                portfolio_weights = self.portfolio_state.asset_weights
            
            if 'var' in text.lower() or 'value at risk' in text.lower():
                var_analysis = self._calculate_portfolio_var(
                    portfolio_weights,
                    confidence=0.95,
                    horizon_days=1
                )
                response = self._format_var_analysis(var_analysis, portfolio_weights)
                
            elif 'sharpe' in text.lower() or 'sortino' in text.lower():
                performance = self._calculate_risk_adjusted_metrics(portfolio_weights)
                response = self._format_performance_analysis(performance, portfolio_weights)
                
            else:
                # General risk analysis
                response = self._format_general_risk_analysis(portfolio_weights, user_context)
            
            return {
                "response": response,
                "source": "realtime_risk_engine",
                "type": "risk_analysis",
                "confidence": 0.88,
                "realtime": True,
                "data_timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "portfolio_metrics": await self._get_portfolio_metrics(portfolio_weights),
                    "risk_analysis": var_analysis if 'var' in text.lower() else performance
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Failed real-time risk analysis: {e}")
            # Don't return here - let it fall through to Tier 2 degraded mode
            return None
    
    async def _handle_realtime_portfolio(
        self, 
        text: str, 
        symbols: List[str], 
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Real-time portfolio optimization with current market data"""
        
        try:
            portfolio = user_context.get('portfolio', {})
            risk_profile = user_context.get('risk_profile', {})
            
            if 'kelly' in text.lower() and 'criterion' in text.lower():
                # Calculate actual Kelly based on strategy performance
                strategy_stats = self._get_strategy_performance(user_context)
                kelly_analysis = self._calculate_actual_kelly(strategy_stats, risk_profile, symbols)
                response = self._format_kelly_analysis(kelly_analysis, strategy_stats, symbols)
                
            elif 'position sizing' in text.lower() and symbols:
                symbol = symbols[0]
                sizing_analysis = await self._calculate_optimal_position_size(
                    symbol, portfolio, risk_profile, user_context
                )
                response = self._format_position_sizing_analysis(sizing_analysis, symbol)
                
            else:
                # General portfolio optimization
                if self.decision_engine and symbols:
                    # Use decision engine for allocation
                    context = self.decision_engine.make_decision(
                        symbol=symbols[0],
                        asset_type=user_context.get('asset_type', 'stock'),
                        context=user_context
                    )
                    response = self._format_portfolio_optimization(context, portfolio)
                else:
                    response = self._format_general_portfolio_analysis(portfolio, risk_profile)
            
            return {
                "response": response,
                "source": "realtime_portfolio_engine",
                "type": "portfolio_optimization",
                "confidence": 0.90,
                "realtime": True,
                "data_timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "recommendations": await self._extract_recommendations(response),
                    "portfolio_analysis": sizing_analysis if 'position sizing' in text.lower() else None
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Failed real-time portfolio analysis: {e}")
            # Don't return here - let it fall through to Tier 2 degraded mode
            return None
    
    async def _handle_realtime_decision(
        self,
        text: str,
        symbols: List[str],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Real-time investment decision using Decision Engine"""
        
        if not symbols or not self.decision_engine:
            return await self._handle_static_fallback(text)
        
        try:
            symbol = symbols[0]
            
            # Get current price
            current_price = None
            if REALTIME_ENHANCER_AVAILABLE:
                price_data = get_real_time_price(symbol, user_context.get('asset_type', 'stock'))
                if price_data:
                    current_price = price_data.get('price')
            
            # Use Decision Engine for real-time analysis
            context: InvestmentContext = self.decision_engine.make_decision(
                symbol=symbol,
                asset_type=user_context.get('asset_type', 'stock'),
                current_price=current_price,
                context=user_context
            )
            
            # Format decision engine response
            response = self._format_decision_engine_response(context, text)
            
            return {
                "response": response,
                "source": "investment_brain",
                "type": "investment_decision",
                "confidence": abs(context.decision.conviction_score) / 10.0,
                "realtime": True,
                "data_timestamp": datetime.utcnow().isoformat(),
                "decision": context.decision.decision,
                "conviction": context.decision.conviction_score,
                "reward_risk_ratio": context.decision.reward_risk_ratio,
                "data": {
                    "investment_context": self._context_to_dict(context)
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Failed real-time decision analysis: {e}")
            # Don't return here - let it fall through to Tier 2 degraded mode
            return None
    
    # REAL-TIME CALCULATION METHODS
    
    def _calculate_live_iv_skew(self, options_chain: Dict[str, Any]) -> Dict[str, float]:
        """Calculate real IV skew from live options data"""
        try:
            atm_iv = options_chain.get('atm_iv', 0.20)
            put_iv = options_chain.get('put_iv', atm_iv)
            call_iv = options_chain.get('call_iv', atm_iv)
            
            skew_ratio = put_iv / call_iv if call_iv > 0 else 1.0
            skew_premium = put_iv - call_iv
            
            return {
                'skew_ratio': skew_ratio,
                'atm_iv': atm_iv,
                'put_iv': put_iv,
                'call_iv': call_iv,
                'put_skew_premium': skew_premium,
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"Error calculating IV skew: {e}")
            return {'skew_ratio': 1.0, 'atm_iv': 0.20, 'put_iv': 0.20, 'call_iv': 0.20}
    
    def _calculate_portfolio_var(
        self, 
        portfolio: Dict[str, float], 
        confidence: float = 0.95,
        horizon_days: int = 1
    ) -> Dict[str, float]:
        """Calculate portfolio VaR (Value at Risk)"""
        try:
            if not portfolio or not REALTIME_ENHANCER_AVAILABLE:
                # Fallback to mock calculation
                return get_risk_metrics(portfolio) if portfolio else {}
            
            # Use realtime enhancer if available
            risk_metrics = get_risk_metrics(portfolio)
            if risk_metrics:
                var_daily = risk_metrics.get('var_95_daily', 0.02)
                var_monthly = risk_metrics.get('var_95_monthly', var_daily * (21 ** 0.5))
                
                return {
                    'var_daily': var_daily,
                    'var_monthly': var_monthly,
                    'var_annual': risk_metrics.get('var_95_annual', var_daily * (252 ** 0.5)),
                    'portfolio_volatility': risk_metrics.get('portfolio_volatility', 0.15),
                    'confidence': confidence,
                    'horizon_days': horizon_days
                }
            
            return {}
        except Exception as e:
            self.logger.error(f"Error calculating VaR: {e}")
            return {}
    
    def _calculate_risk_adjusted_metrics(self, portfolio: Dict[str, float]) -> Dict[str, float]:
        """Calculate Sharpe and Sortino ratios"""
        try:
            if not portfolio or not REALTIME_ENHANCER_AVAILABLE:
                return {}
            
            risk_metrics = get_risk_metrics(portfolio)
            if risk_metrics:
                return {
                    'sharpe_ratio': risk_metrics.get('sharpe_ratio', 1.0),
                    'sortino_ratio': risk_metrics.get('sortino_ratio', 1.2),
                    'portfolio_volatility': risk_metrics.get('portfolio_volatility', 0.15)
                }
            
            return {}
        except Exception as e:
            self.logger.error(f"Error calculating risk-adjusted metrics: {e}")
            return {}
    
    def _calculate_actual_kelly(
        self,
        strategy_stats: Dict[str, float],
        risk_profile: Dict[str, Any],
        symbols: List[str]
    ) -> Dict[str, Any]:
        """Calculate actual Kelly Criterion based on strategy performance"""
        try:
            win_rate = strategy_stats.get('win_rate', 0.60)
            win_loss_ratio = strategy_stats.get('win_loss_ratio', 2.0)
            
            # Kelly formula: f* = (bp - q) / b
            # where b = odds (win/loss ratio), p = win rate, q = loss rate (1-p)
            b = win_loss_ratio
            p = win_rate
            q = 1 - p
            
            full_kelly = (b * p - q) / b if b > 0 else 0.0
            full_kelly = max(0.0, min(1.0, full_kelly))  # Clamp 0-1
            
            half_kelly = full_kelly / 2.0
            quarter_kelly = full_kelly / 4.0
            
            # Get portfolio value
            portfolio_value = risk_profile.get('portfolio_value', 100000.0)
            risk_per_trade = risk_profile.get('risk_per_trade', 0.01)  # 1% default
            
            optimal_size = portfolio_value * risk_per_trade * half_kelly
            
            return {
                'full_kelly': full_kelly,
                'half_kelly': half_kelly,
                'quarter_kelly': quarter_kelly,
                'optimal_size': optimal_size,
                'win_rate': win_rate,
                'win_loss_ratio': win_loss_ratio,
                'risk_per_trade': risk_per_trade,
                'portfolio_value': portfolio_value
            }
        except Exception as e:
            self.logger.error(f"Error calculating Kelly: {e}")
            return {'full_kelly': 0.25, 'half_kelly': 0.125, 'optimal_size': 0}
    
    async def _calculate_optimal_position_size(
        self,
        symbol: str,
        portfolio: Dict[str, Any],
        risk_profile: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate optimal position size using Decision Engine"""
        try:
            if not self.decision_engine:
                return {'optimal_size': 0, 'reasoning': 'Decision engine not available'}
            
            # Get decision from engine
            context = self.decision_engine.make_decision(
                symbol=symbol,
                asset_type=user_context.get('asset_type', 'stock'),
                context=user_context
            )
            
            # Use position size from decision
            position_size_pct = context.decision.position_size or 0.0
            conviction = context.decision.conviction_score
            rrr = context.decision.reward_risk_ratio
            
            # Calculate dollar amount
            portfolio_value = risk_profile.get('portfolio_value', 100000.0)
            optimal_size = portfolio_value * position_size_pct
            
            return {
                'symbol': symbol,
                'optimal_size': optimal_size,
                'position_size_pct': position_size_pct,
                'conviction': conviction,
                'reward_risk_ratio': rrr,
                'decision': context.decision.decision,
                'reasoning': f"Based on conviction {conviction:.2f} and R:R {rrr:.2f}"
            }
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return {'optimal_size': 0, 'reasoning': f'Error: {str(e)}'}
    
    # FORMATTING METHODS
    
    def _format_iv_skew_analysis(self, symbol: str, iv_skew: Dict, options_chain: Dict) -> str:
        """Format real-time IV skew analysis"""
        skew_ratio = iv_skew.get('skew_ratio', 1.0)
        atm_iv = iv_skew.get('atm_iv', 0.20)
        put_iv = iv_skew.get('put_iv', atm_iv)
        call_iv = iv_skew.get('call_iv', atm_iv)
        underlying_price = options_chain.get('underlying_price', 100.0)
        data_source = options_chain.get('data_source', 'mock')
        
        interpretation = "bullish" if skew_ratio < 1.0 else "bearish" if skew_ratio > 1.05 else "neutral"
        
        response = f"""**Real-Time IV Skew Analysis for {symbol}**

**Current Market Data:**
- **Underlying Price**: ${underlying_price:.2f}
- **ATM IV (30-day)**: {atm_iv*100:.1f}%
- **Put IV**: {put_iv*100:.1f}%
- **Call IV**: {call_iv*100:.1f}%
- **IV Skew Ratio**: {skew_ratio:.3f} ({'Higher put IV' if skew_ratio > 1.0 else 'Higher call IV' if skew_ratio < 1.0 else 'Balanced'})

**Interpretation**: {interpretation} sentiment

**Trading Implications**:
"""
        
        if skew_ratio > 1.05:
            response += f"- Positive skew ({skew_ratio:.3f}) → Bearish sentiment, protective demand\n"
            response += "- High put IV indicates fear/protective demand in market\n"
            response += "- Consider put strategies for volatility exposure\n"
        elif skew_ratio < 0.95:
            response += f"- Negative skew ({skew_ratio:.3f}) → Bullish sentiment\n"
            response += "- High call IV indicates bullish speculation\n"
            response += "- Consider call strategies for volatility exposure\n"
        else:
            response += f"- Neutral skew ({skew_ratio:.3f}) → Balanced sentiment\n"
            response += "- Put and call IVs relatively balanced\n"
            response += "- Range-bound expectations\n"
        
        response += f"\n*Data Source: {data_source} | Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        
        return response
    
    def _format_gamma_analysis(
        self, 
        symbol: str, 
        greeks: Dict, 
        user_context: Dict,
        options_chain: Dict
    ) -> str:
        """Format gamma risk analysis"""
        gamma = greeks.get('gamma', 0.01)
        theta = greeks.get('theta', -0.05)
        vega = greeks.get('vega', 0.15)
        atm_iv = options_chain.get('atm_iv', 0.20)
        underlying_price = options_chain.get('underlying_price', 100.0)
        data_source = options_chain.get('data_source', 'mock')
        
        gamma_risk = "High" if abs(gamma) > 0.015 else "Moderate" if abs(gamma) > 0.010 else "Low"
        
        return f"""**Gamma Risk Analysis for {symbol} (Real-Time)**

**Current Greeks:**
- **Gamma**: {gamma:.4f} ({gamma_risk} risk level)
- **Theta**: {theta:.4f} (time decay)
- **Vega**: {vega:.4f} (volatility sensitivity)
- **ATM IV**: {atm_iv*100:.1f}%
- **Underlying Price**: ${underlying_price:.2f}

**Gamma Risk Assessment**:
{"High gamma risk - Monitor delta closely, frequent rebalancing required" if abs(gamma) > 0.015 else "Moderate gamma risk - Standard rebalancing schedule" if abs(gamma) > 0.010 else "Low gamma risk - Minimal delta drift, less frequent rebalancing"}

**Hedging Recommendations**:
- Rebalance when delta exceeds ±0.10 threshold
- {"Higher rebalancing frequency recommended" if abs(gamma) > 0.015 else "Standard rebalancing frequency"}
- Consider volatility hedging if vega exposure is high (current: {vega:.4f})

*Data Source: {data_source} | Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*"""
    
    def _format_iron_condor_analysis(self, symbol: str, options_chain: Dict, user_context: Dict) -> str:
        """Format iron condor strategy analysis"""
        atm_iv = options_chain.get('atm_iv', 0.20)
        underlying_price = options_chain.get('underlying_price', 100.0)
        greeks = options_chain.get('greeks', {})
        data_source = options_chain.get('data_source', 'mock')
        
        if atm_iv > 0.25:
            iv_env = "High (25%+)"
            recommendation = "Favorable for iron condors (high IV premium)"
        elif atm_iv > 0.20:
            iv_env = "Medium-High (20-25%)"
            recommendation = "Good for iron condors (elevated IV)"
        else:
            iv_env = "Low-Medium (<20%)"
            recommendation = "Less favorable for iron condors (low IV premium)"
        
        return f"""**Iron Condor Strategy Analysis - {symbol} (Real-Time)**

**Current Market Environment:**
- **Underlying Price**: ${underlying_price:.2f}
- **IV Environment**: {iv_env} ({atm_iv*100:.1f}% ATM IV)

**Recommendation**: {recommendation}

**Strategy Setup**:
- Structure: Sell OTM call spread + sell OTM put spread
- Target Expiration: 30-45 days
- Delta Targets: ~15-20 delta for short strikes
- Premium Target: 25-33% of max risk

**Risk Considerations**:
- Monitor for volatility expansion (current IV: {atm_iv*100:.1f}%)
- Current theta: {greeks.get('theta', -0.05):.4f} (time decay benefit)
- Adjust if price approaches short strikes (±10% move)
- Close at 50% max profit or 30 days to expiration

*Data Source: {data_source} | Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*"""
    
    def _format_var_analysis(self, var_analysis: Dict, portfolio: Dict[str, float]) -> str:
        """Format VaR analysis"""
        var_daily = var_analysis.get('var_daily', 0.02)
        var_monthly = var_analysis.get('var_monthly', var_daily * (21 ** 0.5))
        portfolio_vol = var_analysis.get('portfolio_volatility', 0.15)
        confidence = var_analysis.get('confidence', 0.95)
        
        portfolio_value = 100000.0  # Default, should come from user context
        var_daily_dollar = portfolio_value * var_daily
        var_monthly_dollar = portfolio_value * var_monthly
        
        portfolio_str = ", ".join([f"{sym}: {wt*100:.1f}%" for sym, wt in list(portfolio.items())[:3]])
        
        return f"""**Portfolio Value at Risk (VaR) Analysis**

**Portfolio Composition**: {portfolio_str if portfolio_str else 'Default portfolio'}

**VaR Calculations ({confidence*100:.0f}% confidence)**:
- **Daily VaR**: {var_daily*100:.2f}% (${var_daily_dollar:,.2f})
- **Monthly VaR**: {var_monthly*100:.2f}% (${var_monthly_dollar:,.2f})
- **Portfolio Volatility**: {portfolio_vol*100:.1f}% (annualized)

**Interpretation**:
- {confidence*100:.0f}% chance losses won't exceed {var_daily*100:.2f}% in 1 day
- {confidence*100:.0f}% chance losses won't exceed {var_monthly*100:.2f}% in 1 month
- Based on current portfolio volatility of {portfolio_vol*100:.1f}%

**Risk Management**:
- Monitor daily VaR for position sizing
- Adjust positions if VaR exceeds risk tolerance
- Diversification reduces overall VaR

*Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*"""
    
    def _format_performance_analysis(self, performance: Dict, portfolio: Dict[str, float]) -> str:
        """Format Sharpe/Sortino analysis"""
        sharpe = performance.get('sharpe_ratio', 1.0)
        sortino = performance.get('sortino_ratio', 1.2)
        vol = performance.get('portfolio_volatility', 0.15)
        
        sharpe_rating = "Excellent" if sharpe > 2.0 else "Good" if sharpe > 1.0 else "Fair" if sharpe > 0.5 else "Poor"
        sortino_rating = "Excellent" if sortino > 2.0 else "Good" if sortino > 1.0 else "Fair" if sortino > 0.5 else "Poor"
        
        return f"""**Risk-Adjusted Performance Metrics**

**Portfolio Ratios**:
- **Sharpe Ratio**: {sharpe:.2f} ({sharpe_rating})
- **Sortino Ratio**: {sortino:.2f} ({sortino_rating})
- **Portfolio Volatility**: {vol*100:.1f}% (annualized)

**Interpretation**:
- **Sharpe**: Measures risk-adjusted return using total volatility
  - {sharpe:.2f} means portfolio returns {sharpe:.2f} units per unit of total risk
  - Higher is better (benchmark: 1.0+)
  
- **Sortino**: Measures risk-adjusted return using downside volatility only
  - {sortino:.2f} means portfolio returns {sortino:.2f} units per unit of downside risk
  - Better than Sharpe for asymmetric return distributions
  - Higher is better (benchmark: 1.0+)

**Comparison**:
- Sharpe ({sharpe:.2f}) vs Sortino ({sortino:.2f}): {"Sortino higher indicates upside volatility" if sortino > sharpe else "Similar ratios indicate balanced volatility"}
- Use Sortino when portfolio has skewed returns (frequent small wins, rare large losses)

*Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*"""
    
    def _format_kelly_analysis(
        self, 
        kelly_analysis: Dict, 
        strategy_stats: Dict,
        symbols: List[str]
    ) -> str:
        """Format real Kelly Criterion analysis"""
        full_kelly = kelly_analysis.get('full_kelly', 0.25)
        half_kelly = kelly_analysis.get('half_kelly', 0.125)
        quarter_kelly = kelly_analysis.get('quarter_kelly', 0.0625)
        optimal_size = kelly_analysis.get('optimal_size', 0)
        win_rate = kelly_analysis.get('win_rate', 0.60)
        win_loss_ratio = kelly_analysis.get('win_loss_ratio', 2.0)
        risk_per_trade = kelly_analysis.get('risk_per_trade', 0.01)
        
        symbol_str = symbols[0] if symbols else "portfolio"
        
        return f"""**Kelly Criterion Position Sizing - {symbol_str}**

**Strategy Performance**:
- **Win Rate**: {win_rate:.1%}
- **Average Win/Loss Ratio**: {win_loss_ratio:.2f}:1

**Kelly Calculation**:
- **Full Kelly**: {full_kelly:.1%} (Maximum growth, high volatility)
- **Half Kelly (Recommended)**: {half_kelly:.1%} (Balanced, moderate risk)
- **Quarter Kelly (Conservative)**: {quarter_kelly:.1%} (Conservative, lower volatility)

**Recommended Position Size**: ${optimal_size:,.2f}
- Based on {risk_per_trade*100:.1f}% portfolio risk per trade
- Half Kelly approach (recommended for practical trading)

**Risk Management Notes**:
- Full Kelly ({full_kelly:.1%}) maximizes long-term growth but can lead to large drawdowns
- Half Kelly ({half_kelly:.1%}) provides {full_kelly*50:.1f}% of growth with 50% less volatility
- Quarter Kelly ({quarter_kelly:.1%}) for conservative traders or uncertain edge
- Position sized for {risk_per_trade*100:.1f}% portfolio risk per trade

**Formula**: f* = (bp - q) / b
- b = odds (win/loss ratio) = {win_loss_ratio:.2f}
- p = win rate = {win_rate:.1%}
- q = loss rate = {1-win_rate:.1%}

*Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*"""
    
    def _format_position_sizing_analysis(self, sizing_analysis: Dict, symbol: str) -> str:
        """Format position sizing analysis"""
        optimal_size = sizing_analysis.get('optimal_size', 0)
        position_size_pct = sizing_analysis.get('position_size_pct', 0.0)
        conviction = sizing_analysis.get('conviction', 0.0)
        rrr = sizing_analysis.get('reward_risk_ratio', 1.0)
        decision = sizing_analysis.get('decision', 'HOLD')
        reasoning = sizing_analysis.get('reasoning', 'Based on investment analysis')
        
        return f"""**Optimal Position Sizing - {symbol}**

**Decision**: {decision}
- **Conviction Score**: {conviction:.2f}/10
- **Reward/Risk Ratio**: {rrr:.2f}:1

**Position Sizing**:
- **Recommended Size**: ${optimal_size:,.2f}
- **Portfolio Allocation**: {position_size_pct*100:.1f}%

**Reasoning**: {reasoning}

**Risk Considerations**:
- Position size reflects conviction and risk/reward profile
- Monitor position and adjust based on market conditions
- Consider reducing size if conviction decreases or risk increases

*Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*"""
    
    def _format_decision_engine_response(self, context: InvestmentContext, text: str) -> str:
        """Format Investment Brain decision response"""
        decision = context.decision
        symbol = context.symbol
        
        response = f"""**Investment Analysis - {symbol} (Real-Time)**

**Decision**: {decision.decision}
- **Conviction**: {decision.conviction_score:.2f}/10 ({'Strong' if abs(decision.conviction_score) > 7 else 'Moderate' if abs(decision.conviction_score) > 3 else 'Weak'})
- **Reward/Risk**: {decision.reward_risk_ratio:.2f}:1 ({'Favorable' if decision.reward_risk_ratio > 2.0 else 'Moderate' if decision.reward_risk_ratio > 1.5 else 'Unfavorable'})

"""
        
        if decision.decision == "BUY" and decision.position_size:
            response += f"- **Suggested Position**: {decision.position_size*100:.1f}% of portfolio\n"
        
        # Key factors
        if context.asset_eval.fundamentals > 7:
            response += "[STRONG] Strong fundamentals\n"
        if context.asset_eval.technicals > 7:
            response += "[STRONG] Strong technical setup\n"
        if context.asset_eval.risk_factors > 7:
            response += "[WARNING] High risk factors\n"
        
        # Market environment
        if context.market_env.macro_trend > 2:
            response += "[POSITIVE] Positive macro trend\n"
        elif context.market_env.macro_trend < -2:
            response += "[WARNING] Negative macro trend\n"
        
        # Exit triggers if active
        if context.exit_triggers.should_exit():
            active_triggers = [
                k for k, v in context.exit_triggers.__dict__.items() 
                if v and k != 'should_exit' and not callable(v)
            ]
            if active_triggers:
                response += f"\n[WARNING] **Exit Triggers Active**: {', '.join(active_triggers)}\n"
        
        response += f"\n*Data Source: Investment Brain | Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        
        return response
    
    def _format_general_options_analysis(
        self, 
        symbol: str, 
        options_chain: Dict, 
        iv_skew: Dict, 
        greeks: Dict
    ) -> str:
        """General options analysis"""
        return self._format_iv_skew_analysis(symbol, iv_skew, options_chain)
    
    def _format_general_risk_analysis(self, portfolio: Dict[str, float], user_context: Dict) -> str:
        """General risk analysis"""
        return """**Portfolio Risk Analysis**

Provide specific risk metric (VaR, Sharpe, Sortino) for detailed analysis."""
    
    def _format_portfolio_optimization(self, context: InvestmentContext, portfolio: Dict) -> str:
        """Format portfolio optimization"""
        return self._format_decision_engine_response(context, "")
    
    def _format_general_portfolio_analysis(self, portfolio: Dict, risk_profile: Dict) -> str:
        """General portfolio analysis"""
        return """**Portfolio Optimization Analysis**

Provide specific optimization request (Kelly, position sizing, Markowitz) for detailed analysis."""
    
    # UTILITY METHODS
    
    async def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock/crypto symbols from text"""
        if REALTIME_ENHANCER_AVAILABLE:
            symbol = extract_symbol(text)
            if symbol:
                return [symbol]
        
        # Fallback regex extraction
        symbol_pattern = r'\b([A-Z]{1,5})\b'
        symbols = re.findall(symbol_pattern, text.upper())
        return [s for s in symbols if s in KNOWN_TICKERS][:3]  # Max 3 symbols
    
    async def _get_portfolio_metrics(self, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """Get portfolio metrics"""
        return {
            'num_positions': len(portfolio),
            'total_weight': sum(portfolio.values()),
            'positions': list(portfolio.keys())[:10]
        }
    
    async def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response"""
        # Simple extraction - can be enhanced
        recommendations = []
        if 'Recommended Position Size' in response:
            recommendations.append('Position sizing recommendation')
        if 'Decision: BUY' in response:
            recommendations.append('Buy recommendation')
        elif 'Decision: SELL' in response:
            recommendations.append('Sell recommendation')
        return recommendations
    
    def _get_strategy_performance(self, user_context: Dict) -> Dict[str, float]:
        """Get strategy performance stats (mock for now)"""
        # TODO: Connect to actual strategy performance tracking
        return {
            'win_rate': 0.60,
            'win_loss_ratio': 2.0,
            'total_trades': 100,
            'avg_return': 0.15
        }
    
    def _portfolio_state_to_dict(self, portfolio: PortfolioState) -> Dict[str, Any]:
        """Convert PortfolioState to dict"""
        return {
            'asset_weights': portfolio.asset_weights,
            'total_exposure': portfolio.total_exposure,
            'correlations': portfolio.correlations,
            'max_risk_limit': portfolio.max_risk_limit,
            'volatility_target': portfolio.volatility_target,
            'risk_ceiling': portfolio.risk_ceiling
        }
    
    def _context_to_dict(self, context: InvestmentContext) -> Dict[str, Any]:
        """Convert InvestmentContext to dict"""
        return {
            'symbol': context.symbol,
            'decision': context.decision.decision,
            'conviction': context.decision.conviction_score,
            'reward_risk_ratio': context.decision.reward_risk_ratio,
            'position_size': context.decision.position_size,
            'current_price': context.current_price,
            'target_price': context.target_price,
            'stop_loss': context.stop_loss
        }
    
    async def _handle_static_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback to static handlers"""
        try:
            from core.qa_engine_advanced_trading import handle_advanced_trading_question
            return await handle_advanced_trading_question(text)
        except Exception as e:
            self.logger.warning(f"Static fallback failed: {e}")
            return {
                "response": f"Unable to process question: {str(e)}",
                "source": "production_handler",
                "type": "error",
                "confidence": 0.0
            }
    
    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """Error response"""
        return {
            "response": f"Unable to provide real-time analysis: {error_msg}",
            "source": "production_handler",
            "type": "error",
            "confidence": 0.0,
            "realtime": False
        }


# Factory function for easy integration
def create_production_handler(config: Optional[Dict[str, Any]] = None) -> ProductionTradingHandler:
    """Factory to create and initialize production handler"""
    return ProductionTradingHandler(config)


# Main entry point for backward compatibility
async def handle_production_trading_question(
    text: str,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Main entry point - creates handler and processes question"""
    handler = create_production_handler()
    return await handler.handle_advanced_question(text, user_context)

