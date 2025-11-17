# 🚀 FAME EC2 Deployment - Manual Steps

## **Quick Deployment (Copy & Paste)**

### **Step 1: SSH to EC2**
```powershell
ssh -i "C:\Users\cavek\Downloads\FAME.pem" ec2-user@52.15.178.92
```

### **Step 2: Once Connected, Run These Commands:**

```bash
# Navigate to FAME directory (or clone if needed)
cd ~/FAME_Desktop 2>/dev/null || git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop && cd FAME_Desktop

# Pull latest code
git pull origin main

# Stop existing containers
sudo docker compose -f docker-compose.prod.yml down

# Build new image
sudo docker compose -f docker-compose.prod.yml build --no-cache

# Start containers
sudo docker compose -f docker-compose.prod.yml up -d

# Check status
sudo docker compose -f docker-compose.prod.yml ps
sudo docker compose -f docker-compose.prod.yml logs -f
```

### **Step 3: Verify Deployment**

```bash
# Check if API is responding
curl http://localhost:8080/healthz

# Or from your local machine:
curl http://52.15.178.92:8080/healthz
```

---

## **Alternative: One-Line Deployment**

If you want to do it all at once (paste into SSH session):

```bash
cd ~/FAME_Desktop && git pull origin main && sudo docker compose -f docker-compose.prod.yml down && sudo docker compose -f docker-compose.prod.yml build --no-cache && sudo docker compose -f docker-compose.prod.yml up -d && sudo docker compose -f docker-compose.prod.yml ps
```

---

## **Troubleshooting**

### **If git is not installed:**
```bash
sudo yum install -y git
```

### **If docker compose fails:**
```bash
# Check Docker is running
sudo systemctl status docker

# Start Docker if needed
sudo systemctl start docker
```

### **If port 8080 is not accessible:**
- Check EC2 Security Group allows inbound traffic on port 8080
- AWS Console → EC2 → Security Groups → Edit inbound rules

---

**Ready to deploy! Just SSH in and run the commands above.**

