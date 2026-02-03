#!/bin/bash
set -e

# Veriqo Platform Unified Update Script
# Usage: ./update.sh [--full]
# --full: Forces a full reinstall of dependencies (removes node_modules)

FULL_UPDATE=false
if [ "$1" == "--full" ]; then
    FULL_UPDATE=true
fi

echo "🚀 Starting Veriqo Platform Update..."

# Configuration
APP_DIR="/opt/veriqo/app"
WEB_DIR="$APP_DIR/apps/web"
API_DIR="$APP_DIR/apps/api"
VERIQO_USER="veriqo"
BRANCH="main"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

cd "$APP_DIR" || exit 1

echo -e "${BLUE}📥 Pulling latest code...${NC}"
sudo -u "$VERIQO_USER" git fetch origin
sudo -u "$VERIQO_USER" git checkout $BRANCH
sudo -u "$VERIQO_USER" git pull origin $BRANCH

echo -e "${BLUE}🐍 Updating Backend...${NC}"
cd "$API_DIR" || exit 1
# Always ensure venv exists
if [ ! -d ".venv" ]; then
    sudo -u "$VERIQO_USER" python3 -m venv .venv
fi
sudo -u "$VERIQO_USER" "$API_DIR/.venv/bin/pip" install -r requirements.txt

echo -e "${BLUE}🗄️ Running Migrations...${NC}"
sudo -u "$VERIQO_USER" PYTHONPATH="$API_DIR/src" "$API_DIR/.venv/bin/alembic" upgrade head

echo -e "${BLUE}🎨 Updating Frontend...${NC}"
cd "$WEB_DIR" || exit 1

if [ "$FULL_UPDATE" = true ]; then
    echo -e "${YELLOW}🧹 Full update: Removing node_modules...${NC}"
    rm -rf node_modules dist
fi

sudo -u "$VERIQO_USER" npm install
sudo -u "$VERIQO_USER" npm run build

echo -e "${BLUE}🔄 Restarting Services...${NC}"
systemctl restart veriqo-api
systemctl reload nginx

# Health Check (Optional, requires curl)
echo -e "${BLUE}❤️ Checking System Health...${NC}"
sleep 2 # Wait for API to come up
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")

if [ "$HTTP_STATUS" == "200" ]; then
    echo -e "${GREEN}✅ System Updated & Healthy!${NC}"
else
    echo -e "${YELLOW}⚠️ System Updated but Health Check returned $HTTP_STATUS (API might still be starting)${NC}"
fi
