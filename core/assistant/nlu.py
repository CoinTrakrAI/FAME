#!/usr/bin/env python3
"""
F.A.M.E. Assistant - Natural Language Understanding
Intent parsing with OpenAI or regex fallback
"""

import os
import re
import json
from typing import Dict, Any, Tuple, Optional

USE_OPENAI_FOR_NLU = os.getenv("FAME_USE_OPENAI_NLU", "false").lower() == "true"
OPENAI_MODEL = os.getenv("FAME_NLU_MODEL", "gpt-4o-mini")  # or gpt-4o-mini, gpt-4o, etc.

# Intent schema
INTENT_SCHEMA = {
    "get_stock_price": {
        "examples": ["what is the price of {ticker}", "price for {ticker}", "how much is {ticker} trading", "analyze {ticker}", "{ticker} stock price"],
        "slots": ["ticker"]
    },
    "get_crypto_price": {
        "examples": ["what is {ticker}", "price of {ticker} coin", "crypto {ticker} price", "how much is {ticker} token"],
        "slots": ["ticker"]
    },
    "get_date": {
        "examples": ["what's today's date", "what is the date", "today's date", "what day is it", "current date"]
    },
    "get_time": {
        "examples": ["what time is it", "current time", "what's the time", "time now"]
    },
    "greet": {
        "examples": ["hello", "hi", "hey", "greetings", "howdy"]
    },
    "set_name": {
        "examples": ["my name is {name}", "call me {name}", "I'm {name}"],
        "slots": ["name"]
    },
    "analyze_market": {
        "examples": ["analyze market", "market analysis", "market report", "what's happening in the market"],
        "slots": []
    },
    "general_query": {
        "examples": ["who is", "what is", "when is", "where is", "why", "how", "tell me about", "explain", "what can you do", "what are you"],
        "slots": []
    },
    "factual_question": {
        "examples": ["who is the current", "who is the president", "what is the current", "when did", "where is", "how many"],
        "slots": []
    },
    "unknown": {
        "examples": [],
        "slots": []
    }
}

CRYPTO_TICKERS = {
    'BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'DOGE', 'MATIC', 'DOT', 'AVAX',
    'LINK', 'UNI', 'BNB', 'LTC', 'BCH', 'XLM'
}

# Map common crypto names to ticker symbols
CRYPTO_NAME_MAP = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'ripple': 'XRP',
    'xrp': 'XRP',
    'cardano': 'ADA',
    'solana': 'SOL',
    'dogecoin': 'DOGE',
    'doge': 'DOGE',
    'polygon': 'MATIC',
    'matic': 'MATIC',
    'polkadot': 'DOT',
    'avalanche': 'AVAX',
    'chainlink': 'LINK',
    'uniswap': 'UNI',
    'binance coin': 'BNB',
    'bnb': 'BNB',
    'litecoin': 'LTC',
    'bitcoin cash': 'BCH',
    'stellar': 'XLM',
}


