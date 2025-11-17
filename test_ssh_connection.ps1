# Comprehensive SSH Connection Diagnostics
# Tests all aspects of EC2 SSH connectivity

$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$user = "ec2-user"
$ec2Host = "52.15.178.92"
$ssh = "C:\Windows\System32\OpenSSH\ssh.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SSH Connection Diagnostics" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Key file exists and is readable
Write-Host "Test 1: SSH Key File" -ForegroundColor Yellow
if (Test-Path $sshKey) {
    $keyInfo = Get-Item $sshKey
    Write-Host "  Key found: $sshKey" -ForegroundColor Green
    Write-Host "  Size: $($keyInfo.Length) bytes" -ForegroundColor Gray
    Write-Host "  Permissions: $($keyInfo.Attributes)" -ForegroundColor Gray
    
    # Check key format
    $keyContent = Get-Content $sshKey -Raw
    if ($keyContent -match "BEGIN.*PRIVATE KEY") {
        Write-Host "  Format: Valid PEM format" -ForegroundColor Green
    } else {
        Write-Host "  Format: WARNING - May need conversion" -ForegroundColor Yellow
        Write-Host "  Run: ssh-keygen -p -m PEM -f `"$sshKey`"" -ForegroundColor Gray
    }
} else {
    Write-Host "  ERROR: Key file not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: OpenSSH available
Write-Host "Test 2: OpenSSH Client" -ForegroundColor Yellow
if (Test-Path $ssh) {
    $version = & $ssh -V 2>&1
    Write-Host "  OpenSSH found: $version" -ForegroundColor Green
} else {
    Write-Host "  ERROR: OpenSSH not found!" -ForegroundColor Red
    Write-Host "  Install: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 3: Network connectivity (ping)
Write-Host "Test 3: Network Connectivity" -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName $ec2Host -Count 2 -Quiet
if ($pingResult) {
    Write-Host "  Ping successful: $ec2Host is reachable" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Cannot ping $ec2Host" -ForegroundColor Yellow
    Write-Host "  This may be normal if ICMP is blocked" -ForegroundColor Gray
}

Write-Host ""

# Test 4: Port 22 connectivity
Write-Host "Test 4: Port 22 (SSH) Connectivity" -ForegroundColor Yellow
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connect = $tcpClient.BeginConnect($ec2Host, 22, $null, $null)
    $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
    if ($wait) {
        $tcpClient.EndConnect($connect)
        Write-Host "  Port 22 is open and accepting connections" -ForegroundColor Green
        $tcpClient.Close()
    } else {
        Write-Host "  ERROR: Port 22 connection timed out" -ForegroundColor Red
        Write-Host "  Check: Security group allows SSH from your IP" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ERROR: Cannot connect to port 22" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Gray
}

Write-Host ""

# Test 5: SSH connection attempt (with timeout)
Write-Host "Test 5: SSH Authentication" -ForegroundColor Yellow
Write-Host "  Attempting SSH connection (5 second timeout)..." -ForegroundColor Gray

$sshTest = Start-Job -ScriptBlock {
    param($sshPath, $key, $host, $user)
    & $sshPath -i $key -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$user@$host" "echo 'SSH test successful'" 2>&1
} -ArgumentList $ssh, $sshKey, $ec2Host, $user

$result = Wait-Job $sshTest -Timeout 6
if ($result) {
    $output = Receive-Job $sshTest
    Remove-Job $sshTest
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  SSH connection successful!" -ForegroundColor Green
        Write-Host "  Output: $output" -ForegroundColor Gray
    } else {
        Write-Host "  SSH connection failed" -ForegroundColor Red
        Write-Host "  Exit code: $LASTEXITCODE" -ForegroundColor Gray
        Write-Host "  Error output:" -ForegroundColor Yellow
        $output | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        
        # Analyze common errors
        $errorText = $output -join " "
        if ($errorText -match "Permission denied") {
            Write-Host ""
            Write-Host "  DIAGNOSIS: Authentication failed" -ForegroundColor Red
            Write-Host "  - Key may be incorrect for this instance" -ForegroundColor Yellow
            Write-Host "  - User may be wrong (try 'ubuntu' for Ubuntu instances)" -ForegroundColor Yellow
        } elseif ($errorText -match "Connection timed out") {
            Write-Host ""
            Write-Host "  DIAGNOSIS: Connection timeout" -ForegroundColor Red
            Write-Host "  - EC2 instance may be stopped" -ForegroundColor Yellow
            Write-Host "  - Security group may block SSH" -ForegroundColor Yellow
            Write-Host "  - IP address may have changed" -ForegroundColor Yellow
        } elseif ($errorText -match "Connection refused") {
            Write-Host ""
            Write-Host "  DIAGNOSIS: Connection refused" -ForegroundColor Red
            Write-Host "  - SSH service may not be running on EC2" -ForegroundColor Yellow
            Write-Host "  - Port 22 may be blocked" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  SSH connection timed out (took longer than 5 seconds)" -ForegroundColor Red
    Write-Host "  This usually means:" -ForegroundColor Yellow
    Write-Host "  - EC2 instance is stopped" -ForegroundColor Gray
    Write-Host "  - Security group blocks your IP" -ForegroundColor Gray
    Write-Host "  - Network routing issue" -ForegroundColor Gray
    Remove-Job $sshTest -Force
}

Write-Host ""

# Test 6: SCP test (if SSH works)
if ($LASTEXITCODE -eq 0) {
    Write-Host "Test 6: SCP Upload Test" -ForegroundColor Yellow
    $testFile = "test_upload.txt"
    "test" | Out-File $testFile
    $scp = "C:\Windows\System32\OpenSSH\scp.exe"
    
    $scpDest = "$user@${ec2Host}:/tmp/"
    & $scp -i $sshKey -o StrictHostKeyChecking=no $testFile $scpDest 2>&1 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  SCP upload successful!" -ForegroundColor Green
    } else {
        Write-Host "  SCP upload failed" -ForegroundColor Red
    }
    
    Remove-Item $testFile -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnostics Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Summary and recommendations
Write-Host "Summary:" -ForegroundColor Yellow
if ($LASTEXITCODE -eq 0) {
    Write-Host "  All tests passed! SSH connection is working." -ForegroundColor Green
    Write-Host "  You can now run: .\deploy_ec2.ps1" -ForegroundColor Cyan
} else {
    Write-Host "  SSH connection is not working. Fix the issues above first." -ForegroundColor Red
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Check EC2 instance status in AWS Console" -ForegroundColor Gray
    Write-Host "  2. Verify security group allows SSH (port 22) from your IP" -ForegroundColor Gray
    Write-Host "  3. Check if IP address changed (get current IP from AWS Console)" -ForegroundColor Gray
    Write-Host "  4. Try converting key: ssh-keygen -p -m PEM -f `"$sshKey`"" -ForegroundColor Gray
}

