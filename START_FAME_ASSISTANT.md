# How to Start and Use FAME Assistant

## Quick Start

### Method 1: Interactive Chat (Easiest)

```bash
python chat_with_fame.py
```

This starts an interactive chat session where you can type questions and FAME will respond.

**Example Session:**
```
YOU: hi
FAME: Hello, how can I help you today?

YOU: what is the price of AAPL?
FAME: AAPL is trading at $270.00

YOU: whats todays date?
FAME: Today's date is Monday, November 03, 2025.

YOU: exit
FAME: Goodbye! Have a great day!
```

### Method 2: Programmatic Use

```python
from core.assistant.assistant_api import handle_text_input

# Simple question
result = handle_text_input("what is the price of AAPL?")
print(result['reply'])  # "AAPL is trading at $270.00"

# With session (remembers context)
session_id = "user_123"
result1 = handle_text_input("my name is Karl", session_id=session_id)
result2 = handle_text_input("hi", session_id=session_id)  # "Hello Karl, ..."
```

### Method 3: Via Brain Orchestrator

```python
from orchestrator.brain import Brain
import asyncio

brain = Brain()
result = await brain.handle_query({
    'text': 'what is the price of AAPL?',
    'use_assistant': True,  # Enable assistant
    'session_id': 'user_123'
})
print(result['response'])
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

### Other Queries
- General questions (will use QA engine)

## Features

- **Natural Language Understanding**: Understands various phrasings
- **Session Memory**: Remembers your name and context
- **Intent Routing**: Routes queries to appropriate FAME plugins
- **Real-time Data**: Fetches live stock prices and current date/time

## Exit

Type `exit`, `quit`, `bye`, or `goodbye` to end the conversation.