def regex_nlu(text: str) -> Dict[str, Any]:
    """
    Lightweight regex-based fallback NLU (fast, deterministic)
    """
    if not text:
        return {"intent": "unknown", "slots": {}, "confidence": 0.0}
    
    t = text.lower().strip()
    
    # FIRST: Check for crypto prediction questions - these should NOT extract tickers
    # This must come BEFORE ticker extraction to prevent false positives
    crypto_prediction_indicators = [
        'crypto prediction', 'cryptocurrency prediction', 'anticipate', 'believe', 'could reach',
        '10 years', 'long term', 'price prediction', 'forecast', 'projection', 'how much will',
        'how high will', 'reach in'
    ]
    is_crypto_prediction = any(indicator in t for indicator in crypto_prediction_indicators)
    
    # If this is a crypto prediction question, route to general_query (brain)
    if is_crypto_prediction:
        return {"intent": "unknown", "slots": {}, "confidence": 0.9}
    
    # Stock price queries - look for ticker symbols
    # Common words that match ticker pattern but aren't tickers
    common_words = {'THE', 'FOR', 'ARE', 'ALL', 'YOU', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 
                    'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'MAN', 'NEW', 'NOW', 
                    'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 
                    'SAY', 'SHE', 'TOO', 'USE', 'WHAT', 'WHEN', 'WHY', 'WITH', 'IS', 'IT',
                    'PRICE', 'STOCK', 'TRADING', 'ANALYZE', 'OF', 'THE', 'WHAT', 'WHATS', 'BASED',
                    'ON', 'IN', 'DO', 'BE', 'HAVE', 'WILL', 'ANTICIPATE', 'BELIEVE', 'REACH'}
    
    ticker = None
    # Only extract tickers for stock queries (not crypto prediction questions)
    if ("price" in t or "analyze" in t or "stock" in t):
        # Pattern 1: "price of AAPL" or "for MSFT" - look AFTER the keyword
        match = re.search(r'\b(?:price|for|of)\s+([A-Z]{2,5})\b', text.upper())
        if match:
            potential = match.group(1)
            if potential not in common_words:
                ticker = potential
        
        # Pattern 2: "$AAPL"
        if not ticker:
            match = re.search(r'\$([A-Z]{1,5})\b', text.upper())
            if match:
                potential = match.group(1)
                if potential not in common_words:
                    ticker = potential
        
        # Pattern 3: "AAPL stock" or "MSFT price" - look BEFORE the keyword
        if not ticker:
            match = re.search(r'\b([A-Z]{2,5})\s+(?:stock|price|trading)', text.upper())
            if match:
                potential = match.group(1)
                if potential not in common_words:
                    ticker = potential
        
        # Pattern 4: Standalone ticker (must be 2-5 uppercase letters, not common words)
        if not ticker:
            # Find all potential tickers, but exclude common words
            all_caps = re.findall(r'\b([A-Z]{2,5})\b', text.upper())
            for potential in all_caps:
                if potential not in common_words and len(potential) >= 2:
                    # Additional check: if it's a real ticker (common ones)
                    known_tickers = {'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA', 'INTC', 'SPY', 'QQQ'}
                    if potential in known_tickers:
                        ticker = potential
                        break
                    # Or if it's not a known word, use it
                    if potential not in common_words:
                        ticker = potential
                        break
        
        if ticker:
            return {"intent": "get_stock_price", "slots": {"ticker": ticker}, "confidence": 0.85}
    
    # "what is/what's the price of [asset]" pattern - check this BEFORE single-word extraction
    price_of_pattern = re.search(r"\b(?:what(?:'s|s| is)?|what's)\s+(?:the\s+)?price\s+of\s+([A-Za-z]+)\b", text, re.IGNORECASE)
    if price_of_pattern:
        asset_name = price_of_pattern.group(1).lower().strip()
        # Check if it's a crypto name
        if asset_name in CRYPTO_NAME_MAP:
            ticker = CRYPTO_NAME_MAP[asset_name]
            return {"intent": "get_crypto_price", "slots": {"ticker": ticker}, "confidence": 0.9}
        # Check if it's already a ticker
        asset_upper = asset_name.upper()
        if asset_upper in CRYPTO_TICKERS:
            return {"intent": "get_crypto_price", "slots": {"ticker": asset_upper}, "confidence": 0.9}
        # Could be a stock - try it as stock ticker
        if asset_upper not in common_words and len(asset_upper) >= 2:
            return {"intent": "get_stock_price", "slots": {"ticker": asset_upper}, "confidence": 0.8}
    
    # "what is/what's" price lookups for stocks or crypto (single word after "whats")
    what_match = re.search(r"\bwhat(?:'s|s| is)?\s+\$?([A-Za-z]{2,5})\b", text, re.IGNORECASE)
    if what_match:
        potential = what_match.group(1).upper()
        if potential not in common_words:
            if potential in CRYPTO_TICKERS:
                return {"intent": "get_crypto_price", "slots": {"ticker": potential}, "confidence": 0.8}
            return {"intent": "get_stock_price", "slots": {"ticker": potential}, "confidence": 0.7}

    # Check for crypto names in price queries (before company names)
    if "price" in t:
        for crypto_name, ticker in CRYPTO_NAME_MAP.items():
            if crypto_name in t:
                return {"intent": "get_crypto_price", "slots": {"ticker": ticker}, "confidence": 0.85}
    
    # Company name to ticker mapping
    company_tickers = {
        'apple': 'AAPL', 'google': 'GOOGL', 'microsoft': 'MSFT',
        'amazon': 'AMZN', 'tesla': 'TSLA', 'meta': 'META',
        'netflix': 'NFLX', 'nvidia': 'NVDA', 'intel': 'INTC'
    }
    for company, ticker in company_tickers.items():
        if company in t and ("price" in t or "analyze" in t or "stock" in t):
            return {"intent": "get_stock_price", "slots": {"ticker": ticker}, "confidence": 0.8}
    
    # Date queries
    if "date" in t or ("today" in t and "day" in t):
        return {"intent": "get_date", "slots": {}, "confidence": 0.9}
    
    # Time queries
    if "time" in t and ("what" in t or "current" in t or "now" in t):
        return {"intent": "get_time", "slots": {}, "confidence": 0.9}
    
    # Name setting
    name_match = re.search(r'\bmy name is (\w+)\b', t)
    if name_match:
        name = name_match.group(1)
        return {"intent": "set_name", "slots": {"name": name}, "confidence": 0.9}
    
    # Call me pattern
    name_match = re.search(r'\bcall me (\w+)\b', t)
    if name_match:
        name = name_match.group(1)
        return {"intent": "set_name", "slots": {"name": name}, "confidence": 0.85}
    
    # Greetings
    if t in ("hi", "hello", "hey", "greetings", "howdy") or len(t) < 3:
        return {"intent": "greet", "slots": {}, "confidence": 0.95}
    
    # Market analysis
    if "market" in t and ("analyze" in t or "analysis" in t or "report" in t):
        return {"intent": "analyze_market", "slots": {}, "confidence": 0.8}
    
    # General factual questions (who, what, when, where, why, how)
    # Handle common misspellings: "whos" -> "who is", "whos the" -> "who is the"
    t_normalized = t.replace("whos", "who is").replace("whos the", "who is the").replace("whos the", "who is")
    
    factual_indicators = ["who is", "what is", "when is", "where is", "why is", "how is", 
                         "who are", "what are", "when did", "where did", "why did", "how did",
                         "tell me about", "explain", "describe", "current president", 
                         "current time", "current date", "president", "who"]
    
    # Check normalized and original text
    check_text = t_normalized if t_normalized != t else t
    
    if any(indicator in check_text for indicator in factual_indicators):
        # Check if it's a specific factual question about president
        if ("president" in check_text) or ("who" in check_text and "president" in check_text):
            # High confidence for president questions
            return {"intent": "factual_question", "slots": {}, "confidence": 0.9}
        elif ("who is" in check_text or "who are" in check_text) and any(word in check_text for word in ["the", "current", "president"]):
            return {"intent": "factual_question", "slots": {}, "confidence": 0.85}
        elif any(q in check_text for q in ["who is", "what is", "when is", "where is", "why", "how"]):
            return {"intent": "factual_question", "slots": {}, "confidence": 0.8}
        else:
            return {"intent": "general_query", "slots": {}, "confidence": 0.75}
    
    # General queries (what can you do, what are you, etc.)
    if any(phrase in t for phrase in ["what can you", "what are you", "what do you", "how can you", 
                                       "can you help", "what is your", "tell me what"]):
        return {"intent": "general_query", "slots": {}, "confidence": 0.8}
    
    # Question words at start (likely a question)
    question_words = ["who", "what", "when", "where", "why", "how", "which", "whose"]
    first_word = t.split()[0] if t.split() else ""
    if first_word in question_words:
        return {"intent": "general_query", "slots": {}, "confidence": 0.7}
    
    # Fallback to unknown (but with lower confidence threshold for routing)
    return {"intent": "unknown", "slots": {}, "confidence": 0.3}


