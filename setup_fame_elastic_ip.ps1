# Setup Elastic IP for FAME EC2 Instance
# Instance ID from AWS Console: i-07f1625aebecb714c
# Current Public IP: 52.15.178.92

param(
    [string]$InstanceId = "i-07f1625aebecb714c"
)

Write-Host "🌐 Setting up Elastic IP for FAME" -ForegroundColor Cyan
Write-Host "Instance ID: $InstanceId" -ForegroundColor Yellow
Write-Host ""

# Run the setup script
.\setup_elastic_ip.ps1 -InstanceId $InstanceId

