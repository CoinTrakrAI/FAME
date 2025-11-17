# FAME Assistant Implementation

## Overview

Siri/Alexa-style voice assistant capabilities have been integrated into FAME. The assistant module provides:

- **Natural Language Understanding (NLU)** - Intent parsing with OpenAI or regex fallback
- **Dialog Management** - Session state, conversation history, and policy
- **Action Router** - Maps intents to FAME plugin calls
- **Audio Pipeline** - STT/TTS and wake-word detection
- **Public API** - Simple interface for integration

## File Structure

```
core/assistant/
├── __init__.py              # Module exports
├── audio_pipeline.py        # STT/TTS + wake-word
├── nlu.py                   # Intent parsing
├── dialog_manager.py        # Session state & policy
├── action_router.py         # Intent → plugin mapping
└── assistant_api.py         # Public interface
```

## Integration

### Basic Usage

```python
from core.assistant.assistant_api import handle_text_input

# Handle text input
result = handle_text_input("what is the price of AAPL?")
print(result['reply'])  # "AAPL is trading at $XXX.XX"

# With session persistence
session_id = "user_123"
result1 = handle_text_input("my name is Karl", session_id=session_id)
result2 = handle_text_input("hi", session_id=session_id)  # Remembers name
```

### Voice Input

```python
from core.assistant.assistant_api import handle_voice_input

# Listen to microphone and respond
result = handle_voice_input(session_id="user_123", speak=True)
```

### Integration with Brain Orchestrator

The assistant is integrated into `orchestrator/brain.py`. To use it, set `use_assistant=True` in queries:

```python
from orchestrator.brain import Brain

brain = Brain()
result = await brain.handle_query({
    'text': 'what is the price of AAPL?',
    'use_assistant': True,  # Use assistant API
    'session_id': 'user_123',
    'speak': False  # Optional: speak response
})
```

## Features

### Supported Intents

- `get_stock_price` - Get current stock price
- `get_date` - Get today's date
- `get_time` - Get current time
- `greet` - Greeting with name memory
- `set_name` - Remember user's name
- `analyze_market` - Market analysis

### NLU Backends

1. **Regex NLU** (default) - Fast, deterministic, works offline
2. **OpenAI NLU** - Enable with `FAME_USE_OPENAI_NLU=true` and `OPENAI_API_KEY`

### Session Management

- Automatic session creation
- Conversation history (last 50 turns)
- User metadata (name, preferences)
- Session timeout (5 minutes default)
- Slot filling across turns

### Audio Pipeline

- **STT Backends**: whisper, vosk, speech_recognition (default), google
- **TTS Backends**: pyttsx3 (default), polly, gcloud
- **Wake-word**: Text-based detection (production: use Porcupine/Snowboy)

## Configuration

Environment variables:

```bash
# NLU
FAME_USE_OPENAI_NLU=true          # Use OpenAI for NLU
FAME_NLU_MODEL=gpt-4o-mini        # OpenAI model

# Audio
FAME_STT_BACKEND=speech_recognition  # STT backend
FAME_TTS_BACKEND=pyttsx3            # TTS backend
```

## Testing

Basic test:

```python
from core.assistant.assistant_api import handle_text_input

# Test stock price
result = handle_text_input("what is the price of AAPL?")
print(result['reply'])

# Test date
result = handle_text_input("whats todays date?")
print(result['reply'])

# Test name memory
result1 = handle_text_input("my name is Karl")
session = result1['session']
result2 = handle_text_input("hi", session_id=session)
print(result2['reply'])  # "Hello Karl, how can I help you today?"
```

## Next Steps

### Production Enhancements

1. **Wake-word Detection**: Integrate Porcupine (Picovoice) for audio-level wake-word
2. **Better STT**: Use Whisper (local GPU) or OpenAI Whisper API
3. **Better TTS**: Use Amazon Polly or Google Cloud TTS
4. **Intent Training**: Add more intents and examples
5. **Multi-turn Dialogs**: Enhance dialog manager for complex workflows
6. **Confidence Thresholds**: Tune confidence levels for better accuracy

### Safety Features

- Rate limiting per session
- Audit logging for all actions
- Confirmation for destructive actions
- Kill switch integration

## Files Modified

- `financial_integration.py` - Added `get_price_for_ticker()` function
- `orchestrator/brain.py` - Integrated assistant API option

