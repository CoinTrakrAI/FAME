#!/bin/bash
# Check FAME deployment status on EC2

echo "=== Checking FAME Deployment Status ==="
echo ""

echo "[1] Container Status:"
ssh -i "C:\Users\cavek\Downloads\FAME.pem" -o StrictHostKeyChecking=no ec2-user@3.135.222.143 "sudo docker ps -a | grep -i fame || echo 'No FAME containers found'"

echo ""
echo "[2] Checking if port 8080 is listening:"
ssh -i "C:\Users\cavek\Downloads\FAME.pem" -o StrictHostKeyChecking=no ec2-user@3.135.222.143 "sudo netstat -tlnp | grep 8080 || sudo ss -tlnp | grep 8080 || echo 'Port 8080 not listening'"

echo ""
echo "[3] Container logs (last 30 lines):"
ssh -i "C:\Users\cavek\Downloads\FAME.pem" -o StrictHostKeyChecking=no ec2-user@3.135.222.143 "sudo docker logs fame_agi_core --tail 30 2>&1 || sudo docker logs \$(sudo docker ps -aq -f name=fame) --tail 30 2>&1 || echo 'Could not read logs'"

echo ""
echo "[4] Testing health endpoint from EC2:"
ssh -i "C:\Users\cavek\Downloads\FAME.pem" -o StrictHostKeyChecking=no ec2-user@3.135.222.143 "curl -s http://localhost:8080/healthz | head -20 || echo 'Health check failed'"

echo ""
echo "[5] Docker Compose status:"
ssh -i "C:\Users\cavek\Downloads\FAME.pem" -o StrictHostKeyChecking=no ec2-user@3.135.222.143 "cd /home/ec2-user/FAME_Desktop && sudo docker-compose -f docker-compose.prod.yml ps 2>/dev/null || sudo docker compose -f docker-compose.prod.yml ps 2>/dev/null || echo 'Docker Compose not available or no services'"

echo ""
echo "=== Status Check Complete ==="

