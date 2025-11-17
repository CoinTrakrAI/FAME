# Diagnostic script to identify deployment issues
Write-Host "=== FAME Deployment Diagnostics ===" -ForegroundColor Cyan
Write-Host ""

# Check 1: SSH key exists
$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
Write-Host "1. Checking SSH key..." -ForegroundColor Yellow
if (Test-Path $sshKey) {
    Write-Host "   SSH key found: $sshKey" -ForegroundColor Green
    $keyInfo = Get-Item $sshKey
    Write-Host "   Key size: $($keyInfo.Length) bytes" -ForegroundColor Gray
} else {
    Write-Host "   ERROR: SSH key not found!" -ForegroundColor Red
    exit 1
}

# Check 2: OpenSSH available
Write-Host ""
Write-Host "2. Checking OpenSSH..." -ForegroundColor Yellow
$sshPath = "C:\Windows\System32\OpenSSH\ssh.exe"
if (Test-Path $sshPath) {
    Write-Host "   OpenSSH found: $sshPath" -ForegroundColor Green
    $sshVersion = & $sshPath -V 2>&1
    Write-Host "   Version: $sshVersion" -ForegroundColor Gray
} else {
    Write-Host "   ERROR: OpenSSH not found!" -ForegroundColor Red
    Write-Host "   Install with: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor Yellow
    exit 1
}

# Check 3: Deployment scripts exist
Write-Host ""
Write-Host "3. Checking deployment scripts..." -ForegroundColor Yellow
$localScript = "deploy_ec2.sh"
$psScript = "deploy_ec2.ps1"
if (Test-Path $localScript) {
    Write-Host "   deploy_ec2.sh found" -ForegroundColor Green
} else {
    Write-Host "   ERROR: deploy_ec2.sh not found!" -ForegroundColor Red
    exit 1
}
if (Test-Path $psScript) {
    Write-Host "   deploy_ec2.ps1 found" -ForegroundColor Green
} else {
    Write-Host "   ERROR: deploy_ec2.ps1 not found!" -ForegroundColor Red
    exit 1
}

# Check 4: Test SSH connection (non-interactive)
Write-Host ""
Write-Host "4. Testing SSH connection..." -ForegroundColor Yellow
Write-Host "   This will attempt to connect (may take a few seconds)..." -ForegroundColor Gray
$testResult = & $sshPath -i $sshKey -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@18.220.108.23 "echo 'test'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   SSH connection successful!" -ForegroundColor Green
} else {
    Write-Host "   SSH connection failed. Exit code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "   Error output:" -ForegroundColor Yellow
    $testResult | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    Write-Host ""
    Write-Host "   Common issues:" -ForegroundColor Yellow
    Write-Host "   - EC2 instance may be stopped" -ForegroundColor Gray
    Write-Host "   - Security group may not allow SSH (port 22)" -ForegroundColor Gray
    Write-Host "   - IP address may have changed" -ForegroundColor Gray
    Write-Host "   - SSH key format may be incorrect" -ForegroundColor Gray
}

# Check 5: Key format
Write-Host ""
Write-Host "5. Checking SSH key format..." -ForegroundColor Yellow
$keyContent = Get-Content $sshKey -Raw
if ($keyContent -match "BEGIN.*PRIVATE KEY") {
    Write-Host "   Key format appears valid" -ForegroundColor Green
} else {
    Write-Host "   WARNING: Key format may be incorrect" -ForegroundColor Yellow
    Write-Host "   Expected: BEGIN PRIVATE KEY or BEGIN RSA PRIVATE KEY" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Diagnostics Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If SSH connection failed, check:" -ForegroundColor Yellow
Write-Host "1. EC2 instance is running (AWS Console)" -ForegroundColor Gray
Write-Host "2. Security group allows SSH from your IP" -ForegroundColor Gray
Write-Host "3. IP address is correct (18.220.108.23)" -ForegroundColor Gray
Write-Host "4. Try manual SSH: ssh -i `"$sshKey`" ec2-user@18.220.108.23" -ForegroundColor Gray

