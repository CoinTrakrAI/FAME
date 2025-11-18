# Quick test - just test FAME NOW

$sshKey = "C:\Users\cavek\Downloads\FAME.pem"
$ec2Host = "3.135.222.143"
$user = "ec2-user"

Write-Host "Testing FAME NOW..." -ForegroundColor Green

# Quick test from EC2
ssh -i $sshKey -o StrictHostKeyChecking=no "${user}@${ec2Host}" @"
curl -s -X POST http://localhost:8080/query -H 'Content-Type: application/json' -d '{\"text\":\"What is today date?\",\"session_id\":\"test\"}' 2>&1 | python3 -m json.tool 2>/dev/null || echo 'FAILED'
"@

