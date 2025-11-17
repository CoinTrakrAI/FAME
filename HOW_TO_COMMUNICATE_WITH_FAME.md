# How to Communicate with FAME AGI

## 🎯 Quick Answer: Multiple Ways to Talk to FAME

FAME now has **enhanced AGI capabilities** with multiple communication methods:

### 1. **REST API** (Recommended for Integration) ⭐
### 2. **WebSocket** (Real-time Communication) 🆕
### 3. **Streaming API** (Server-Sent Events) 🆕
### 4. **Interactive Chat** (Local Testing)
### 5. **Desktop GUI** (Full Experience with Voice)

---

## 1. REST API - Standard HTTP Requests

### **Base URL:** 
- **AWS EC2:** `http://18.220.108.23:8080`
- **Local:** `http://localhost:8080`

### **Main Endpoint:** `POST /query`

**Request:**
```json
{
  "text": "What is the price of Bitcoin?",
  "session_id": "user_123",  // Optional - for conversation memory
  "source": "web_app"         // Optional
}
```

**Response:**
```json
{
  "response": "Bitcoin (BTC) is currently trading at...",
  "confidence": 0.95,
  "sources": ["web", "knowledge"],
  "breakdown": [...],
  "metrics": {...}
}
```

### **Enhanced AGI Endpoints** (New!):

#### `POST /ask` - Full AGI Pipeline
```json
{
  "prompt": "Analyze Apple stock comprehensively",
  "context": [],
  "stream": false
}
```

Returns full AGI response with:
- Planning information
- Task results
- Audit report
- Confidence scores

#### `GET /health` - System Health
```bash
curl http://18.220.108.23:8080/health
```

#### `GET /metrics` - Performance Metrics
```bash
curl http://18.220.108.23:8080/metrics
```

#### `POST /plan` - Create Execution Plan
```json
{
  "goal": "Research renewable energy investments",
  "parameters": {}
}
```

#### `GET /plan/{plan_id}` - Get Plan Status
```bash
curl http://18.220.108.23:8080/plan/plan_abc123
```

#### `POST /feedback` - Submit Learning Feedback
```json
{
  "query": "previous query",
  "response_id": "response_id",
  "reward": 0.8,
  "tone_preference": "professional"
}
```

#### `GET /persona` - Get Persona Profile
```bash
curl http://18.220.108.23:8080/persona
```

#### `POST /persona` - Update Persona
```json
{
  "tone": "friendly",
  "verbosity": "high"
}
```

#### `POST /memory/wipe` - Wipe Memory (with confirmation)
```bash
curl -X POST "http://18.220.108.23:8080/memory/wipe?confirm=true"
```

#### `POST /memory/rebuild` - Rebuild Vector Store
```bash
curl -X POST http://18.220.108.23:8080/memory/rebuild
```

---

## 2. WebSocket - Real-Time Communication 🆕

### **Endpoint:** `ws://18.220.108.23:8080/ws`

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://18.220.108.23:8080/ws');

