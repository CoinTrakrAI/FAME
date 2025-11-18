# Restart FAME deployment on EC2

$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$ec2Host = "3.135.222.143"
$user = "ec2-user"

Write-Host "=== Restarting FAME Deployment ===" -ForegroundColor Cyan
Write-Host ""

# SSH into EC2 and run deployment
$deployScript = @"
cd /home/ec2-user/FAME_Desktop || (git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop && cd FAME_Desktop)
git pull origin main
sudo docker-compose -f docker-compose.prod.yml down 2>/dev/null || sudo docker compose -f docker-compose.prod.yml down 2>/dev/null || true
sudo docker system prune -f
chmod +x deploy_ec2.sh
sudo bash deploy_ec2.sh
"@

Write-Host "Executing deployment on EC2..." -ForegroundColor Yellow
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" $deployScript

Write-Host ""
Write-Host "Deployment started. This may take 3-5 minutes for Docker build." -ForegroundColor Green
Write-Host "Wait a few minutes then run: powershell -File check_fame_status.ps1" -ForegroundColor Yellow

