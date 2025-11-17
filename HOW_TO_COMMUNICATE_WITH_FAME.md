# How to Communicate with FAME

## 🎯 Quick Answer: 3 Ways to Talk to FAME

### 1. **Via API (For Frontend Apps)** ⭐ RECOMMENDED FOR INTEGRATION
### 2. **Interactive Chat (Local Testing)**
### 3. **Desktop GUI (Full Experience)**

---

## 1. API Method - Connect to Frontend Apps

### **Endpoint:** `POST /query`

**Base URL:** `http://18.220.108.23:8080` (or `http://localhost:8080` for local)

### **Request Format:**
```json
{
  "text": "What is the price of Bitcoin?",
  "session_id": "user_123",  // Optional - for conversation memory
  "source": "web_app",        // Optional - track where query came from
  "metadata": {}              // Optional - any extra data
}
```

### **Response Format:**
```json
{
  "response": "Bitcoin (BTC) is currently trading at $67,234.50...",
  "intent": "get_crypto_price",
  "confidence": 0.95,
  "session_id": "user_123",
  "metadata": {
    "ticker": "BTC",
    "price": 67234.50
  }
}
```

### **Example: JavaScript/Frontend Integration**

```javascript
// Simple fetch example
async function askFAME(question, sessionId = null) {
  const response = await fetch('http://18.220.108.23:8080/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: question,
      session_id: sessionId || `session_${Date.now()}`,
      source: 'web_app'
    })
  });
  
  const data = await response.json();
  return data;
}

// Usage
const result = await askFAME("What is the price of Apple stock?");
console.log(result.response); // FAME's answer
```

### **Example: React Component**

```jsx
import React, { useState } from 'react';

function FAME Chat() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [sessionId] = useState(`session_${Date.now()}`);

  const sendMessage = async () => {
    const res = await fetch('http://18.220.108.23:8080/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: message,
        session_id: sessionId,
        source: 'react_app'
      })
    });
    const data = await res.json();
    setResponse(data.response);
  };

  return (
    <div>
      <input 
        value={message} 
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask FAME anything..."
      />
      <button onClick={sendMessage}>Send</button>
      <div>{response}</div>
    </div>
  );
}
```

### **Example: Python Client**

```python
import requests

def ask_fame(question, session_id=None):
    url = "http://18.220.108.23:8080/query"
    payload = {
        "text": question,
        "session_id": session_id or f"session_{int(time.time())}",
        "source": "python_client"
    }
    response = requests.post(url, json=payload)
    return response.json()

# Usage
result = ask_fame("What is the price of Bitcoin?")
print(result['response'])
```

### **Test in Browser (Interactive API Docs)**

1. Go to: `http://18.220.108.23:8080/docs`
2. Click on **POST /query**
3. Click **"Try it out"**
4. Enter your question in the JSON body:
   ```json
   {
     "text": "What is the price of Bitcoin?"
   }
   ```
5. Click **"Execute"**
6. See FAME's response!

---

## 2. Interactive Chat (Local Testing)

### **Run Local Chat Interface:**

```bash
cd C:\Users\cavek\Downloads\FAME_Desktop
python chat_with_fame.py
```

### **What You'll See:**
```
======================================================================
FAME ASSISTANT - INTERACTIVE CHAT
======================================================================

Welcome! I'm FAME Assistant. I can help you with:
  • Stock prices (e.g., 'what is the price of AAPL?')
  • Crypto prices
  • Date and time queries
  • General questions

Type 'exit' or 'quit' to end the conversation
======================================================================

YOU: 
```

### **Example Conversation:**
```
YOU: hi
FAME: Hello, how can I help you today?
      [Intent: greet, Confidence: 0.95]

YOU: what is the price of Bitcoin?
FAME: Bitcoin (BTC) is currently trading at $67,234.50...
      [Intent: get_crypto_price, Confidence: 0.92]

YOU: analyze Apple stock
FAME: Analyzing AAPL...
      [Intent: analyze_stock, Confidence: 0.88]

YOU: exit
FAME: Goodbye! Have a great day!
```

---

## 3. Desktop GUI (Full Experience with Voice)

### **Run Desktop Application:**

```bash
cd C:\Users\cavek\Downloads\FAME_Desktop
python enhanced_fame_communicator.py
```

### **Features:**
- ✅ **Text Chat** - Type questions and get responses
- ✅ **Voice Input** - Speak to FAME (if microphone enabled)
- ✅ **Voice Output** - FAME speaks back (ElevenLabs TTS)
- ✅ **Business Analysis** - Stock analysis, market trends
- ✅ **Multiple Personas** - Business Expert, Technical Advisor, Strategic Thinker

### **Tabs Available:**
1. **Voice Chat** - Real-time voice conversation
2. **Text Chat** - Traditional chat interface
3. **Business Analysis** - Market analysis tools
4. **System Status** - FAME's current state

---

## 🧠 Training FAME

### **Method 1: Historical Data Training**