ws.onopen = () => {
  console.log('Connected to FAME');
  
  // Send query
  ws.send(JSON.stringify({
    type: 'query',
    prompt: 'What is the price of Bitcoin?',
    context: []
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'response') {
    console.log('FAME:', data.response);
    console.log('Confidence:', data.confidence);
    console.log('Sources:', data.sources);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

**Python Example:**
```python
import asyncio
import websockets
import json

async def chat_with_fame():
    uri = "ws://18.220.108.23:8080/ws"
    async with websockets.connect(uri) as websocket:
        # Send query
        await websocket.send(json.dumps({
            "type": "query",
            "prompt": "What is the price of Bitcoin?",
            "context": []
        }))
        
        # Receive response
        response = await websocket.recv()
        data = json.loads(response)
        print("FAME:", data["response"])

asyncio.run(chat_with_fame())
```

---

## 3. Streaming API - Server-Sent Events 🆕

### **Endpoint:** `POST /ask` with `stream: true`

**JavaScript Example:**
```javascript
async function streamFromFAME(prompt) {
  const response = await fetch('http://18.220.108.23:8080/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: prompt,
      stream: true
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        console.log('Token:', data.token);
        
        if (data.done) {
          console.log('Complete! Confidence:', data.confidence);
        }
      }
    }
  }
}

// Usage
streamFromFAME("Explain quantum computing");
```

---

## 4. Interactive Chat (Local)

### **Run:**
```bash
cd C:\Users\cavek\Downloads\FAME_Desktop
python chat_with_fame.py
```

### **What You'll See:**
```
======================================================================
FAME ASSISTANT - INTERACTIVE CHAT
======================================================================

YOU: What is the price of Bitcoin?
FAME: Bitcoin (BTC) is currently trading at $67,234.50...
      [Intent: get_crypto_price, Confidence: 0.92]
```

---

## 5. Desktop GUI (Full Experience)

### **Run:**
```bash
cd C:\Users\cavek\Downloads\FAME_Desktop
python enhanced_fame_communicator.py
```

**Features:**
- Voice input/output
- Multiple AI personas
- Business analysis tools
- Real-time system status

---

## 6. Enhanced AGI Service (New!)

### **Run Enhanced Service:**
```bash
cd C:\Users\cavek\Downloads\FAME_Desktop
python -m api.fastapi_app_enhanced
```

This starts the **full AGI system** with:
- TaskRouter (intent classification)
- Planner (multi-step reasoning)
- MemoryGraph (knowledge graph)
- Multi-Agent System
- RL Learning
- All 12 AGI components

---

## 📊 Quick Test Commands

### **Test REST API:**
```bash
# Simple query
curl -X POST http://18.220.108.23:8080/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the price of Bitcoin?"}'

# Enhanced AGI query
curl -X POST http://18.220.108.23:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze Apple stock", "context": []}'
```

### **Test Health:**
```bash
curl http://18.220.108.23:8080/health
curl http://18.220.108.23:8080/healthz  # Legacy endpoint
```

### **Test Metrics:**
```bash
curl http://18.220.108.23:8080/metrics
```

### **Interactive API Docs:**
Open in browser: `http://18.220.108.23:8080/docs`

---

## 🔌 Frontend Integration Examples

### **Simple HTML/JavaScript:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>FAME AGI Chat</title>
</head>
<body>
    <div id="chat">
        <div id="messages"></div>
        <input type="text" id="input" placeholder="Ask FAME...">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        const FAME_API = 'http://18.220.108.23:8080/ask';
        let sessionId = `session_${Date.now()}`;

        async function sendMessage() {
            const input = document.getElementById('input');
            const messages = document.getElementById('messages');
            const question = input.value;
            
            if (!question) return;
            
            messages.innerHTML += `<div><strong>You:</strong> ${question}</div>`;
            input.value = '';
            
            const response = await fetch(FAME_API, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: question,
                    context: []
                })
            });
            
            const data = await response.json();
            messages.innerHTML += `<div><strong>FAME:</strong> ${data.response}</div>`;
            messages.innerHTML += `<div><small>Confidence: ${data.confidence.toFixed(2)}</small></div>`;
        }
        
        document.getElementById('input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

---

## 🚀 Which API to Use?

### **Use `/query` (Legacy) if:**
- You need simple, fast responses
- You're using the existing FAME unified system
- You want backward compatibility

### **Use `/ask` (Enhanced AGI) if:**
- You want full AGI capabilities (planning, reflection, multi-agent)
- You need detailed breakdowns and audit reports
- You want access to all 12 AGI components

### **Use WebSocket if:**
- You need real-time bidirectional communication
- You're building a chat application
- You want persistent connections

### **Use Streaming if:**
- You want to show responses as they're generated
- You're building a chat UI with typing indicators
- You need progressive response display

---

## 📝 Session Management

FAME remembers context within a session:

```javascript
const sessionId = 'user_karl_123';

// First message
await fetch('http://18.220.108.23:8080/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: "My name is Karl",
    context: []
  })
});

// Second message (FAME remembers)
const response = await fetch('http://18.220.108.23:8080/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: "What's my name?",
    context: []
  })
});
// Response: "Your name is Karl"
```

---

## 🎯 Example Questions

### **Financial:**
- "What is the price of Bitcoin?"
- "Analyze Apple stock comprehensively"
- "What are current crypto market trends?"

### **Complex (Uses Full AGI):**
- "Plan a comprehensive investment strategy"
- "Research renewable energy opportunities step by step"
- "Create a detailed analysis of AI market trends"

### **General:**
- "What's today's date?"
- "Explain quantum computing"
- "Tell me about recent AI developments"

---

## 📚 Full API Documentation

**Interactive Docs:** `http://18.220.108.23:8080/docs`

**All Endpoints:**
- `POST /query` - Legacy query endpoint
- `POST /ask` - Enhanced AGI query (recommended)
- `GET /health` - System health
- `GET /metrics` - Performance metrics
- `POST /plan` - Create execution plan
- `GET /plan/{id}` - Get plan status
- `POST /feedback` - Submit learning feedback
- `GET /persona` - Get persona profile
- `POST /persona` - Update persona
- `POST /memory/wipe` - Wipe memory
- `POST /memory/rebuild` - Rebuild vector store
- `WebSocket /ws` - Real-time communication

---

## ✅ Status Check

**GitHub:** ✅ All updates pushed and synced  
**GitHub CI/CD:** ✅ Configured (automated deployment on push to main)  
**AWS EC2:** ⚠️ Auto-deploy via GitHub Actions (requires EC2_HOST and EC2_SSH_KEY secrets)

### CI/CD Pipeline:
- **CI Workflow:** `.github/workflows/ci.yml` - Runs tests, linting, and builds Docker image
- **CD Workflow (EC2):** `.github/workflows/deploy-ec2.yml` - Auto-deploys to EC2 on push to main
- **CD Workflow (K8s):** `.github/workflows/cd.yml` - Optional Kubernetes deployment

**Manual Deployment:** Run `.\deploy_ec2.ps1` for immediate deployment

---

**Last Updated:** 2025-01-17  
**Version:** 6.1 (Enhanced AGI)
