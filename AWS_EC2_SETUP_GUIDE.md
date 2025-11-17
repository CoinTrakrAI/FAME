# 🚀 AWS EC2 Setup Guide - Static IP & Deployment

## 📋 **Table of Contents**
1. [Check Current EC2 Instance Status](#check-current-ec2-instance-status)
2. [Set Up Elastic IP (Static IP)](#set-up-elastic-ip-static-ip)
3. [Deploy FAME to EC2](#deploy-fame-to-ec2)
4. [Verify Deployment](#verify-deployment)

---

## 🔍 **Check Current EC2 Instance Status**

### **Method 1: AWS Console (Easiest)**

1. **Log into AWS Console:**
   - Go to: https://console.aws.amazon.com/ec2/
   - Sign in with your AWS account

2. **Navigate to EC2 Instances:**
   - Click "Instances" in the left sidebar
   - Find your FAME instance

3. **Check Instance Details:**
   - Look at the instance state (running, stopped, etc.)
   - Check the **Public IPv4 address** (this is your current IP)
   - Note the **Instance ID** (e.g., `i-0123456789abcdef0`)

4. **If Instance is Stopped:**
   - Select the instance
   - Click "Start instance"
   - Wait 1-2 minutes for it to start
   - **Note:** The IP will change when you restart!

### **Method 2: AWS CLI (Command Line)**

```powershell
# Install AWS CLI if not installed
# Download from: https://aws.amazon.com/cli/

# Configure AWS CLI (first time only)
aws configure
# Enter: Access Key ID, Secret Access Key, Region (e.g., us-east-2), Output format (json)

# List all EC2 instances
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress,PrivateIpAddress]' --output table

# Get specific instance details
aws ec2 describe-instances --instance-ids i-YOUR-INSTANCE-ID --query 'Reservations[0].Instances[0].[PublicIpAddress,State.Name]' --output table
```

### **Method 3: PowerShell Script**

Create `check_ec2_status.ps1`:

```powershell
# Check EC2 Instance Status
# Requires AWS CLI and credentials configured

Write-Host "🔍 Checking EC2 Instance Status..." -ForegroundColor Cyan
Write-Host ""

# List instances
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value|[0],InstanceId,State.Name,PublicIpAddress]' --output table

Write-Host ""
Write-Host "To get more details, use:" -ForegroundColor Yellow
Write-Host "  aws ec2 describe-instances --instance-ids i-YOUR-INSTANCE-ID" -ForegroundColor Gray
```

---

## 🌐 **Set Up Elastic IP (Static IP)**

**Why Elastic IP?**
- EC2 instances get a new public IP every time they restart
- Elastic IP gives you a **permanent static IP address**
- Free as long as it's attached to a running instance

### **Step-by-Step: Create and Assign Elastic IP**

#### **Method 1: AWS Console**

1. **Allocate Elastic IP:**
   - Go to EC2 Console → **Elastic IPs** (left sidebar)
   - Click **"Allocate Elastic IP address"**
   - Choose **"Amazon's pool of IPv4 addresses"**
   - Click **"Allocate"**
   - **Copy the Elastic IP address** (e.g., `54.123.45.67`)

2. **Associate Elastic IP with Instance:**
   - Select the Elastic IP you just created
   - Click **"Actions"** → **"Associate Elastic IP address"**
   - Select your FAME EC2 instance
   - Click **"Associate"**

3. **Verify:**
   - Go back to **Instances**
   - Your instance should now show the Elastic IP as its Public IP
   - **This IP will never change!**

#### **Method 2: AWS CLI**

```powershell
# 1. Allocate Elastic IP
$allocation = aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text
Write-Host "Elastic IP allocated: $allocation"

# 2. Get your instance ID (replace with your instance ID)
$instanceId = "i-0123456789abcdef0"

# 3. Associate Elastic IP with instance
aws ec2 associate-address --instance-id $instanceId --allocation-id $allocation

# 4. Get the Elastic IP address
$elasticIp = aws ec2 describe-addresses --allocation-ids $allocation --query 'Addresses[0].PublicIp' --output text
Write-Host "Elastic IP: $elasticIp"
```

#### **Method 3: PowerShell Script**

Create `setup_elastic_ip.ps1`:

```powershell
# Setup Elastic IP for FAME EC2 Instance
param(
    [Parameter(Mandatory=$true)]
    [string]$InstanceId
)

Write-Host "🌐 Setting up Elastic IP for instance: $InstanceId" -ForegroundColor Cyan
Write-Host ""

# Check if instance is running
$instanceState = aws ec2 describe-instances --instance-ids $InstanceId --query 'Reservations[0].Instances[0].State.Name' --output text

if ($instanceState -ne "running") {
    Write-Host "❌ Instance is not running. Current state: $instanceState" -ForegroundColor Red
    Write-Host "Please start the instance first." -ForegroundColor Yellow
    exit 1
}

# Allocate Elastic IP
Write-Host "📡 Allocating Elastic IP..." -ForegroundColor Yellow
$allocationId = aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text

if (-not $allocationId) {
    Write-Host "❌ Failed to allocate Elastic IP" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Elastic IP allocated: $allocationId" -ForegroundColor Green

# Associate with instance
Write-Host "🔗 Associating Elastic IP with instance..." -ForegroundColor Yellow
aws ec2 associate-address --instance-id $InstanceId --allocation-id $allocationId

# Get the Elastic IP address
$elasticIp = aws ec2 describe-addresses --allocation-ids $allocationId --query 'Addresses[0].PublicIp' --output text

Write-Host ""
Write-Host "✅ Elastic IP setup complete!" -ForegroundColor Green
Write-Host "📍 Static IP Address: $elasticIp" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now SSH using:" -ForegroundColor Yellow
Write-Host "  ssh -i `"C:\Users\cavek\Downloads\FAME.pem`" ec2-user@$elasticIp" -ForegroundColor Gray
Write-Host ""
Write-Host "Update your deployment scripts with this IP!" -ForegroundColor Yellow
```

**Usage:**
```powershell
.\setup_elastic_ip.ps1 -InstanceId "i-0123456789abcdef0"
```

---

## 🚀 **Deploy FAME to EC2**

### **Step 1: Update Deployment Script with Elastic IP**

Edit `deploy_to_ec2.ps1` and update the IP:

```powershell
param(
    [string]$EC2IP = "YOUR_ELASTIC_IP_HERE"  # ← Update this!
)
```

### **Step 2: Deploy**

```powershell
# Deploy to EC2
.\deploy_to_ec2.ps1

# Or specify IP manually
.\deploy_to_ec2.ps1 -EC2IP "54.123.45.67"
```

### **Step 3: Manual Deployment (Alternative)**

```powershell
# 1. SSH to EC2
ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@YOUR_ELASTIC_IP

# 2. On EC2, navigate to FAME directory
cd FAME_Desktop

# 3. Pull latest code
git pull origin main

# 4. Stop existing containers
docker compose -f docker-compose.prod.yml down

# 5. Build new containers
docker compose -f docker-compose.prod.yml build --no-cache

# 6. Start containers
docker compose -f docker-compose.prod.yml up -d

# 7. Check status
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

---

## ✅ **Verify Deployment**

### **1. Check Container Status**

```powershell
# SSH to EC2
ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@YOUR_ELASTIC_IP

# Check containers
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f fame
```

### **2. Test API Endpoints**

```powershell
# Health check
curl http://YOUR_ELASTIC_IP:8080/healthz

# Readiness check
curl http://YOUR_ELASTIC_IP:8080/readyz

# API docs
# Open in browser: http://YOUR_ELASTIC_IP:8080/docs
```

### **3. Test from Browser**

- **API Docs:** `http://YOUR_ELASTIC_IP:8080/docs`
- **Health:** `http://YOUR_ELASTIC_IP:8080/healthz`
- **Query:** `http://YOUR_ELASTIC_IP:8080/query` (POST request)

---

## 🔒 **Security Group Configuration**

Make sure your EC2 security group allows:

1. **SSH (Port 22):**
   - Type: SSH
   - Port: 22
   - Source: Your IP address (or 0.0.0.0/0 for testing - **not recommended for production**)

2. **FAME API (Port 8080):**
   - Type: Custom TCP
   - Port: 8080
   - Source: 0.0.0.0/0 (or specific IPs for production)

**To update Security Group:**
1. EC2 Console → Security Groups
2. Select your FAME security group
3. Inbound Rules → Edit
4. Add rules as above
5. Save

---

## 📝 **Quick Reference**

### **Important IPs to Save:**

```
Elastic IP: 54.123.45.67  ← Use this for SSH and API
Instance ID: i-0123456789abcdef0
Allocation ID: eipalloc-0123456789abcdef0
```

### **SSH Command:**
```powershell
ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@YOUR_ELASTIC_IP
```

### **Deployment Command:**
```powershell
.\deploy_to_ec2.ps1 -EC2IP "YOUR_ELASTIC_IP"
```

---

## ⚠️ **Important Notes**

1. **Elastic IP Costs:**
   - Free when attached to a running instance
   - $0.005/hour when not attached to any instance
   - Always attach to an instance to avoid charges

2. **IP Changes:**
   - Regular EC2 IPs change on restart
   - Elastic IPs never change (unless you release them)

3. **Backup:**
   - Save your Elastic IP address
   - Document your instance ID
   - Keep your .pem key secure

---

## 🆘 **Troubleshooting**

### **Can't SSH:**
- Check security group allows port 22
- Verify instance is running
- Check .pem key permissions: `icacls "C:\Users\cavek\Downloads\FAME.pem" /inheritance:r`
- Try: `ssh -v -i "FAME.pem" ec2-user@IP` for verbose output

### **Can't Access API:**
- Check security group allows port 8080
- Verify containers are running: `docker ps`
- Check logs: `docker compose logs -f`

### **Elastic IP Not Working:**
- Verify it's associated with your instance
- Check instance is running
- Wait a few minutes for DNS propagation

---

**Last Updated:** 2025-01-XX
**Status:** Ready for deployment with static IP

