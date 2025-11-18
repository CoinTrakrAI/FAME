# Check FAME deployment status on EC2

$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$ec2Host = "3.135.222.143"
$user = "ec2-user"

Write-Host "=== Checking FAME Deployment Status ===" -ForegroundColor Cyan
Write-Host ""

# Check container status
Write-Host "[1] Container Status:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "sudo docker ps -a | grep -i fame || echo 'No FAME containers found'"

Write-Host ""
Write-Host "[2] Checking if port 8080 is listening:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "sudo netstat -tlnp 2>/dev/null | grep 8080 || sudo ss -tlnp 2>/dev/null | grep 8080 || echo 'Port 8080 not listening'"

Write-Host ""
Write-Host "[3] Testing health endpoint from EC2:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "curl -s http://localhost:8080/healthz 2>/dev/null | head -20 || echo 'Health check failed'"

Write-Host ""
Write-Host "[4] Container logs (last 20 lines):" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "sudo docker logs fame_agi_core --tail 20 2>&1 || sudo docker ps -aq | head -1 | xargs -I {} sudo docker logs {} --tail 20 2>&1 || echo 'Could not read logs'"

Write-Host ""
Write-Host "[5] Docker Compose status:" -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" "cd /home/ec2-user/FAME_Desktop 2>/dev/null && (sudo docker-compose -f docker-compose.prod.yml ps 2>/dev/null || sudo docker compose -f docker-compose.prod.yml ps 2>/dev/null || echo 'Docker Compose not available')"

Write-Host ""
Write-Host "=== Testing External Connection ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://${ec2Host}:8080/healthz" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[SUCCESS] FAME is accessible externally!" -ForegroundColor Green
    Write-Host "Status Code: $($response.StatusCode)"
    Write-Host "Response: $($response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)))"
} catch {
    Write-Host "[FAILED] Cannot connect externally: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "If container is running, check:"
    Write-Host "  1. Security Group allows port 8080 from your IP"
    Write-Host "  2. Container is binding to 0.0.0.0:8080 (not 127.0.0.1)"
    Write-Host "  3. No firewall blocking the port"
}

