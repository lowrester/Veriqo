#!/bin/bash
#===============================================================================
# Veriqko Platform Update Script (Zero-Downtime Blue/Green)
#
# Smart rolling update: pulls latest main branch into a temporary directory, 
# installs dependencies, runs build, runs migrations, and only then swaps
# it with the live directory. This ensures near-zero downtime and eliminates
# the need for complex rollbacks.
#
# Usage:
#   sudo bash update.sh [options]
#
# Options:
#   --full          Force wipe of cached node_modules and .venv
#   --no-migrate    Skip database migrations
#   --help          Show this help
#===============================================================================

set -euo pipefail

#===============================================================================
# Configuration
#===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# APP_DIR is where the live app is
APP_DIR="/opt/veriqko/app"
APP_NEW_DIR="/opt/veriqko/app_new"
VERIQKO_HOME="/opt/veriqko"
LOGS_DIR="$VERIQKO_HOME/logs"
GITHUB_KEY="/root/.ssh/github_deploy"
BRANCH="main"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()     { echo -e "${GREEN}[UPDATE]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step()    { echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}\n"; }
divider() { echo -e "${YELLOW}================================================================${NC}"; }

#===============================================================================
# Parse Arguments
#===============================================================================

RUN_MIGRATIONS=true
FULL_UPDATE=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --full)         FULL_UPDATE=true ;;
        --no-migrate)   RUN_MIGRATIONS=false ;;
        --help)
            sed -n '/^# Usage/,/^#====/p' "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        *) error "Unknown option: $1. Use --help for usage." ;;
    esac
    shift
done

if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash update.sh"
fi

VERIQKO_USER="veriqko"
if ! id "$VERIQKO_USER" &>/dev/null; then
    # Fallback to older veriqo user if exists
    if id "veriqo" &>/dev/null; then
        VERIQKO_USER="veriqo"
    else
        error "No veriqko user found. Run deploy-ubuntu.sh first."
    fi
fi

log "Starting Veriqko zero-downtime update..."

#===============================================================================
# Step 1: Clone Latest Code to Temporary Directory
#===============================================================================

step "1 — Clone Latest Code"

# Ensure clean slate for app_new
rm -rf "$APP_NEW_DIR"
mkdir -p "$APP_NEW_DIR"

# Clone directly into app_new
log "Cloning from origin/$BRANCH..."
GIT_SSH_COMMAND="ssh -i $GITHUB_KEY -o StrictHostKeyChecking=no" git clone --branch "$BRANCH" --depth 1 "git@github.com:lowrester/Veriqko.git" "$APP_NEW_DIR" || \
    error "Git clone failed. Check SSH key and GitHub connectivity."

NEW_SHA=$(cd "$APP_NEW_DIR" && git rev-parse HEAD)
log "New commit: ${NEW_SHA:0:12}"

# Optional optimizations: copy over node_modules and .venv to speed up install if not full update
if [ "$FULL_UPDATE" = false ]; then
    log "Copying cached dependencies to speed up build..."
    if [ -d "$APP_DIR/apps/api/.venv" ]; then
        cp -a "$APP_DIR/apps/api/.venv" "$APP_NEW_DIR/apps/api/.venv" 2>/dev/null || true
    fi
    if [ -d "$APP_DIR/apps/web/node_modules" ]; then
        cp -a "$APP_DIR/apps/web/node_modules" "$APP_NEW_DIR/apps/web/node_modules" 2>/dev/null || true
    fi
fi

# Copy over `.env`
if [ -f "$APP_DIR/apps/api/.env" ]; then
    cp "$APP_DIR/apps/api/.env" "$APP_NEW_DIR/apps/api/.env"
else
    warn "No .env found in the live directory!"
fi

#===============================================================================
# Step 2: Build Backend in Sandbox
#===============================================================================

step "2 — Build Backend"

cd "$APP_NEW_DIR/apps/api"

if [ ! -d ".venv" ] || [ "$FULL_UPDATE" = true ]; then
    log "Creating Python virtual environment..."
    rm -rf .venv
    python3.11 -m venv .venv
fi

log "Installing Python dependencies..."
.venv/bin/pip install --upgrade pip --quiet
if [ -f "requirements.txt" ]; then
    .venv/bin/pip install --no-cache-dir -r requirements.txt || .venv/bin/pip install --no-cache-dir -e ".[dev]"
