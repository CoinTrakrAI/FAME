# Test if SSH service is running on EC2 instance
$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$user = "ec2-user"
$ec2Host = "52.15.178.92"

Write-Host "Testing SSH service on EC2 instance..." -ForegroundColor Cyan
Write-Host "Instance: $ec2Host" -ForegroundColor Yellow
Write-Host ""

# Test 1: Port 22 is open (we know this from security group)
Write-Host "1. Security Group Check:" -ForegroundColor Yellow
Write-Host "   Port 22 (SSH) is open from 0.0.0.0/0" -ForegroundColor Green
Write-Host ""

# Test 2: Try SSH with different timeout
Write-Host "2. Testing SSH connection (10 second timeout)..." -ForegroundColor Yellow

$sshTest = Start-Job -ScriptBlock {
    param($key, $host, $user)
    $ssh = "C:\Windows\System32\OpenSSH\ssh.exe"
    & $ssh -i $key -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$user@$host" "echo 'SSH test'" 2>&1
} -ArgumentList $sshKey, $ec2Host, $user

$result = Wait-Job $sshTest -Timeout 12
if ($result) {
    $output = Receive-Job $sshTest
    Remove-Job $sshTest
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   SSH connection successful!" -ForegroundColor Green
        Write-Host "   Output: $output" -ForegroundColor Gray
    } else {
        Write-Host "   SSH connection failed" -ForegroundColor Red
        Write-Host "   Error details:" -ForegroundColor Yellow
        $output | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
    }
} else {
    Write-Host "   SSH connection timed out" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Possible causes:" -ForegroundColor Yellow
    Write-Host "   - SSH service not running on instance" -ForegroundColor Gray
    Write-Host "   - Instance firewall blocking SSH" -ForegroundColor Gray
    Write-Host "   - Instance still initializing" -ForegroundColor Gray
    Write-Host "   - Network routing issue" -ForegroundColor Gray
    Remove-Job $sshTest -Force
}

Write-Host ""
Write-Host "3. Recommendations:" -ForegroundColor Yellow
Write-Host "   - Check instance system logs in AWS Console" -ForegroundColor Gray
Write-Host "   - Try restarting the instance (stop/start)" -ForegroundColor Gray
Write-Host "   - Check if instance has internal firewall rules" -ForegroundColor Gray
Write-Host "   - Verify instance is fully initialized (wait 2-3 minutes after start)" -ForegroundColor Gray

