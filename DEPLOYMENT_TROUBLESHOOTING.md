# Deployment Troubleshooting Guide

## Issue: Script Freezes During SSH/SCP

**Root Cause:** SSH commands are interactive and wait for responses, causing PowerShell to hang when run through automation tools.

## Solution: Run Diagnostics First

Run the diagnostic script to identify the exact issue:

```powershell
cd "C:\Users\cavek\Downloads\FAME_Desktop"
.\diagnose_deployment.ps1
```

## Common Issues and Fixes

### 1. SSH Connection Timeout
**Symptoms:** Script hangs at "Uploading script..." or "Connecting to..."

**Fixes:**
- Check EC2 instance is running: AWS Console → EC2 → Instances
- Verify IP address hasn't changed: Check current public IP in AWS Console
- Check security group allows SSH (port 22) from your IP
- Test manually: `ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@52.15.178.92`

### 2. SSH Key Format Issues
**Symptoms:** "identity file type -1" in verbose output

**Fixes:**
- Ensure key is in PEM format
- Check key permissions (should be readable)
- Try converting key: `ssh-keygen -p -m PEM -f "C:\Users\cavek\Downloads\FAME.pem"`

### 3. Script Upload Fails
**Symptoms:** SCP upload fails with exit code 1

**Fixes:**
- Check disk space on EC2: `df -h`
- Verify SSH connection works first
- Check file permissions on EC2

### 4. Remote Script Execution Fails
**Symptoms:** Upload succeeds but execution fails

**Fixes:**
- SSH in manually and run: `bash /home/ec2-user/deploy_ec2.sh`
- Check for errors in the script output
- Verify Docker is installed: `docker --version`
- Verify docker-compose is available: `docker compose version`

## Manual Deployment Steps

If automated deployment continues to fail, deploy manually:

1. **SSH to EC2:**
   ```powershell
   ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@52.15.178.92
   ```

2. **On EC2, run:**
   ```bash
   cd ~/FAME_Desktop || git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop && cd FAME_Desktop
   git pull origin main
   sudo docker compose -f docker-compose.prod.yml down
   sudo docker compose -f docker-compose.prod.yml build --no-cache
   sudo docker compose -f docker-compose.prod.yml up -d
   sudo docker compose -f docker-compose.prod.yml ps
   ```

## Next Steps

1. Run `.\diagnose_deployment.ps1` to identify the issue
2. Fix the identified problem
3. Try deployment again
4. If it still fails, use manual deployment steps above

