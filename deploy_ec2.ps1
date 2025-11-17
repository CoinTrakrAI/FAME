# FAME EC2 Automated Deployment Script
# Run this from Windows PowerShell to deploy FAME to EC2

param(
    [string]$EC2IP = "52.15.178.92",
    [string]$SSH_KEY = "C:\Users\cavek\Downloads\FAME.pem",
    [string]$EC2_USER = "ec2-user"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 FAME EC2 Automated Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target: ${EC2_USER}@${EC2IP}" -ForegroundColor Yellow
Write-Host ""

# Check if SSH key exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "❌ SSH key not found: $SSH_KEY" -ForegroundColor Red
    Write-Host "Please update the SSH_KEY variable in this script" -ForegroundColor Yellow
    exit 1
}

# Check if deploy script exists
$DeployScript = Join-Path $PSScriptRoot "deploy_ec2.sh"
if (-not (Test-Path $DeployScript)) {
    Write-Host "❌ Deployment script not found: $DeployScript" -ForegroundColor Red
    exit 1
}

Write-Host "📤 Step 1: Uploading deployment script..." -ForegroundColor Yellow

# Upload the shell script to EC2
$uploadCommand = @"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$DeployScript" ${EC2_USER}@${EC2IP}:~/deploy_ec2.sh
"@

try {
    Invoke-Expression $uploadCommand
    if ($LASTEXITCODE -ne 0) {
        throw "SCP upload failed"
    }
    Write-Host "✅ Script uploaded successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to upload script: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "▶️  Step 2: Executing deployment on EC2..." -ForegroundColor Yellow
Write-Host ""

# Execute the deployment script on EC2
$deployCommand = @"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${EC2_USER}@${EC2IP} "chmod +x ~/deploy_ec2.sh && bash ~/deploy_ec2.sh"
"@

try {
    # Execute and capture output
    $output = Invoke-Expression $deployCommand 2>&1
    
    # Print output with colors preserved where possible
    $output | ForEach-Object {
        $line = $_.ToString()
        if ($line -match "✅") {
            Write-Host $line -ForegroundColor Green
        } elseif ($line -match "⚠️|WARNING") {
            Write-Host $line -ForegroundColor Yellow
        } elseif ($line -match "❌|ERROR|FAILED") {
            Write-Host $line -ForegroundColor Red
        } elseif ($line -match "🚀|📂|🔄|🐳|🔨|📊|🏥|📋") {
            Write-Host $line -ForegroundColor Cyan
        } else {
            Write-Host $line
        }
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Deployment failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Deployment error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Test the API:" -ForegroundColor Yellow
Write-Host "   http://${EC2IP}:8080/healthz" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 View logs (SSH in and run):" -ForegroundColor Yellow
Write-Host "   sudo docker compose -f docker-compose.prod.yml logs -f" -ForegroundColor Gray
Write-Host ""

