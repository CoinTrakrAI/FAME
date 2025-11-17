#!/bin/bash
# FAME Deployment Script for AWS EC2
# Usage: ./deploy_to_ec2.sh <EC2_IP_ADDRESS>

set -e  # Exit on error

EC2_IP=${1:-"18.117.163.241"}
SSH_KEY="C:/Users/cavek/Downloads/FAME.pem"
EC2_USER="ec2-user"

echo "🚀 FAME Deployment to EC2"
echo "=========================="
echo "Target: ${EC2_USER}@${EC2_IP}"
echo ""

# Check if SSH key exists (Windows path)
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found: $SSH_KEY"
    echo "Please update SSH_KEY variable in this script"
    exit 1
fi

echo "📡 Connecting to EC2 instance..."
echo ""

# Deploy commands
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_IP} << 'ENDSSH'
    echo "✅ Connected to EC2 instance"
    echo ""
    
    # Check if FAME_Desktop directory exists
    if [ -d "FAME_Desktop" ]; then
        echo "📂 Found existing FAME_Desktop directory"
        cd FAME_Desktop
        echo "🔄 Pulling latest code from GitHub..."
        git pull origin main || echo "⚠️ Git pull failed, continuing with existing code"
    else
        echo "📂 Cloning FAME repository..."
        git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop
        cd FAME_Desktop
    fi
    
    echo ""
    echo "🐳 Stopping existing containers..."
    docker compose -f docker-compose.prod.yml down || echo "No containers to stop"
    
    echo ""
    echo "🔨 Building new containers..."
    docker compose -f docker-compose.prod.yml build --no-cache
    
    echo ""
    echo "🚀 Starting containers..."
    docker compose -f docker-compose.prod.yml up -d
    
    echo ""
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    echo ""
    echo "📊 Container status:"
    docker compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "📋 Recent logs:"
    docker compose -f docker-compose.prod.yml logs --tail=20
    
    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 API should be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
ENDSSH

echo ""
echo "🎉 Deployment script completed!"
echo ""
echo "To check status manually:"
echo "  ssh -i \"$SSH_KEY\" ${EC2_USER}@${EC2_IP}"
echo "  cd FAME_Desktop"
echo "  docker compose -f docker-compose.prod.yml logs -f"

