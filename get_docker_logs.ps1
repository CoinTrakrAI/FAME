# Get Docker logs from EC2 instance
$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$ec2Host = "3.17.56.74"
$user = "ec2-user"

Write-Host "Fetching Docker logs from EC2..." -ForegroundColor Cyan
Write-Host "=" * 70

# First check if container exists
Write-Host "`n[1/3] Checking container status..." -ForegroundColor Yellow
ssh -i `"$sshKey`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3 $user@$ec2Host "sudo docker ps -a | grep fame" 2>&1 | Out-String

# Get recent logs
Write-Host "`n[2/3] Fetching container logs (last 100 lines)..." -ForegroundColor Yellow
ssh -i `"$sshKey`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3 $user@$ec2Host "sudo docker logs fame_agi_core --tail 100 2>&1" 2>&1 | Out-String

# Get all logs if recent ones aren't helpful
Write-Host "`n[3/3] Checking for any error patterns..." -ForegroundColor Yellow
ssh -i `"$sshKey`" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3 $user@$ec2Host "sudo docker logs fame_agi_core 2>&1 | grep -i 'error\|exception\|traceback\|failed\|crash' | tail -50" 2>&1 | Out-String

Write-Host "`nDone!" -ForegroundColor Green
Write-Host "=" * 70

