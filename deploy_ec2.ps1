$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$user = "ec2-user"
$ec2Host = "52.15.178.92"
$localScript = "C:\Users\cavek\Downloads\FAME_Desktop\deploy_ec2.sh"
$remoteScript = "~/deploy_ec2.sh"

Write-Host "Uploading script..."
scp -i $sshKey $localScript "${user}@${ec2Host}:${remoteScript}"

Write-Host "Running script on EC2..."
ssh -i $sshKey "${user}@${ec2Host}" "chmod +x $remoteScript && bash $remoteScript"
