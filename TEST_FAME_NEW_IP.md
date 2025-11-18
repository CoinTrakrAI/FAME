# Testing FAME on New IP: 3.135.222.143

## Updated Files
- ✅ `deploy_ec2.ps1` - Deployment script
- ✅ `test_fame_connection.py` - Connection test
- ✅ `test_fame_live.py` - Live question testing
- ✅ `chat_with_fame_aws.py` - Chat client
- ✅ `communicate_with_fame_aws.py` - Quick communication
- ✅ `fame_chat.html` - Web chat interface

## Test FAME

### Option 1: Python Script
```bash
python test_fame_questions.py
```

### Option 2: Interactive Chat
```bash
python chat_with_fame_aws.py
```

### Option 3: Quick Test
```bash
python communicate_with_fame_aws.py "What's today's date?"
```

## If Connection Fails

### 1. Check Security Group
Go to AWS Console → EC2 → Security Groups → Edit Inbound Rules:
- Type: Custom TCP
- Port: 8080
- Source: 0.0.0.0/0 (or your IP for security)

### 2. Check Deployment Status
The deployment script may still be running. Wait 2-3 minutes for Docker build to complete.

### 3. Test Directly on EC2
SSH into EC2 and check:
```bash
ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@3.135.222.143
sudo docker ps | grep fame
curl http://localhost:8080/healthz
```

## Questions to Test FAME AGI

1. **Basic Knowledge**: "What's today's date?"
2. **Current Prices**: "What's the current price of XRP?"
3. **Stock Prices**: "What's the price of Apple stock?"
4. **General Knowledge**: "What is artificial intelligence?"
5. **Complex Query**: "Compare Bitcoin and Ethereum for long-term investment"

