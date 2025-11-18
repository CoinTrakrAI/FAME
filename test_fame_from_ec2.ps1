# Test FAME directly from EC2 to see if it's working internally

$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$ec2Host = "3.135.222.143"
$user = "ec2-user"

Write-Host "=== Testing FAME from EC2 (Internal) ===" -ForegroundColor Cyan
Write-Host ""

# Test health
Write-Host "[1] Health Check:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "curl -s http://localhost:8080/healthz 2>&1 | head -50"

Write-Host ""
Write-Host "[2] Testing Query:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "curl -s -X POST http://localhost:8080/query -H 'Content-Type: application/json' -d '{\"text\":\"What is today date?\",\"session_id\":\"test\"}' 2>&1 | head -100"

Write-Host ""
Write-Host "[3] Container Status:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'NAME|fame'"

Write-Host ""
Write-Host "[4] Recent Logs:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "sudo docker logs fame_agi_core --tail 20 2>&1"

