#!/bin/bash
#===============================================================================
# Veriqko Ubuntu Server Deployment Script
#
# Deploys the complete Veriqko platform on Ubuntu Server 22.04/24.04
#
# Components:
#   - PostgreSQL 15
#   - Python 3.11 + FastAPI backend
#   - Node.js 20 + React frontend
#   - Nginx reverse proxy
#   - Systemd services
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqko/main/infra/deploy-ubuntu.sh | sudo bash
#
#   Or with custom settings:
#   VERIQKO_DOMAIN=myveriqko.com VERIQKO_DB_PASSWORD=secret sudo -E bash deploy-ubuntu.sh
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[VERIQKO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (sudo)"
fi

#===============================================================================
# Configuration
#===============================================================================

VERIQKO_USER="${VERIQKO_USER:-veriqko}"
VERIQKO_HOME="/opt/veriqko"
VERIQKO_DOMAIN="${VERIQKO_DOMAIN:-$(hostname -f)}"
VERIQKO_REPO="${VERIQKO_REPO:-https://github.com/lowrester/Veriqko.git}"
VERIQKO_BRANCH="${VERIQKO_BRANCH:-claude/add-pdf-support-166IR}"

# Database
DB_NAME="${DB_NAME:-veriqko}"
DB_USER="${DB_USER:-veriqko}"
DB_PASSWORD="${VERIQKO_DB_PASSWORD:-$(openssl rand -base64 24)}"

# Application
JWT_SECRET="${VERIQKO_JWT_SECRET:-$(openssl rand -base64 48)}"
ADMIN_EMAIL="${VERIQKO_ADMIN_EMAIL:-admin@${VERIQKO_DOMAIN}}"
ADMIN_PASSWORD="${VERIQKO_ADMIN_PASSWORD:-$(openssl rand -base64 16)}"

# Save credentials
CREDENTIALS_FILE="/root/veriqko-credentials.txt"

log "Starting Veriqko deployment..."
log "Domain: $VERIQKO_DOMAIN"

#===============================================================================
# System Setup
#===============================================================================

log "Updating system packages..."
apt-get update
apt-get upgrade -y

log "Installing dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    gnupg \
    lsb-release \
    openssh-client \
    ssh-askpass

#===============================================================================
# SSH Key Setup
#===============================================================================

log "Setting up SSH..."
SSH_DIR="/root/.ssh"
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [ ! -f "$SSH_DIR/id_ed25519" ]; then
    log "Generating new ED25519 SSH key..."
    ssh-keygen -t ed25519 -C "deploy@veriqko" -f "$SSH_DIR/id_ed25519" -N ""
fi

# Ensure ssh-agent is running and key is added
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
fi
ssh-add "$SSH_DIR/id_ed25519"

# Add ssh-agent to profile for persistence
if ! grep -q "ssh-agent" /root/.bashrc; then
    cat >> /root/.bashrc <<'EOF'

# Start SSH Agent on login
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)" > /dev/null
    ssh-add ~/.ssh/id_ed25519 2>/dev/null
fi
EOF
fi

echo -e "\n${YELLOW}================================================================${NC}"
echo -e "${YELLOW}ACTION REQUIRED: ADD THIS SSH PUBLIC KEY TO GITHUB${NC}"
echo -e "${YELLOW}================================================================${NC}\n"
cat "$SSH_DIR/id_ed25519.pub"
echo -e "\n${YELLOW}URL: https://github.com/settings/keys${NC}"
echo -e "${YELLOW}Waiting 30 seconds for you to copy the key... (or press Enter to continue)${NC}\n"

read -t 30 -p "Press Enter to continue deployment..." || true

#===============================================================================
# PostgreSQL
#===============================================================================

log "Installing PostgreSQL..."
apt-get install -y postgresql postgresql-contrib

log "Configuring PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql <<EOF
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\c ${DB_NAME}
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF

log "PostgreSQL configured successfully"

#===============================================================================
# Python 3.11
#===============================================================================

log "Installing Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev

#===============================================================================
# Node.js 20
#===============================================================================

log "Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

#===============================================================================
# Create Veriqko User and Directory
#===============================================================================

log "Creating veriqko user..."
id -u $VERIQKO_USER &>/dev/null || useradd -r -m -d $VERIQKO_HOME -s /bin/bash $VERIQKO_USER

mkdir -p $VERIQKO_HOME
mkdir -p $VERIQKO_HOME/data
mkdir -p $VERIQKO_HOME/logs
chown -R $VERIQKO_USER:$VERIQKO_USER $VERIQKO_HOME

#===============================================================================
# Clone Repository
#===============================================================================

log "Cloning Veriqko repository..."
cd $VERIQKO_HOME

if [ -d "app" ]; then
    rm -rf app
fi

git clone --branch $VERIQKO_BRANCH $VERIQKO_REPO app
chown -R $VERIQKO_USER:$VERIQKO_USER app

#===============================================================================
# Backend Setup
#===============================================================================

log "Setting up backend..."
cd $VERIQKO_HOME/app/apps/api

# Create virtual environment
sudo -u $VERIQKO_USER python3.11 -m venv venv
sudo -u $VERIQKO_USER ./venv/bin/pip install --upgrade pip
sudo -u $VERIQKO_USER ./venv/bin/pip install -e ".[dev]"

# Create .env file
cat > .env <<EOF
# Veriqko API Configuration
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
STORAGE_BASE_PATH=${VERIQKO_HOME}/data
STORAGE_MAX_FILE_SIZE_MB=100

