# FAME Deployment Script with Timeout Fix
# Usage: .\deploy_with_timeout_fix.ps1 <EC2_IP_ADDRESS>

param(
    [string]$EC2IP = "3.17.56.74"  # Current EC2 IP from testing
)

$SSH_KEY = "C:\Users\cavek\Downloads\FAME.pem"
$EC2_USER = "ec2-user"

Write-Host "================================================" -ForegroundColor Green
Write-Host "FAME Deployment - Timeout Fix & Logging Updates" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Target: ${EC2_USER}@${EC2IP}" -ForegroundColor Yellow
Write-Host ""

# Check if SSH key exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "[ERROR] SSH key not found: $SSH_KEY" -ForegroundColor Red
    Write-Host "Please update SSH_KEY variable in this script" -ForegroundColor Yellow
    exit 1
}

Write-Host "[INFO] Connecting to EC2 instance..." -ForegroundColor Cyan
Write-Host ""

# Deployment commands
$deployCommands = @"
set -e
echo '[STEP 1] Connected to EC2 instance'
echo ''

# Navigate to FAME directory
if [ -d 'FAME_Desktop' ]; then
    echo '[STEP 2] Found FAME_Desktop directory'
    cd FAME_Desktop
    echo '[STEP 3] Pulling latest code from GitHub...'
    git fetch origin main
    git reset --hard origin/main || echo '[WARNING] Git reset failed, continuing...'
else
    echo '[STEP 2] Cloning FAME repository...'
    git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop
    cd FAME_Desktop
fi

echo ''
echo '[STEP 4] Stopping existing containers...'
sudo docker compose -f docker-compose.prod.yml down || echo '[INFO] No containers to stop'

echo ''
echo '[STEP 5] Building new containers with timeout fix...'
sudo docker compose -f docker-compose.prod.yml build --no-cache

echo ''
echo '[STEP 6] Starting containers...'
sudo docker compose -f docker-compose.prod.yml up -d

echo ''
echo '[STEP 7] Waiting for services to start (15 seconds)...'
sleep 15

echo ''
echo '[STEP 8] Checking container status...'
sudo docker compose -f docker-compose.prod.yml ps

echo ''
echo '[STEP 9] Recent logs (last 30 lines):'
sudo docker compose -f docker-compose.prod.yml logs --tail=30

echo ''
echo '[STEP 10] Testing health endpoint...'
sleep 5
curl -s http://localhost:8080/healthz | head -20 || echo '[WARNING] Health check failed'

echo ''
echo '[SUCCESS] Deployment complete!'
echo ''
echo 'To view logs: sudo docker compose -f docker-compose.prod.yml logs -f'
echo 'To check status: sudo docker compose -f docker-compose.prod.yml ps'
"@

# Execute SSH command
try {
    ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${EC2_USER}@${EC2IP}" $deployCommands
    
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "Deployment Complete!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Test FAME with:" -ForegroundColor Yellow
    Write-Host "  python test_fame_ultra_minimal_test.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or check health:" -ForegroundColor Yellow
    Write-Host "  curl http://${EC2IP}:8080/healthz" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[ERROR] Deployment failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check EC2 IP is correct: $EC2IP" -ForegroundColor Cyan
    Write-Host "2. Verify SSH key path: $SSH_KEY" -ForegroundColor Cyan
    Write-Host "3. Check EC2 security group allows SSH (port 22)" -ForegroundColor Cyan
    Write-Host "4. Verify EC2 instance is running in AWS Console" -ForegroundColor Cyan
    exit 1
}

