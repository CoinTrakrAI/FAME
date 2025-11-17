# Check EC2 Instance Status
# Requires AWS CLI: https://aws.amazon.com/cli/

Write-Host "🔍 Checking EC2 Instance Status..." -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is installed
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✅ AWS CLI found: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found!" -ForegroundColor Red
    Write-Host "Please install AWS CLI: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "📊 EC2 Instances:" -ForegroundColor Yellow
Write-Host ""

# List all instances with details
aws ec2 describe-instances `
    --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value|[0],InstanceId,State.Name,PublicIpAddress,PrivateIpAddress,InstanceType]' `
    --output table

Write-Host ""
Write-Host "🌐 Elastic IPs:" -ForegroundColor Yellow
Write-Host ""

# List Elastic IPs
aws ec2 describe-addresses `
    --query 'Addresses[*].[PublicIp,InstanceId,AssociationId,AllocationId]' `
    --output table

Write-Host ""
Write-Host "💡 To get more details about a specific instance:" -ForegroundColor Cyan
Write-Host "   aws ec2 describe-instances --instance-ids i-YOUR-INSTANCE-ID" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 To start a stopped instance:" -ForegroundColor Cyan
Write-Host "   aws ec2 start-instances --instance-ids i-YOUR-INSTANCE-ID" -ForegroundColor Gray

