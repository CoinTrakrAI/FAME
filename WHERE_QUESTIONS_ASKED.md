# Where Questions Are Asked to FAME

## Exact Location in Code

### Step 1: User Input
**File:** `chat_with_fame.py`  
**Line:** 28
```python
user_input = input("YOU: ").strip()
```
This is where YOU type your question.

### Step 2: Question Asked to FAME
**File:** `chat_with_fame.py`  
**Line:** 40
```python
result = handle_text_input(user_input, session_id=session_id)
```
**THIS IS WHERE THE QUESTION IS ASKED TO FAME**

### Step 3: Inside handle_text_input()
**File:** `core/assistant/assistant_api.py`  
**Line:** 16-178
```python
def handle_text_input(user_text: str, session_id: str = None, speak: bool = False):
    # user_text = "what is the price of AAPL?"  <-- Your question arrives here
    
    session = get_session(session_id)
    
    # Line 32: Parse intent
    intent = parse_intent(user_text)  
    # Returns: {"intent": "get_stock_price", "slots": {"ticker": "AAPL"}}
    
    # Line 35: Get policy response
    policy = respond_to_intent(session, intent)
    
    # Line 75-80: Execute action
    if policy["action"] == "execute":
        result = execute_action(policy["name"], policy["payload"])
        # Returns: {"ok": True, "text": "AAPL is trading at $270.00", ...}
    
    return {"reply": result["text"], ...}  # Response sent back
```

## Code Flow Diagram

```
chat_with_fame.py (Line 28)
    |
    | user_input = input("YOU: ")
    |
    v
chat_with_fame.py (Line 40)  <-- QUESTION ASKED HERE
    |
    | result = handle_text_input(user_input, session_id)
    |
    v
core/assistant/assistant_api.py (Line 16)
    |
    | def handle_text_input(user_text, session_id):
    |
    v
core/assistant/nlu.py (Line 32)
    |
    | intent = parse_intent(user_text)
    |
    v
core/assistant/dialog_manager.py (Line 35)
    |
    | policy = respond_to_intent(session, intent)
    |
    v
core/assistant/action_router.py (Line 75)
    |
    | result = execute_action(action_name, payload)
    |
    v
financial_integration.py or enhanced_market_oracle.py
    |
    | Gets actual stock price/data
    |
    v
Response returns back through the chain
    |
    v
chat_with_fame.py (Line 47)
    |
    | print(f"FAME: {result.get('reply')}")
    |
```

## Live Example

When you run `python chat_with_fame.py` and type "what is the price of AAPL?":

1. **Line 28** in `chat_with_fame.py`: Your input is captured
2. **Line 40** in `chat_with_fame.py`: **Question is asked to FAME here**
3. **Line 16** in `assistant_api.py`: Question enters the assistant system
4. **Line 32** in `assistant_api.py`: Intent is parsed
5. **Line 35** in `assistant_api.py`: Policy is determined
6. **Line 75** in `assistant_api.py`: Action is executed (gets stock price)
7. **Line 47** in `chat_with_fame.py`: Response is displayed

## Key Functions

- **`handle_text_input()`** - Main entry point (Line 16 in `assistant_api.py`)
- **`parse_intent()`** - Understands what you're asking (Line 32 in `assistant_api.py`)
- **`respond_to_intent()`** - Decides what to do (Line 35 in `assistant_api.py`)
- **`execute_action()`** - Actually does it (Line 75 in `assistant_api.py`)

## Summary

**The question is asked at:**
- **File:** `chat_with_fame.py`
- **Line:** 40
- **Code:** `result = handle_text_input(user_input, session_id=session_id)`

This single line triggers the entire FAME processing pipeline!

