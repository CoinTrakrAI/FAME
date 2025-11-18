# Next Steps: Deploy Timeout Fix & Logging Updates

## Summary of Changes

### ✅ Completed
1. **Timeout Protection** (`api/server.py`):
   - Added 60-second timeout wrapper to prevent infinite hangs
   - Returns timeout error instead of hanging
   - Configurable via `FAME_QUERY_TIMEOUT` environment variable

2. **Granular Timing Logs** (`fame_unified.py`):
   - Added timing logs at each major processing step
   - Will help identify exactly where queries hang
   - Logs include: TaskRouter, MemoryGraph, Reasoning Engine, Brain processing

3. **3-Tier Degradation System**:
   - Tier 1: Real-time data
   - Tier 2: Degraded mode (cached data)
   - Tier 3: Conceptual only (no fake numbers)

4. **Emoji Removal**: All production code cleaned

---

## Step 1: Commit & Push Changes

```bash
cd C:\Users\cavek\Downloads\FAME_Desktop

# Add critical files
git add api/server.py
git add fame_unified.py
git add core/qa_engine/
git add core/qa_engine_advanced_trading.py
git add core/qa_engine/cache_manager.py
git add core/qa_engine/degraded_mode_handler.py
git add core/investment_brain/integration.py

# Commit with descriptive message
git commit -m "Fix: Add timeout protection and granular logging to identify query hangs

- Add 60s timeout wrapper in API server (configurable via FAME_QUERY_TIMEOUT)
- Add timing logs at each processing step (TaskRouter, MemoryGraph, Reasoning, Brain)
- Implement 3-tier degradation system (real-time → cached → conceptual)
- Remove emojis from production code
- Add cache manager and degraded mode handler for fallback"

# Push to GitHub
git push origin main
```

---

## Step 2: Deploy to AWS EC2

### Option A: Use Deployment Script (Recommended)

```powershell
cd C:\Users\cavek\Downloads\FAME_Desktop

# Update EC2 IP if needed (currently set to 3.17.56.74)
.\deploy_with_timeout_fix.ps1

# Or specify IP:
.\deploy_with_timeout_fix.ps1 -EC2IP "YOUR_EC2_IP"
```

### Option B: Manual SSH Deployment

```powershell
# SSH to EC2
ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@3.17.56.74

# Once connected, run:
cd FAME_Desktop
git pull origin main
sudo docker compose -f docker-compose.prod.yml down
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo docker compose -f docker-compose.prod.yml up -d
sleep 15
sudo docker compose -f docker-compose.prod.yml logs --tail=50
```

---

## Step 3: Verify Deployment

### Test Health Endpoint

```powershell
# From local machine
curl http://3.17.56.74:8080/healthz
```

### Test with Ultra-Minimal Test

```powershell
cd C:\Users\cavek\Downloads\FAME_Desktop
python fame_ultra_minimal_test.py
```

**Expected Results:**
- Health check: ✅ Should pass quickly (0.2-0.5s)
- Query: Should either:
  - ✅ Return response within 60 seconds
  - ⚠️ Return timeout error (better than hanging indefinitely)

---

## Step 4: Check Logs for Hang Points

### View FAME Logs on EC2

```bash
# SSH to EC2 first
ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@3.17.56.74

# View logs with timing information
sudo docker compose -f docker-compose.prod.yml logs -f | grep -E "TIMING|ERROR|WARNING"
```

**What to Look For:**
- `[TIMING] Starting TaskRouter...` - If this appears but no completion, TaskRouter is hanging
- `[TIMING] Starting MemoryGraph...` - If this appears but no completion, MemoryGraph is hanging
- `[TIMING] Starting brain.handle_query...` - If this appears but no completion, Brain processing is hanging
- Last log message before timeout = where it's hanging

### Example Good Log Flow:
```
[TIMING] Query start: What is the price of AAPL?...
[TIMING] Starting decision_engine.route_query...
[TIMING] decision_engine.route_query completed in 0.15s
[TIMING] Starting MemoryGraph search...
[TIMING] MemoryGraph search completed in 0.05s
[TIMING] Starting brain.handle_query...
[TIMING] brain.handle_query completed in 2.35s
```

