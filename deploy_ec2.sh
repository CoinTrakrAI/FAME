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

# Install Docker Compose plugin (preferred method)
if ! docker compose version &> /dev/null 2>&1; then
    echo "Installing Docker Compose plugin..." | tee -a $LOG_FILE
    # Try to install docker-compose-plugin via yum (Amazon Linux 2023)
    if sudo yum install -y docker-compose-plugin -q 2>/dev/null; then
        echo "Docker Compose plugin installed via yum" | tee -a $LOG_FILE
    elif ! command -v docker-compose &> /dev/null; then
        # Fallback: install standalone docker-compose only if not already present
        echo "Installing standalone docker-compose..." | tee -a $LOG_FILE
        # Remove old version if it exists and is not busy
        if [ -f /usr/local/bin/docker-compose ]; then
            sudo rm -f /usr/local/bin/docker-compose
        fi
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    else
        echo "docker-compose already installed, skipping..." | tee -a $LOG_FILE
    fi
fi

# Determine which compose command to use (prefer docker compose plugin)
if docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    echo "Using: docker compose (plugin)" | tee -a $LOG_FILE
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo "Using: docker-compose (standalone)" | tee -a $LOG_FILE
else
    echo "ERROR: Docker Compose not available" | tee -a $LOG_FILE
    echo "Attempting to install..." | tee -a $LOG_FILE
    sudo yum install -y docker-compose-plugin -q
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        echo "Docker Compose plugin installed successfully" | tee -a $LOG_FILE
    else
        echo "ERROR: Failed to install Docker Compose" | tee -a $LOG_FILE
        exit 1
    fi
fi

# Verify the command works
echo "Verifying Docker Compose..." | tee -a $LOG_FILE
$COMPOSE_CMD version | tee -a $LOG_FILE

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

# Step 3: Clean up Docker and system to free space
echo "Cleaning up Docker to free space..." | tee -a $LOG_FILE
# Remove all stopped containers, unused networks, images, and build cache
sudo docker system prune -af --volumes | tee -a $LOG_FILE
sudo docker builder prune -af | tee -a $LOG_FILE
# Clean up old logs and temporary files
sudo journalctl --vacuum-time=1d 2>/dev/null || true
sudo apt-get clean 2>/dev/null || true
# Check disk space
echo "Current disk space:" | tee -a $LOG_FILE
df -h | tee -a $LOG_FILE

# Step 4: Stop and remove old containers (handle conflicts)
echo "Stopping and removing existing containers..." | tee -a $LOG_FILE
# Stop docker-compose managed containers
sudo $COMPOSE_CMD -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

# Remove any containers with conflicting names
EXISTING_CONTAINER=$(sudo docker ps -aq -f name=fame_desktop-fame-1 2>/dev/null || echo "")
if [ ! -z "$EXISTING_CONTAINER" ]; then
    echo "Removing conflicting container: $EXISTING_CONTAINER" | tee -a $LOG_FILE
    sudo docker rm -f $EXISTING_CONTAINER 2>/dev/null || true
fi

# Remove any other FAME containers that might be hanging around
sudo docker ps -a | grep -i fame | awk '{print $1}' | xargs -r sudo docker rm -f 2>/dev/null || true

# Clean up any hanging networks
sudo docker network prune -f 2>/dev/null || true

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

# Step 6: Build new Docker images (with cleanup between steps to save space)
echo "Building Docker images..." | tee -a $LOG_FILE
# Clean pip cache before build
sudo docker system prune -f 2>/dev/null || true
sudo $COMPOSE_CMD -f docker-compose.prod.yml build --no-cache | tee -a $LOG_FILE
# Clean up build cache after build to free space
sudo docker builder prune -f | tee -a $LOG_FILE

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
