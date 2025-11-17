#!/usr/bin/env python3
"""
F.A.M.E. Assistant - Action Router
Safely maps intents to plugin/function calls
"""

from typing import Dict, Any
import traceback
import logging
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_action(action_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an action by name with payload.
    Maps intents to FAME plugin calls safely.
    """
    try:
        from services.premium_price_service import premium_price_service

        if action_name == "get_stock_price":
            ticker = payload.get("ticker", "").upper()
            if not ticker:
                return {"ok": False, "text": "No ticker symbol provided", "data": {}}
            
            premium_quote = premium_price_service.get_price(ticker)
            if premium_quote:
                text = premium_quote.get("text", "")
                data = {k: v for k, v in premium_quote.items() if k != "text"}
                if text:
                    return {"ok": True, "text": text, "data": data}

            # Try financial_integration first
            try:
                from financial_integration import get_price_for_ticker
                price = get_price_for_ticker(ticker)
                if price > 0:
                    return {
                        "ok": True,
                        "text": f"{ticker} is trading at ${price:.2f}",
                        "data": {"ticker": ticker, "price": price}
                    }
            except ImportError:
                pass
            
            # Try enhanced_market_oracle
            try:
                from core.enhanced_market_oracle import EnhancedMarketOracle
                
                async def get_market_data():
                    async with EnhancedMarketOracle() as oracle:
                        return await oracle.get_enhanced_market_analysis(ticker)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(get_market_data())
                    if result and 'current_price' in result:
                        price = result['current_price']
                        return {
                            "ok": True,
                            "text": f"{ticker} is trading at ${price:.2f}",
                            "data": {"ticker": ticker, "price": price, "full_analysis": result}
                        }
                finally:
                    loop.close()
            except Exception as e:
                logger.debug(f"Enhanced market oracle error: {e}")
            
            # Fallback to yfinance if available
            try:
                import yfinance as yf
                stock = yf.Ticker(ticker)
                info = stock.info
                if 'currentPrice' in info:
                    price = float(info['currentPrice'])
                    return {
                        "ok": True,
                        "text": f"{ticker} is trading at ${price:.2f}",
                        "data": {"ticker": ticker, "price": price}
                    }
                elif 'regularMarketPrice' in info:
                    price = float(info['regularMarketPrice'])
                    return {
                        "ok": True,
                        "text": f"{ticker} is trading at ${price:.2f}",
                        "data": {"ticker": ticker, "price": price}
                    }
            except Exception as e:
                logger.debug(f"yfinance error: {e}")
            
            return {
                "ok": False,
                "text": f"Could not fetch price for {ticker}. Please check the ticker symbol.",
                "data": {}
            }

        elif action_name == "get_crypto_price":
            ticker = payload.get("ticker", "").upper()
            if not ticker:
                return {"ok": False, "text": "No crypto ticker provided", "data": {}}

            # Try premium service (timeouts are handled internally at 5s per API)
            try:
                premium_quote = premium_price_service.get_price(ticker)
                if premium_quote and premium_quote.get("asset_class") == "crypto":
                    text = premium_quote.get("text", "")
                    data = {k: v for k, v in premium_quote.items() if k != "text"}
                    if text:
                        return {"ok": True, "text": text, "data": data}
            except Exception as e:
                logger.debug(f"Premium service error: {e}")

            # Fast fallback to yfinance if premium services failed
            try:
                import yfinance as yf
                symbol = f"{ticker}-USD"
                # Use fast_info for quicker response (no full history download)
                ticker_obj = yf.Ticker(symbol)
                fast_info = ticker_obj.fast_info
                if hasattr(fast_info, 'lastPrice') and fast_info.lastPrice:
                    price = float(fast_info.lastPrice)
                    return {
                        "ok": True,
                        "text": f"{ticker} (USD) is trading at ${price:.4f} [Source: yfinance]",
                        "data": {"ticker": ticker, "price": price, "source": "yfinance"},
                    }
                # Fallback to history if fast_info not available
                coin = ticker_obj.history(period="1d", interval="1m")
                if not coin.empty:
                    price = float(coin["Close"].iloc[-1])
                    return {
                        "ok": True,
                        "text": f"{ticker} (USD) is trading at ${price:.4f} [Source: yfinance]",
                        "data": {"ticker": ticker, "price": price, "source": "yfinance"},
                    }
            except Exception as exc:
                logger.debug("yfinance crypto fallback error: %s", exc)

            return {
                "ok": False,
                "text": f"Could not fetch data for {ticker}.",
                "data": {},
            }
        
        elif action_name == "analyze_market":
            # Use enhanced_market_oracle for market analysis
            try:
                from core.enhanced_market_oracle import EnhancedMarketOracle
                
                async def analyze():
                    async with EnhancedMarketOracle() as oracle:
                        # Analyze major indices
                        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
                        results = {}
                        for symbol in symbols:
                            try:
                                result = await oracle.get_enhanced_market_analysis(symbol)
                                if result:
                                    results[symbol] = result
                            except:
                                continue
                        return results
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    results = loop.run_until_complete(analyze())
                    summary = "Market Analysis:\n"
                    for symbol, data in results.items():
                        if 'current_price' in data:
                            price = data['current_price']
                            change = data.get('price_change_percent', 0)
                            summary += f"{symbol}: ${price:.2f} ({change:+.2f}%)\n"
                    
                    return {
                        "ok": True,
                        "text": summary.strip(),
                        "data": results
                    }
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Market analysis error: {e}")
                return {
                    "ok": False,
                    "text": "Could not analyze market at this time.",
                    "data": {}
                }
        
        elif action_name == "general_query":
            # Route general knowledge questions to brain/qa_engine
            query_text = payload.get("query", payload.get("text", ""))
            if query_text:
                try:
                    from orchestrator.brain import Brain
                    brain = Brain()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            brain.handle_query({"text": query_text, "source": "assistant", "use_assistant": False})
                        )
                        if isinstance(result, dict) and 'response' in result:
                            return {
                                "ok": True,
                                "text": result['response'],
                                "data": result
                            }
                        elif isinstance(result, dict):
                            # Try to extract response from nested structure
                            if 'responses' in result:
                                responses = result['responses']
                                if isinstance(responses, list) and len(responses) > 0:
                                    first = responses[0]
                                    if isinstance(first, dict) and 'result' in first:
                                        response_text = first['result'].get('response', str(first['result']))
                                        return {
                                            "ok": True,
                                            "text": response_text[:500],
                                            "data": result
                                        }
                            # Last resort: convert to string
                            return {
                                "ok": True,
                                "text": str(result)[:500],
                                "data": result
                            }
                    finally:
                        loop.close()
                except Exception as e:
                    logger.debug(f"Brain query error: {e}")
                    return {
                        "ok": False,
                        "text": f"Could not process your question: {str(e)}",
                        "data": {}
                    }
            else:
                return {
                    "ok": False,
                    "text": "No query text provided",
                    "data": {}
                }
        
        else:
            # Fallback: try to use qa_engine or brain orchestrator
            query_text = payload.get("query", payload.get("text", ""))
            if query_text:
                try:
                    from orchestrator.brain import Brain
                    brain = Brain()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            brain.handle_query({"text": query_text, "source": "assistant", "use_assistant": False})
                        )
                        if isinstance(result, dict) and 'response' in result:
                            return {
                                "ok": True,
                                "text": result['response'],
                                "data": result
                            }
                    finally:
                        loop.close()
                except Exception as e:
                    logger.debug(f"Brain fallback error: {e}")
            
            return {
                "ok": False,
                "text": f"Unknown action: {action_name}",
                "data": {}
            }
    
    except Exception as e:
        logger.exception("execute_action error")
        return {
            "ok": False,
            "text": f"Action failed: {str(e)}",
            "data": {}
        }