### Example Bad Log Flow (Hanging):
```
[TIMING] Query start: What is the price of AAPL?...
[TIMING] Starting decision_engine.route_query...
[TIMING] decision_engine.route_query completed in 0.15s
[TIMING] Starting brain.handle_query...
[No completion message - hangs here]
```

---

## Step 5: Test with Realistic Questions

Once deployment is verified, test with full question suite:

```powershell
python test_fame_realistic_questions.py
```

**Expected Results:**
- ✅ Successful responses for simple questions
- ⚠️ Timeout errors for complex questions (instead of hanging)
- Timing information in logs to identify bottlenecks

---

## Step 6: Adjust Timeout if Needed

If queries consistently timeout but you know they should work:

```bash
# On EC2, edit docker-compose.prod.yml or .env
# Add environment variable:
FAME_QUERY_TIMEOUT=90  # Increase to 90 seconds

# Restart container
sudo docker compose -f docker-compose.prod.yml restart fame_api
```

Or set in EC2 environment:
```bash
export FAME_QUERY_TIMEOUT=90
sudo docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### If Deployment Script Fails:

1. **Check SSH Connection:**
   ```powershell
   ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@3.17.56.74
   ```
   If this fails, check:
   - EC2 instance is running
   - Security group allows SSH (port 22)
   - IP address is correct

2. **Check Disk Space:**
   ```bash
   # On EC2
   df -h
   ```
   Need at least 5GB free for Docker build

3. **Check Docker:**
   ```bash
   # On EC2
   sudo systemctl status docker
   sudo docker ps
   ```

### If Queries Still Hang:

1. **Check logs immediately after timeout:**
   ```bash
   sudo docker compose -f docker-compose.prod.yml logs --since 5m | grep -E "TIMING|ERROR"
   ```

2. **Check specific component:**
   - If TaskRouter hangs → Check LLM API keys and connectivity
   - If MemoryGraph hangs → Check ChromaDB/vector store
   - If Brain hangs → Check plugin loading

3. **Test individual components:**
   ```bash
   # Test LLM connectivity
   curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
   
   # Test Redis (if used)
   docker compose exec redis redis-cli ping
   ```

---

## Quick Reference Commands

### Local Testing:
```powershell
# Minimal test
python fame_ultra_minimal_test.py

# Debug test (5 questions)
python fame_debug_test.py

# Realistic questions (33 questions)
python test_fame_realistic_questions.py
```

### EC2 Management:
```bash
# Check status
sudo docker compose -f docker-compose.prod.yml ps

# View logs
sudo docker compose -f docker-compose.prod.yml logs -f

# Restart
sudo docker compose -f docker-compose.prod.yml restart fame_api

# Rebuild
sudo docker compose -f docker-compose.prod.yml down
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo docker compose -f docker-compose.prod.yml up -d
```

---

## Success Criteria

✅ **Deployment Successful When:**
1. Health endpoint returns `200 OK` in < 1 second
2. Queries return responses OR timeout errors (not hang)
3. Logs show timing information for each step
4. No infinite hangs (all requests complete within timeout)

✅ **Issue Identified When:**
1. Logs show which step is hanging (last `[TIMING] Starting...` without completion)
2. Timeout errors provide actionable information
3. Can identify root cause (LLM, database, memory, etc.)

---

## Next Steps After Deployment

Once deployed and logs show where it hangs:

1. **If TaskRouter hangs:**
   - Check LLM API connectivity
   - Verify API keys are valid
   - Check rate limits

2. **If MemoryGraph hangs:**
   - Check ChromaDB status
   - Verify vector store connectivity
   - Check database locks

3. **If Brain processing hangs:**
   - Check plugin loading
   - Verify all dependencies installed
   - Check for infinite loops in handlers

4. **If specific queries hang:**
   - Add query-specific timeout handling
   - Route complex queries to simplified handlers
   - Implement query complexity scoring

---

**Ready to deploy! Start with Step 1 (Commit & Push).**

