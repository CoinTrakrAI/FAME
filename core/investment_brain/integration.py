#!/usr/bin/env python3
"""
FAME Investment Brain - Integration Layer
Wires Investment Brain into FAME's query processing
"""

import logging
from typing import Dict, Any, Optional
from .decision_engine import get_investment_brain
from .models import InvestmentContext

logger = logging.getLogger(__name__)


def enhance_financial_response(symbol: str, asset_type: str, price_data: Dict[str, Any],
                              query_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhance financial price response with Investment Brain analysis
    
    Args:
        symbol: Asset symbol
        asset_type: "stock" or "crypto"
        price_data: Price data from market APIs
        query_text: Original query text
    
    Returns:
        Enhanced response dict with investment analysis
    """
    try:
        # Get Investment Brain decision
        brain = get_investment_brain()
        current_price = price_data.get('price') or price_data.get('price_usd')
        
        context = brain.make_decision(
            symbol=symbol,
            asset_type=asset_type,
            current_price=current_price,
            context={'query_text': query_text}
        )
        
        # Build enhanced response
        base_response = price_data.get('response', f"{symbol} price: ${current_price}")
        
        # Add Investment Brain insights
        investment_insight = format_investment_analysis(context)
        
        enhanced_response = f"{base_response}\n\n{investment_insight}"
        
        return {
            'response': enhanced_response,
            'source': 'investment_brain',
            'type': 'investment_analysis',
            'confidence': abs(context.decision.conviction_score) / 10.0,
            'data': {
                'price_data': price_data,
                'investment_context': context_to_dict(context)
            },
            'decision': context.decision.decision,
            'conviction': context.decision.conviction_score,
            'reward_risk_ratio': context.decision.reward_risk_ratio
        }
    except Exception as e:
        logger.error(f"Error enhancing financial response with Investment Brain: {e}", exc_info=True)
        # Return original response on error
        return price_data


def format_investment_analysis(context: InvestmentContext) -> str:
    """Format Investment Brain analysis into readable text"""
    decision = context.decision
    
    analysis_parts = []
    
    # Decision
    analysis_parts.append(f"**Investment Analysis: {context.symbol}**")
    analysis_parts.append(f"**Decision:** {decision.decision}")
    
    # Conviction
    if abs(decision.conviction_score) > 5:
        analysis_parts.append(f"**Conviction:** {decision.conviction_score:.1f}/10 ({'Strong' if abs(decision.conviction_score) > 7 else 'Moderate'})")
    
    # Reward/Risk
    if decision.reward_risk_ratio > 2.0:
        analysis_parts.append(f"**Reward/Risk:** {decision.reward_risk_ratio:.2f}:1 (Favorable)")
    elif decision.reward_risk_ratio < 1.5:
        analysis_parts.append(f"**Reward/Risk:** {decision.reward_risk_ratio:.2f}:1 (Unfavorable)")
    
    # Position size if BUY
    if decision.decision == "BUY" and decision.position_size:
        analysis_parts.append(f"**Suggested Position:** {decision.position_size*100:.1f}% of portfolio")
    
    # Key factors
    if context.asset_eval.fundamentals > 7:
        analysis_parts.append("[STRONG] Strong fundamentals")
    if context.asset_eval.technicals > 7:
        analysis_parts.append("[STRONG] Strong technical setup")
    if context.asset_eval.risk_factors > 7:
        analysis_parts.append("[WARNING] High risk factors")
    
    # Reasoning
    if decision.reasoning:
        analysis_parts.append(f"**Reasoning:** {decision.reasoning}")
    
    # Exit triggers if active
    if context.exit_triggers.should_exit():
        active_triggers = [
            k for k, v in context.exit_triggers.__dict__.items() 
            if v and k != 'should_exit'
        ]
        if active_triggers:
            analysis_parts.append(f"[WARNING] **Exit Triggers Active:** {', '.join(active_triggers)}")
    
    return "\n".join(analysis_parts)


def context_to_dict(context: InvestmentContext) -> Dict[str, Any]:
    """Convert InvestmentContext to dict for serialization"""
    return {
        'symbol': context.symbol,
        'asset_type': context.asset_type,
        'timestamp': context.timestamp,
        'decision': {
            'decision': context.decision.decision,
            'conviction': context.decision.conviction_score,
            'reward_risk_ratio': context.decision.reward_risk_ratio,
            'position_size': context.decision.position_size,
            'reasoning': context.decision.reasoning
        },
        'market_env': {
            'macro_trend': context.market_env.macro_trend,
            'volatility': context.market_env.volatility,
            'sector_strength': context.market_env.sector_strength,
            'liquidity': context.market_env.liquidity,
            'sentiment': context.market_env.sentiment
        },
        'asset_eval': {
            'fundamentals': context.asset_eval.fundamentals,
            'technicals': context.asset_eval.technicals,
            'narrative': context.asset_eval.narrative,
            'catalysts': context.asset_eval.catalysts,
            'competition': context.asset_eval.competition,
            'smart_money_flow': context.asset_eval.smart_money_flow,
            'risk_factors': context.asset_eval.risk_factors
        },
        'timing': {
            'trend_strength': context.timing.trend_strength,
            'entry_confirmation': context.timing.entry_confirmation,
            'breakout_probability': context.timing.breakout_probability,
            'momentum_strength': context.timing.momentum_strength,
            'reward_risk_ratio': context.timing.reward_risk_ratio
        },
        'exit_triggers': {
            k: v for k, v in context.exit_triggers.__dict__.items()
            if not callable(v)
        },
        'current_price': context.current_price,
        'target_price': context.target_price,
        'stop_loss': context.stop_loss
    }


def should_use_investment_brain(query_text: str) -> bool:
    """
    Determine if query should use Investment Brain analysis
    
    Investment Brain is used for:
    - Investment advice queries
    - Analysis requests
    - Decision requests (should I buy/sell/hold)
    - Strategic queries
    """
    if not query_text:
        return False
    
    query_lower = query_text.lower()
    
    # Investment-related keywords
    investment_keywords = [
        'should i', 'buy or sell', 'invest in', 'analysis', 'analysis',
        'evaluate', 'assess', 'recommendation', 'advice', 'strategy',
        'conviction', 'risk', 'reward', 'position', 'portfolio',
        'timing', 'entry', 'exit', 'hold', 'trade'
    ]
    
    return any(keyword in query_lower for keyword in investment_keywords)

