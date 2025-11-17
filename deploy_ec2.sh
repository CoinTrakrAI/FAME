#!/bin/bash
# FAME EC2 Deployment Script
# This script is uploaded and executed on the EC2 instance

set -e  # Exit on error

echo "=========================================="
echo "🚀 FAME Production Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FAME_DIR="$HOME/FAME_Desktop"
COMPOSE_FILE="docker-compose.prod.yml"

echo -e "${YELLOW}📂 Step 1: Navigate to FAME directory${NC}"
if [ -d "$FAME_DIR" ]; then
    cd "$FAME_DIR"
    echo -e "${GREEN}✅ Found existing FAME directory${NC}"
else
    echo -e "${YELLOW}📥 Cloning FAME repository...${NC}"
    git clone https://github.com/CoinTrakrAI/FAME.git "$FAME_DIR"
    cd "$FAME_DIR"
    echo -e "${GREEN}✅ Repository cloned${NC}"
fi

echo ""
echo -e "${YELLOW}🔄 Step 2: Update repository${NC}"
git fetch origin
git pull origin main
LATEST_COMMIT=$(git log -1 --oneline)
echo -e "${GREEN}✅ Updated to: $LATEST_COMMIT${NC}"

echo ""
echo -e "${YELLOW}🐳 Step 3: Stop existing containers${NC}"
if sudo docker compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
    sudo docker compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}✅ Containers stopped${NC}"
else
    echo -e "${YELLOW}⚠️  No running containers found${NC}"
fi

echo ""
echo -e "${YELLOW}🔨 Step 4: Rebuild Docker images${NC}"
sudo docker compose -f "$COMPOSE_FILE" build --no-cache
echo -e "${GREEN}✅ Images rebuilt${NC}"

echo ""
echo -e "${YELLOW}🚀 Step 5: Start production containers${NC}"
sudo docker compose -f "$COMPOSE_FILE" up -d
echo -e "${GREEN}✅ Containers started${NC}"

echo ""
echo -e "${YELLOW}⏳ Step 6: Wait for services to be ready${NC}"
sleep 10

echo ""
echo -e "${YELLOW}📊 Step 7: Container Status${NC}"
sudo docker compose -f "$COMPOSE_FILE" ps

echo ""
echo -e "${YELLOW}🏥 Step 8: Health Check${NC}"
HEALTH_URL="http://localhost:8080/healthz"
if command -v curl &> /dev/null; then
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
    if [ "$HEALTH_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Health check passed (HTTP $HEALTH_STATUS)${NC}"
    else
        echo -e "${RED}⚠️  Health check returned HTTP $HEALTH_STATUS${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  curl not available, skipping health check${NC}"
fi

echo ""
echo -e "${YELLOW}📋 Step 9: Recent Logs${NC}"
sudo docker compose -f "$COMPOSE_FILE" logs --tail=20

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "🌐 API should be available at:"
echo "   http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
echo ""
echo "📊 To view logs:"
echo "   sudo docker compose -f $COMPOSE_FILE logs -f"
echo ""
echo "🛑 To stop services:"
echo "   sudo docker compose -f $COMPOSE_FILE down"
echo ""

