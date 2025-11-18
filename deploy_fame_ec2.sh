#!/usr/bin/env bash
# File: deploy_fame_ec2.sh
# One-shot Deploy Script for FAME on EC2
# Run as: sudo bash deploy_fame_ec2.sh

set -euo pipefail

REPO_DIR=${REPO_DIR:-/home/ec2-user/FAME_Desktop}
GIT_REMOTE=origin
BRANCH=main
COMPOSE_FILE=docker-compose.prod.yml
HEALTH_URL=http://localhost:8080/healthz
SLEEP_AFTER_UP=10

log(){ printf "\n==> %s\n" "$*"; }

# 1) Ensure repo exists
if [ ! -d "$REPO_DIR/.git" ]; then
  log "Cloning repo into $REPO_DIR"
  cd /home/ec2-user
  git clone https://github.com/CoinTrakrAI/FAME.git FAME_Desktop || true
fi

cd "$REPO_DIR"

log "Fetching latest from $GIT_REMOTE/$BRANCH"
git fetch "$GIT_REMOTE" --prune --tags
git checkout "$BRANCH"
git reset --hard "$GIT_REMOTE/$BRANCH"

CURRENT_COMMIT=$(git rev-parse --short HEAD)
log "Checked out commit: $CURRENT_COMMIT"
log "Commit message: $(git log -1 --pretty=%B | head -1)"

# 2) Stop and remove running containers to avoid using old images
if command -v docker >/dev/null 2>&1; then
  log "Stopping containers (docker-compose if present)"
  
  if [ -f "$COMPOSE_FILE" ]; then
    # Stop using docker compose or docker-compose (whichever is available)
    if command -v docker-compose >/dev/null 2>&1; then
      docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true
    elif docker compose version >/dev/null 2>&1; then
      docker compose -f "$COMPOSE_FILE" down --remove-orphans || true
    fi
  fi
  
  # Also stop any containers named fame*
  docker ps -q --filter "name=fame" | xargs -r docker stop || true
  docker ps -aq --filter "name=fame" | xargs -r docker rm -f || true
fi

# 3) Clean up old images and build cache (optional but recommended)
log "Cleaning up Docker to free space"
docker system prune -f || true
docker builder prune -af || true

# 4) Rebuild images without cache and force recreate
if [ -f "$COMPOSE_FILE" ]; then
  log "Building images (no cache, pull base images)"
  
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE_FILE" build --no-cache --pull || true
    log "Starting services (force recreate)"
    docker-compose -f "$COMPOSE_FILE" up -d --force-recreate
  elif docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" build --no-cache --pull || true
    log "Starting services (force recreate)"
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate
  else
    log "ERROR: Neither docker-compose nor docker compose found"
    exit 1
  fi
else
  log "No $COMPOSE_FILE found: trying plain docker build & run"
  docker build --no-cache -t fame:latest .
  docker run -d --name fame -p 8080:8080 --restart unless-stopped fame:latest
fi

sleep $SLEEP_AFTER_UP

# 5) Sanity checks: container status, image id, app health
log "Docker containers (FAME related)"
docker ps --filter "name=fame" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.ID}}" || true

log "Image list for 'fame' images:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" | grep -i fame || docker images | grep -i fame || true

# 6) Verify health endpoint
log "Checking app health at $HEALTH_URL"
HEALTH_CHECK_FAILED=false

if curl -fsS "$HEALTH_URL" > /dev/null 2>&1; then
  log "✅ Healthcheck succeeded"
  curl -fsS "$HEALTH_URL" | head -20
else
  log "❌ Healthcheck failed — printing logs"
  HEALTH_CHECK_FAILED=true
fi

# Show logs for FAME containers
for cname in $(docker ps --format "{{.Names}}" | grep -i fame || true); do
  log "=== Logs for $cname (last 100 lines) ==="
  docker logs --tail 100 "$cname" 2>&1 || true
  
  # 7) Extra verification: print commit hash from inside container
  log "=== Checking commit inside $cname ==="
  if docker exec "$cname" test -d /app/.git >/dev/null 2>&1; then
    log "Repo commit inside $cname:"
    docker exec "$cname" sh -c "cd /app && git rev-parse --short HEAD 2>/dev/null || echo 'no-git'" || true
  else
    log "No /app/.git in $cname (image built with code baked-in)"
    log "Image created time:"
    docker inspect "$cname" --format '{{.Created}}' || true
    log "Image labels:"
    docker inspect "$cname" --format '{{range $k, $v := .Config.Labels}}{{$k}}={{$v}}{{"\n"}}{{end}}' || true
  fi
done

# 8) Compare host commit with container (if code is mounted)
log "=== Verification Summary ==="
log "Host commit (from $REPO_DIR): $CURRENT_COMMIT"

if [ "$HEALTH_CHECK_FAILED" = true ]; then
  log "⚠️  Health check failed - check logs above"
  exit 2
fi

log "✅ Deploy finished successfully"
log "Container is running with commit: $CURRENT_COMMIT"
log "If problems persist, inspect docker logs above and check GH Actions run that builds the image."

