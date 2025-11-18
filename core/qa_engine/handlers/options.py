#!/usr/bin/env python3
"""
FAME Advanced Trading Handlers - Options Handler V2
Options trading questions with real-time data integration
"""

import logging
from typing import Dict, Any, Optional
import re

from .base import BaseTradingHandler
from ..realtime_enhancer import get_options_chain, extract_symbol

logger = logging.getLogger(__name__)


class OptionsHandlerV2(BaseTradingHandler):
    """
    V2 Options Handler with real-time data support
    
    Handles:
    - IV skew analysis
    - Iron condor strategies
    - Gamma risk / delta neutral portfolios
    """
    
    def can_handle(self, text: str) -> bool:
        """Check if this is an options-related question"""
        text_lower = text.lower()
        options_keywords = [
            'option', 'iv', 'implied volatility', 'skew', 'iron condor',
            'gamma', 'delta', 'theta', 'vega', 'greeks', 'delta neutral',
            'straddle', 'strangle', 'spread'
        ]
        return any(kw in text_lower for kw in options_keywords)
    
    def has_realtime_data(self, text: str) -> bool:
        """Check if we have real-time options data for symbols in question"""
        symbol = extract_symbol(text)
        if not symbol:
            return False
        
        # Check if we can get options chain (even if mocked)
        options_data = get_options_chain(symbol)
        return options_data is not None
    
    def handle_realtime(self, text: str) -> Optional[Dict[str, Any]]:
        """Generate real-time options analysis"""
        text_lower = text.lower()
        
        # IV Skew
        if 'implied volatility' in text_lower and ('skew' in text_lower or any(sym in text.upper() for sym in ['SPY', 'AAPL', 'QQQ'])):
            return self._handle_iv_skew_realtime(text)
        
        # Iron Condor
        if 'iron condor' in text_lower:
            return self._handle_iron_condor_realtime(text)
        
        # Gamma Risk / Delta Neutral
        if 'gamma' in text_lower or 'delta neutral' in text_lower:
            return self._handle_gamma_risk_realtime(text)
        
        # Fall back to static if no specific real-time handler
        return None
    
    def _handle_iv_skew_realtime(self, text: str) -> Dict[str, Any]:
        """Handle IV skew with real-time data"""
        symbol = extract_symbol(text) or 'SPY'  # Default to SPY
        
        # Get real-time options data
        options_data = get_options_chain(symbol, expiration_days=30)
        if not options_data:
            return None  # Fall back to static
        
        # Extract IV skew from real-time data
        atm_iv = options_data.get('atm_iv', 0.20)
        put_iv = options_data.get('put_iv', atm_iv)
        call_iv = options_data.get('call_iv', atm_iv)
        skew = options_data.get('skew', 0.0)
        underlying_price = options_data.get('underlying_price', 100.0)
        data_source = options_data.get('data_source', 'unknown')
        
        # Generate real-time response
        response_text = f"""**Implied Volatility Skew Analysis - {symbol} (Real-Time):**

**Current Market Data:**
- **Underlying Price**: ${underlying_price:.2f}
- **ATM IV (30-day)**: {atm_iv*100:.1f}%
- **Put IV**: {put_iv*100:.1f}%
- **Call IV**: {call_iv*100:.1f}%
- **IV Skew**: {skew*100:.2f}% ({skew*100:.2f}% premium for puts)

**Interpretation:**
"""
        
        if skew > 0.05:
            response_text += f"- **Positive skew detected** ({skew*100:.1f}% premium) → Bearish sentiment, protective demand\n"
            response_text += "- High put skew indicates fear/protective demand in the market\n"
            response_text += "- Potential downside protection priced into options\n"
        elif skew < -0.05:
            response_text += f"- **Negative skew detected** ({skew*100:.1f}%) → Bullish sentiment\n"
            response_text += "- High call skew indicates bullish speculation\n"
            response_text += "- Upside expectations priced into options\n"
        else:
            response_text += f"- **Neutral skew** ({skew*100:.1f}%) → Balanced sentiment\n"
            response_text += "- Put and call IVs are relatively balanced\n"
            response_text += "- Range-bound expectations\n"
        
        response_text += f"\n**Data Source**: {data_source} | **Timestamp**: Real-time"
        
        return self.build_response(
            response_text=response_text,
            source="options_handler",
            response_type="options_analysis",
            confidence=0.90 if data_source == 'real' else 0.75,
            realtime=True,
            data={
                'symbol': symbol,
                'iv_skew': skew,
                'atm_iv': atm_iv,
                'put_iv': put_iv,
                'call_iv': call_iv,
                'underlying_price': underlying_price,
                'options_data': options_data
            }
        )
    
    def _handle_iron_condor_realtime(self, text: str) -> Dict[str, Any]:
        """Handle iron condor strategy with real-time data"""
        symbol = extract_symbol(text) or 'AAPL'  # Default to AAPL
        
        # Get real-time options data
        options_data = get_options_chain(symbol, expiration_days=30)
        if not options_data:
            return None  # Fall back to static
        
        atm_iv = options_data.get('atm_iv', 0.20)
        underlying_price = options_data.get('underlying_price', 100.0)
        greeks = options_data.get('greeks', {})
        data_source = options_data.get('data_source', 'unknown')
        
        # Determine IV environment
        if atm_iv > 0.25:
            iv_env = "High (25%+)"
            iv_recommendation = "Favorable for iron condors (high IV premium)"
        elif atm_iv > 0.20:
            iv_env = "Medium-High (20-25%)"
            iv_recommendation = "Good for iron condors (elevated IV)"
        else:
            iv_env = "Low-Medium (<20%)"
            iv_recommendation = "Less favorable for iron condors (low IV premium)"
        
        response_text = f"""**Iron Condor Strategy Analysis - {symbol} (Real-Time):**

**Current Market Environment:**
- **Underlying Price**: ${underlying_price:.2f}
- **IV Environment**: {iv_env} ({atm_iv*100:.1f}% ATM IV)
- **Data Source**: {data_source}

**Strategy Setup:**
- **Structure**: Sell OTM call spread + sell OTM put spread
- **Target Expiration**: 30-45 days
- **Delta Targets**: ~15-20 delta for short strikes
- **Premium Target**: 25-33% of max risk

**Recommendation:**
{iv_recommendation}

**Risk Considerations:**
- Monitor for volatility expansion (current IV: {atm_iv*100:.1f}%)
- Adjust if price approaches short strikes (±10% move)
- Close at 50% max profit or 30 days to expiration
- Current theta: {greeks.get('theta', -0.05):.4f} (time decay benefit)

**Market Regime Check:** 
Current IV suggests {"favorable" if atm_iv > 0.20 else "less favorable"} conditions for iron condors.
"""
        
        return self.build_response(
            response_text=response_text,
            source="options_handler",
            response_type="options_strategy",
            confidence=0.85 if data_source == 'real' else 0.70,
            realtime=True,
            data={
                'symbol': symbol,
                'atm_iv': atm_iv,
                'iv_environment': iv_env,
                'underlying_price': underlying_price,
                'greeks': greeks,
                'options_data': options_data
            }
        )
    
    def _handle_gamma_risk_realtime(self, text: str) -> Dict[str, Any]:
        """Handle gamma risk / delta neutral with real-time data"""
        symbol = extract_symbol(text) or 'SPY'
        
        # Get real-time options data
        options_data = get_options_chain(symbol)
        if not options_data:
            return None  # Fall back to static
        
        greeks = options_data.get('greeks', {})
        underlying_price = options_data.get('underlying_price', 100.0)
        atm_iv = options_data.get('atm_iv', 0.20)
        data_source = options_data.get('data_source', 'unknown')
        
        gamma = greeks.get('gamma', 0.01)
        theta = greeks.get('theta', -0.05)
        vega = greeks.get('vega', 0.15)
        delta_put = greeks.get('delta_put', -0.40)
        delta_call = greeks.get('delta_call', 0.40)
        
        # Calculate gamma risk level
        if abs(gamma) > 0.015:
            gamma_risk = "High"
            risk_advice = "Monitor delta closely, frequent rebalancing may be required"
        elif abs(gamma) > 0.010:
            gamma_risk = "Moderate"
            risk_advice = "Standard rebalancing schedule should suffice"
        else:
            gamma_risk = "Low"
            risk_advice = "Minimal delta drift, less frequent rebalancing needed"
        
        response_text = f"""**Gamma Risk in Delta-Neutral Portfolios - {symbol} (Real-Time):**

**Current Greeks:**
- **Delta (Put)**: {delta_put:.3f} | **Delta (Call)**: {delta_call:.3f}
- **Gamma**: {gamma:.4f} ({gamma_risk} risk level)
- **Theta**: {theta:.4f} (time decay)
- **Vega**: {vega:.4f} (volatility sensitivity)
- **ATM IV**: {atm_iv*100:.1f}%

**Gamma Risk Analysis:**
{risk_advice}

**Delta-Neutral Portfolio Issues:**
1. **Gamma risk**: Delta changes as price moves (current gamma: {gamma:.4f})
2. **Re-hedging cost**: Frequent rebalancing required to maintain neutrality
3. **Volatility dependency**: P&L depends on realized vs implied volatility (current IV: {atm_iv*100:.1f}%)
4. **Time decay (theta)**: Current theta: {theta:.4f} erodes option value daily

**Hedging Strategies:**
- **Gamma scalping**: Adjust delta as price moves (buy high, sell low)
  - Threshold: Rebalance when delta exceeds ±0.10
  - Current gamma: {gamma:.4f} → {"Higher rebalancing frequency" if abs(gamma) > 0.015 else "Standard frequency"}
- **Volatility hedging**: Use VIX or variance swaps if vega exposure is high (current: {vega:.4f})
- **Dynamic delta hedging**: Automated rebalancing when delta threshold exceeded
- **Calendar spreads**: Use different expirations to offset gamma

**Key Insight**: Delta-neutral doesn't mean risk-neutral. Current gamma ({gamma:.4f}) and vega ({vega:.4f}) create risk exposure.

**Data Source**: {data_source} | **Timestamp**: Real-time
"""
        
        return self.build_response(
            response_text=response_text,
            source="options_handler",
            response_type="options_greeks",
            confidence=0.92 if data_source == 'real' else 0.78,
            realtime=True,
            data={
                'symbol': symbol,
                'greeks': greeks,
                'gamma_risk': gamma_risk,
                'underlying_price': underlying_price,
                'atm_iv': atm_iv,
                'options_data': options_data
            }
        )
    
    def handle_static(self, text: str) -> Dict[str, Any]:
        """
        Fallback to static response (original implementation)
        Import and call the original function
        """
        # Import original handler
        from ...qa_engine_advanced_trading import _handle_options_question
        
        # Call original static handler
        return _handle_options_question(text)

