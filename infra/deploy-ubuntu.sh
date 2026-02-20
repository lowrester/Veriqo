#!/bin/bash
#===============================================================================
# Veriqko Ubuntu Server Deployment Script
#
# Provisions the OS and system dependencies for the Veriqko platform.
# Run this FIRST on a fresh Ubuntu 22.04/24.04 server (bare-metal or VM).
# After this completes, run deploy-platform-v2.sh to install the application.
#
# Usage (direct):
#   curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqko/main/infra/deploy-ubuntu.sh | sudo bash
#
# Usage (with custom settings):
#   VERIQKO_DOMAIN=myveriqko.com VERIQKO_DB_PASSWORD=secret sudo -E bash deploy-ubuntu.sh
#
# What this script does:
#   1. Updates system packages
#   2. Installs system dependencies (PostgreSQL, Python 3.11, Node.js 20, Nginx, etc.)
#   3. Installs and enables QEMU Guest Agent (for Proxmox)
#   4. Generates a cloud-init/server SSH key and displays it
#   5. Generates a dedicated GitHub deploy key and displays it (with pause)
#   6. Configures SSH for GitHub (SSH-only, no HTTPS)
#   7. Sets up ssh-agent as a systemd user service (autostart on boot)
#   8. Creates the veriqko system user and directories
#   9. Configures PostgreSQL
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
banner()  { echo -e "\n${BOLD}${CYAN}$1${NC}\n"; }
divider() { echo -e "${YELLOW}================================================================${NC}"; }

# Must run as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash deploy-ubuntu.sh"
fi

#===============================================================================
# Configuration — Source from env, local file, or use defaults
#===============================================================================

# Source configuration file if it exists in the same directory
if [ -f "$(dirname "$0")/config.env" ]; then
    source "$(dirname "$0")/config.env"
fi

VERIQKO_USER="${VERIQKO_USER:-veriqko}"
VERIQKO_HOME="/opt/veriqko"
VERIQKO_DOMAIN="${VERIQKO_DOMAIN:-$(hostname -f)}"
GITHUB_REPO_SSH="git@github.com:lowrester/Veriqko.git"

# Database
DB_NAME="${DB_NAME:-veriqko}"
DB_USER="${DB_USER:-veriqko}"
DB_PASSWORD="${VERIQKO_DB_PASSWORD:-$(openssl rand -base64 24)}"

# Application secrets
JWT_SECRET="${VERIQKO_JWT_SECRET:-$(openssl rand -base64 48)}"
ADMIN_EMAIL="${VERIQKO_ADMIN_EMAIL:-admin@${VERIQKO_DOMAIN}}"
ADMIN_PASSWORD="${VERIQKO_ADMIN_PASSWORD:-$(openssl rand -base64 16)}"

CREDENTIALS_FILE="/root/veriqko-credentials.txt"

log "Starting Veriqko OS provisioning..."
log "Domain: $VERIQKO_DOMAIN"

#===============================================================================
# System Packages
#===============================================================================

log "Updating system packages..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

log "Installing base dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    openssh-client \
    openssl \
    ufw \
    htop \
    unzip \
    jq \
    fail2ban \
    logrotate \
    rsync

#===============================================================================
# QEMU Guest Agent (Proxmox)
#===============================================================================

log "Installing and enabling QEMU Guest Agent..."
DEBIAN_FRONTEND=noninteractive apt-get install -y qemu-guest-agent

systemctl enable qemu-guest-agent
systemctl start qemu-guest-agent || true   # may already be running

log "QEMU Guest Agent status:"
systemctl is-active qemu-guest-agent && log "  ✅ qemu-guest-agent is running" || warn "  ⚠️  qemu-guest-agent may not be active inside the VM (normal if not on Proxmox)"

#===============================================================================
# SSH Key Setup — Server / Cloud-Init Key
#===============================================================================

