# FAME API Usage Examples

## ✅ Correct Request Format

### **Single JSON Object Only:**

```json
{
  "text": "What is the price of Bitcoin?"
}
```

### **With Optional Fields:**

```json
{
  "text": "What is the price of Bitcoin?",
  "session_id": "user_123",
  "source": "web_app"
}
```

---

## ❌ Common Mistakes

### **Mistake 1: Two JSON Objects (WRONG)**
```json
{
  "text": "string",
  "session_id": "string"
}

{
  "text": "What is the price of Bitcoin?"
}
```
**Error:** "Extra data" - JSON decode error

### **Mistake 2: Template Values (WRONG)**
```json
{
  "text": "string",  // ❌ Don't use "string" - use your actual question
  "session_id": "string"
}
```

### **Mistake 3: Missing Quotes (WRONG)**
```json
{
  text: "What is the price of Bitcoin?"  // ❌ Missing quotes around "text"
}
```

---

## ✅ How to Use API Docs Correctly

### **Step-by-Step:**

1. **Go to:** `http://18.220.108.23:8080/docs`

2. **Click:** `POST /query` → **"Try it out"**

3. **In the Request body field, DELETE everything and type:**
   ```json
   {
     "text": "What is the price of Bitcoin?"
   }
   ```

4. **Click:** **"Execute"**

5. **See response!**

---

## 📝 Working Examples

### **Example 1: Simple Question**
```json
{
  "text": "What is the price of Bitcoin?"
}
```

### **Example 2: With Session (Remembers Context)**
```json
{
  "text": "What is the price of Bitcoin?",
  "session_id": "karl_123"
}
```

### **Example 3: With Source Tracking**
```json
{
  "text": "Analyze Apple stock",
  "session_id": "karl_123",
  "source": "web_app"
}
```

### **Example 4: With Metadata**
```json
{
  "text": "What is the price of Bitcoin?",
  "session_id": "karl_123",
  "source": "web_app",
  "metadata": {
    "user_id": "karl",
    "platform": "chrome"
  }
}
```

---

## 🔧 Using curl (Command Line)

### **Simple Request:**
```bash
curl -X POST http://18.220.108.23:8080/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the price of Bitcoin?"}'
```

### **With Session:**
```bash
curl -X POST http://18.220.108.23:8080/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the price of Bitcoin?", "session_id": "user_123"}'
```

---

## 💻 JavaScript Examples

### **Simple Fetch:**
```javascript
const response = await fetch('http://18.220.108.23:8080/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'What is the price of Bitcoin?'
  })
});

const data = await response.json();
console.log(data.response);
```

### **With Error Handling:**
```javascript
async function askFAME(question) {
  try {
    const response = await fetch('http://18.220.108.23:8080/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: question })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.response;
  } catch (error) {
    console.error('Error asking FAME:', error);
    return 'Sorry, I encountered an error.';
  }
}
```

---

## 🐍 Python Examples

### **Simple Request:**
```python
import requests

response = requests.post(
    'http://18.220.108.23:8080/query',
    json={'text': 'What is the price of Bitcoin?'}
)
print(response.json()['response'])
```

### **With Session:**
```python
import requests

session_id = 'user_123'

response = requests.post(
    'http://18.220.108.23:8080/query',
    json={
        'text': 'What is the price of Bitcoin?',
        'session_id': session_id,
        'source': 'python_client'
    }
)

data = response.json()
print(f"FAME: {data['response']}")
```

---

## 📊 Expected Response Format

### **Success Response (200):**
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

### **Error Response (422 - Validation Error):**
```json
{
  "detail": [
    {
      "type": "json_invalid",
      "loc": ["body", 119],
      "msg": "JSON decode error",
      "ctx": {
        "error": "Extra data"
      }
    }
  ]
}
```

**This means:** Your JSON is malformed (usually two objects or syntax error)

---

## 🎯 Quick Test Checklist

- [ ] Only ONE JSON object in request body
- [ ] All keys have quotes: `"text"` not `text`
- [ ] No template values like `"string"` - use actual text
- [ ] Proper JSON syntax (commas, brackets)
- [ ] Content-Type header: `application/json`

---

## 🔍 Debugging Tips

1. **Validate JSON first:** Use https://jsonlint.com/
2. **Check the error message:** It tells you exactly what's wrong
3. **Start simple:** Just `{"text": "your question"}` first
4. **Add fields gradually:** Add `session_id`, `source`, etc. one at a time

