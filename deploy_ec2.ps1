# ==============================
# FAME EC2 Deployment Script
# ==============================
# Configuration
$sshKey       = "C:\Users\cavek\Downloads\FAME.pem"
$user         = "ec2-user"
$ec2Host      = "3.135.222.143"
$localScript  = "deploy_ec2.sh"
$remoteScript = "/home/ec2-user/deploy_ec2.sh"

# Ensure local script exists
if (-not (Test-Path $localScript)) {
    Write-Host "Local deployment script $localScript not found!" -ForegroundColor Red
    exit 1
}

# Convert script to Unix line endings to avoid CRLF issues
Write-Host "Converting script to Unix line endings..."
$content = Get-Content $localScript -Raw
$content = $content -replace "`r`n", "`n" -replace "`r", "`n"
[System.IO.File]::WriteAllText((Resolve-Path $localScript), $content, [System.Text.UTF8Encoding]::new($false))

# Step 1: Upload the script to EC2
Write-Host "Uploading deployment script to EC2..." -ForegroundColor Yellow
$dest = "$user@${ec2Host}:$remoteScript"
scp -v -i $sshKey -o StrictHostKeyChecking=no $localScript $dest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Upload failed. Exit code: $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

Write-Host "Script uploaded successfully." -ForegroundColor Green

# Step 2: Run the script on EC2
Write-Host "Executing deployment script on EC2..." -ForegroundColor Yellow
ssh -v -i $sshKey -o StrictHostKeyChecking=no $user@$ec2Host "chmod +x $remoteScript && bash $remoteScript"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed on EC2. Exit code: $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

Write-Host "Deployment complete!" -ForegroundColor Green
