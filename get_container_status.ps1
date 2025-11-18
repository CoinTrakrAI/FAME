# Get comprehensive container status from EC2
$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$ec2Host = "3.17.56.74"
$user = "ec2-user"

Write-Host "=== FAME Container Status Check ===" -ForegroundColor Cyan
Write-Host ""

# SSH options for better reliability (properly quoted)
$sshOpts = "-i `"$sshKey`" -o StrictHostKeyChecking=no -o ConnectTimeout=15 -o ServerAliveInterval=5 -o ServerAliveCountMax=3"

try {
    Write-Host "[1] Container Status..." -ForegroundColor Yellow
    ssh $sshOpts $user@$ec2Host "sudo docker ps -a | head -10" 2>&1
    
    Write-Host "`n[2] Docker Compose Status..." -ForegroundColor Yellow
    ssh $sshOpts $user@$ec2Host "cd /home/ec2-user/FAME_Desktop && sudo docker-compose -f docker-compose.prod.yml ps 2>&1 || sudo docker compose -f docker-compose.prod.yml ps 2>&1" 2>&1
    
    Write-Host "`n[3] Container Logs (Last 50 lines)..." -ForegroundColor Yellow
    ssh $sshOpts $user@$ec2Host "sudo docker logs fame_agi_core --tail 50 2>&1" 2>&1
    
    Write-Host "`n[4] Checking for Errors..." -ForegroundColor Yellow
    ssh $sshOpts $user@$ec2Host "sudo docker logs fame_agi_core 2>&1 | tail -100 | grep -i -E 'error|exception|traceback|failed|crash|cannot|module|import' | tail -20" 2>&1
    
    Write-Host "`n[5] Port 8080 Status..." -ForegroundColor Yellow
    ssh $sshOpts $user@$ec2Host "sudo netstat -tlnp | grep 8080 || sudo ss -tlnp | grep 8080" 2>&1
    
} catch {
    Write-Host "SSH Connection Failed: $_" -ForegroundColor Red
    Write-Host "`nTry accessing EC2 Console -> EC2 Instance Connect instead" -ForegroundColor Yellow
}

