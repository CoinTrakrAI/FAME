#!/bin/bash
# ==============================
# FAME EC2 Deployment Script
# ==============================
set -euo pipefail

LOG_FILE="/home/ec2-user/fame_deploy.log"

echo "========== FAME Deployment ==========" | tee -a $LOG_FILE
echo "Starting deployment at $(date)" | tee -a $LOG_FILE

# Step 0: Install required tools
echo "Installing required tools..." | tee -a $LOG_FILE
if ! command -v git &> /dev/null; then
    echo "Installing git..." | tee -a $LOG_FILE
    sudo yum update -y -q
    sudo yum install -y git -q
fi

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..." | tee -a $LOG_FILE
    sudo yum install -y docker -q
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker ec2-user
fi

# Step 1: Ensure repo is present
cd /home/ec2-user || exit 1
if [ ! -d "FAME_Desktop" ]; then
    echo "Cloning FAME repository..." | tee -a $LOG_FILE
    git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop | tee -a $LOG_FILE
fi

cd FAME_Desktop

# Step 2: Pull latest changes
echo "Pulling latest changes..." | tee -a $LOG_FILE
git fetch origin main | tee -a $LOG_FILE
git reset --hard origin/main | tee -a $LOG_FILE

# Step 3: Stop old containers (if any)
if docker compose -f docker-compose.prod.yml ps -q | grep -q .; then
    echo "Stopping old containers..." | tee -a $LOG_FILE
    sudo docker compose -f docker-compose.prod.yml down | tee -a $LOG_FILE
fi

# Step 4: Build new Docker images
echo "Building Docker images..." | tee -a $LOG_FILE
sudo docker compose -f docker-compose.prod.yml build --no-cache | tee -a $LOG_FILE

# Step 5: Start containers
echo "Starting containers..." | tee -a $LOG_FILE
sudo docker compose -f docker-compose.prod.yml up -d | tee -a $LOG_FILE

# Step 6: Show container status
echo "Container status:" | tee -a $LOG_FILE
sudo docker compose -f docker-compose.prod.yml ps | tee -a $LOG_FILE

# Step 7: Health checks
echo "Performing health checks..." | tee -a $LOG_FILE
for service in $(sudo docker compose -f docker-compose.prod.yml ps --services); do
    echo "Checking $service..." | tee -a $LOG_FILE
    status=$(sudo docker inspect -f '{{.State.Health.Status}}' "$service" 2>/dev/null || echo "unknown")
    echo "$service: $status" | tee -a $LOG_FILE
done

echo "Deployment finished at $(date)" | tee -a $LOG_FILE
echo "========== END ==========" | tee -a $LOG_FILE