log "Setting up server SSH key..."
ROOT_SSH_DIR="/root/.ssh"
mkdir -p "$ROOT_SSH_DIR"
chmod 700 "$ROOT_SSH_DIR"

if [ ! -f "$ROOT_SSH_DIR/id_ed25519" ]; then
    log "Generating server ED25519 SSH key..."
    ssh-keygen -t ed25519 -C "veriqko-server@$(hostname)" -f "$ROOT_SSH_DIR/id_ed25519" -N ""
fi

SERVER_PUBKEY=$(cat "$ROOT_SSH_DIR/id_ed25519.pub")

divider
banner "📋 SERVER / CLOUD-INIT SSH PUBLIC KEY"
echo "Add this key to Proxmox cloud-init 'SSH Public Keys' field"
echo "or to ~/.ssh/authorized_keys on this server for admin access:"
echo ""
echo -e "${BOLD}${SERVER_PUBKEY}${NC}"
divider
echo ""

#===============================================================================
# SSH Key Setup — GitHub Deploy Key
#===============================================================================

log "Generating GitHub deploy key..."
GITHUB_KEY_FILE="$ROOT_SSH_DIR/github_deploy"

if [ ! -f "$GITHUB_KEY_FILE" ]; then
    ssh-keygen -t ed25519 -C "veriqko-deploy@$(hostname)" -f "$GITHUB_KEY_FILE" -N ""
fi

GITHUB_PUBKEY=$(cat "${GITHUB_KEY_FILE}.pub")

divider
banner "🔑 GITHUB DEPLOY SSH KEY — ACTION REQUIRED"
echo -e "${RED}${BOLD}You MUST add this key to GitHub before the platform install can clone the repo.${NC}"
echo ""
echo "Steps:"
echo "  1. Copy the key below"
echo "  2. Go to: https://github.com/settings/keys  (or repo Deploy Keys)"
echo "  3. Click 'New SSH key', paste the key, save"
echo ""
echo -e "${BOLD}${GITHUB_PUBKEY}${NC}"
echo ""
divider
echo ""
echo -e "${YELLOW}Waiting 60 seconds for you to add the key to GitHub...${NC}"
echo -e "${YELLOW}Press Enter to continue immediately if already done.${NC}"
echo ""
read -t 60 -p "Press Enter to continue..." || true
echo ""

#===============================================================================
# SSH Config — GitHub SSH-Only
#===============================================================================

log "Configuring SSH for GitHub (SSH-only, no HTTPS)..."

SSH_CONFIG="$ROOT_SSH_DIR/config"

# Remove any existing github.com block and rewrite cleanly
if grep -q "Host github.com" "$SSH_CONFIG" 2>/dev/null; then
    # Remove the existing block
    sed -i '/^Host github\.com/,/^Host /{ /^Host github\.com/d; /^Host /!d }' "$SSH_CONFIG" 2>/dev/null || true
fi

cat >> "$SSH_CONFIG" <<EOF

Host github.com
    HostName github.com
    User git
    IdentityFile $GITHUB_KEY_FILE
    IdentitiesOnly yes
    StrictHostKeyChecking no
    PreferredAuthentications publickey
EOF

chmod 600 "$SSH_CONFIG"

# Configure git globally to always use SSH for GitHub
git config --global url."git@github.com:".insteadOf "https://github.com/"
git config --global core.sshCommand "ssh -i $GITHUB_KEY_FILE -o StrictHostKeyChecking=no"

log "SSH GitHub config written to $SSH_CONFIG"

#===============================================================================
# ssh-agent — Systemd User Service (Autostart on Boot)
#===============================================================================

log "Setting up ssh-agent as a systemd user service..."

# Create the systemd user service directory for root
SYSTEMD_USER_DIR="/root/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

cat > "$SYSTEMD_USER_DIR/ssh-agent.service" <<'EOF'
[Unit]
Description=SSH Key Agent
Documentation=man:ssh-agent(1)
After=default.target

