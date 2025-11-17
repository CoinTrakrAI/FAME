# How to Ask FAME Questions

## Method 1: Interactive Chat (Easiest)

### Start the Chat Interface

```bash
cd C:\Users\cavek\Downloads\FAME_Desktop
python chat_with_fame.py
```

### What You'll See

```
======================================================================
FAME ASSISTANT - INTERACTIVE CHAT
======================================================================

Welcome! I'm FAME Assistant. I can help you with:
  • Stock prices (e.g., 'what is the price of AAPL?')
  • Date and time queries
  • General questions

Type 'exit' or 'quit' to end the conversation
======================================================================

YOU: 
```

### Example Conversation

```
YOU: hi
FAME: Hello, how can I help you today?
      [Intent: greet, Confidence: 0.95]

YOU: what is the price of AAPL?
FAME: AAPL is trading at $270.00
      [Intent: get_stock_price, Confidence: 0.85]

YOU: whats todays date?
FAME: Today's date is Monday, November 03, 2025.
      [Intent: get_date, Confidence: 0.90]

YOU: exit
FAME: Goodbye! Have a great day!
```

## Method 2: Programmatic Use

### Simple Question

```python
from core.assistant.assistant_api import handle_text_input

result = handle_text_input("what is the price of AAPL?")
print(result['reply'])  # "AAPL is trading at $270.00"
print(result['intent'])  # "get_stock_price"
```

### With Session (Remembers Context)

```python
from core.assistant.assistant_api import handle_text_input

session_id = "user_123"

# First question
result1 = handle_text_input("my name is Karl", session_id=session_id)
print(result1['reply'])  # "Nice to meet you, karl. I'll remember that."

# Second question (remembers name)
result2 = handle_text_input("hi", session_id=session_id)
print(result2['reply'])  # "Hello karl, how can I help you today?"
```

## Method 3: Via Brain Orchestrator

```python
from orchestrator.brain import Brain
import asyncio

async def ask_fame():
    brain = Brain()
    
    result = await brain.handle_query({
        'text': 'what is the price of AAPL?',
        'use_assistant': True,  # Enable assistant API
        'session_id': 'user_123'
    })
    
    print(result['response'])  # "AAPL is trading at $270.00"
    print(result['intent'])    # "get_stock_price"

asyncio.run(ask_fame())
```

## What You Can Ask

### Stock Prices
- "what is the price of AAPL?"
- "price for MSFT"
- "how much is TSLA trading at?"
- "analyze Apple stock"

### Date & Time
- "whats todays date?"
- "what time is it?"
- "current date"

### Personalization
- "my name is Karl" (FAME will remember)
- "hi" (will use your name if remembered)

### General Questions
- Any question (will use QA engine)

## Response Format

Every response includes:
- `reply`: The text response from FAME
- `intent`: The detected intent (e.g., "get_stock_price", "get_date", "greet")
- `confidence`: Confidence score (0.0-1.0)
- `session`: Session ID for context
- `data`: Optional data (e.g., stock price info)

## Example Response

```python
{
    'session': '2cc6eea5-079f-4722-a5e7-f0544a4fa346',
    'reply': 'AAPL is trading at $270.00',
    'intent': 'get_stock_price',
    'confidence': 0.85,
    'data': {
        'ticker': 'AAPL',
        'price': 269.9995
    }
}
```

## Exit

In interactive mode, type:
- `exit`
- `quit`
- `bye`
- `goodbye`

## Files

- `chat_with_fame.py` - Interactive chat interface
- `core/assistant/assistant_api.py` - Programmatic API
- `orchestrator/brain.py` - Brain orchestrator integration

