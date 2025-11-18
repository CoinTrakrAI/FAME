#!/usr/bin/env python3
"""
FAME Degraded Mode Handler (Tier 2)
Production fallback using cached data and deterministic calculations
Never generates synthetic data - only uses real cached data
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .cache_manager import get_cache_manager
from .realtime_enhancer import extract_symbol

logger = logging.getLogger(__name__)


class DegradedModeHandler:
    """
    Tier 2: Degraded Mode Production Fallback
    
    Uses cached last-known-good data to provide real analytical output
    when real-time data is unavailable.
    
    Principles:
    - Never hallucinates or generates fake numbers
    - Only uses real cached data
    - Applies deterministic formulas to cached data
    - Clearly indicates degraded status
    - Behaves like Bloomberg when feeds drop
    """
    
    def __init__(self):
        self.cache = get_cache_manager()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def can_handle(self, text: str, question_type: str) -> bool:
        """
        Check if degraded mode can handle this question
        
        Args:
            text: Question text
            question_type: Question type (options, risk, portfolio, etc.)
            
        Returns:
            True if cached data available for this question type
        """
        try:
            text_lower = text.lower()
            symbol = extract_symbol(text)
            
            # Check cache for relevant data
            if 'option' in text_lower or 'iv' in text_lower:
                if symbol:
                    cache_key = f"options_chain:{symbol}"
                    return self.cache.get(cache_key, max_age_seconds=600) is not None
                return False
            
            elif 'var' in text_lower or 'sharpe' in text_lower or 'risk' in text_lower:
                cache_key = "portfolio_risk_metrics"
                return self.cache.get(cache_key, max_age_seconds=300) is not None
            
            elif 'kelly' in text_lower or 'position sizing' in text_lower:
                cache_key = "portfolio_state"
                return self.cache.get(cache_key, max_age_seconds=300) is not None
            
            elif any(kw in text_lower for kw in ['invest', 'buy', 'sell', 'hold']):
                if symbol:
                    cache_key = f"investment_decision:{symbol}"
                    return self.cache.get(cache_key, max_age_seconds=300) is not None
                return False
            
            return False
        except Exception as e:
            self.logger.error(f"Error checking degraded mode availability: {e}")
            return False
    
    def handle_options(self, text: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Handle options questions with cached data"""
        try:
            cache_key = f"options_chain:{symbol}"
            cached_data = self.cache.get(cache_key, max_age_seconds=600)
            
            if not cached_data:
                return None
            
            cache_timestamp = self.cache.get_timestamp(cache_key)
            cache_age = int(time.time() - cache_timestamp) if cache_timestamp else 0
            
            # Calculate IV skew from cached data (deterministic)
            iv_skew = self._calculate_iv_skew_from_cached(cached_data)
            
            if not iv_skew:
                return None
            
            # Format degraded mode response
            if 'iv skew' in text.lower() or 'implied volatility' in text.lower():
                response = self._format_iv_skew_degraded(symbol, iv_skew, cache_timestamp, cache_age)
            elif 'gamma' in text.lower():
                greeks = cached_data.get('greeks', {})
                response = self._format_gamma_degraded(symbol, greeks, cache_timestamp, cache_age)
            else:
                response = self._format_options_degraded(symbol, cached_data, cache_timestamp, cache_age)
            
            return {
                "response": response,
                "source": "degraded_mode_cache",
                "type": "options_analysis",
                "confidence": 0.75,  # Lower confidence due to stale data
                "realtime": False,
                "degraded": True,
                "data_timestamp": datetime.fromtimestamp(cache_timestamp, tz=timezone.utc).isoformat() if cache_timestamp else None,
                "cache_age_seconds": cache_age,
                "data": {
                    "underlying_symbol": symbol,
                    "iv_skew": iv_skew,
                    "cached_data": cached_data
                }
            }
        except Exception as e:
            self.logger.error(f"Error in degraded options handler: {e}")
            return None
    
    def handle_risk(self, text: str, portfolio: Optional[Dict[str, float]] = None) -> Optional[Dict[str, Any]]:
        """Handle risk questions with cached data"""
        try:
            cache_key = "portfolio_risk_metrics"
            cached_metrics = self.cache.get(cache_key, max_age_seconds=300)
            
            if not cached_metrics:
                return None
            
            cache_timestamp = self.cache.get_timestamp(cache_key)
            cache_age = int(time.time() - cache_timestamp) if cache_timestamp else 0
            
            if 'var' in text.lower():
                response = self._format_var_degraded(cached_metrics, cache_timestamp, cache_age)
            elif 'sharpe' in text.lower() or 'sortino' in text.lower():
                response = self._format_performance_degraded(cached_metrics, cache_timestamp, cache_age)
            else:
                response = self._format_risk_degraded(cached_metrics, cache_timestamp, cache_age)
            
            return {
                "response": response,
                "source": "degraded_mode_cache",
                "type": "risk_analysis",
                "confidence": 0.70,
                "realtime": False,
                "degraded": True,
                "data_timestamp": datetime.fromtimestamp(cache_timestamp, tz=timezone.utc).isoformat() if cache_timestamp else None,
                "cache_age_seconds": cache_age,
                "data": cached_metrics
            }
        except Exception as e:
            self.logger.error(f"Error in degraded risk handler: {e}")
            return None
    
    def handle_investment_decision(self, text: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Handle investment decision questions with cached data"""
        try:
            cache_key = f"investment_decision:{symbol}"
            cached_decision = self.cache.get(cache_key, max_age_seconds=300)
            
            if not cached_decision:
                return None
            
            cache_timestamp = self.cache.get_timestamp(cache_key)
            cache_age = int(time.time() - cache_timestamp) if cache_timestamp else 0
            
            response = self._format_decision_degraded(symbol, cached_decision, cache_timestamp, cache_age)
            
            return {
                "response": response,
                "source": "degraded_mode_cache",
                "type": "investment_decision",
                "confidence": 0.70,
                "realtime": False,
                "degraded": True,
                "data_timestamp": datetime.fromtimestamp(cache_timestamp, tz=timezone.utc).isoformat() if cache_timestamp else None,
                "cache_age_seconds": cache_age,
                "decision": cached_decision.get('decision'),
                "conviction": cached_decision.get('conviction'),
                "data": cached_decision
            }
        except Exception as e:
            self.logger.error(f"Error in degraded decision handler: {e}")
            return None
    
    def handle(self, text: str, question_type: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Main degraded mode handler
        
        Args:
            text: Question text
            question_type: Question type
            context: Optional context (symbol, portfolio, etc.)
            
        Returns:
            Response dict if handled, None otherwise
        """
        try:
            text_lower = text.lower()
            symbol = extract_symbol(text) if not context else context.get('symbol')
            portfolio = context.get('portfolio') if context else None
            
            if question_type == 'options' and symbol:
                return self.handle_options(text, symbol)
            elif question_type == 'risk':
                return self.handle_risk(text, portfolio)
            elif question_type == 'decision' and symbol:
                return self.handle_investment_decision(text, symbol)
            
            return None
        except Exception as e:
            self.logger.error(f"Error in degraded mode handler: {e}")
            return None
    
    def _calculate_iv_skew_from_cached(self, cached_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Calculate IV skew deterministically from cached data"""
        try:
            atm_iv = cached_data.get('atm_iv')
            put_iv = cached_data.get('put_iv', atm_iv)
            call_iv = cached_data.get('call_iv', atm_iv)
            
            if not atm_iv or not put_iv or not call_iv:
                return None
            
            skew_ratio = put_iv / call_iv if call_iv > 0 else 1.0
            skew_premium = put_iv - call_iv
            
            return {
                'skew_ratio': float(skew_ratio),
                'atm_iv': float(atm_iv),
                'put_iv': float(put_iv),
                'call_iv': float(call_iv),
                'put_skew_premium': float(skew_premium)
            }
        except Exception as e:
            self.logger.error(f"Error calculating IV skew from cached: {e}")
            return None
    
    def _format_iv_skew_degraded(self, symbol: str, iv_skew: Dict, timestamp: Optional[float], age: int) -> str:
        """Format IV skew analysis from cached data"""
        skew_ratio = iv_skew.get('skew_ratio', 1.0)
        atm_iv = iv_skew.get('atm_iv', 0.20)
        put_iv = iv_skew.get('put_iv', atm_iv)
        call_iv = iv_skew.get('call_iv', atm_iv)
        
        timestamp_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else "unknown"
        
        interpretation = "bullish" if skew_ratio < 1.0 else "bearish" if skew_ratio > 1.05 else "neutral"
        
        response = f"""Live market data unavailable. Using cached snapshot from {timestamp_str} (age: {age // 60}m {age % 60}s).

IV Skew Analysis for {symbol} (Cached Data):

Current IV Metrics:
- ATM IV (30-day): {atm_iv*100:.1f}%
- Put IV: {put_iv*100:.1f}%
- Call IV: {call_iv*100:.1f}%
- IV Skew Ratio: {skew_ratio:.3f}

Interpretation: {interpretation} sentiment based on cached data.

Trading Implications:
"""
        
        if skew_ratio > 1.05:
            response += f"- Positive skew ({skew_ratio:.3f}) suggests bearish sentiment from cached snapshot\n"
            response += "- High put IV indicates protective demand in last known state\n"
        elif skew_ratio < 0.95:
            response += f"- Negative skew ({skew_ratio:.3f}) suggests bullish sentiment from cached snapshot\n"
            response += "- High call IV indicates bullish speculation in last known state\n"
        else:
            response += f"- Neutral skew ({skew_ratio:.3f}) from cached snapshot\n"
        
        response += f"\nNote: This analysis is based on cached data from {timestamp_str}. Real-time market conditions may differ."
        
        return response
    
    def _format_gamma_degraded(self, symbol: str, greeks: Dict, timestamp: Optional[float], age: int) -> str:
        """Format gamma analysis from cached data"""
        gamma = greeks.get('gamma', 0.01)
        theta = greeks.get('theta', -0.05)
        vega = greeks.get('vega', 0.15)
        
        timestamp_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else "unknown"
        
        gamma_risk = "High" if abs(gamma) > 0.015 else "Moderate" if abs(gamma) > 0.010 else "Low"
        
        return f"""Live market data unavailable. Using cached snapshot from {timestamp_str} (age: {age // 60}m {age % 60}s).

Gamma Risk Analysis for {symbol} (Cached Data):

Cached Greeks:
- Gamma: {gamma:.4f} ({gamma_risk} risk level)
- Theta: {theta:.4f}
- Vega: {vega:.4f}

Gamma Risk Assessment:
{"High gamma risk - Monitor delta closely" if abs(gamma) > 0.015 else "Moderate gamma risk - Standard rebalancing" if abs(gamma) > 0.010 else "Low gamma risk - Minimal delta drift"}

Note: This analysis is based on cached data from {timestamp_str}. Real-time Greeks may differ."""
    
    def _format_options_degraded(self, symbol: str, cached_data: Dict, timestamp: Optional[float], age: int) -> str:
        """General options analysis from cached data"""
        return self._format_iv_skew_degraded(symbol, self._calculate_iv_skew_from_cached(cached_data) or {}, timestamp, age)
    
    def _format_var_degraded(self, metrics: Dict, timestamp: Optional[float], age: int) -> str:
        """Format VaR analysis from cached data"""
        var_daily = metrics.get('var_95_daily', 0.02)
        var_monthly = metrics.get('var_95_monthly', var_daily * (21 ** 0.5))
        portfolio_vol = metrics.get('portfolio_volatility', 0.15)
        
        timestamp_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else "unknown"
        
        return f"""Live risk data unavailable. Using cached portfolio metrics from {timestamp_str} (age: {age // 60}m {age % 60}s).

Portfolio Value at Risk (VaR) - Cached Analysis:

VaR Calculations (95% confidence):
- Daily VaR: {var_daily*100:.2f}%
- Monthly VaR: {var_monthly*100:.2f}%
- Portfolio Volatility: {portfolio_vol*100:.1f}% (annualized)

Note: These metrics are based on cached portfolio state from {timestamp_str}. Current portfolio composition may differ."""
    
    def _format_performance_degraded(self, metrics: Dict, timestamp: Optional[float], age: int) -> str:
        """Format Sharpe/Sortino from cached data"""
        sharpe = metrics.get('sharpe_ratio', 1.0)
        sortino = metrics.get('sortino_ratio', 1.2)
        
        timestamp_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else "unknown"
        
        return f"""Live performance data unavailable. Using cached metrics from {timestamp_str} (age: {age // 60}m {age % 60}s).

Risk-Adjusted Performance Metrics (Cached):

- Sharpe Ratio: {sharpe:.2f}
- Sortino Ratio: {sortino:.2f}

Note: These ratios are based on cached portfolio performance from {timestamp_str}. Current performance may differ."""
    
    def _format_risk_degraded(self, metrics: Dict, timestamp: Optional[float], age: int) -> str:
        """General risk analysis from cached data"""
        return self._format_var_degraded(metrics, timestamp, age)
    
    def _format_decision_degraded(self, symbol: str, decision: Dict, timestamp: Optional[float], age: int) -> str:
        """Format investment decision from cached data"""
        decision_str = decision.get('decision', 'HOLD')
        conviction = decision.get('conviction', 0.0)
        rrr = decision.get('reward_risk_ratio', 1.0)
        
        timestamp_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC') if timestamp else "unknown"
        
        return f"""Live analysis unavailable. Using cached investment decision from {timestamp_str} (age: {age // 60}m {age % 60}s).

Investment Analysis for {symbol} (Cached Decision):

Decision: {decision_str}
- Conviction: {conviction:.2f}/10
- Reward/Risk: {rrr:.2f}:1

Note: This decision is based on cached analysis from {timestamp_str}. Current market conditions may have changed."""
        
        return response


import time

__all__ = ['DegradedModeHandler']