[Service]
Type=simple
Environment=SSH_AUTH_SOCK=%t/ssh-agent.socket
ExecStart=/usr/bin/ssh-agent -D -a %t/ssh-agent.socket
Restart=on-failure

[Install]
WantedBy=default.target
EOF

# Enable lingering so user services start at boot (not just on login)
loginctl enable-linger root 2>/dev/null || true

# Enable the service
systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable ssh-agent 2>/dev/null || true
systemctl --user start ssh-agent 2>/dev/null || true

# Set SSH_AUTH_SOCK in /etc/environment for system-wide availability
if ! grep -q "SSH_AUTH_SOCK" /etc/environment 2>/dev/null; then
    echo 'SSH_AUTH_SOCK="${XDG_RUNTIME_DIR}/ssh-agent.socket"' >> /etc/environment
fi

# Also add to .bashrc for interactive sessions (belt-and-suspenders)
if ! grep -q "ssh-agent" /root/.bashrc 2>/dev/null; then
    cat >> /root/.bashrc <<'BASHEOF'

# SSH Agent (autostart via systemd user service; this is a fallback)
export SSH_AUTH_SOCK="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/ssh-agent.socket"
if ! ssh-add -l &>/dev/null; then
    ssh-add ~/.ssh/github_deploy 2>/dev/null || true
fi
BASHEOF
fi

# Add the GitHub deploy key to the agent now (for this session)
export SSH_AUTH_SOCK="${XDG_RUNTIME_DIR:-/run/user/0}/ssh-agent.socket"
ssh-agent -D -a "$SSH_AUTH_SOCK" &>/dev/null &
sleep 1
ssh-add "$GITHUB_KEY_FILE" 2>/dev/null || true

log "ssh-agent systemd user service configured"

#===============================================================================
# PostgreSQL
#===============================================================================

log "Installing PostgreSQL..."
DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql postgresql-contrib

log "Configuring PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user (idempotent)
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
        CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
    ELSE
        ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec

GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\c ${DB_NAME}
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF

log "PostgreSQL configured"

#===============================================================================
# Python 3.11
#===============================================================================

log "Installing Python 3.11..."
if ! python3.11 --version &>/dev/null; then
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq
fi
DEBIAN_FRONTEND=noninteractive apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

log "Python version: $(python3.11 --version)"

#===============================================================================
# Node.js 20
#===============================================================================

log "Installing Node.js 20..."
if ! node --version 2>/dev/null | grep -q "v20"; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs
fi

log "Node version: $(node --version)"
log "npm version:  $(npm --version)"

#===============================================================================
# Nginx
#===============================================================================

log "Installing Nginx..."
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx
systemctl enable nginx

#===============================================================================
# Production Hardening: Fail2Ban & Logrotate
#===============================================================================

log "Configuring Fail2Ban..."
cat > /etc/fail2ban/jail.local <<EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
EOF
systemctl restart fail2ban

log "Configuring Logrotate for Veriqko..."
cat > /etc/logrotate.d/veriqko <<EOF
/opt/veriqko/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $VERIQKO_USER $VERIQKO_USER
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>/dev/null || true
        systemctl restart veriqko-api > /dev/null 2>/dev/null || true
    endscript
}
EOF

#===============================================================================
# Veriqko User and Directories
#===============================================================================

log "Creating veriqko system user and directories..."
id -u "$VERIQKO_USER" &>/dev/null || useradd -r -m -d "$VERIQKO_HOME" -s /bin/bash "$VERIQKO_USER"

mkdir -p "$VERIQKO_HOME"/{app,data,logs,backups,scripts}
chown -R "$VERIQKO_USER:$VERIQKO_USER" "$VERIQKO_HOME"

log "Creating scheduled backup script..."
BACKUP_SCRIPT="$VERIQKO_HOME/scripts/backup.sh"
cat > "$BACKUP_SCRIPT" <<EOF
#!/bin/bash
# Veriqko Nightly Backup Script
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$VERIQKO_HOME/backups"
KEEP_DAYS=7

