# How to Communicate with FAME

## 🎯 Quick Start - Test FAME on Deployed Server

**IMPORTANT:** For production testing and training preparation, test FAME on the deployed EC2 server (not locally). This ensures:
- ✅ FAME is accessible from the internet
- ✅ FAME has internet access (for web search, real-time data)
- ✅ You can test FAME's current knowledge
- ✅ Ready for training phase

### **🚀 Quick Test on Server:**

1. **Get your EC2 IP:** AWS Console → EC2 → Instances → Public IPv4 address
2. **Run test script:**
   ```bash
   export FAME_SERVER_URL="http://YOUR_EC2_IP:8080"
   python test_fame_on_server.py
   ```
3. **Or test manually:**
   ```bash
   curl http://YOUR_EC2_IP:8080/healthz
   curl -X POST http://YOUR_EC2_IP:8080/query \
     -H "Content-Type: application/json" \
     -d '{"text": "What is Bitcoin?"}'
   ```

See `TEST_FAME_ON_SERVER.md` for comprehensive testing guide.

---

## 1. 🌐 REST API (Recommended for Integration)

### **Base URLs:**
- **Production Server:** `http://YOUR_EC2_IP:8080` (get IP from AWS Console)
- **Local Development:** `http://localhost:8080` (if running locally)
- **Interactive Docs:** `http://YOUR_EC2_IP:8080/docs` (FastAPI Swagger UI)

### **Main Endpoint: `POST /query`**

**Python Example (Production Server):**
```python
import requests

# Replace with your EC2 IP address
FAME_SERVER = "http://YOUR_EC2_IP:8080"

response = requests.post(
    f'{FAME_SERVER}/query',
    json={
        'text': 'What is the price of Bitcoin?',
        'session_id': 'my_session_123',  # Optional - for conversation memory
        'source': 'my_app'               # Optional
    },
    timeout=90
)

data = response.json()
print(f"FAME: {data['response']}")
print(f"Confidence: {data.get('confidence', 0)}")
```

**cURL Example (Production Server):**
```bash
# Replace YOUR_EC2_IP with your actual EC2 IP
curl -X POST http://YOUR_EC2_IP:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the price of Bitcoin?",
    "session_id": "test_session"
  }'
```

**JavaScript/TypeScript Example (Production Server):**
```javascript
// Replace with your EC2 IP address
const FAME_SERVER = 'http://YOUR_EC2_IP:8080';

async function askFAME(question) {
  const response = await fetch(`${FAME_SERVER}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: question,
      session_id: 'web_session_123'
    })
  });
  
  const data = await response.json();
  console.log('FAME:', data.response);
  console.log('Confidence:', data.confidence);
  return data;
}

// Use it
askFAME("What are the best stocks to buy?");
```

### **Response Format:**
```json
{
  "response": "FAME's detailed response to your question...",
  "confidence": 0.95,
  "source": "qa_engine",
  "session_id": "my_session_123",
  "reasoning": {...},
  "breakdown": {...},
  "timestamp": 1234567890
}
```

---

## 2. 🏥 Health & Status Endpoints

### **Check if FAME is Running (Production Server):**
```bash
# Health check - Replace YOUR_EC2_IP with your actual IP
curl http://YOUR_EC2_IP:8080/healthz

# Readiness check (returns 503 if not ready)
curl http://YOUR_EC2_IP:8080/readyz
```

**Response:**
```json
{
  "overall_status": "healthy",
  "components": {...},
  "timestamp": 1234567890
}
```

### **Interactive API Documentation:**
Open in your browser:
- **Swagger UI:** `http://YOUR_EC2_IP:8080/docs` (Production)
- **ReDoc:** `http://YOUR_EC2_IP:8080/redoc` (Production)
- **Local:** `http://localhost:8080/docs` (If running locally)

This lets you:
- See all available endpoints
- Test queries directly in the browser
- View request/response schemas
- Try different parameters

---

## 3. 🧪 Test Scripts (Quick Testing)

FAME includes several test scripts for easy communication:

### **Python Test Script:**
```bash
# Run the realistic questions test
python test_fame_realistic_questions.py

# Or use the minimal test
python fame_ultra_minimal_test.py
```

These scripts will:
- ✅ Check if FAME is running
- ✅ Send test questions
- ✅ Display responses with timing
- ✅ Show confidence scores and sources

### **Example Test Script:**
Create `test_fame.py`:
```python
import requests

def ask_fame(question):
    response = requests.post(
        'http://localhost:8080/query',
        json={'text': question},
        timeout=90
    )
    return response.json()

# Test it
result = ask_fame("What is Bitcoin?")
print(result['response'])
```

---

## 📋 Available Endpoints

