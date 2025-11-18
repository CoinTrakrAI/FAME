#!/bin/bash
# Test FAME directly on EC2 instance

echo "=== Testing FAME on EC2 ==="
echo ""

# Test health endpoint
echo "[1] Testing health endpoint..."
curl -s http://localhost:8080/healthz | python3 -m json.tool || echo "Health check failed"

echo ""
echo "[2] Testing query endpoint..."
curl -s -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is today'\''s date?", "session_id": "test", "source": "test"}' | python3 -m json.tool || echo "Query failed"

echo ""
echo "[3] Checking container logs (last 10 lines)..."
sudo docker logs fame_agi_core --tail 10 2>&1

echo ""
echo "=== Test Complete ==="

