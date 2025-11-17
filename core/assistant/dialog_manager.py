#!/usr/bin/env python3
"""
F.A.M.E. Assistant - Dialog Manager
Session state and conversation policy
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque

# Per-session memory: ephemeral but persists across short conversations
_SESSION_STORE = {}


class Session:
    """Represents a user session with conversation history and state"""
    
    def __init__(self, session_id: str):
        self.id = session_id
        self.history = deque(maxlen=50)  # Last 50 turns
        self.slots = {}  # Filled slots (e.g., {"ticker": "AAPL"})
        self.last_active = time.time()
        self.awaiting_confirmation = None  # e.g., {'intent':..., 'payload':...}
        self.user_metadata = {}  # User preferences, name, etc.
        self.confidence_history = deque(maxlen=10)  # Track NLU confidence


def get_session(session_id: str) -> Session:
    """Get or create a session"""
    if session_id not in _SESSION_STORE:
        _SESSION_STORE[session_id] = Session(session_id)
    
    s = _SESSION_STORE[session_id]
    s.last_active = time.time()
    return s


def clear_old_sessions(timeout_seconds: int = 300):
    """Clear sessions older than timeout (default 5 minutes)"""
    current_time = time.time()
    to_remove = []
    
    for session_id, session in _SESSION_STORE.items():
        if current_time - session.last_active > timeout_seconds:
            to_remove.append(session_id)
    
    for session_id in to_remove:
        del _SESSION_STORE[session_id]


def respond_to_intent(session: Session, intent_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple policy engine: maps intents to actions
    """
    intent = intent_obj.get("intent", "unknown")
    conf = intent_obj.get("confidence", 0.0)
    slots = intent_obj.get("slots", {})
    
    # Track confidence
    session.confidence_history.append(conf)
    
    # If intent is unknown, route to brain/qa_engine instead of asking for clarification
    if intent == "unknown":
        # Get the original user text from session history
        user_text = ""
        if session.history:
            last_user_msg = [h for h in session.history if h.get("role") == "user"]
            if last_user_msg:
                user_text = last_user_msg[-1].get("content", "")
        
        # Route to brain for general knowledge questions
        return {
            "action": "execute",
            "name": "general_query",
            "payload": {"query": user_text, "text": user_text},
            "text": "Let me find that information for you...",
            "confirmed": True
        }
    
    # If confidence low but intent is known, ask clarifying question
    if conf < 0.5:
        return {
            "action": "ask_clarify",
            "text": "I didn't catch that. Could you rephrase or provide more details?",
            "confirmed": False
        }
    
    # Basic dispatch by intent
    if intent == "get_stock_price":
        if not slots.get("ticker"):
            return {
                "action": "ask_slot",
                "slot": "ticker",
                "text": "Which ticker do you mean? e.g. AAPL, MSFT, TSLA",
                "confirmed": False
            }
        return {
            "action": "execute",
            "name": "get_stock_price",
            "payload": slots,
            "text": f"Fetching price for {slots.get('ticker')}...",
            "confirmed": True
        }
    
    if intent == "get_crypto_price":
        if not slots.get("ticker"):
            return {
                "action": "ask_slot",
                "slot": "ticker",
                "text": "Which crypto ticker? e.g. BTC, ETH, XRP",
                "confirmed": False
            }
        return {
            "action": "execute",
            "name": "get_crypto_price",
            "payload": slots,
            "text": f"Pulling premium data for {slots.get('ticker')}...",
            "confirmed": True
        }

    if intent == "get_date":
        from datetime import datetime
        d = datetime.now().strftime("%A, %B %d, %Y")
        return {
            "action": "reply",
            "text": f"Today's date is {d}.",
            "confirmed": True
        }
    
    if intent == "get_time":
        from datetime import datetime
        t = datetime.now().strftime("%I:%M %p")
        return {
            "action": "reply",
            "text": f"The current time is {t}.",
            "confirmed": True
        }
    
    if intent == "greet":
        name = session.user_metadata.get('name', '')
        greeting = f"Hello {name}, " if name else "Hello, "
        greeting += "how can I help you today?"
        return {
            "action": "reply",
            "text": greeting,
            "confirmed": True
        }
    
    if intent == "set_name":
        name = slots.get("name")
        if name:
            session.user_metadata['name'] = name
            return {
                "action": "reply",
                "text": f"Nice to meet you, {name}. I'll remember that.",
                "confirmed": True
            }
        else:
            return {
                "action": "ask_slot",
                "slot": "name",
                "text": "What name should I call you?",
                "confirmed": False
            }
    
    if intent == "analyze_market":
        return {
            "action": "execute",
            "name": "analyze_market",
            "payload": {},
            "text": "Analyzing market conditions...",
            "confirmed": True
        }
    
    # Handle general queries and factual questions
    if intent in ["general_query", "factual_question"]:
        user_text = ""
        if session.history:
            last_user_msg = [h for h in session.history if h.get("role") == "user"]
            if last_user_msg:
                user_text = last_user_msg[-1].get("content", "")
        
        # Route to brain for web search / knowledge base lookup
        return {
            "action": "execute",
            "name": "general_query",
            "payload": {"query": user_text, "text": user_text, "intent": intent},
            "text": "Let me find that information for you...",
            "confirmed": True
        }
    
    # Unknown intent - should not reach here if we handled it above
    # But as fallback, route to brain
    user_text = ""
    if session.history:
        last_user_msg = [h for h in session.history if h.get("role") == "user"]
        if last_user_msg:
            user_text = last_user_msg[-1].get("content", "")
    
    return {
        "action": "execute",
        "name": "general_query",
        "payload": {"query": user_text, "text": user_text},
        "text": "Let me find that information for you...",
        "confirmed": True
    }


def add_to_history(session: Session, role: str, content: str):
    """Add a turn to conversation history"""
    session.history.append({
        "role": role,
        "content": content,
        "timestamp": time.time()
    })


def get_context(session: Session, max_turns: int = 5) -> list:
    """Get recent conversation context"""
    return list(session.history[-max_turns:])