### **Main Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Main query endpoint - ask FAME anything |
| `/healthz` | GET | Health check (always returns 200) |
| `/readyz` | GET | Readiness check (returns 503 if not ready) |
| `/docs` | GET | Interactive API documentation (Swagger) |
| `/redoc` | GET | Alternative API documentation (ReDoc) |

### **Request Format (`/query`):**
```json
{
  "text": "Your question here",
  "session_id": "optional_session_id",  // Optional - for conversation context
  "source": "optional_source_name",     // Optional - e.g., "web_app", "cli"
  "metadata": {}                        // Optional - additional context
}
```

### **Response Format:**
```json
{
  "response": "FAME's response text",
  "confidence": 0.95,                   // 0.0 to 1.0
  "source": "qa_engine",                // Which component answered
  "session_id": "session_123",
  "reasoning": {...},                   // Internal reasoning (if available)
  "breakdown": {...},                   // Response breakdown (if available)
  "timestamp": 1234567890,
  "error": null                         // null if successful, error message if failed
}
```

---

## 🔧 Configuration

### **Query Timeout:**
FAME has a configurable timeout to prevent hanging queries:
- **Default:** 60 seconds
- **Set via environment:** `FAME_QUERY_TIMEOUT=90` (in seconds)

If a query times out, you'll get:
```json
{
  "response": "Query processing timed out...",
  "error": "timeout",
  "timeout_seconds": 60
}
```

---

## 💡 Example Questions

### **Financial Questions:**
```python
ask_fame("What is the current price of Bitcoin?")
ask_fame("Should I invest in Apple stock?")
ask_fame("What are the best dividend stocks?")
ask_fame("Explain options trading")
```

### **Investment Analysis:**
```python
ask_fame("Analyze Tesla stock comprehensively")
ask_fame("What's the IV skew for SPY options?")
ask_fame("Calculate optimal position size using Kelly Criterion")
ask_fame("What are the current market risks?")
```

### **General Questions:**
```python
ask_fame("What is artificial intelligence?")
ask_fame("Explain quantum computing")
ask_fame("What's today's date?")
```

---

## 🔄 Session Management

FAME maintains conversation context within sessions:

```python
session_id = "my_conversation_123"

# First message
ask_fame("My name is John", session_id=session_id)

# Second message (FAME remembers context)
ask_fame("What's my name?", session_id=session_id)
# Response: "Your name is John"
```

---

## 🚨 Error Handling

### **Common Errors:**

1. **Connection Refused:**
   - FAME is not running
   - Wrong URL/port
   - Firewall blocking

2. **Timeout:**
   - Query too complex
   - System overloaded
   - Increase timeout or simplify question

3. **500 Internal Server Error:**
   - Check FAME logs
   - Verify API keys are set
   - Check system health: `GET /healthz`

### **Error Response Format:**
```json
{
  "response": "Error message here",
  "error": "error_type",
  "confidence": 0.0,
  "timestamp": 1234567890
}
```

---

## 🔐 Security Notes

- **CORS:** Currently enabled for all origins (change in production)
- **Authentication:** No authentication required (add in production)
- **Rate Limiting:** Not implemented (add in production)
- **HTTPS:** Use reverse proxy (nginx/traefik) for HTTPS in production

---

## 🚀 Next Steps - Test on Deployed Server

1. **Get Your EC2 IP Address:**
   - Go to: AWS Console → EC2 → Instances
   - Find your FAME instance
   - Copy the **Public IPv4 address**

2. **Test Connection:**
   ```bash
   # Replace YOUR_EC2_IP with your actual IP
   curl http://YOUR_EC2_IP:8080/healthz
   ```

3. **Run Comprehensive Tests:**
   ```bash
   export FAME_SERVER_URL="http://YOUR_EC2_IP:8080"
   python test_fame_on_server.py
   ```

4. **Try a Query:**
   ```bash
   curl -X POST http://YOUR_EC2_IP:8080/query \
     -H "Content-Type: application/json" \
     -d '{"text": "What is Bitcoin?"}'
   ```

5. **Open Interactive Docs:**
   ```
   http://YOUR_EC2_IP:8080/docs
   ```

See `TEST_FAME_ON_SERVER.md` for detailed testing guide.

---

## 📚 Additional Resources

- **API Documentation:** `http://localhost:8080/docs`
- **Test Scripts:** See `test_fame_*.py` files in the repository
- **Example Integration:** Check `test_fame_realistic_questions.py`

---

## ✅ Quick Checklist

- [ ] FAME is running (`GET /healthz` returns 200)
- [ ] You can access `http://localhost:8080/docs`
- [ ] Test query works: `POST /query` with `{"text": "test"}`
- [ ] Response includes `response`, `confidence`, and `source` fields

---

**Ready to communicate with FAME!** 🎉
