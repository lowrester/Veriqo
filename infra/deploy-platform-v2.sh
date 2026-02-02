#!/bin/bash
set -e

# Veriqo Platform V2 Deployment Script
# This script deploys the new platform version

echo "🚀 Starting Veriqo Platform V2 deployment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/veriqo/app"
WEB_DIR="$APP_DIR/apps/web"
VERIQO_USER="veriqo"
BRANCH="platform-v2"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Navigate to app directory
cd "$APP_DIR" || exit 1

echo -e "${BLUE}📥 Switching to branch $BRANCH...${NC}"
# Fetch and checkout branch
sudo -u "$VERIQO_USER" git fetch origin
sudo -u "$VERIQO_USER" git checkout $BRANCH
sudo -u "$VERIQO_USER" git pull origin $BRANCH

echo -e "${BLUE}📦 Cleaning generated files...${NC}"
# Remove generated files to avoid conflicts
sudo -u "$VERIQO_USER" rm -rf "$WEB_DIR/node_modules"
sudo -u "$VERIQO_USER" rm -rf "$WEB_DIR/dist"
sudo -u "$VERIQO_USER" rm -f "$WEB_DIR/package-lock.json"

echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
# Install properties
cd "$WEB_DIR" || exit 1
sudo -u "$VERIQO_USER" npm install

echo -e "${BLUE}🔨 Building frontend...${NC}"
# Build frontend
sudo -u "$VERIQO_USER" npm run build

# TODO: Run database migrations when they are ready
# echo -e "${BLUE}🗄️ Running database migrations...${NC}"
# cd "$API_DIR"
# sudo -u "$VERIQO_USER" alembic upgrade head

echo -e "${BLUE}🔄 Restarting services...${NC}"
systemctl restart veriqo-api
systemctl reload nginx

echo -e "${GREEN}✅ Platform V2 deployed successfully!${NC}"
echo -e "${YELLOW}🌐 Access at: http://$(hostname -I | awk '{print $1}')/${NC}"
