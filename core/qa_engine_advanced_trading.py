#!/usr/bin/env python3
"""
FAME Advanced Trading Question Handlers - CONCEPTUAL ONLY (Tier 3)
Handles sophisticated trading/hedge fund questions
TIER 3: Conceptual/Educational - NO NUMBERS, NO FAKE DATA
Only explains frameworks, theories, and strategies
"""

import logging
from typing import Dict, Any, Optional, List
import re
import asyncio

logger = logging.getLogger(__name__)


async def handle_advanced_trading_question_conceptual(text: str) -> Dict[str, Any]:
    """
    Tier 3: Conceptual handler - ONLY explains concepts
    NO specific numbers, NO fake data, NO examples with values
    Only returns when question is asking for understanding, not calculations
    """
    try:
        text_lower = text.lower()
        
        # Check if question is asking for specific calculation
        calculation_keywords = ['calculate', 'what is the', 'how much', "what's the", 'current', 'right now', 'today', 'show me', 'give me']
        is_calculation_request = any(kw in text_lower for kw in calculation_keywords)
        
        if is_calculation_request:
            return {
                "response": "Unable to provide specific calculation without real-time or cached market data. Real-time data feeds are currently unavailable and no cached data exists. Would you like me to explain the concept instead?",
                "source": "conceptual_handler",
                "type": "error",
                "confidence": 0.0,
                "realtime": False,
                "degraded": False
            }
        
        # Route to conceptual handlers (theory only, no numbers)
        if any(kw in text_lower for kw in ['option', 'iv', 'gamma', 'delta', 'iron condor', 'implied volatility']):
            return _handle_options_conceptual(text)
        
        elif any(kw in text_lower for kw in ['var', 'value at risk', 'sharpe', 'sortino', 'risk metric']):
            return _handle_risk_metrics_conceptual(text)
        
        elif any(kw in text_lower for kw in ['kelly', 'markowitz', 'position sizing', 'portfolio optimization']):
            return _handle_portfolio_conceptual(text)
        
        elif any(kw in text_lower for kw in ['microstructure', 'bid-ask', 'spread', 'order flow']):
            return _handle_microstructure_conceptual(text)
        
        elif any(kw in text_lower for kw in ['technical', 'rsi', 'bollinger', 'divergence']):
            return _handle_technical_conceptual(text)
        
        elif any(kw in text_lower for kw in ['fundamental', 'dcf', 'ev/ebitda', 'valuation']):
            return _handle_fundamental_conceptual(text)
        
        elif any(kw in text_lower for kw in ['macro', 'fed', 'yield curve', 'sector rotation']):
            return _handle_macro_conceptual(text)
        
        elif any(kw in text_lower for kw in ['crypto', 'whale', 'exchange flow', 'mvrv', 'on-chain']):
            return _handle_crypto_conceptual(text)
        
        elif any(kw in text_lower for kw in ['vix', 'volatility', 'arbitrage']):
            return _handle_volatility_conceptual(text)
        
        elif any(kw in text_lower for kw in ['regime', 'bull market', 'bear market']):
            return _handle_regime_conceptual(text)
        
        elif any(kw in text_lower for kw in ['pairs', 'arbitrage']):
            return _handle_arbitrage_conceptual(text)
        
        # Generic conceptual response
        return {
            "response": """I can explain advanced trading concepts including:

- Options strategies (IV skew, iron condor, gamma risk)
- Risk metrics (VaR, Sharpe, Sortino, correlation)
- Market microstructure (spreads, order flow, HFT)
- Technical analysis (RSI divergence, Bollinger squeeze, Wyckoff)
- Fundamental analysis (DCF, EV/EBITDA, FCF yield)
- Macro analysis (Fed policy, yield curve, sector rotation)
- Crypto analysis (whales, exchange flows, MVRV)
- Volatility trading (VIX strategies, volatility arbitrage)
- Market regimes (bull, bear, sideways)
- Arbitrage (pairs trading, statistical arbitrage)
- Portfolio optimization (Kelly Criterion, Markowitz)

For specific calculations or current market data, real-time or cached data is required.

Please ask a conceptual question about trading theory or strategy.""",
            "source": "conceptual_handler",
            "type": "general",
            "confidence": 0.75,
            "realtime": False,
            "degraded": False
        }
    except Exception as e:
        logger.error(f"Error handling conceptual question: {e}", exc_info=True)
        return {
            "response": f"Error processing question: {str(e)}",
            "source": "conceptual_handler",
            "type": "error",
            "confidence": 0.0
        }