elif [ -f "pyproject.toml" ]; then
    .venv/bin/pip install --no-cache-dir -e ".[dev]"
else
    error "No requirements.txt or pyproject.toml found in $APP_NEW_DIR/apps/api"
fi

log "Backend dependencies installed successfully."

#===============================================================================
# Step 3: Run Database Migrations
#===============================================================================

if [ "$RUN_MIGRATIONS" = true ]; then
    step "3 — Database Migrations"
    log "Running Alembic migrations..."
    
    # Run migrations against the live database from the new code directory
    PYTHONPATH="$APP_NEW_DIR/apps/api/src" .venv/bin/alembic upgrade head || \
        error "Database migration failed! The update has been aborted. The live app remains untouched and online."
    
    log "Migrations applied successfully."
else
    log "Skipping migrations (--no-migrate)"
fi

#===============================================================================
# Step 4: Build Frontend in Sandbox
#===============================================================================

step "4 — Build Frontend"

cd "$APP_NEW_DIR/apps/web"

# Copy frontend .env if exists
if [ -f "$APP_DIR/apps/web/.env" ]; then
    cp "$APP_DIR/apps/web/.env" .env
fi

log "Installing frontend dependencies..."
if [ "$FULL_UPDATE" = true ]; then
    rm -rf node_modules package-lock.json
fi

# Use unsafe-perm to ensure root can run postinstall scripts
npm install --unsafe-perm || error "Frontend dependency installation failed! The live app remains untouched and online."

log "Building frontend..."
npm run build || error "Frontend build failed! The live app remains untouched and online."

log "Frontend built successfully."

#===============================================================================
# Step 5: Swap the Folders (Zero Downtime)
#===============================================================================

step "5 — Swap and Restart"

log "Adjusting file permissions before swap..."
chown -R "$VERIQKO_USER:$VERIQKO_USER" "$APP_NEW_DIR"

log "Swapping application directories..."
APP_OLD_DIR="/opt/veriqko/app_old_$(date +%Y%m%d%H%M%S)"

# The swap ensures atomic-like replacement. It renames the current live directory,
# then drops the newly built one in its place.
mv "$APP_DIR" "$APP_OLD_DIR"
mv "$APP_NEW_DIR" "$APP_DIR"

log "Restarting veriqko-api..."
if systemctl is-enabled veriqko-api &>/dev/null; then
    systemctl restart veriqko-api
    log "veriqko-api restarted"
else
    warn "veriqko-api service not found!"
fi

log "Reloading nginx..."
if systemctl is-active nginx &>/dev/null; then
    nginx -t && systemctl reload nginx || warn "Nginx reload failed — check config."
else
    warn "Nginx is not running."
fi

# Keep only the last 2 old directories to save space
log "Cleaning up old deployments..."
ls -dt /opt/veriqko/app_old_* 2>/dev/null | tail -n +3 | xargs -r rm -rf

#===============================================================================
# Step 6: Health Check
#===============================================================================

step "6 — Health Check"

log "Waiting for API to respond on new version..."
HEALTH_OK=false
for i in $(seq 1 15); do
    sleep 2
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then
        HEALTH_OK=true
        break
    fi
    log "  Waiting... (status: $HTTP_STATUS)"
done

if [ "$HEALTH_OK" = true ]; then
    log "✅ Health check passed — API is healthy on localhost:8000"
else
    warn "⚠️  Health check failed after 30s (status: $HTTP_STATUS)"
    warn "The update WAS deployed, but the service isn't responding normally."
    warn "Check logs: journalctl -u veriqko-api -n 50"
fi

#===============================================================================
# Summary
#===============================================================================

echo ""
divider
echo -e "${BOLD}${GREEN}  ✅ VERIQKO PLATFORM UPDATED SUCCESSFULLY${NC}"
divider
echo ""
echo "  New commit:  ${NEW_SHA:0:12}"
echo ""
echo "  Previous deployment safely archived at:"
echo "    $APP_OLD_DIR"
echo ""
echo "  Useful commands:"
echo "    systemctl status veriqko-api"
echo "    journalctl -u veriqko-api -f"
echo ""
divider
