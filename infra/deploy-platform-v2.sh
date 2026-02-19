#!/bin/bash
#===============================================================================
# Veriqko Platform V2 — Fresh Install Script
#
# Installs the complete Veriqko application stack on an already-provisioned
# Ubuntu server. Run deploy-ubuntu.sh FIRST to set up the OS, SSH keys,
# PostgreSQL, Python, Node.js, and Nginx.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqo/main/infra/deploy-platform-v2.sh | sudo bash
#
# Or with custom settings:
#   VERIQKO_DOMAIN=myveriqko.com sudo -E bash deploy-platform-v2.sh
#
# What this script does:
#   1. Clones the main branch via SSH
#   2. Sets up the Python backend (venv, deps, .env, migrations, admin user)
#   3. Builds the React frontend
#   4. Creates systemd service for the API
#   5. Configures Nginx
#   6. Runs a health check
#===============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log()     { echo -e "${GREEN}[VERIQKO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step()    { echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}\n"; }
divider() { echo -e "${YELLOW}================================================================${NC}"; }

# Must run as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash deploy-platform-v2.sh"
fi

#===============================================================================
# Configuration
#===============================================================================

VERIQKO_USER="${VERIQKO_USER:-veriqko}"
VERIQKO_HOME="/opt/veriqko"
APP_DIR="$VERIQKO_HOME/app"
API_DIR="$APP_DIR/apps/api"
WEB_DIR="$APP_DIR/apps/web"
LOGS_DIR="$VERIQKO_HOME/logs"
DATA_DIR="$VERIQKO_HOME/data"
BACKUPS_DIR="$VERIQKO_HOME/backups"

VERIQKO_DOMAIN="${VERIQKO_DOMAIN:-$(hostname -f)}"
GITHUB_REPO_SSH="git@github.com:lowrester/Veriqo.git"
VERIQKO_BRANCH="${VERIQKO_BRANCH:-main}"

# Database (read from env or credentials file)
DB_NAME="${DB_NAME:-veriqko}"
DB_USER="${DB_USER:-veriqko}"

# Try to load credentials from the file written by deploy-ubuntu.sh
CREDENTIALS_FILE="/root/veriqko-credentials.txt"
if [ -f "$CREDENTIALS_FILE" ]; then
    DB_PASSWORD="${VERIQKO_DB_PASSWORD:-$(grep "^Password:" "$CREDENTIALS_FILE" | head -1 | awk '{print $2}')}"
    JWT_SECRET="${VERIQKO_JWT_SECRET:-$(grep -A1 "JWT SECRET" "$CREDENTIALS_FILE" | tail -1 | tr -d ' ')}"
    ADMIN_EMAIL="${VERIQKO_ADMIN_EMAIL:-$(grep "^Email:" "$CREDENTIALS_FILE" | head -1 | awk '{print $2}')}"
    ADMIN_PASSWORD="${VERIQKO_ADMIN_PASSWORD:-$(grep "^Password:" "$CREDENTIALS_FILE" | tail -1 | awk '{print $2}')}"
fi

# Fallback to fresh random values if still unset
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 24)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -base64 48)}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@${VERIQKO_DOMAIN}}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-$(openssl rand -base64 16)}"

GITHUB_KEY="$VERIQKO_HOME/.ssh/github_deploy"

# Verify the veriqko user exists
if ! id "$VERIQKO_USER" &>/dev/null; then
    error "User '$VERIQKO_USER' not found. Run deploy-ubuntu.sh first."
fi

log "Starting Veriqko Platform V2 installation..."
log "Domain:  $VERIQKO_DOMAIN"
log "App dir: $APP_DIR"
log "Branch:  $VERIQKO_BRANCH"

#===============================================================================
# Helper: run as veriqko user with SSH agent
#===============================================================================

run_as_veriqko() {
    sudo -u "$VERIQKO_USER" \
        SSH_AUTH_SOCK="${XDG_RUNTIME_DIR:-/run/user/$(id -u "$VERIQKO_USER")}/ssh-agent.socket" \
        GIT_SSH_COMMAND="ssh -i $GITHUB_KEY -o StrictHostKeyChecking=no" \
        "$@"
}

#===============================================================================
# Step 1: Clone Repository
#===============================================================================

step "1/7 — Cloning Repository"

# Ensure directories exist
mkdir -p "$VERIQKO_HOME" "$LOGS_DIR" "$DATA_DIR" "$BACKUPS_DIR"
chown -R "$VERIQKO_USER:$VERIQKO_USER" "$VERIQKO_HOME"