def _handle_options_conceptual(text: str) -> Dict[str, Any]:
    """Explain options concepts - NO NUMBERS"""
    text_lower = text.lower()
    
    if 'iv skew' in text_lower or 'implied volatility' in text_lower:
        return {
            "response": """**Implied Volatility Skew - Conceptual Framework:**

IV skew measures the difference in implied volatility between out-of-the-money puts and out-of-the-money calls.

**Calculation Method:**
1. Extract ATM implied volatility from options chain
2. Compare OTM put IV vs OTM call IV
3. Calculate skew ratio: (Put IV - Call IV) / ATM IV

**Interpretation:**
- Positive skew (puts > calls): Bearish sentiment, protective demand in the market
- Negative skew (calls > puts): Bullish sentiment, upside speculation
- Neutral skew (puts ≈ calls): Balanced sentiment, range-bound expectations

**Trading Implications:**
- High put skew indicates fear/protective demand
- Low call skew indicates limited upside speculation
- Skew changes reflect market sentiment shifts

**Requirements for Analysis:**
To calculate actual IV skew, real-time or cached options chain data is required. The calculation is deterministic once options chain data is available.""",
            "source": "conceptual_handler",
            "type": "options_concept",
            "confidence": 0.90,
            "realtime": False,
            "degraded": False
        }
    
    if 'iron condor' in text_lower:
        return {
            "response": """**Iron Condor Strategy - Conceptual Framework:**

An iron condor is a neutral, income-generating options strategy that profits from low volatility.

**Structure:**
- Sell OTM call spread (sell lower strike call, buy higher strike call)
- Sell OTM put spread (sell higher strike put, buy lower strike put)
- Both spreads share same expiration

**Profit/Loss Profile:**
- Max Profit: Net premium received
- Max Loss: Width of spread minus premium
- Break-even: Upper and lower strikes ± premium

**Optimal Conditions:**
- Range-bound markets (low price movement)
- Elevated implied volatility (collect higher premium)
- Sufficient time to expiration (30-45 days typical)
- Delta targets: ~15-20 delta for short strikes

**Risk Management:**
- Monitor for volatility expansion (can hurt position)
- Adjust if price approaches short strikes
- Close at 50% max profit or 30 days to expiration

**Requirements for Setup:**
To determine optimal iron condor setup, real-time options chain data with current IV levels and Greeks is required.""",
            "source": "conceptual_handler",
            "type": "options_concept",
            "confidence": 0.90,
            "realtime": False,
            "degraded": False
        }
    
    if 'gamma' in text_lower or 'delta neutral' in text_lower:
        return {
            "response": """**Gamma Risk in Delta-Neutral Portfolios - Conceptual Framework:**

Gamma measures the rate of change in delta per $1 move in the underlying asset price.

**Delta-Neutral Portfolio Challenges:**
1. Gamma risk: Delta changes as price moves, causing options to lose delta neutrality
2. Re-hedging cost: Frequent rebalancing required to maintain neutrality
3. Volatility dependency: P&L depends on realized vs implied volatility
4. Time decay (theta): Erodes option value over time

**Hedging Strategies:**
- Gamma scalping: Adjust delta as price moves (buy high, sell low)
- Volatility hedging: Use VIX or variance swaps
- Dynamic delta hedging: Rebalance when delta exceeds threshold
- Calendar spreads: Use different expirations to offset gamma

**Key Insight:**
Delta-neutral does not mean risk-neutral. Gamma, vega, and theta all create risk exposure that must be managed.

**Requirements for Analysis:**
To calculate actual gamma exposure and hedging requirements, real-time Greeks from options chain data is required.""",
            "source": "conceptual_handler",
            "type": "options_concept",
            "confidence": 0.90,
            "realtime": False,
            "degraded": False
        }
    
    return {
        "response": """**Options Trading - Conceptual Overview:**

Options trading involves complex strategies based on:

**Key Components:**
- Greeks: Delta (price sensitivity), Gamma (delta sensitivity), Theta (time decay), Vega (volatility sensitivity), Rho (interest rate sensitivity)
- Volatility: Implied (market expectation) vs Realized (actual movement)
- Strategy Types: Directional (long/short), Neutral (income-generating), Hedging
- Risk Management: Position sizing, stop losses, hedging

**Common Strategies:**
- Long/Short positions
- Spreads (vertical, horizontal, diagonal)
- Straddles/Strangles
- Iron condors, butterflies

**Requirements for Specific Analysis:**
To provide specific options analysis or recommendations, real-time or cached options chain data with current IV, Greeks, and pricing is required.""",
        "source": "conceptual_handler",
        "type": "options_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_risk_metrics_conceptual(text: str) -> Dict[str, Any]:
    """Explain risk metrics concepts - NO NUMBERS"""
    text_lower = text.lower()
    
    if 'var' in text_lower or 'value at risk' in text_lower:
        return {
            "response": """**Value at Risk (VaR) - Conceptual Framework:**

VaR measures the maximum expected loss over a time period at a specified confidence level.

**Calculation Methods:**

1. **Parametric (Variance-Covariance)**: Assumes normal distribution
   - Formula: VaR = Portfolio Value × Z-score × Portfolio Volatility × √Time
   - Z-score: 1.645 (95% confidence), 2.326 (99% confidence)
   - Requires: Portfolio weights, asset volatilities, correlations

2. **Historical Simulation**: Uses actual historical returns
   - Sort historical returns, take percentile
   - Requires: Historical return data for portfolio

3. **Monte Carlo**: Simulates thousands of scenarios
   - Generate random price paths, calculate portfolio P&L distribution
   - Requires: Statistical models for asset returns

**Key Assumptions:**
- Normal distribution (often violated in tail events)
- Constant correlations (breaks down in market crises)
- Liquidity assumptions (may not hold in stress)

**Limitations:**
- Doesn't predict tail events beyond confidence level
- Assumes normal distribution (fat tails in reality)
- Doesn't account for correlation breakdown in stress

**Requirements for Calculation:**
To calculate VaR for a specific portfolio, real-time or cached data including:
- Portfolio composition (asset weights)
- Asset volatilities
- Asset correlations
- Historical return data (for historical simulation)

The calculation is deterministic once these inputs are available.""",
            "source": "conceptual_handler",
            "type": "risk_concept",
            "confidence": 0.90,
            "realtime": False,
            "degraded": False
        }
    
    if 'sharpe' in text_lower or 'sortino' in text_lower:
        return {
            "response": """**Sharpe Ratio vs Sortino Ratio - Conceptual Framework:**

Both measure risk-adjusted return, but use different volatility measures.

**Sharpe Ratio:**
- Formula: (Return - Risk-free rate) / Standard Deviation
- Uses: Total volatility (upside + downside)
- Penalizes: Both upside and downside volatility equally
- Best for: Symmetric return distributions

**Sortino Ratio:**
- Formula: (Return - Risk-free rate) / Downside Deviation
- Uses: Only downside volatility (losses)
- Penalizes: Only downside volatility
- Best for: Asymmetric return distributions (skewed returns)

**Key Differences:**
1. Sharpe uses total volatility; Sortino uses only downside volatility
2. Sortino better for strategies with frequent small wins, rare large losses
3. Sortino typically higher than Sharpe for asymmetric strategies
4. Sharpe standard in academic contexts; Sortino preferred by practitioners for asymmetric strategies

**When to Use:**
- Sharpe: Balanced portfolios, long-only strategies, symmetric distributions
- Sortino: Options strategies, hedge funds, alternative investments, asymmetric returns

**Requirements for Calculation:**
To calculate actual Sharpe or Sortino ratios, real-time or cached portfolio return data is required. The calculations are deterministic once return series and risk-free rate are available.""",
            "source": "conceptual_handler",
            "type": "risk_concept",
            "confidence": 0.90,
            "realtime": False,
            "degraded": False
        }
    
    return {
        "response": """**Risk Metrics - Conceptual Overview:**

Risk metrics quantify portfolio risk and risk-adjusted performance.

**Common Metrics:**
- VaR (Value at Risk): Maximum expected loss
- Sharpe Ratio: Risk-adjusted return (total volatility)
- Sortino Ratio: Risk-adjusted return (downside only)
- Correlation: Relationship between assets
- Beta: Sensitivity to market movements
- Maximum Drawdown: Largest peak-to-trough decline

**Requirements for Calculation:**
To calculate specific risk metrics, real-time or cached portfolio data including positions, returns, and market data is required.""",
        "source": "conceptual_handler",
        "type": "risk_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_portfolio_conceptual(text: str) -> Dict[str, Any]:
    """Explain portfolio optimization concepts - NO NUMBERS"""
    text_lower = text.lower()
    
    if 'kelly' in text_lower and 'criterion' in text_lower:
        return {
            "response": """**Kelly Criterion - Conceptual Framework:**

Kelly Criterion calculates optimal position size to maximize long-term growth.

**Formula:**
f* = (bp - q) / b

Where:
- f* = optimal fraction of portfolio to bet
- b = odds (win/loss ratio or reward/risk ratio)
- p = win probability
- q = loss probability (1 - p)

**Interpretation:**
- Full Kelly: Optimal for maximum growth (high volatility)
- Half Kelly: Common practice, reduces volatility by 50%
- Quarter Kelly: Conservative, smoother returns

**Key Assumptions:**
- Infinite bankroll (unrealistic in practice)
- Constant edge (edge changes in real trading)
- No correlations between bets (doesn't account for portfolio correlations)
- Known win rate and odds (requires strategy performance data)

**Practical Application:**
- Use actual strategy performance (win rate, average win/loss ratio)
- Apply Kelly fraction to risk per trade (e.g., 1% of portfolio)
- Adjust for portfolio constraints and correlations
- Consider volatility targeting

**Limitations:**
- Can lead to large drawdowns with full Kelly
- Assumes edge is constant (reality: edge changes)
- Doesn't account for portfolio correlations
- Requires accurate win rate and odds (past performance)

**Requirements for Calculation:**
To calculate actual Kelly Criterion position size, real-time or cached strategy performance data is required:
- Win rate (historical performance)
- Average win/loss ratio (reward/risk)
- Current portfolio value
- Risk per trade preference

The calculation is deterministic once these inputs are available.""",
            "source": "conceptual_handler",
            "type": "portfolio_concept",
            "confidence": 0.90,
            "realtime": False,
            "degraded": False
        }
    
    if 'markowitz' in text_lower or 'mean-variance' in text_lower:
        return {
            "response": """**Markowitz Mean-Variance Optimization - Conceptual Framework:**

Modern Portfolio Theory optimizes asset allocation for risk-adjusted returns.

**Objective:**
Maximize: Expected Return - (Risk Aversion × Variance)
Subject to: Sum of weights = 1.0 (fully invested)

**Inputs Required:**
1. Expected returns for each asset
2. Covariance matrix (asset volatilities and correlations)
3. Risk aversion parameter (investor's risk tolerance)

**Output:**
- Efficient frontier: Best return for given risk level
- Optimal portfolio: Maximum Sharpe ratio portfolio
- Minimum variance portfolio: Lowest risk portfolio

**Key Assumptions:**
- Normal distribution of returns (fat tails in reality)
- Constant expected returns and correlations (they change)
- Single-period optimization (doesn't adapt)

**Limitations:**
- Sensitive to input estimates (garbage in, garbage out)
- Assumes normal distributions (fat tails in reality)
- Static optimization (doesn't adapt to market changes)
- Ignores tail risk and black swan events

**Requirements for Calculation:**
To perform Markowitz optimization, real-time or cached data is required:
- Expected returns for each asset
- Asset volatilities
- Asset correlations
- Risk aversion parameter

The optimization is deterministic once these inputs are available.""",
            "source": "conceptual_handler",
            "type": "portfolio_concept",
            "confidence": 0.90,
            "realtime": False,
            "degraded": False
        }
    
    return {
        "response": """**Portfolio Optimization - Conceptual Overview:**

Portfolio optimization aims to maximize risk-adjusted returns through asset allocation.

**Common Approaches:**
- Markowitz Mean-Variance Optimization
- Kelly Criterion (position sizing)
- Risk Parity (equal risk contribution)
- Factor-Based Allocation
- Volatility Targeting

**Requirements for Specific Optimization:**
To provide specific portfolio optimization recommendations, real-time or cached data including portfolio holdings, asset returns, volatilities, and correlations is required.""",
        "source": "conceptual_handler",
        "type": "portfolio_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_microstructure_conceptual(text: str) -> Dict[str, Any]:
    """Explain market microstructure concepts - NO NUMBERS"""
    return {
        "response": """**Market Microstructure - Conceptual Framework:**

Market microstructure studies how trading mechanisms affect price formation and market quality.

**Key Components:**

**Bid-Ask Spreads:**
- Difference between highest bid and lowest ask
- Components: Inventory risk, order processing costs, adverse selection
- Wider spreads indicate lower liquidity

**Order Flow:**
- Buy vs sell pressure imbalance
- Affects short-term price discovery
- Large imbalances can cause price gaps

**Market Making:**
- Liquidity provision by market makers
- Profit from spread, risk from inventory

**High-Frequency Trading (HFT):**
- Very fast trading using algorithms
- Provides liquidity but can create fragility
- Impacts market structure and price discovery

**Requirements for Analysis:**
To analyze specific market microstructure metrics (spreads, order flow, etc.), real-time or cached order book data and transaction data is required.""",
        "source": "conceptual_handler",
        "type": "microstructure_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_technical_conceptual(text: str) -> Dict[str, Any]:
    """Explain technical analysis concepts - NO NUMBERS"""
    return {
        "response": """**Technical Analysis - Conceptual Framework:**

Technical analysis uses price patterns and indicators to predict future price movements.

**Key Concepts:**

**Indicators:**
- RSI (Relative Strength Index): Momentum oscillator
- MACD: Trend-following momentum indicator
- Bollinger Bands: Volatility bands around moving average
- Moving Averages: Trend identification

**Patterns:**
- Divergence: Price and indicator move opposite (potential reversal signal)
- Squeezes: Low volatility periods (potential breakout signal)
- Wyckoff: Accumulation/distribution patterns

**Requirements for Analysis:**
To perform specific technical analysis, real-time or cached historical price data is required. Indicators are calculated deterministically from price history.""",
        "source": "conceptual_handler",
        "type": "technical_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_fundamental_conceptual(text: str) -> Dict[str, Any]:
    """Explain fundamental analysis concepts - NO NUMBERS"""
    return {
        "response": """**Fundamental Analysis - Conceptual Framework:**

Fundamental analysis evaluates securities by examining financial and economic factors.

**Valuation Methods:**

**DCF (Discounted Cash Flow):**
- Value = Sum of future cash flows discounted to present
- Requires: Cash flow projections, discount rate (WACC), terminal value
- Sensitive to assumptions

**EV/EBITDA:**
- Enterprise Value to EBITDA multiple
- Compares company valuation to operating earnings
- Removes impact of capital structure
- Useful for M&A and relative valuation

**Free Cash Flow Yield:**
- FCF / Market Cap
- Measures cash generation relative to valuation
- Higher yield indicates better value

**Requirements for Analysis:**
To perform specific fundamental analysis, real-time or cached financial statements, market data, and financial models are required.""",
        "source": "conceptual_handler",
        "type": "fundamental_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_macro_conceptual(text: str) -> Dict[str, Any]:
    """Explain macro analysis concepts - NO NUMBERS"""
    return {
        "response": """**Macro Analysis - Conceptual Framework:**

Macro analysis examines economy-wide factors affecting markets.

**Key Components:**

**Monetary Policy:**
- Central bank interest rate decisions
- Impact on asset valuations (discount rates)
- Yield curve implications

**Economic Indicators:**
- GDP, inflation, employment
- Sector rotation patterns
- Business cycle phases

**Sector Rotation:**
- Early cycle: Technology, Consumer Discretionary outperform
- Late cycle: Defensive sectors outperform
- Recession: Quality premium

**Requirements for Analysis:**
To provide specific macro analysis, real-time or cached economic data, Fed policy data, and yield curve data is required.""",
        "source": "conceptual_handler",
        "type": "macro_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_crypto_conceptual(text: str) -> Dict[str, Any]:
    """Explain crypto analysis concepts - NO NUMBERS"""
    return {
        "response": """**Crypto On-Chain Analysis - Conceptual Framework:**

On-chain analysis examines blockchain data to understand market dynamics.

**Key Metrics:**

**Whale Transactions:**
- Large transactions (typically >$1M)
- Exchange deposits (potential selling pressure)
- Exchange withdrawals (accumulation signal)

**Exchange Flows:**
- Net inflow: Potential selling pressure
- Net outflow: Accumulation (bullish)

**MVRV (Market Value to Realized Value):**
- Ratio: Market Cap / Realized Cap
- Measures if price is above/below average cost basis
- High MVRV: Overvalued, potential top
- Low MVRV: Undervalued, potential bottom

**Requirements for Analysis:**
To perform specific on-chain analysis, real-time or cached blockchain transaction data and exchange wallet data is required.""",
        "source": "conceptual_handler",
        "type": "crypto_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_volatility_conceptual(text: str) -> Dict[str, Any]:
    """Explain volatility trading concepts - NO NUMBERS"""
    return {
        "response": """**Volatility Trading - Conceptual Framework:**

Volatility trading exploits mispricing between implied and realized volatility.

**Key Concepts:**

**VIX:**
- 30-day implied volatility index
- Mean-reverting (tends to revert to ~15-20)
- Spikes during market stress

**Volatility Arbitrage:**
- Long volatility: Buy options when IV < RV (underpriced)
- Short volatility: Sell options when IV > RV (overpriced)
- Delta-neutral: Hedge directional risk

**Requirements for Analysis:**
To provide specific volatility trading recommendations, real-time or cached options data with IV levels, VIX data, and volatility forecasts is required.""",
        "source": "conceptual_handler",
        "type": "volatility_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_regime_conceptual(text: str) -> Dict[str, Any]:
    """Explain market regime concepts - NO NUMBERS"""
    return {
        "response": """**Market Regime Classification - Conceptual Framework:**

Market regimes characterize broad market conditions that affect trading strategies.

**Regime Types:**
- Bull Market: Sustained uptrend, higher highs/lows
- Bear Market: Sustained downtrend, lower highs/lows
- Sideways/Range-bound: Consolidation, support/resistance

**Identification Factors:**
- Trend (moving averages, ADX)
- Volatility (VIX levels)
- Breadth (advance/decline ratio)
- Sentiment (fear/greed index)

**Strategy Implications:**
- Bull Market: Growth stocks, leveraged positions
- Bear Market: Defensive stocks, cash, hedges
- Sideways: Income strategies, range trading

**Requirements for Classification:**
To classify current market regime, real-time or cached market data including price trends, volatility measures, and breadth indicators is required.""",
        "source": "conceptual_handler",
        "type": "regime_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


def _handle_arbitrage_conceptual(text: str) -> Dict[str, Any]:
    """Explain arbitrage concepts - NO NUMBERS"""
    return {
        "response": """**Arbitrage Strategies - Conceptual Framework:**

Arbitrage exploits temporary price discrepancies between related assets.

**Types:**

**Pairs Trading:**
- Trade two correlated assets
- Profit from temporary divergence
- Requires: High correlation, mean-reversion pattern

**Statistical Arbitrage:**
- Quantitative models identify mispricing
- Market-neutral strategies
- Requires: Historical data, statistical models

**Exchange Arbitrage:**
- Price differences across exchanges
- Requires: Fast execution, low transaction costs

**Requirements for Analysis:**
To identify specific arbitrage opportunities, real-time or cached price data from multiple sources, correlation data, and execution capabilities are required.""",
        "source": "conceptual_handler",
        "type": "arbitrage_concept",
        "confidence": 0.85,
        "realtime": False,
        "degraded": False
    }


# Legacy handlers - kept for backward compatibility but should be migrated
def _handle_options_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead - this returns conceptual responses only"""
    return _handle_options_conceptual(text)


def _handle_risk_metrics_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead - this returns conceptual responses only"""
    return _handle_risk_metrics_conceptual(text)


def _handle_microstructure_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_microstructure_conceptual(text)


def _handle_technical_advanced_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_technical_conceptual(text)


def _handle_fundamental_advanced_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_fundamental_conceptual(text)


def _handle_macro_advanced_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_macro_conceptual(text)


def _handle_crypto_advanced_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_crypto_conceptual(text)


def _handle_volatility_advanced_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_volatility_conceptual(text)


def _handle_regime_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_regime_conceptual(text)


def _handle_arbitrage_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_arbitrage_conceptual(text)


def _handle_portfolio_advanced_question(text: str) -> Dict[str, Any]:
    """DEPRECATED: Use conceptual handler instead"""
    return _handle_portfolio_conceptual(text)


async def handle_advanced_trading_question(
    text: str, 
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main handler for advanced trading/hedge fund questions
    Routes to specific handlers based on question type
    
    V2 Enhancement: 
    - First tries Production Handler (real-time data + Decision Engine)
    - Falls back to V2 class-based handlers (real-time data support)
    - Falls back to conceptual handlers (Tier 3 - theory only, no numbers)
    
    Args:
        text: Question text
        user_context: Optional user context (portfolio, risk_profile, session_id, etc.)
    """
    try:
        text_lower = text.lower()
        user_context = user_context or {}
        
        # Try Production Handler first (real-time data + Decision Engine integration)
        try:
            from core.qa_engine.production_trading_handler import ProductionTradingHandler
            production_handler = ProductionTradingHandler()
            production_response = await production_handler.handle_advanced_question(text, user_context)
            
            # If production handler succeeded, use it
            if production_response and (production_response.get('realtime') or production_response.get('degraded') or production_response.get('confidence', 0) > 0.5):
                logger.debug("Using production handler response")
                return production_response
        except (ImportError, AttributeError, Exception) as e:
            logger.debug(f"Production handler not available or failed: {e}, trying conceptual handlers")
        
        # Try V2 class-based handlers (with real-time data support)
        if any(kw in text_lower for kw in ['option', 'iv', 'gamma', 'delta', 'iron condor', 'straddle', 'implied volatility']):
            try:
                from core.qa_engine.handlers.options import OptionsHandlerV2
                v2_handler = OptionsHandlerV2()
                if v2_handler.can_handle(text):
                    result = v2_handler.handle(text)
                    if result and (result.get('realtime') or result.get('confidence', 0) > 0.5):
                        return result
            except (ImportError, AttributeError) as e:
                logger.debug(f"V2 options handler not available: {e}, using conceptual")
        
        # Tier 3: Fall back to conceptual/educational (theory only, no numbers)
        return await handle_advanced_trading_question_conceptual(text)
        
    except Exception as e:
        logger.error(f"Error handling advanced trading question: {e}", exc_info=True)
        return {
            "response": f"Error processing advanced trading question: {str(e)}",
            "source": "advanced_trading",
            "type": "error",
            "confidence": 0.0
        }