echo "Starting backup: \$TIMESTAMP"

# Database Backup
sudo -u postgres pg_dump $DB_NAME > "\$BACKUP_DIR/db_\$TIMESTAMP.sql"

# Config Backup
cp "$VERIQKO_HOME/app/apps/api/.env" "\$BACKUP_DIR/env_api_\$TIMESTAMP" 2>/dev/null || true

# Cleanup old backups
find "\$BACKUP_DIR" -type f -mtime +\$KEEP_DAYS -delete

echo "Backup complete. Files in \$BACKUP_DIR"
EOF

chmod +x "$BACKUP_SCRIPT"
chown "$VERIQKO_USER:$VERIQKO_USER" "$BACKUP_SCRIPT"

# Add cron job for nightly backup at 03:00
(crontab -l 2>/dev/null; echo "0 3 * * * $BACKUP_SCRIPT >> $VERIQKO_HOME/logs/backup.log 2>&1") | crontab -

# Create systemd user service dir for veriqko user (for ssh-agent)
VERIQKO_SYSTEMD_DIR="/home/$VERIQKO_USER/.config/systemd/user"
mkdir -p "$VERIQKO_SYSTEMD_DIR"

cat > "$VERIQKO_SYSTEMD_DIR/ssh-agent.service" <<'EOF'
[Unit]
Description=SSH Key Agent
Documentation=man:ssh-agent(1)
After=default.target

[Service]
Type=simple
Environment=SSH_AUTH_SOCK=%t/ssh-agent.socket
ExecStart=/usr/bin/ssh-agent -D -a %t/ssh-agent.socket
Restart=on-failure

[Install]
WantedBy=default.target
EOF

chown -R "$VERIQKO_USER:$VERIQKO_USER" "/home/$VERIQKO_USER/.config" 2>/dev/null || true

# Enable lingering for veriqko user
loginctl enable-linger "$VERIQKO_USER" 2>/dev/null || true

# Copy GitHub deploy key to veriqko user's SSH dir
VERIQKO_SSH_DIR="$VERIQKO_HOME/.ssh"
mkdir -p "$VERIQKO_SSH_DIR"
cp "$GITHUB_KEY_FILE" "$VERIQKO_SSH_DIR/github_deploy"
cp "${GITHUB_KEY_FILE}.pub" "$VERIQKO_SSH_DIR/github_deploy.pub"
chown -R "$VERIQKO_USER:$VERIQKO_USER" "$VERIQKO_SSH_DIR"
chmod 700 "$VERIQKO_SSH_DIR"
chmod 600 "$VERIQKO_SSH_DIR/github_deploy"

# Copy authorized_keys so direct SSH login works for the veriqko user
# Try ubuntu cloud-init user first, fall back to root
AUTHORIZED_KEYS_SRC=""
for src in /home/ubuntu/.ssh/authorized_keys /root/.ssh/authorized_keys; do
    if [ -f "$src" ]; then
        AUTHORIZED_KEYS_SRC="$src"
        break
    fi
done

if [ -n "$AUTHORIZED_KEYS_SRC" ]; then
    cp "$AUTHORIZED_KEYS_SRC" "$VERIQKO_SSH_DIR/authorized_keys"
    chown "$VERIQKO_USER:$VERIQKO_USER" "$VERIQKO_SSH_DIR/authorized_keys"
    chmod 600 "$VERIQKO_SSH_DIR/authorized_keys"
    log "SSH authorized_keys copied to veriqko user (from $AUTHORIZED_KEYS_SRC)"
    log "  → You can now SSH directly: ssh veriqko@<VM_IP>"
else
    warn "No authorized_keys found to copy for veriqko user."
    warn "  Direct SSH as veriqko will not work until you add keys manually."
fi