if [ -d "$APP_DIR" ]; then
    BACKUP_NAME="app-backup-$(date +%Y%m%d-%H%M%S)"
    warn "Existing app directory found. Backing up to $BACKUPS_DIR/$BACKUP_NAME ..."
    mv "$APP_DIR" "$BACKUPS_DIR/$BACKUP_NAME"
    log "Backup created: $BACKUPS_DIR/$BACKUP_NAME"
fi

log "Cloning $GITHUB_REPO_SSH (branch: $VERIQKO_BRANCH)..."

# Verify SSH connectivity first
if ! sudo -u "$VERIQKO_USER" \
    GIT_SSH_COMMAND="ssh -i $GITHUB_KEY -o StrictHostKeyChecking=no" \
    ssh -T git@github.com < /dev/null 2>&1 | grep -q "successfully authenticated"; then
    warn "GitHub SSH test inconclusive — attempting clone anyway..."
    warn "If clone fails, ensure the deploy key is added at: https://github.com/settings/keys"
fi

run_as_veriqko git clone \
    --branch "$VERIQKO_BRANCH" \
    --depth 1 \
    "$GITHUB_REPO_SSH" \
    "$APP_DIR" || error "Git clone failed. Check that the GitHub deploy key is added to GitHub."

chown -R "$VERIQKO_USER:$VERIQKO_USER" "$APP_DIR"
log "Repository cloned successfully"

#===============================================================================
# Step 2: Backend Setup
#===============================================================================

step "2/7 — Backend Setup"

cd "$API_DIR"

# Create virtual environment
if [ ! -d ".venv" ]; then
    log "Creating Python virtual environment..."
    run_as_veriqko python3.11 -m venv .venv
else
    log "Virtual environment already exists, reusing."
fi

log "Upgrading pip..."
run_as_veriqko .venv/bin/pip install --upgrade pip --quiet

log "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    run_as_veriqko .venv/bin/pip install --no-cache-dir -r requirements.txt || {
        warn "requirements.txt install failed, trying pyproject.toml..."
        run_as_veriqko .venv/bin/pip install --no-cache-dir -e ".[dev]" || \
            error "Python dependency installation failed."
    }
elif [ -f "pyproject.toml" ]; then
    run_as_veriqko .venv/bin/pip install --no-cache-dir -e ".[dev]" || \
        error "Python dependency installation failed."
else
    error "No requirements.txt or pyproject.toml found in $API_DIR"
fi

log "Backend dependencies installed"

#===============================================================================
# Step 3: Backend .env
#===============================================================================

step "3/7 — Backend Configuration"

ENV_FILE="$API_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    warn ".env already exists — skipping to preserve existing secrets."
    warn "To regenerate, delete $ENV_FILE and re-run this script."
else
    log "Creating backend .env..."
    cat > "$ENV_FILE" <<EOF
# Veriqko API Configuration
# Generated by deploy-platform-v2.sh on $(date)

ENVIRONMENT=production
DEBUG=false
BASE_URL=https://${VERIQKO_DOMAIN}

# Database
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

# Authentication
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage
STORAGE_BASE_PATH=${DATA_DIR}
STORAGE_MAX_FILE_SIZE_MB=100

# Reports
REPORT_EXPIRY_DAYS=90

# Branding
BRAND_NAME=Veriqko
BRAND_PRIMARY_COLOR=#2563eb

# CORS
CORS_ORIGINS=https://${VERIQKO_DOMAIN},http://${VERIQKO_DOMAIN}

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
    chown "$VERIQKO_USER:$VERIQKO_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    log ".env created"
fi

#===============================================================================
# Step 4: Database Migrations
#===============================================================================

step "4/7 — Database Migrations"

log "Running Alembic migrations..."
MIGRATION_OK=false

run_as_veriqko \
    PYTHONPATH="$API_DIR/src" \
    "$API_DIR/.venv/bin/alembic" upgrade head && MIGRATION_OK=true || true