# Reports
REPORT_EXPIRY_DAYS=90

# Branding
BRAND_NAME=Veriqko
BRAND_PRIMARY_COLOR=#2563eb

# CORS
CORS_ORIGINS=https://${VERIQKO_DOMAIN}

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

chown $VERIQKO_USER:$VERIQKO_USER .env
chmod 600 .env

# Run migrations
log "Running database migrations..."
sudo -u $VERIQKO_USER ./venv/bin/alembic upgrade head

# Create admin user
log "Creating admin user..."
PASSWORD_HASH=$(sudo -u $VERIQKO_USER ./venv/bin/python3 -c "from veriqko.auth.password import hash_password; print(hash_password('${ADMIN_PASSWORD}'))")

sudo -u postgres psql -d $DB_NAME <<EOSQL
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

log "Admin user created: ${ADMIN_EMAIL}"

log "Backend setup complete"

#===============================================================================
# Frontend Setup
#===============================================================================

log "Setting up frontend..."
cd $VERIQKO_HOME/app/apps/web

# Create .env file
cat > .env <<EOF
VITE_API_URL=https://${VERIQKO_DOMAIN}
EOF

# Install dependencies and build
sudo -u $VERIQKO_USER npm install
sudo -u $VERIQKO_USER npm run build

log "Frontend setup complete"

#===============================================================================
# Systemd Services
#===============================================================================

log "Creating systemd services..."

# Backend service
cat > /etc/systemd/system/veriqko-api.service <<EOF
[Unit]
Description=Veriqko API Server
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=${VERIQKO_USER}
Group=${VERIQKO_USER}
WorkingDirectory=${VERIQKO_HOME}/app/apps/api
Environment=PATH=${VERIQKO_HOME}/app/apps/api/venv/bin:/usr/bin
ExecStart=${VERIQKO_HOME}/app/apps/api/venv/bin/uvicorn veriqko.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=append:${VERIQKO_HOME}/logs/api.log
StandardError=append:${VERIQKO_HOME}/logs/api-error.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable veriqko-api
systemctl start veriqko-api

log "Systemd services configured"

#===============================================================================
# Nginx Configuration
#===============================================================================

log "Configuring Nginx..."
apt-get install -y nginx

cat > /etc/nginx/sites-available/veriqko <<EOF
server {
    listen 80;
    server_name ${VERIQKO_DOMAIN};

    # Frontend static files
    root ${VERIQKO_HOME}/app/apps/web/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

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
    }

    # SPA routing - serve index.html for all other routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/veriqko /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

log "Nginx configured"

#===============================================================================
# Firewall
#===============================================================================

log "Configuring firewall..."
apt-get install -y ufw
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

#===============================================================================
# SSL Certificate (Let's Encrypt)
#===============================================================================

if [ "$VERIQKO_DOMAIN" != "$(hostname -f)" ] && [ "$VERIQKO_DOMAIN" != "localhost" ]; then
    log "Setting up SSL with Let's Encrypt..."
    apt-get install -y certbot python3-certbot-nginx

    # Only run certbot if domain is publicly accessible
    if host "$VERIQKO_DOMAIN" &>/dev/null; then
        certbot --nginx -d "$VERIQKO_DOMAIN" --non-interactive --agree-tos --email "$ADMIN_EMAIL" || warn "Certbot failed - you may need to run it manually"
    else
        warn "Domain not publicly accessible. Run certbot manually when DNS is configured."
    fi
else
    warn "Skipping SSL setup for local domain. Configure manually for production."
fi

#===============================================================================
# Save Credentials
#===============================================================================

log "Saving credentials..."
cat > $CREDENTIALS_FILE <<EOF
===============================================================================
VERIQKO DEPLOYMENT CREDENTIALS
Generated: $(date)
===============================================================================

Domain: https://${VERIQKO_DOMAIN}

DATABASE
--------
Host: localhost
Port: 5432
Database: ${DB_NAME}
Username: ${DB_USER}
Password: ${DB_PASSWORD}

ADMIN USER
----------
Email: ${ADMIN_EMAIL}
Password: ${ADMIN_PASSWORD}

JWT SECRET
----------
${JWT_SECRET}

IMPORTANT: Keep this file secure and delete after saving credentials elsewhere!
===============================================================================
EOF

chmod 600 $CREDENTIALS_FILE

#===============================================================================
# Final Status
#===============================================================================

log "Checking services..."
systemctl status veriqko-api --no-pager || true
systemctl status nginx --no-pager || true
systemctl status postgresql --no-pager || true

echo ""
echo "=============================================="
echo -e "${GREEN}VERIQKO DEPLOYMENT COMPLETE!${NC}"
echo "=============================================="
echo ""
echo "Access your Veriqko instance:"
echo "  URL: https://${VERIQKO_DOMAIN}"
echo ""
echo "Admin login:"
echo "  Email: ${ADMIN_EMAIL}"
echo "  Password: ${ADMIN_PASSWORD}"
echo ""
echo "Credentials saved to: ${CREDENTIALS_FILE}"
echo ""
echo "Useful commands:"
echo "  systemctl status veriqko-api    # Check API status"
echo "  journalctl -u veriqko-api -f    # View API logs"
echo "  tail -f ${VERIQKO_HOME}/logs/   # View log files"
echo ""
echo "=============================================="