# SSH config for veriqko user
cat > "$VERIQKO_SSH_DIR/config" <<EOF
Host github.com
    HostName github.com
    User git
    IdentityFile $VERIQKO_SSH_DIR/github_deploy
    IdentitiesOnly yes
    StrictHostKeyChecking no
    PreferredAuthentications publickey
EOF
chmod 600 "$VERIQKO_SSH_DIR/config"

# Git config for veriqko user
sudo -u "$VERIQKO_USER" git config --global url."git@github.com:".insteadOf "https://github.com/"
sudo -u "$VERIQKO_USER" git config --global core.sshCommand "ssh -i $VERIQKO_SSH_DIR/github_deploy -o StrictHostKeyChecking=no"

log "Veriqko user and directories configured"

#===============================================================================
# Firewall
#===============================================================================

log "Configuring firewall..."
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

#===============================================================================
# Save Credentials
#===============================================================================

log "Saving credentials..."
cat > "$CREDENTIALS_FILE" <<EOF
===============================================================================
VERIQKO DEPLOYMENT CREDENTIALS
Generated: $(date)
===============================================================================

Domain: https://${VERIQKO_DOMAIN}

DATABASE
--------
Host:     localhost
Port:     5432
Database: ${DB_NAME}
Username: ${DB_USER}
Password: ${DB_PASSWORD}

ADMIN USER (set during platform install)
-----------------------------------------
Email:    ${ADMIN_EMAIL}
Password: ${ADMIN_PASSWORD}

JWT SECRET
----------
${JWT_SECRET}

SSH KEYS
--------
Server key (cloud-init/admin access):
  Private: /root/.ssh/id_ed25519
  Public:  /root/.ssh/id_ed25519.pub

GitHub deploy key:
  Private: /root/.ssh/github_deploy
  Public:  /root/.ssh/github_deploy.pub
  Also at: ${VERIQKO_HOME}/.ssh/github_deploy

IMPORTANT: Keep this file secure. Delete after saving credentials elsewhere!
===============================================================================
EOF

chmod 600 "$CREDENTIALS_FILE"

# Export for use by deploy-platform-v2.sh
export VERIQKO_DB_PASSWORD="$DB_PASSWORD"
export VERIQKO_JWT_SECRET="$JWT_SECRET"
export VERIQKO_ADMIN_EMAIL="$ADMIN_EMAIL"
export VERIQKO_ADMIN_PASSWORD="$ADMIN_PASSWORD"

#===============================================================================
# Verify GitHub SSH Connectivity
#===============================================================================

log "Testing GitHub SSH connectivity..."
if sudo -u "$VERIQKO_USER" ssh -T git@github.com < /dev/null -o StrictHostKeyChecking=no -i "$VERIQKO_SSH_DIR/github_deploy" 2>&1 | grep -q "successfully authenticated"; then
    log "✅ GitHub SSH authentication successful!"
else
    warn "⚠️  GitHub SSH test inconclusive (key may not be added to GitHub yet)."
    warn "   Run: ssh -T git@github.com -i $VERIQKO_SSH_DIR/github_deploy"
    warn "   After adding the deploy key at: https://github.com/settings/keys"
fi

#===============================================================================
# Summary
#===============================================================================

echo ""
divider
banner "✅ VERIQKO OS PROVISIONING COMPLETE"
divider
echo ""
echo "System is ready. Next step:"
echo ""
echo -e "  ${BOLD}Run the platform installer:${NC}"
echo "  curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqko/main/infra/deploy-platform-v2.sh | sudo bash"
echo ""
echo "Or if you cloned the repo:"
echo "  sudo bash /path/to/infra/deploy-platform-v2.sh"
echo ""
echo "Credentials saved to: ${CREDENTIALS_FILE}"
echo ""
echo "GitHub deploy key (add to GitHub if not done):"
echo "  cat /root/.ssh/github_deploy.pub"
echo "  https://github.com/settings/keys"
echo ""
divider
