# Test FAME on Deployed Server (Internet Access)

## 🎯 Purpose

Test FAME on the deployed EC2 server to:
- ✅ Verify FAME is accessible from the internet
- ✅ Confirm FAME has internet access (for web search, real-time data)
- ✅ Test FAME's current knowledge base
- ✅ Validate investment analysis capabilities
- ✅ Prepare for training phase

---

## 🚀 Quick Start

### **Step 1: Get Your EC2 IP Address**

1. Go to: **AWS Console → EC2 → Instances**
2. Find your FAME instance (should be running)
3. Copy the **Public IPv4 address** (e.g., `3.17.56.74`)

### **Step 2: Update Test Script**

Edit `test_fame_on_server.py` and update:
```python
FAME_SERVER = "http://YOUR_EC2_IP:8080"  # Replace with your IP
```

Or set environment variable:
```bash
export FAME_SERVER_URL="http://YOUR_EC2_IP:8080"
python test_fame_on_server.py
```

### **Step 3: Run Tests**

```bash
python test_fame_on_server.py
```

This will:
- ✅ Check server health
- ✅ Test internet connectivity
- ✅ Test knowledge base
- ✅ Test investment analysis
- ✅ Offer interactive mode

---

## 📋 Test Categories

### **1. Internet Access Test**

Tests if FAME can access real-time information:
- Current Bitcoin price
- Latest Apple stock news
- Today's date/time
- Recent events

**Success Criteria:** FAME can fetch real-time data from the web

### **2. Knowledge Base Test**

Tests FAME's trained knowledge:
- Options trading concepts
- Kelly Criterion
- IV skew
- Investment strategies

**Success Criteria:** FAME demonstrates understanding of financial concepts

### **3. Investment Analysis Test**

Tests FAME's investment capabilities:
- Stock analysis
- Market risk assessment
- Options analysis
- Portfolio recommendations

**Success Criteria:** FAME provides investment insights and analysis

---

## 🔧 Manual Testing

### **Test Health:**
```bash
curl http://YOUR_EC2_IP:8080/healthz
```

### **Test Query:**
```bash
curl -X POST http://YOUR_EC2_IP:8080/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the current price of Bitcoin?", "session_id": "test"}'
```

### **Test Interactive Docs:**
Open in browser: `http://YOUR_EC2_IP:8080/docs`

---

## 🐍 Python Testing

### **Quick Test:**
```python
import requests

response = requests.post(
    'http://YOUR_EC2_IP:8080/query',
    json={'text': 'What is Bitcoin?'},
    timeout=90
)

print(response.json()['response'])
```

### **Comprehensive Test:**
```bash
python test_fame_on_server.py
```

---

## 📊 Example Questions for Testing

### **Internet Access (Real-Time Data):**
```python
"What is the current price of Bitcoin?"
"What's the latest news about Apple stock?"
"What is today's date and time?"
"Who won the 2024 US Presidential election?"
```

### **Knowledge Base (Training Data):**
```python
"Explain what options trading is"
"What is the Kelly Criterion?"
"Explain implied volatility skew"
"What are the differences between growth and value stocks?"
```

### **Investment Analysis (Expertise):**
```python
"Should I invest in Apple stock right now?"
"Analyze Tesla stock comprehensively"
"What are the best dividend stocks for 2024?"
"What are the current market risks?"
"What's the IV skew for SPY options?"
```

---

## ✅ Success Indicators

### **Health Check:**
```json
{
  "overall_status": "healthy",
  "components": {...},
  "timestamp": 1234567890
}
```

### **Good Response:**
```json
{
  "response": "Detailed, accurate answer...",
  "confidence": 0.8-0.95,
  "source": "qa_engine",
  "timestamp": 1234567890
}
```

### **Internet Access Confirmed:**
- FAME can fetch current prices
- FAME can access recent news
- FAME knows today's date
- Real-time data is accurate

---

## 🚨 Troubleshooting

### **Cannot Connect to Server:**
1. **Check EC2 Instance:**
   - AWS Console → EC2 → Instances
   - Verify instance is "running"
   - Get current Public IPv4 address

2. **Check Security Group:**
   - EC2 → Security Groups
   - Inbound rules → Port 8080 must be open
   - Source: `0.0.0.0/0` (or your IP)

3. **Check FAME Container:**
   ```bash
   ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@YOUR_IP
   sudo docker ps | grep fame
   sudo docker logs fame_agi_core --tail 50
   ```

### **Timeout Errors:**
- Increase timeout in test script
- Check EC2 instance resources (CPU/memory)
- Verify FAME is not stuck processing

### **No Internet Access:**
- Check EC2 instance has public IP
- Verify security group allows outbound traffic
- Test from EC2: `curl https://www.google.com`

---

## 🔐 Security Notes

- **Port 8080:** Should be open for HTTP access
- **HTTPS:** Consider adding nginx/traefik reverse proxy for HTTPS
- **Authentication:** Add API keys/tokens for production
- **Rate Limiting:** Implement to prevent abuse

---

## 📝 Pre-Training Checklist

Before starting FAME's training phase:

- [ ] ✅ FAME is accessible from the internet
- [ ] ✅ Health check returns "healthy"
- [ ] ✅ Internet access test passes (can fetch real-time data)
- [ ] ✅ Knowledge base test passes (demonstrates understanding)
- [ ] ✅ Investment analysis test passes (provides insights)
- [ ] ✅ Response times are acceptable (< 60s)
- [ ] ✅ Confidence scores are reasonable (> 0.7)
- [ ] ✅ Interactive docs are accessible (`/docs`)

---

## 🎯 Next Steps After Testing

Once all tests pass:

1. **Review Test Results:** Understand FAME's current capabilities
2. **Identify Gaps:** Note areas where FAME needs improvement
3. **Plan Training:** Design training data/strategies based on gaps
4. **Begin Training:** Start FAME's learning phase

---

## 📚 Additional Resources

- **API Documentation:** `http://YOUR_EC2_IP:8080/docs`
- **Health Check:** `http://YOUR_EC2_IP:8080/healthz`
- **Deployment Guide:** See `NEXT_STEPS_DEPLOYMENT.md`

---

**Ready to test FAME on the server!** 🚀

