# Check detailed container status and logs

$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$ec2Host = "3.135.222.143"
$user = "ec2-user"

Write-Host "=== Detailed Container Status ===" -ForegroundColor Cyan
Write-Host ""

# Container status
Write-Host "[1] Container Status:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'NAME|fame'"

Write-Host ""
Write-Host "[2] Container Logs (last 50 lines):" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "sudo docker logs fame_agi_core --tail 50 2>&1"

Write-Host ""
Write-Host "[3] Testing health from EC2 (localhost):" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "curl -s -m 5 http://localhost:8080/healthz | head -30 || echo 'Health check failed'"

Write-Host ""
Write-Host "[4] Testing query from EC2 (localhost):" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "curl -s -X POST http://localhost:8080/query -H 'Content-Type: application/json' -d '{\"text\":\"What is today date?\",\"session_id\":\"test\"}' | head -50 || echo 'Query failed'"