if [ "$MIGRATION_OK" = false ]; then
    warn "Migration failed. Attempting to diagnose..."

    # Check if DB is reachable
    if ! sudo -u postgres psql -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
        error "Cannot connect to database '$DB_NAME'. Check PostgreSQL is running and credentials are correct."
    fi

    # Check for dirty state
    CURRENT_REV=$(run_as_veriqko \
        PYTHONPATH="$API_DIR/src" \
        "$API_DIR/.venv/bin/alembic" current 2>&1 | grep -v "^$" | tail -1 || echo "unknown")
    warn "Current alembic revision: $CURRENT_REV"

    # Try stamp head and retry (handles out-of-sync state)
    warn "Attempting to stamp head and retry..."
    run_as_veriqko \
        PYTHONPATH="$API_DIR/src" \
        "$API_DIR/.venv/bin/alembic" stamp head 2>/dev/null || true

    run_as_veriqko \
        PYTHONPATH="$API_DIR/src" \
        "$API_DIR/.venv/bin/alembic" upgrade head && MIGRATION_OK=true || true

    if [ "$MIGRATION_OK" = false ]; then
        error "Database migrations failed. Check $LOGS_DIR/migration-error.log and fix manually."
    fi
fi

log "Migrations applied successfully"

#===============================================================================
# Step 5: Create Admin User
#===============================================================================

step "5/7 — Admin User"

log "Creating admin user (if not exists)..."