```bash
cd C:\Users\cavek\Downloads\FAME_Desktop
python training/historical_training_orchestrator.py
```

This trains FAME using:
- yfinance data
- Alpha Vantage data
- Finnhub data
- CoinGecko data
- Google AI enhancements

### **Method 2: Interactive Learning**

FAME learns from conversations. Just chat with it:

```bash
python chat_with_fame.py
```

Ask questions, and FAME will:
- Remember your preferences
- Learn from context
- Improve responses over time

### **Method 3: Living System Training**

FAME's "Living System" continuously learns:

```python
from core.living_system import FAMELivingSystem

fame = FAMELivingSystem()
# FAME automatically:
# - Stores experiences in memory
# - Extracts skills from interactions
# - Adapts behavior based on goals
# - Self-heals when issues detected
```

---

## 📊 Example Questions to Test FAME

### **Financial Queries:**
- "What is the price of Bitcoin?"
- "Analyze Apple stock"
- "What's happening with Tesla today?"
- "Show me crypto market trends"
- "Compare AAPL and MSFT"

### **General Questions:**
- "What's today's date?"
- "What time is it?"
- "Tell me about AI trends"
- "Explain quantum computing"

### **Business Intelligence:**
- "What are the market trends?"
- "Analyze the competitive landscape"
- "What are investment opportunities?"
- "Assess market risks"

---

## 🔌 Frontend Integration Examples

### **Simple HTML/JavaScript:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>FAME Chat</title>
</head>
<body>
    <div id="chat">
        <div id="messages"></div>
        <input type="text" id="input" placeholder="Ask FAME...">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        const FAME_API = 'http://18.220.108.23:8080/query';
        let sessionId = `session_${Date.now()}`;

        async function sendMessage() {
            const input = document.getElementById('input');
            const messages = document.getElementById('messages');
            const question = input.value;
            
            if (!question) return;
            
            // Add user message
            messages.innerHTML += `<div><strong>You:</strong> ${question}</div>`;
            input.value = '';
            
            // Get FAME's response
            const response = await fetch(FAME_API, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: question,
                    session_id: sessionId
                })
            });
            
            const data = await response.json();
            messages.innerHTML += `<div><strong>FAME:</strong> ${data.response}</div>`;
        }
        
        // Send on Enter key
        document.getElementById('input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

### **Vue.js Component:**

```vue
<template>
  <div class="fame-chat">
    <div v-for="msg in messages" :key="msg.id">
      <strong>{{ msg.sender }}:</strong> {{ msg.text }}
    </div>
    <input v-model="input" @keyup.enter="send" placeholder="Ask FAME...">
    <button @click="send">Send</button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      input: '',
      messages: [],
      sessionId: `session_${Date.now()}`
    }
  },
  methods: {
    async send() {
      if (!this.input) return;
      
      this.messages.push({ id: Date.now(), sender: 'You', text: this.input });
      const question = this.input;
      this.input = '';
      
      const res = await fetch('http://18.220.108.23:8080/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: question,
          session_id: this.sessionId
        })
      });
      
      const data = await res.json();
      this.messages.push({ 
        id: Date.now(), 
        sender: 'FAME', 
        text: data.response 
      });
    }
  }
}
</script>
```

---

## 🎯 Quick Test Commands

### **Test via API (curl):**
```bash
curl -X POST http://18.220.108.23:8080/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the price of Bitcoin?"}'
```

### **Test via Python:**
```python
import requests
response = requests.post(
    'http://18.220.108.23:8080/query',
    json={'text': 'What is the price of Bitcoin?'}
)
print(response.json()['response'])
```

### **Test via Browser:**
1. Open: `http://18.220.108.23:8080/docs`
2. Click **POST /query** → **Try it out**
3. Enter: `{"text": "What is the price of Bitcoin?"}`
4. Click **Execute**

---

## 📝 Session Management

FAME remembers context within a session:

```javascript
// Create a session
const sessionId = 'user_karl_123';

// First message
await askFAME("My name is Karl", sessionId);

// Second message (FAME remembers your name)
const response = await askFAME("What's my name?", sessionId);
// Response: "Your name is Karl"
```

---

## 🚀 Next Steps

1. **Test FAME Now:**
   - Go to `http://18.220.108.23:8080/docs` and try the `/query` endpoint

2. **Build Your Frontend:**
   - Use the JavaScript examples above
   - Connect to `http://18.220.108.23:8080/query`

3. **Train FAME:**
   - Run `python training/historical_training_orchestrator.py`
   - Chat with FAME to improve its knowledge

4. **Monitor FAME:**
   - Health: `http://18.220.108.23:8080/healthz`
   - Status: `http://18.220.108.23:8080/readyz`

---

## 📚 API Documentation

Full interactive docs: `http://18.220.108.23:8080/docs`

Endpoints:
- `POST /query` - Ask FAME questions
- `GET /healthz` - Check system health
- `GET /readyz` - Check readiness status

