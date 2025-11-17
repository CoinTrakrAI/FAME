# Setup Elastic IP for FAME EC2 Instance
# Usage: .\setup_elastic_ip.ps1 -InstanceId "i-0123456789abcdef0"

param(
    [Parameter(Mandatory=$true)]
    [string]$InstanceId,
    
    [switch]$Force
)

Write-Host "🌐 Setting up Elastic IP for FAME EC2 Instance" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
} catch {
    Write-Host "❌ AWS CLI not found!" -ForegroundColor Red
    Write-Host "Please install AWS CLI: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}

# Check if instance exists and get its state
Write-Host "🔍 Checking instance status..." -ForegroundColor Yellow
try {
    $instanceState = aws ec2 describe-instances --instance-ids $InstanceId --query 'Reservations[0].Instances[0].State.Name' --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Instance not found: $InstanceId" -ForegroundColor Red
        Write-Host "Please check the instance ID in AWS Console" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "   Instance State: $instanceState" -ForegroundColor $(if ($instanceState -eq "running") { "Green" } else { "Yellow" })
    
    if ($instanceState -ne "running") {
        if (-not $Force) {
            Write-Host ""
            Write-Host "⚠️  Instance is not running. Current state: $instanceState" -ForegroundColor Yellow
            Write-Host "Would you like to start it? (Y/N)" -ForegroundColor Yellow
            $response = Read-Host
            if ($response -eq "Y" -or $response -eq "y") {
                Write-Host "🚀 Starting instance..." -ForegroundColor Cyan
                aws ec2 start-instances --instance-ids $InstanceId
                Write-Host "⏳ Waiting for instance to start..." -ForegroundColor Yellow
                Start-Sleep -Seconds 30
            } else {
                Write-Host "❌ Cannot proceed. Instance must be running to associate Elastic IP." -ForegroundColor Red
                exit 1
            }
        }
    }
} catch {
    Write-Host "❌ Error checking instance: $_" -ForegroundColor Red
    exit 1
}

# Check if instance already has an Elastic IP
Write-Host ""
Write-Host "🔍 Checking for existing Elastic IP..." -ForegroundColor Yellow
$existingEip = aws ec2 describe-addresses --filters "Name=instance-id,Values=$InstanceId" --query 'Addresses[0].PublicIp' --output text

if ($existingEip -and $existingEip -ne "None") {
    Write-Host "✅ Instance already has Elastic IP: $existingEip" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Your static IP address: $existingEip" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "SSH command:" -ForegroundColor Yellow
    Write-Host "  ssh -i `"C:\Users\cavek\Downloads\FAME.pem`" ec2-user@$existingEip" -ForegroundColor Gray
    exit 0
}

# Allocate new Elastic IP
Write-Host "📡 Allocating new Elastic IP..." -ForegroundColor Yellow
try {
    $allocationResult = aws ec2 allocate-address --domain vpc --output json | ConvertFrom-Json
    $allocationId = $allocationResult.AllocationId
    $elasticIp = $allocationResult.PublicIp
    
    Write-Host "✅ Elastic IP allocated successfully!" -ForegroundColor Green
    Write-Host "   Allocation ID: $allocationId" -ForegroundColor Gray
    Write-Host "   IP Address: $elasticIp" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Failed to allocate Elastic IP: $_" -ForegroundColor Red
    exit 1
}

# Associate Elastic IP with instance
Write-Host ""
Write-Host "🔗 Associating Elastic IP with instance..." -ForegroundColor Yellow
try {
    $associationResult = aws ec2 associate-address --instance-id $InstanceId --allocation-id $allocationId --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Elastic IP associated successfully!" -ForegroundColor Green
        Write-Host "   Association ID: $($associationResult.AssociationId)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed to associate Elastic IP" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error associating Elastic IP: $_" -ForegroundColor Red
    Write-Host "⚠️  Elastic IP was allocated but not associated. You can associate it manually in AWS Console." -ForegroundColor Yellow
    exit 1
}

# Verify
Write-Host ""
Write-Host "✅ Elastic IP setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Static IP Address: $elasticIp" -ForegroundColor Cyan
Write-Host "   This IP will never change!" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Save this information:" -ForegroundColor Yellow
Write-Host "   Elastic IP: $elasticIp" -ForegroundColor Gray
Write-Host "   Allocation ID: $allocationId" -ForegroundColor Gray
Write-Host "   Instance ID: $InstanceId" -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 SSH Command:" -ForegroundColor Yellow
Write-Host "   ssh -i `"C:\Users\cavek\Downloads\FAME.pem`" ec2-user@$elasticIp" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 API Endpoint:" -ForegroundColor Yellow
Write-Host "   http://$elasticIp:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Update deploy_to_ec2.ps1 with this IP address" -ForegroundColor Gray
Write-Host "   2. Update security group to allow port 8080" -ForegroundColor Gray
Write-Host "   3. Deploy FAME: .\deploy_to_ec2.ps1 -EC2IP `"$elasticIp`"" -ForegroundColor Gray

