# Simple EC2 Deployment Script
param(
    [string]$EC2IP = "52.15.178.92"
)

$SSH_KEY = "C:\Users\cavek\Downloads\FAME.pem"
$EC2_USER = "ec2-user"

Write-Host "🚀 Deploying FAME to EC2..." -ForegroundColor Green
Write-Host "IP: $EC2IP" -ForegroundColor Yellow
Write-Host ""

# Single SSH command to do everything
ssh -i $SSH_KEY ${EC2_USER}@${EC2IP} @"
cd ~/FAME_Desktop 2>/dev/null || (git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop && cd FAME_Desktop)
git pull origin main
sudo docker compose -f docker-compose.prod.yml down 2>/dev/null || true
sudo docker compose -f docker-compose.prod.yml build --no-cache
sudo docker compose -f docker-compose.prod.yml up -d
sleep 5
sudo docker compose -f docker-compose.prod.yml ps
"@

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green

