$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$user = "ec2-user"
$ec2Host = "52.15.178.92"
$localScript = "C:\Users\cavek\Downloads\FAME_Desktop\deploy_ec2.sh"
$remoteScript = "/home/ec2-user/deploy_ec2.sh"
$ssh = "C:\Windows\System32\OpenSSH\ssh.exe"
$scp = "C:\Windows\System32\OpenSSH\scp.exe"

if (-not (Test-Path $localScript)) {
    Write-Host "Error: deploy_ec2.sh not found at $localScript"
    exit 1
}

Write-Host "Uploading script..."
$dest = "$user@$ec2Host`:$remoteScript"
& $scp -i $sshKey -o StrictHostKeyChecking=no $localScript $dest

if ($LASTEXITCODE -ne 0) {
    Write-Host "Upload failed. Exit code: $LASTEXITCODE"
    exit 1
}

Write-Host "Script uploaded successfully"
Write-Host "Running script on EC2..."
$sshCmd = "chmod +x $remoteScript; bash $remoteScript"
& $ssh -i $sshKey -o StrictHostKeyChecking=no "$user@$ec2Host" $sshCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed. Exit code: $LASTEXITCODE"
    exit 1
}

Write-Host "Deployment complete."
