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

# Install Docker Compose if not available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose..." | tee -a $LOG_FILE
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Determine which compose command to use
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "ERROR: Docker Compose not available" | tee -a $LOG_FILE
    exit 1
fi

# Step 1: Ensure repo is present
cd /home/ec2-user || exit 1
if [ ! -d "FAME_Desktop" ]; then
    echo "Cloning FAME repository..." | tee -a $LOG_FILE
    git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop | tee -a $LOG_FILE
    cd FAME_Desktop
elif [ ! -d "FAME_Desktop/.git" ]; then
    echo "FAME_Desktop exists but is not a git repo. Removing and cloning..." | tee -a $LOG_FILE
    rm -rf FAME_Desktop
    git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop | tee -a $LOG_FILE
    cd FAME_Desktop
else
    cd FAME_Desktop
    # Step 2: Pull latest changes
    echo "Pulling latest changes..." | tee -a $LOG_FILE
    git fetch origin main | tee -a $LOG_FILE
    git reset --hard origin/main | tee -a $LOG_FILE
fi

# Step 3: Clean up Docker to free space
echo "Cleaning up Docker to free space..." | tee -a $LOG_FILE
sudo docker system prune -af --volumes | tee -a $LOG_FILE
sudo docker builder prune -af | tee -a $LOG_FILE

# Step 4: Stop old containers (if any)
if $COMPOSE_CMD -f docker-compose.prod.yml ps -q 2>/dev/null | grep -q .; then
    echo "Stopping old containers..." | tee -a $LOG_FILE
    sudo $COMPOSE_CMD -f docker-compose.prod.yml down | tee -a $LOG_FILE
fi

# Step 5: Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..." | tee -a $LOG_FILE
    if [ -f "config/env.example" ]; then
        cp config/env.example .env
        echo "WARNING: .env file created from template. Please update with your API keys!" | tee -a $LOG_FILE
    else
        echo "ERROR: config/env.example not found. Creating minimal .env..." | tee -a $LOG_FILE
        cat > .env << 'EOF'
# FAME Environment Variables
# Update these with your actual API keys
FAME_ENV=production
EOF
    fi
fi

# Step 6: Build new Docker images
echo "Building Docker images..." | tee -a $LOG_FILE
sudo $COMPOSE_CMD -f docker-compose.prod.yml build --no-cache | tee -a $LOG_FILE

# Step 7: Start containers
echo "Starting containers..." | tee -a $LOG_FILE
sudo $COMPOSE_CMD -f docker-compose.prod.yml up -d | tee -a $LOG_FILE

# Step 8: Show container status
echo "Container status:" | tee -a $LOG_FILE
sudo $COMPOSE_CMD -f docker-compose.prod.yml ps | tee -a $LOG_FILE

# Step 9: Health checks
echo "Performing health checks..." | tee -a $LOG_FILE
for service in $(sudo $COMPOSE_CMD -f docker-compose.prod.yml ps --services 2>/dev/null); do
    echo "Checking $service..." | tee -a $LOG_FILE
    status=$(sudo docker inspect -f '{{.State.Health.Status}}' "$service" 2>/dev/null || echo "unknown")
    echo "$service: $status" | tee -a $LOG_FILE
done

echo "Deployment finished at $(date)" | tee -a $LOG_FILE
echo "========== END ==========" | tee -a $LOG_FILE