def openai_nlu(text: str) -> Dict[str, Any]:
    """
    OpenAI-powered NLU (recommended for complex utterances)
    """
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return regex_nlu(text)  # Fallback to regex
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""You are an intent and slot extractor. Output JSON with keys: intent (one of get_stock_price, get_date, get_time, greet, set_name, analyze_market, general_query, factual_question, unknown), slots (object), confidence (0.0-1.0).

Available intents:
- get_stock_price: Stock price queries
- get_date: Current date queries
- get_time: Current time queries
- greet: Greetings
- set_name: Setting user name
- analyze_market: Market analysis requests
- general_query: General knowledge questions (what, how, why, explain, tell me)
- factual_question: Factual questions (who is, what is, when is, current president, etc.)
- unknown: Unknown/unclear intent

Utterance: "{text}"

Output only valid JSON, no markdown formatting."""
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You extract intents and slots. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        txt = response.choices[0].message.content
        
        # Parse JSON
        try:
            j = json.loads(txt)
            return j
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'\{[^}]+\}', txt)
            if json_match:
                j = json.loads(json_match.group(0))
                return j
            return regex_nlu(text)  # Fallback
    
    except ImportError:
        return regex_nlu(text)
    except Exception as e:
        print(f"[NLU] OpenAI error: {e}")
        return regex_nlu(text)  # Fallback


def parse_intent(text: str) -> Dict[str, Any]:
    """
    Parse user intent from text. Uses OpenAI if available, otherwise regex fallback.
    """
    text = text or ""
    
    if USE_OPENAI_FOR_NLU and os.getenv("OPENAI_API_KEY"):
        out = openai_nlu(text)
    else:
        out = regex_nlu(text)
    
    # Normalize output
    out.setdefault("confidence", 0.0)
    out.setdefault("slots", {})
    out.setdefault("intent", "unknown")
    
    return out

