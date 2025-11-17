$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$user = "ec2-user"
$ec2Host = "52.15.178.92"
$localScript = "C:\Users\cavek\Downloads\FAME_Desktop\deploy_ec2.sh"
$remoteScript = "~/deploy_ec2.sh"
$ssh = "C:\Windows\System32\OpenSSH\ssh.exe"
$scp = "C:\Windows\System32\OpenSSH\scp.exe"

Write-Host "Uploading script..."
& $scp -i $sshKey -o StrictHostKeyChecking=no $localScript "$user@$ec2Host:$remoteScript"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Upload failed. Exit code: $LASTEXITCODE"
    exit 1
}

Write-Host "Running script on EC2..."
& $ssh -i $sshKey -o StrictHostKeyChecking=no "$user@$ec2Host" "chmod +x $remoteScript && bash $remoteScript"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed. Exit code: $LASTEXITCODE"
    exit 1
}

Write-Host "Deployment complete."