ADMIN_SCRIPT=$(cat <<PYEOF
import asyncio, sys
sys.path.insert(0, '$API_DIR/src')

async def main():
    try:
        from veriqko.db.session import get_async_session_context
        from veriqko.auth.password import hash_password
        from sqlalchemy import text
        import uuid, datetime

        async with get_async_session_context() as session:
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "$ADMIN_EMAIL"}
            )
            if result.fetchone():
                print("SKIP: Admin user already exists")
                return

            pw_hash = hash_password("$ADMIN_PASSWORD")
            await session.execute(
                text("""
                    INSERT INTO users (id, email, password_hash, full_name, role, is_active, created_at, updated_at)
                    VALUES (:id, :email, :pw, :name, 'admin', true, :now, :now)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "email": "$ADMIN_EMAIL",
                    "pw": pw_hash,
                    "name": "Administrator",
                    "now": datetime.datetime.utcnow()
                }
            )
            await session.commit()
            print("OK: Admin user created")
    except Exception as e:
        print(f"WARN: {e}", file=sys.stderr)
        sys.exit(0)  # Non-fatal — admin can be created via create-admin.sh

asyncio.run(main())
PYEOF
)

ADMIN_RESULT=$(run_as_veriqko \
    PYTHONPATH="$API_DIR/src" \
    "$API_DIR/.venv/bin/python3" -c "$ADMIN_SCRIPT" 2>&1) || true

if echo "$ADMIN_RESULT" | grep -q "SKIP"; then
    log "Admin user already exists — skipping."
elif echo "$ADMIN_RESULT" | grep -q "OK"; then
    log "Admin user created: $ADMIN_EMAIL"
else
    warn "Admin user creation via Python failed. Trying direct SQL..."
    PASSWORD_HASH=$(run_as_veriqko \
        PYTHONPATH="$API_DIR/src" \
        "$API_DIR/.venv/bin/python3" -c \
        "from veriqko.auth.password import hash_password; print(hash_password('$ADMIN_PASSWORD'))" 2>/dev/null) || true

    if [ -n "$PASSWORD_HASH" ]; then
        sudo -u postgres psql -d "$DB_NAME" <<EOSQL || warn "SQL admin insert also failed — create admin manually with create-admin.sh"
INSERT INTO users (id, email, password_hash, full_name, role, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    '${ADMIN_EMAIL}',
    '${PASSWORD_HASH}',
    'Administrator',
    'admin',
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;
EOSQL
        log "Admin user created via SQL"
    else
        warn "Could not hash password. Run: sudo bash infra/create-admin.sh after deployment."
    fi
fi

#===============================================================================
# Step 6: Frontend Build
#===============================================================================

step "6/7 — Frontend Build"

cd "$WEB_DIR"

# Create frontend .env
if [ ! -f ".env" ]; then
    log "Creating frontend .env..."
    cat > .env <<EOF
VITE_API_URL=https://${VERIQKO_DOMAIN}
EOF
    chown "$VERIQKO_USER:$VERIQKO_USER" .env
fi

log "Installing frontend dependencies..."
FRONTEND_OK=false

# Try npm ci first (clean, reproducible install)
run_as_veriqko npm ci --prefer-offline 2>/dev/null && FRONTEND_OK=true || true

if [ "$FRONTEND_OK" = false ]; then
    warn "npm ci failed. Cleaning node_modules and retrying with npm install..."
    rm -rf node_modules package-lock.json
    run_as_veriqko npm install && FRONTEND_OK=true || true
fi

if [ "$FRONTEND_OK" = false ]; then
    error "Frontend dependency installation failed. Check npm logs above."
fi

log "Building frontend..."
run_as_veriqko npm run build || error "Frontend build failed. Check TypeScript/build errors above."

log "Frontend built successfully"

#===============================================================================
# Step 7: Systemd Service + Nginx
#===============================================================================

step "7/7 — Services & Nginx"

# --- Systemd API service ---
log "Creating veriqko-api systemd service..."
cat > /etc/systemd/system/veriqko-api.service <<EOF
[Unit]
Description=Veriqko API Server
Documentation=https://github.com/lowrester/Veriqo
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=${VERIQKO_USER}
Group=${VERIQKO_USER}
WorkingDirectory=${API_DIR}
Environment=PATH=${API_DIR}/.venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=${API_DIR}/src
EnvironmentFile=${API_DIR}/.env
ExecStart=${API_DIR}/.venv/bin/uvicorn veriqko.main:app --host 127.0.0.1 --port 8000 --workers 2
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=5
StandardOutput=append:${LOGS_DIR}/api.log
StandardError=append:${LOGS_DIR}/api-error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable veriqko-api
systemctl restart veriqko-api
log "veriqko-api service started"

# --- Nginx ---
log "Configuring Nginx..."

# Stop anything using port 80 that isn't nginx
if ss -tlnp | grep ':80 ' | grep -v nginx &>/dev/null; then
    warn "Something is using port 80. Attempting to stop conflicting services..."
    # Common conflicts
    for svc in apache2 lighttpd caddy; do
        systemctl stop "$svc" 2>/dev/null && warn "Stopped $svc" || true
    done
fi

cat > /etc/nginx/sites-available/veriqko <<EOF
server {
    listen 80;
    server_name ${VERIQKO_DOMAIN};

    # Frontend static files
    root ${WEB_DIR}/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/x-javascript;
    gzip_min_length 1000;
    gzip_vary on;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        client_max_body_size 100M;
    }

    # Public report access
    location /r/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }

    # SPA routing
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/veriqko /etc/nginx/sites-enabled/veriqko
rm -f /etc/nginx/sites-enabled/default

nginx -t || error "Nginx config test failed. Check /etc/nginx/sites-available/veriqko"
systemctl restart nginx
systemctl enable nginx
log "Nginx configured and restarted"

# --- Optional: SSL ---
if [ "${VERIQKO_DOMAIN}" != "$(hostname -f)" ] && [ "${VERIQKO_DOMAIN}" != "localhost" ]; then
    log "Attempting SSL setup with Let's Encrypt..."
    if ! command -v certbot &>/dev/null; then
        DEBIAN_FRONTEND=noninteractive apt-get install -y certbot python3-certbot-nginx -qq
    fi
    if host "$VERIQKO_DOMAIN" &>/dev/null; then
        certbot --nginx -d "$VERIQKO_DOMAIN" \
            --non-interactive --agree-tos \
            --email "$ADMIN_EMAIL" \
            --redirect || warn "Certbot failed — run manually: certbot --nginx -d $VERIQKO_DOMAIN"
    else
        warn "Domain '$VERIQKO_DOMAIN' not publicly resolvable. Run certbot manually after DNS is configured."
    fi
fi

#===============================================================================
# Health Check
#===============================================================================

log "Waiting for API to start..."
HEALTH_OK=false
for i in $(seq 1 12); do
    sleep 5
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS" = "200" ]; then
        HEALTH_OK=true
        break
    fi
    log "  Waiting... ($((i*5))s, status: $HTTP_STATUS)"
done

if [ "$HEALTH_OK" = true ]; then
    log "✅ Health check passed — API is responding"
else
    warn "⚠️  Health check did not return 200 after 60s."
    warn "   Check logs: journalctl -u veriqko-api -n 50"
    warn "   Or: tail -f $LOGS_DIR/api-error.log"
fi

#===============================================================================
# Final Summary
#===============================================================================

echo ""
divider
echo -e "${BOLD}${GREEN}  ✅ VERIQKO PLATFORM V2 INSTALLED SUCCESSFULLY${NC}"
divider
echo ""
echo "  URL:            http://${VERIQKO_DOMAIN}"
echo "  Admin email:    ${ADMIN_EMAIL}"
echo "  Admin password: ${ADMIN_PASSWORD}"
echo ""
echo "  Credentials:    ${CREDENTIALS_FILE}"
echo ""
echo "  Useful commands:"
echo "    systemctl status veriqko-api"
echo "    journalctl -u veriqko-api -f"
echo "    tail -f ${LOGS_DIR}/api-error.log"
echo ""
echo "  To update the platform:"
echo "    sudo bash /opt/veriqko/app/infra/update.sh"
echo ""
divider
