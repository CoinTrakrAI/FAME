#!/bin/bash
# Quick EC2 status check script

echo "=== Checking FAME Container Status ==="
ssh -i "C:\Users\cavek\Downloads\FAME.pem" -o StrictHostKeyChecking=no ec2-user@18.220.108.23 << 'EOF'
echo "Container Status:"
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -i fame || echo "No FAME containers found"

echo ""
echo "=== Checking Container Logs (last 30 lines) ==="
sudo docker logs fame_agi_core --tail 30 2>&1 || echo "Could not read logs"

echo ""
echo "=== Checking if port 8080 is listening ==="
sudo netstat -tlnp | grep 8080 || sudo ss -tlnp | grep 8080 || echo "Port 8080 not listening"

echo ""
echo "=== Checking EC2 Security Group ==="
echo "Note: Check AWS Console -> EC2 -> Security Groups -> Inbound Rules"
echo "Port 8080 should allow inbound from 0.0.0.0/0 or your IP"
EOF

