# EC2 Instance Cleanup and Verification Checklist
# Helps identify and clean up multiple EC2 instances

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EC2 Instance Cleanup Checklist" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is available
$awsCliAvailable = $false
try {
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $awsCliAvailable = $true
        Write-Host "AWS CLI found: $awsVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "AWS CLI not found (optional)" -ForegroundColor Yellow
}

Write-Host ""

if ($awsCliAvailable) {
    Write-Host "Listing all EC2 instances..." -ForegroundColor Yellow
    Write-Host ""
    
    # List all instances
    $instances = aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress,PrivateIpAddress,Tags[?Key==`Name`].Value|[0]]' --output table
    
    Write-Host $instances
    Write-Host ""
    
    # Check for multiple running instances
    $runningInstances = aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress]' --output text
    
    Write-Host "Running instances:" -ForegroundColor Yellow
    $runningInstances | ForEach-Object {
        if ($_ -match "i-") {
            Write-Host "  Instance ID: $_" -ForegroundColor Gray
        } elseif ($_ -match "\d+\.\d+\.\d+\.\d+") {
            Write-Host "  Public IP: $_" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "Target IP: 52.15.178.92" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if target IP exists
    $targetInstance = aws ec2 describe-instances --filters "Name=ip-address,Values=52.15.178.92" --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' --output text
    
    if ($targetInstance) {
        Write-Host "Instance with IP 52.15.178.92:" -ForegroundColor Green
        Write-Host "  $targetInstance" -ForegroundColor Gray
    } else {
        Write-Host "WARNING: No instance found with IP 52.15.178.92" -ForegroundColor Yellow
        Write-Host "  The IP may have changed. Check AWS Console for current IP." -ForegroundColor Gray
    }
    
} else {
    Write-Host "Manual Checklist (AWS CLI not available):" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Go to AWS Console → EC2 → Instances" -ForegroundColor Cyan
    Write-Host "2. Check for multiple running instances" -ForegroundColor Gray
    Write-Host "3. Identify which instance has IP: 52.15.178.92" -ForegroundColor Gray
    Write-Host "4. Stop or terminate any unnecessary instances" -ForegroundColor Gray
    Write-Host "5. Verify only ONE instance is running for FAME deployment" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Before deploying, verify:" -ForegroundColor Yellow
Write-Host "  [ ] Only ONE EC2 instance is running" -ForegroundColor Gray
Write-Host "  [ ] Instance IP matches: 52.15.178.92" -ForegroundColor Gray
Write-Host "  [ ] Security group allows SSH (port 22) from your IP" -ForegroundColor Gray
Write-Host "  [ ] Instance is in 'running' state (not stopping/starting)" -ForegroundColor Gray
Write-Host "  [ ] No other deployments are active on this instance" -ForegroundColor Gray
Write-Host ""
Write-Host "If multiple instances found:" -ForegroundColor Yellow
Write-Host "  1. Stop unnecessary instances (AWS Console → EC2 → Instances → Stop)" -ForegroundColor Gray
Write-Host "  2. Or terminate if no longer needed" -ForegroundColor Gray
Write-Host "  3. Wait 1-2 minutes for instance to fully stop" -ForegroundColor Gray
Write-Host "  4. Verify only target instance is running" -ForegroundColor Gray
Write-Host ""
Write-Host "After cleanup, test SSH:" -ForegroundColor Yellow
Write-Host "  ssh -i `"C:\Users\cavek\Downloads\FAME.pem`" ec2-user@52.15.178.92" -ForegroundColor Cyan
Write-Host ""
Write-Host "If SSH works, deploy with:" -ForegroundColor Yellow
Write-Host "  .\deploy_ec2.ps1" -ForegroundColor Cyan
Write-Host ""

