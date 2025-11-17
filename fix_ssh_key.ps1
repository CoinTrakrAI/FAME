# Fix SSH key format for OpenSSH compatibility
$sshKey = "C:\Users\cavek\Downloads\FAME.pem"

Write-Host "Checking SSH key format..." -ForegroundColor Yellow

if (-not (Test-Path $sshKey)) {
    Write-Host "SSH key not found: $sshKey" -ForegroundColor Red
    exit 1
}

$keyContent = Get-Content $sshKey -Raw

if ($keyContent -match "BEGIN.*PRIVATE KEY") {
    Write-Host "Key format appears valid" -ForegroundColor Green
    Write-Host ""
    Write-Host "To convert key format (if needed):" -ForegroundColor Yellow
    Write-Host "ssh-keygen -p -m PEM -f `"$sshKey`"" -ForegroundColor Gray
} else {
    Write-Host "Key format may need conversion" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Run this command to convert:" -ForegroundColor Yellow
    Write-Host "ssh-keygen -p -m PEM -f `"$sshKey`"" -ForegroundColor Cyan
}

