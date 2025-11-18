# Check container status and test if it's running

$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$ec2Host = "3.135.222.143"

# Check if container exists and test
ssh -i $sshKey -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$ec2Host "sudo docker ps | grep fame && curl -s http://localhost:8080/healthz | head -5" 2>&1

