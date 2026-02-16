#!/bin/bash
#===============================================================================
# Veriqko Platform Unified Update Script
#
# Usage: ./update.sh [options]
#
# Options:
#   --full          Forces a full reinstall (removes node_modules)
#   --api           Update only the API/Backend
#   --web           Update only the Web/Frontend
#   --infra         Update only infrastructure configs
#   --no-migrate    Skip database migrations
#   --help          Show this help
#===============================================================================

set -e

# Configuration
INFRA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$INFRA_DIR/.." && pwd)"
WEB_DIR="$APP_DIR/apps/web"
API_DIR="$APP_DIR/apps/api"
BRANCH="main"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Parse arguments
UPDATE_API=true
UPDATE_WEB=true
UPDATE_INFRA=false
RUN_MIGRATIONS=true
FULL_UPDATE=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --full) FULL_UPDATE=true ;;
        --api) UPDATE_API=true; UPDATE_WEB=false ;;
        --web) UPDATE_WEB=true; UPDATE_API=false ;;
        --infra) UPDATE_INFRA=true ;;
        --no-migrate) RUN_MIGRATIONS=false ;;
        --help)
            echo "Usage: $0 [--full] [--api|--web|--infra] [--no-migrate]"
            exit 0
            ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root (use sudo)"
fi

# Detect user
if id "veriqko" &>/dev/null; then
    VERIQKO_USER="veriqko"
elif id "veriqo" &>/dev/null; then
    VERIQKO_USER="veriqo"
else
    VERIQKO_USER=$(logname || echo $USER)
fi

update_repo() {
    log "📥 Pulling latest code from $BRANCH..."
    cd "$APP_DIR"
    sudo -u "$VERIQKO_USER" git fetch origin
    sudo -u "$VERIQKO_USER" git reset --hard origin/$BRANCH
}

update_backend() {
    log "🐍 Updating Backend..."
    cd "$API_DIR"
    
    if [ ! -d ".venv" ]; then
        warn "Virtual environment not found, creating..."
        sudo -u "$VERIQKO_USER" python3 -m venv .venv
    fi
    
    sudo -u "$VERIQKO_USER" "$API_DIR/.venv/bin/pip" install --no-cache-dir -r requirements.txt
    
    if [ "$RUN_MIGRATIONS" = true ]; then
        log "🗄️ Running Migrations..."
        sudo -u "$VERIQKO_USER" PYTHONPATH="$API_DIR/src" "$API_DIR/.venv/bin/alembic" upgrade head
    fi
}

update_frontend() {
    log "🎨 Updating Frontend..."
    cd "$WEB_DIR"
    
    if [ "$FULL_UPDATE" = true ]; then
        log "🧹 Full update: Removing node_modules and dist..."
        rm -rf node_modules dist
    fi
    
    sudo -u "$VERIQKO_USER" npm install
    sudo -u "$VERIQKO_USER" npm run build
}

restart_services() {
    log "🔄 Restarting Services..."
    if systemctl is-active --quiet veriqko-api; then
        systemctl restart veriqko-api
    fi
    systemctl reload nginx
}

health_check() {
    log "❤️ Checking System Health..."
    sleep 3
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
    
    if [ "$HTTP_STATUS" == "200" ]; then
        log "✅ System Updated & Healthy!"
    else
        warn "⚠️ System Updated but Health Check returned $HTTP_STATUS (API might still be starting)"
    fi
}

# Main Execution
log "🚀 Starting Veriqko Platform Update..."

update_repo

if [ "$UPDATE_API" = true ]; then
    update_backend
fi

if [ "$UPDATE_WEB" = true ]; then
    update_frontend
fi

if [ "$UPDATE_INFRA" = true ]; then
    log "🛠️ Updating Infrastructure configs..."
    # Add logic here to sync nginx configs if needed
    cp "$INFRA_DIR/veriqko.nginx.conf" /etc/nginx/sites-available/veriqko
    nginx -t && systemctl reload nginx
fi

restart_services
health_check

log "✨ Update procedure finished."
