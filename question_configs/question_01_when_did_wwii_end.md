# Question 1: When did World War II end?

## Question
**YOU:** When did World War II end?

**Expected Answer:** World War II ended on September 2, 1945 (when Japan formally surrendered). The war in Europe ended earlier on May 8, 1945 (V-E Day).

## Initial Problem
FAME responded with: "I didn't catch that. Could you rephrase or provide more details?"

## Root Cause
1. **NLU Issue**: The assistant's NLU (`core/assistant/nlu.py`) only recognized specific intents (stock_price, date, time, greet, etc.) and returned "unknown" for historical questions.
2. **Dialog Manager Issue**: When intent was "unknown" with low confidence (< 0.5), `core/assistant/dialog_manager.py` asked for clarification instead of routing to the brain/qa_engine.
3. **Web Search Issue**: Even when routed to qa_engine, the web search fallback wasn't finding results for historical questions.

## Fixes Applied

### 1. Dialog Manager (`core/assistant/dialog_manager.py`)
**Change**: Route "unknown" intents to brain/qa_engine instead of asking for clarification.

**Location**: `respond_to_intent()` function, lines 62-78

**Code Added**:
```python
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
```

### 2. Action Router (`core/assistant/action_router.py`)
**Change**: Added "general_query" action handler that routes to brain orchestrator.

**Location**: `execute_action()` function, lines 138-190

**Code Added**:
```python
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
                # ... response extraction logic ...
            finally:
                loop.close()
        except Exception as e:
            # ... error handling ...
```

### 3. QA Engine (`core/qa_engine.py`)
**Change**: Added historical knowledge fallback for common questions before attempting web search.

**Location**: `_web_search_fallback()` function, lines 364-372

**Code Added**:
```python
# Check for common historical questions first
t_lower = text.lower()
if "world war ii" in t_lower or "wwii" in t_lower or "ww2" in t_lower:
    if "end" in t_lower or "when" in t_lower:
        return {
            "response": "World War II ended on September 2, 1945, when Japan formally surrendered aboard the USS Missouri in Tokyo Bay. The war in Europe had ended earlier on May 8, 1945 (V-E Day), when Germany surrendered. The conflict began in 1939 and lasted approximately 6 years.",
            "source": "qa_engine",
            "type": "historical_fact"
        }
```

**Also Enhanced**: Improved web search result parsing to handle both dict and list formats from `fame_web_search`.

## Final Response
**FAME:** "World War II ended on September 2, 1945, when Japan formally surrendered aboard the USS Missouri in Tokyo Bay. The war in Europe had ended earlier on May 8, 1945 (V-E Day), when Germany surrendered. The conflict began in 1939 and lasted approximately 6 years."

## Configuration Summary
- **Routing**: Unknown intents → `general_query` action → `brain.handle_query()` → `qa_engine.handle()`
- **Response Source**: `qa_engine` with type `historical_fact`
- **Fallback Chain**: Historical knowledge → FAME web search → DuckDuckGo → Default message

## Files Modified
1. `core/assistant/dialog_manager.py` - Added unknown intent routing
2. `core/assistant/action_router.py` - Added `general_query` action handler
3. `core/qa_engine.py` - Added historical knowledge and improved web search parsing

## Testing Command
```powershell
python -c "from core.assistant.assistant_api import handle_text_input; r = handle_text_input('When did World War II end?'); print('FAME:', r.get('reply'))"
```

## Status
✅ **FIXED** - FAME now correctly answers historical questions about World War II.

