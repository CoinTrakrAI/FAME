# How to Communicate with FAME on AWS EC2

FAME is now running in a Docker container on AWS EC2. All communication should go through the AWS server endpoint.

## 🌐 AWS Server Information

- **Server URL:** `http://18.220.108.23:8080`
- **Query Endpoint:** `POST /query`
- **Health Check:** `GET /healthz`
- **Status:** ✅ Running and Healthy

---

## 🚀 Quick Start - Communication Methods

### 1. **Python AWS Chat Script** (Recommended)

Run the AWS-focused chat client:

```bash
python chat_with_fame_aws.py
```

This script:
- ✅ Connects directly to FAME on AWS
- ✅ Checks health before starting
- ✅ Maintains session memory
- ✅ Shows confidence scores and sources

**Features:**
- Health check on startup
- Session management
- Error handling with helpful messages
- Real-time responses from AWS

---

### 2. **Web Chat Interface** (Easiest)

Start the local web server (HTML connects to AWS):

```bash
python start_fame_chat.py
```

Then open: `http://localhost:8000/fame_chat.html`

**Note:** The HTML file already points to AWS (`http://18.220.108.23:8080/query`), so you're talking directly to FAME on AWS!

---

### 3. **Quick Command-Line Query**

Use the simple communication script:

```bash
# Interactive mode
python communicate_with_fame_aws.py

# Single query mode
python communicate_with_fame_aws.py "What is the price of Bitcoin?"
```

---

### 4. **Direct REST API** (For Integration)

```python
import requests

response = requests.post(
    'http://18.220.108.23:8080/query',
    json={
        'text': 'Your question here',
        'session_id': 'your_session_id',
        'source': 'your_app_name'
    },
    timeout=30
)

data = response.json()
print(data['response'])
```

**Response Format:**
```json
{
  "response": "FAME's response text",
  "confidence": 0.95,
  "source": "qa_engine",
  "session_id": "session_123",
  "reasoning": {...},
  "breakdown": {...}
}
```

---

## 📊 Health Check

Check if FAME is running on AWS:

```bash
curl http://18.220.108.23:8080/healthz
```

Or use Python:

```python
import requests
health = requests.get('http://18.220.108.23:8080/healthz').json()
print(f"Status: {health['overall_status']}")
print(f"Memory: {health['system']['memory_percent']}%")
```

---

## 🔧 Troubleshooting

### Connection Issues

If you can't connect to FAME on AWS:

1. **Check EC2 Status:**
   ```bash
   ssh -i "FAME.pem" ec2-user@18.220.108.23 "sudo docker ps | grep fame"
   ```

2. **Check Port Access:**
   - Ensure your network allows connections to port 8080
   - Verify AWS Security Group allows inbound traffic on port 8080

3. **Test Health Endpoint:**
   ```bash
   curl http://18.220.108.23:8080/healthz
   ```

### Timeout Issues

If requests timeout:
- FAME may be processing a complex query
- Try a simpler question first
- Check AWS instance resource usage (CPU/Memory)

---

## 📝 Session Management

All communication methods support session management. Use the same `session_id` to maintain conversation context:

```python
session_id = "my_conversation_123"

# Question 1
response1 = chat_with_fame("What is Bitcoin?", session_id)

# Question 2 - FAME remembers the context
response2 = chat_with_fame("What about Ethereum?", session_id)
```

---

## 🎯 Best Practices

1. **Use AWS Chat Script:** `chat_with_fame_aws.py` for interactive conversations
2. **Use Web Chat:** `start_fame_chat.py` for a nice UI experience
3. **Use Direct API:** For programmatic integration
4. **Maintain Sessions:** Use consistent session IDs for context

---

## ✅ Status Check

**Current Status:**
- ✅ FAME running on AWS EC2
- ✅ Container: `fame_desktop-fame-1` (Healthy)
- ✅ Port: 8080 (Accessible)
- ✅ All communication methods tested and working

**Last Verified:** 2025-01-17

---

## 🆘 Need Help?

- Check container logs: `ssh ec2-user@18.220.108.23 "sudo docker logs fame_desktop-fame-1 --tail 50"`
- Restart container: `ssh ec2-user@18.220.108.23 "cd /home/ec2-user/FAME_Desktop && sudo docker-compose -f docker-compose.prod.yml restart"`
- Deploy updates: `.\deploy_ec2.ps1` or `bash deploy_ec2.sh`

