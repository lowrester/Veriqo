#!/bin/bash
#===============================================================================
# Veriqo Ubuntu Server Deployment Script
#
# Deploys the complete Veriqo platform on Ubuntu Server 22.04/24.04
#
# Components:
#   - PostgreSQL 15
#   - Python 3.11 + FastAPI backend
#   - Node.js 20 + React frontend
#   - Nginx reverse proxy
#   - Systemd services
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqo/main/infra/deploy-ubuntu.sh | sudo bash
#
#   Or with custom settings:
#   VERIQO_DOMAIN=myveriqo.com VERIQO_DB_PASSWORD=secret sudo -E bash deploy-ubuntu.sh
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[VERIQO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (sudo)"
fi

#===============================================================================
# Configuration
#===============================================================================

VERIQO_USER="${VERIQO_USER:-veriqo}"
VERIQO_HOME="/opt/veriqo"
VERIQO_DOMAIN="${VERIQO_DOMAIN:-$(hostname -f)}"
VERIQO_REPO="${VERIQO_REPO:-https://github.com/lowrester/Veriqo.git}"
VERIQO_BRANCH="${VERIQO_BRANCH:-claude/add-pdf-support-166IR}"

# Database
DB_NAME="${DB_NAME:-veriqo}"
DB_USER="${DB_USER:-veriqo}"
DB_PASSWORD="${VERIQO_DB_PASSWORD:-$(openssl rand -base64 24)}"

# Application
JWT_SECRET="${VERIQO_JWT_SECRET:-$(openssl rand -base64 48)}"
ADMIN_EMAIL="${VERIQO_ADMIN_EMAIL:-admin@${VERIQO_DOMAIN}}"
ADMIN_PASSWORD="${VERIQO_ADMIN_PASSWORD:-$(openssl rand -base64 16)}"

# Save credentials
CREDENTIALS_FILE="/root/veriqo-credentials.txt"

log "Starting Veriqo deployment..."
log "Domain: $VERIQO_DOMAIN"

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
    lsb-release

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
# Create Veriqo User and Directory
#===============================================================================

log "Creating veriqo user..."
id -u $VERIQO_USER &>/dev/null || useradd -r -m -d $VERIQO_HOME -s /bin/bash $VERIQO_USER

mkdir -p $VERIQO_HOME
mkdir -p $VERIQO_HOME/data
mkdir -p $VERIQO_HOME/logs
chown -R $VERIQO_USER:$VERIQO_USER $VERIQO_HOME

#===============================================================================
# Clone Repository
#===============================================================================

log "Cloning Veriqo repository..."
cd $VERIQO_HOME

if [ -d "app" ]; then
    rm -rf app
fi

git clone --branch $VERIQO_BRANCH $VERIQO_REPO app
chown -R $VERIQO_USER:$VERIQO_USER app

#===============================================================================
# Backend Setup
#===============================================================================

log "Setting up backend..."
cd $VERIQO_HOME/app/apps/api

# Create virtual environment
sudo -u $VERIQO_USER python3.11 -m venv venv
sudo -u $VERIQO_USER ./venv/bin/pip install --upgrade pip
sudo -u $VERIQO_USER ./venv/bin/pip install -e ".[dev]"

# Create .env file
cat > .env <<EOF
# Veriqo API Configuration
ENVIRONMENT=production
DEBUG=false
BASE_URL=https://${VERIQO_DOMAIN}

# Database
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

# Authentication
JWT_SECRET_KEY=${JWT_SECRET}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage
STORAGE_BASE_PATH=${VERIQO_HOME}/data
STORAGE_MAX_FILE_SIZE_MB=100

# Reports
REPORT_EXPIRY_DAYS=90

# Branding
BRAND_NAME=Veriqo
BRAND_PRIMARY_COLOR=#2563eb

# CORS
CORS_ORIGINS=https://${VERIQO_DOMAIN}

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

chown $VERIQO_USER:$VERIQO_USER .env
chmod 600 .env

# Run migrations
log "Running database migrations..."
sudo -u $VERIQO_USER ./venv/bin/alembic upgrade head

# Create admin user
log "Creating admin user..."
sudo -u $VERIQO_USER ./venv/bin/python3 - <<EOF
import asyncio
from uuid import uuid4
from veriqo.db.base import async_session_factory
from veriqo.users.models import User, UserRole
from veriqo.auth.password import hash_password

async def create_admin():
    async with async_session_factory() as session:
        admin = User(
            id=str(uuid4()),
            email="${ADMIN_EMAIL}",
            password_hash=hash_password("${ADMIN_PASSWORD}"),
            full_name="Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Admin user created: ${ADMIN_EMAIL}")

asyncio.run(create_admin())
EOF

log "Backend setup complete"

#===============================================================================
# Frontend Setup
#===============================================================================

log "Setting up frontend..."
cd $VERIQO_HOME/app/apps/web

# Create .env file
cat > .env <<EOF
VITE_API_URL=https://${VERIQO_DOMAIN}
EOF

# Install dependencies and build
sudo -u $VERIQO_USER npm install
sudo -u $VERIQO_USER npm run build

log "Frontend setup complete"

#===============================================================================
# Systemd Services
#===============================================================================

log "Creating systemd services..."

# Backend service
cat > /etc/systemd/system/veriqo-api.service <<EOF
[Unit]
Description=Veriqo API Server
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=${VERIQO_USER}
Group=${VERIQO_USER}
WorkingDirectory=${VERIQO_HOME}/app/apps/api
Environment=PATH=${VERIQO_HOME}/app/apps/api/venv/bin:/usr/bin
ExecStart=${VERIQO_HOME}/app/apps/api/venv/bin/uvicorn veriqo.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=append:${VERIQO_HOME}/logs/api.log
StandardError=append:${VERIQO_HOME}/logs/api-error.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable veriqo-api
systemctl start veriqo-api

log "Systemd services configured"

#===============================================================================
# Nginx Configuration
#===============================================================================

log "Configuring Nginx..."
apt-get install -y nginx

cat > /etc/nginx/sites-available/veriqo <<EOF
server {
    listen 80;
    server_name ${VERIQO_DOMAIN};

    # Frontend static files
    root ${VERIQO_HOME}/app/apps/web/dist;
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
ln -sf /etc/nginx/sites-available/veriqo /etc/nginx/sites-enabled/
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

if [ "$VERIQO_DOMAIN" != "$(hostname -f)" ] && [ "$VERIQO_DOMAIN" != "localhost" ]; then
    log "Setting up SSL with Let's Encrypt..."
    apt-get install -y certbot python3-certbot-nginx

    # Only run certbot if domain is publicly accessible
    if host "$VERIQO_DOMAIN" &>/dev/null; then
        certbot --nginx -d "$VERIQO_DOMAIN" --non-interactive --agree-tos --email "$ADMIN_EMAIL" || warn "Certbot failed - you may need to run it manually"
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
VERIQO DEPLOYMENT CREDENTIALS
Generated: $(date)
===============================================================================

Domain: https://${VERIQO_DOMAIN}

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
systemctl status veriqo-api --no-pager || true
systemctl status nginx --no-pager || true
systemctl status postgresql --no-pager || true

echo ""
echo "=============================================="
echo -e "${GREEN}VERIQO DEPLOYMENT COMPLETE!${NC}"
echo "=============================================="
echo ""
echo "Access your Veriqo instance:"
echo "  URL: https://${VERIQO_DOMAIN}"
echo ""
echo "Admin login:"
echo "  Email: ${ADMIN_EMAIL}"
echo "  Password: ${ADMIN_PASSWORD}"
echo ""
echo "Credentials saved to: ${CREDENTIALS_FILE}"
echo ""
echo "Useful commands:"
echo "  systemctl status veriqo-api    # Check API status"
echo "  journalctl -u veriqo-api -f    # View API logs"
echo "  tail -f ${VERIQO_HOME}/logs/   # View log files"
echo ""
echo "=============================================="
