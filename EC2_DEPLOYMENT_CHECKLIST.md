# EC2 Deployment Checklist - Multiple Instance Cleanup

## Problem: SSH Hangs Due to Multiple Instances

If you have **multiple EC2 instances running**, SSH can hang because:
- Multiple instances share the same security group
- IP conflicts or routing issues
- Stale connections to wrong instances
- Conflicting Elastic IP assignments

---

## Step-by-Step Cleanup Process

### **Step 1: Identify All Running Instances**

#### Option A: AWS Console (Recommended)
1. Go to: https://console.aws.amazon.com/ec2/
2. Click **"Instances"** (left sidebar)
3. Check the **"State"** column for all instances
4. Note which instances are **"running"**

#### Option B: AWS CLI
```powershell
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' --output table
```

Or run:
```powershell
.\ec2_cleanup_checklist.ps1
```

---

### **Step 2: Identify Your Target Instance**

Your deployment target:
- **IP Address:** `52.15.178.92`
- **User:** `ec2-user`
- **Purpose:** FAME production deployment

**Action:** Find which instance ID has this IP address.

---

### **Step 3: Stop Unnecessary Instances**

For each instance that is **NOT** your target:

1. **Select the instance** in AWS Console
2. **Instance State** → **Stop Instance**
3. **Confirm** the stop action
4. **Wait 1-2 minutes** for instance to fully stop

**OR** if you don't need them:
- **Instance State** → **Terminate Instance**
- **Confirm** termination

---

### **Step 4: Verify Only Target Instance is Running**

After cleanup:
- Only **ONE** instance should be in "running" state
- That instance should have IP: `52.15.178.92`
- Instance should be fully started (not "pending" or "stopping")

---

### **Step 5: Verify Security Group**

1. Select your target instance
2. Click **"Security"** tab
3. Click on the **Security Group** name
4. Check **"Inbound rules"**:
   - **Type:** SSH
   - **Port:** 22
   - **Source:** Your IP address (or `0.0.0.0/0` for testing)

If SSH rule is missing:
- Click **"Edit inbound rules"**
- Click **"Add rule"**
- Type: SSH, Port: 22, Source: Your IP
- Click **"Save rules"**

---

### **Step 6: Test SSH Connection**

```powershell
ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@52.15.178.92
```

**Expected:** You should get a shell prompt immediately.

**If it hangs:**
- Instance may still be starting (wait 2-3 minutes)
- Security group may still be updating (wait 30 seconds)
- IP address may have changed (check AWS Console)

---

### **Step 7: Get Current IP (If Changed)**

If the instance was stopped/started, the IP may have changed:

1. AWS Console → EC2 → Instances
2. Select your instance
3. Check **"Public IPv4 address"** field
4. Update `deploy_ec2.ps1` with new IP if different

---

### **Step 8: Deploy**

Once SSH works:

```powershell
cd "C:\Users\cavek\Downloads\FAME_Desktop"
.\deploy_ec2.ps1
```

---

## Quick Verification Commands

### Check Instance Status (AWS CLI)
```powershell
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --query 'Reservations[*].Instances[*].[InstanceId,PublicIpAddress,State.Name]' --output table
```

### Check Specific IP
```powershell
aws ec2 describe-instances --filters "Name=ip-address,Values=52.15.178.92" --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' --output text
```

### Stop All Except Target
```powershell
# Get target instance ID first, then:
aws ec2 stop-instances --instance-ids i-OTHER-INSTANCE-ID
```

---

## Common Issues

### Issue: "Multiple instances with same IP"
**Fix:** Only one instance can have a public IP at a time. Stop others.

### Issue: "SSH connects but hangs"
**Fix:** Instance may be starting. Wait 2-3 minutes after start.

### Issue: "Connection refused"
**Fix:** Security group doesn't allow SSH. Add inbound rule for port 22.

### Issue: "Permission denied"
**Fix:** Wrong SSH key or wrong user. Verify key matches instance.

---

## After Cleanup

Once only ONE instance is running:

1. ✅ Verify SSH works: `ssh -i "FAME.pem" ec2-user@52.15.178.92`
2. ✅ Run diagnostics: `.\test_ssh_connection.ps1`
3. ✅ Deploy: `.\deploy_ec2.ps1`

Your deployment scripts are ready - they just need a clean, single-instance environment to work properly.

