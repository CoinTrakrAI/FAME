# FAME Deployment Script for AWS EC2 (PowerShell)
# Usage: .\deploy_to_ec2.ps1 <EC2_IP_ADDRESS>

param(
    [string]$EC2IP = "18.220.108.23"  # Update with Elastic IP after setup
)

$SSH_KEY = "C:\Users\cavek\Downloads\FAME.pem"
$EC2_USER = "ec2-user"

Write-Host "🚀 FAME Deployment to EC2" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Green
Write-Host "Target: ${EC2_USER}@${EC2IP}" -ForegroundColor Yellow
Write-Host ""

# Check if SSH key exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "❌ SSH key not found: $SSH_KEY" -ForegroundColor Red
    Write-Host "Please update SSH_KEY variable in this script" -ForegroundColor Yellow
    exit 1
}

Write-Host "📡 Connecting to EC2 instance..." -ForegroundColor Cyan
Write-Host ""

# SSH commands
$deployCommands = @"
echo '✅ Connected to EC2 instance'
echo ''

# Check if FAME_Desktop directory exists
if [ -d 'FAME_Desktop' ]; then
    echo '📂 Found existing FAME_Desktop directory'
    cd FAME_Desktop
    echo '🔄 Pulling latest code from GitHub...'
    git pull origin main || echo '⚠️ Git pull failed, continuing with existing code'
else
    echo '📂 Cloning FAME repository...'
    git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop
    cd FAME_Desktop
fi

echo ''
echo '🐳 Stopping existing containers...'
docker compose -f docker-compose.prod.yml down || echo 'No containers to stop'

echo ''
echo '🔨 Building new containers...'
docker compose -f docker-compose.prod.yml build --no-cache

echo ''
echo '🚀 Starting containers...'
docker compose -f docker-compose.prod.yml up -d

echo ''
echo '⏳ Waiting for services to start...'
sleep 10

echo ''
echo '📊 Container status:'
docker compose -f docker-compose.prod.yml ps

echo ''
echo '📋 Recent logs:'
docker compose -f docker-compose.prod.yml logs --tail=20

echo ''
echo '✅ Deployment complete!'
"@

# Execute SSH command
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "${EC2_USER}@${EC2IP}" $deployCommands

Write-Host ""
Write-Host "🎉 Deployment script completed!" -ForegroundColor Green
Write-Host ""
Write-Host "To check status manually:" -ForegroundColor Yellow
Write-Host "  ssh -i `"$SSH_KEY`" ${EC2_USER}@${EC2IP}"
Write-Host "  cd FAME_Desktop"
Write-Host "  docker compose -f docker-compose.prod.yml logs -f"

