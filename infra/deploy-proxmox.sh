#!/bin/bash
#===============================================================================
# Veriqko — All-in-One Proxmox Deployment Script
#
# Run this on your Proxmox HOST. It will:
#   1. Generate an SSH key pair on the Proxmox host (for VM access)
#   2. Download Ubuntu 22.04 cloud image (cached)
#   3. Create and configure the VM (disk, CPU, RAM, cloud-init, QEMU agent)
#   4. Start the VM and wait for it to boot
#   5. SSH into the VM and run the full OS provisioning:
#      - System packages (PostgreSQL, Python 3.11, Node.js 20, Nginx, UFW)
#      - QEMU Guest Agent (enabled + started)
#      - GitHub deploy key (generated + displayed — you add it to GitHub)
#      - SSH-only GitHub config
#      - ssh-agent as systemd user service (autostart on boot)
#      - veriqko system user + directories
#   6. Display the GitHub deploy key and wait for you to add it
#   7. Run deploy-platform-v2.sh inside the VM to install the application
#
# Usage (on Proxmox host):
#   bash deploy-proxmox.sh
#
# Custom settings:
#   VMID=202 VM_MEMORY=8192 VERIQKO_DOMAIN=veriqko.example.com bash deploy-proxmox.sh
#
# Requirements:
#   - Proxmox VE 7.x or 8.x
#   - Internet access
#===============================================================================

set -euo pipefail

#===============================================================================
# Configuration — edit or override via environment variables
#===============================================================================

# VM
VMID="${VMID:-201}"
VM_NAME="${VM_NAME:-veriqko}"
VM_MEMORY="${VM_MEMORY:-4096}"       # MB
VM_CORES="${VM_CORES:-2}"
VM_DISK="${VM_DISK:-32G}"
VM_BRIDGE="${VM_BRIDGE:-vmbr0}"
STORAGE="${STORAGE:-local-lvm}"
UBUNTU_VERSION="${UBUNTU_VERSION:-jammy}"   # jammy=22.04, noble=24.04

# Veriqko application
VERIQKO_DOMAIN="${VERIQKO_DOMAIN:-veriqko.local}"
VERIQKO_BRANCH="${VERIQKO_BRANCH:-main}"
VERIQKO_DB_PASSWORD="${VERIQKO_DB_PASSWORD:-$(openssl rand -base64 24)}"
VERIQKO_JWT_SECRET="${VERIQKO_JWT_SECRET:-$(openssl rand -base64 48)}"
VERIQKO_ADMIN_EMAIL="${VERIQKO_ADMIN_EMAIL:-admin@${VERIQKO_DOMAIN}}"
VERIQKO_ADMIN_PASSWORD="${VERIQKO_ADMIN_PASSWORD:-$(openssl rand -base64 16)}"

# SSH
PROXMOX_SSH_KEY="/root/.ssh/veriqko_vm_deploy"
VM_USER="ubuntu"   # Ubuntu cloud images default user

# Your personal SSH public key — injected into cloud-init so you can SSH
# directly from your laptop (not just from the Proxmox host).
# Set via env var or leave blank to be prompted.
ADMIN_SSH_PUBKEY="${ADMIN_SSH_PUBKEY:-}"

# Console password — emergency access via Proxmox UI if SSH fails.
# Set via env var or leave blank to auto-generate.
VM_CONSOLE_PASSWORD="${VM_CONSOLE_PASSWORD:-$(openssl rand -base64 16)}"

# Paths
CLOUD_IMAGE_DIR="/var/lib/vz/template/iso"
SNIPPETS_DIR="/var/lib/vz/snippets"
CLOUD_IMAGE="${CLOUD_IMAGE_DIR}/${UBUNTU_VERSION}-server-cloudimg-amd64.img"
CLOUD_IMAGE_URL="https://cloud-images.ubuntu.com/${UBUNTU_VERSION}/current/${UBUNTU_VERSION}-server-cloudimg-amd64.img"

# Credentials output
CREDENTIALS_FILE="/root/veriqko-credentials-${VMID}.txt"

#===============================================================================
# Colors & helpers
#===============================================================================

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
banner()  { echo -e "\n${BOLD}${CYAN}$1${NC}\n"; }

#===============================================================================
# Preflight checks
#===============================================================================

if ! command -v qm &>/dev/null; then
    error "This script must be run on a Proxmox VE host (qm not found)."
fi

if [ "$EUID" -ne 0 ]; then
    error "Run as root on the Proxmox host."
fi

divider
banner "  🚀 Veriqko All-in-One Proxmox Deployment"
divider
echo ""
echo "  VM ID:      $VMID"
echo "  VM Name:    $VM_NAME"
echo "  Memory:     ${VM_MEMORY}MB"
echo "  Cores:      $VM_CORES"
echo "  Disk:       $VM_DISK"
echo "  Storage:    $STORAGE"
echo "  Bridge:     $VM_BRIDGE"
echo "  Ubuntu:     $UBUNTU_VERSION"
echo "  Domain:     $VERIQKO_DOMAIN"
echo "  Branch:     $VERIQKO_BRANCH"
echo ""

# Prompt for personal SSH public key if not set
if [ -z "$ADMIN_SSH_PUBKEY" ]; then
    # Try to auto-detect from common locations on the Proxmox host
    for keyfile in /root/.ssh/id_ed25519.pub /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys; do
        if [ -f "$keyfile" ]; then
            DETECTED_KEY=$(head -1 "$keyfile")
            echo ""
            echo -e "${CYAN}Detected SSH public key: ${NC}${DETECTED_KEY:0:60}..."
            read -rp "Use this key for VM access? [Y/n] " USE_DETECTED
            if [[ ! "$USE_DETECTED" =~ ^[Nn]$ ]]; then
                ADMIN_SSH_PUBKEY="$DETECTED_KEY"
            fi
            break
        fi
    done
fi

if [ -z "$ADMIN_SSH_PUBKEY" ]; then
    echo ""
    warn "No personal SSH public key set."
    warn "Without it you can only SSH into the VM from this Proxmox host."
    read -rp "Paste your SSH public key (or press Enter to skip): " ADMIN_SSH_PUBKEY
fi

# Confirm before proceeding
read -rp "Proceed with deployment? [y/N] " CONFIRM
[[ "$CONFIRM" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

#===============================================================================
# Step 1: SSH key on Proxmox host (for accessing the VM)
#===============================================================================

step "1/8 — Proxmox Host SSH Key"

mkdir -p /root/.ssh
chmod 700 /root/.ssh

if [ ! -f "$PROXMOX_SSH_KEY" ]; then
    log "Generating SSH key for VM access..."
    ssh-keygen -t ed25519 -C "proxmox-veriqko-deploy" -f "$PROXMOX_SSH_KEY" -N ""
else
    log "SSH key already exists: $PROXMOX_SSH_KEY"
fi

PROXMOX_PUBKEY=$(cat "${PROXMOX_SSH_KEY}.pub")
log "Proxmox deploy key: ${PROXMOX_SSH_KEY}.pub"

#===============================================================================
# Step 2: Download Ubuntu cloud image
#===============================================================================

step "2/8 — Ubuntu Cloud Image"

mkdir -p "$CLOUD_IMAGE_DIR"

if [ -f "$CLOUD_IMAGE" ]; then
    log "Cloud image already cached: $CLOUD_IMAGE"
else
    log "Downloading Ubuntu $UBUNTU_VERSION cloud image..."
    wget --progress=bar:force -O "$CLOUD_IMAGE" "$CLOUD_IMAGE_URL"
    log "Download complete"
fi

#===============================================================================
# Step 3: Create and configure VM
#===============================================================================

step "3/8 — Create VM"

# Remove existing VM with same ID if present
if qm status "$VMID" &>/dev/null; then
    warn "VM $VMID already exists."
    read -rp "Destroy and recreate it? [y/N] " DESTROY_CONFIRM
    if [[ "$DESTROY_CONFIRM" =~ ^[Yy]$ ]]; then
        log "Stopping and destroying VM $VMID..."
        qm stop "$VMID" 2>/dev/null || true
        sleep 3
        qm destroy "$VMID" --purge 2>/dev/null || true
        sleep 2
    else
        error "Aborted. Choose a different VMID or destroy the existing VM manually."
    fi
fi

log "Creating VM $VMID ($VM_NAME)..."
qm create "$VMID" \
    --name "$VM_NAME" \
    --memory "$VM_MEMORY" \
    --cores "$VM_CORES" \
    --net0 "virtio,bridge=${VM_BRIDGE}" \
    --ostype l26 \
    --onboot 1

log "Importing disk..."
qm importdisk "$VMID" "$CLOUD_IMAGE" "$STORAGE"

log "Configuring VM hardware..."

# Build combined SSH authorized keys (Proxmox host key + operator personal key)
ALL_SSH_KEYS="$PROXMOX_PUBKEY"
if [ -n "$ADMIN_SSH_PUBKEY" ]; then
    ALL_SSH_KEYS="${PROXMOX_PUBKEY}
${ADMIN_SSH_PUBKEY}"
    log "Injecting Proxmox host key + personal admin key into cloud-init"
else
    log "Injecting Proxmox host key into cloud-init (no personal key provided)"
fi

qm set "$VMID" \
    --scsihw virtio-scsi-pci \
    --scsi0 "${STORAGE}:vm-${VMID}-disk-0,discard=on" \
    --ide2 "${STORAGE}:cloudinit" \
    --boot "order=scsi0" \
    --serial0 socket \
    --vga serial0 \
    --agent enabled=1 \
    --ipconfig0 ip=dhcp \
    --ciuser "$VM_USER" \
    --cipassword "$VM_CONSOLE_PASSWORD" \
    --sshkeys <(echo "$ALL_SSH_KEYS")

log "Cloud-init: SSH keys injected, console password set"

log "Resizing disk to $VM_DISK..."
qm resize "$VMID" scsi0 "$VM_DISK"

log "VM $VMID created and configured"

#===============================================================================
# Step 4: Start VM and wait for boot + IP
#===============================================================================

step "4/8 — Boot VM"

log "Starting VM $VMID..."
qm start "$VMID"

echo ""
log "VM is booting. Check the IP in:"
log "  • Proxmox web UI → VM $VMID → Summary"
log "  • Your router's DHCP leases"
log "  • Or run: qm guest cmd $VMID network-get-interfaces"
echo ""
log "Waiting 30 seconds for VM to boot..."
sleep 30

VM_IP=""
while true; do
    read -rp "Enter VM IP address: " VM_IP
    if [[ "$VM_IP" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        break
    else
        warn "Invalid format. Enter a valid IPv4 address (e.g. 192.168.1.100)"
    fi
done

log "Using IP: $VM_IP"

# Wait for SSH to be ready
log "Waiting for SSH to become available..."
for i in $(seq 1 24); do
    if ssh -o StrictHostKeyChecking=no \
           -o ConnectTimeout=5 \
           -o BatchMode=yes \
           -i "$PROXMOX_SSH_KEY" \
           "${VM_USER}@${VM_IP}" "echo ok" &>/dev/null; then
        log "SSH is ready"
        break
    fi
    log "  Waiting for SSH... ($((i*5))s)"
    sleep 5
done

#===============================================================================
# Helper: run command inside VM via SSH
#===============================================================================

vm_ssh() {
    ssh -o StrictHostKeyChecking=no \
        -o ConnectTimeout=30 \
        -o ServerAliveInterval=10 \
        -i "$PROXMOX_SSH_KEY" \
        "${VM_USER}@${VM_IP}" "$@"
}

vm_ssh_sudo() {
    vm_ssh "sudo bash -c $(printf '%q' "$1")"
}

#===============================================================================
# Step 5: OS Provisioning inside VM
#===============================================================================

step "5/8 — OS Provisioning (inside VM)"

log "Uploading provisioning environment to VM..."

# Build the environment block to inject into the VM
ENV_BLOCK="export VERIQKO_DOMAIN='${VERIQKO_DOMAIN}'
export VERIQKO_BRANCH='${VERIQKO_BRANCH}'
export VERIQKO_DB_PASSWORD='${VERIQKO_DB_PASSWORD}'
export VERIQKO_JWT_SECRET='${VERIQKO_JWT_SECRET}'
export VERIQKO_ADMIN_EMAIL='${VERIQKO_ADMIN_EMAIL}'
export VERIQKO_ADMIN_PASSWORD='${VERIQKO_ADMIN_PASSWORD}'"

# Write env to VM
vm_ssh "echo '$ENV_BLOCK' | sudo tee /root/veriqko-env.sh > /dev/null"
vm_ssh "sudo chmod 600 /root/veriqko-env.sh"

log "Running deploy-ubuntu.sh inside VM..."
vm_ssh "sudo bash -c 'source /root/veriqko-env.sh && curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqo/main/infra/deploy-ubuntu.sh | bash'" || \
    error "deploy-ubuntu.sh failed inside VM. Check VM console for details."

log "OS provisioning complete"

#===============================================================================
# Step 6: Retrieve and display GitHub deploy key
#===============================================================================

step "6/8 — GitHub Deploy Key"

GITHUB_PUBKEY=$(vm_ssh "sudo cat /root/.ssh/github_deploy.pub" 2>/dev/null || echo "")

if [ -z "$GITHUB_PUBKEY" ]; then
    warn "Could not retrieve GitHub deploy key from VM."
    warn "SSH into the VM and run: cat /root/.ssh/github_deploy.pub"
else
    divider
    banner "🔑 GITHUB DEPLOY KEY — ADD THIS TO GITHUB NOW"
    echo -e "${RED}${BOLD}You MUST add this key to GitHub before the platform can be installed.${NC}"
    echo ""
    echo "  1. Copy the key below"
    echo "  2. Go to: https://github.com/settings/keys"
    echo "  3. Click 'New SSH key' → paste → save"
    echo ""
    echo -e "${BOLD}${GITHUB_PUBKEY}${NC}"
    echo ""
    divider
    echo ""
    echo -e "${YELLOW}Waiting up to 120 seconds for you to add the key...${NC}"
    echo -e "${YELLOW}Press Enter to continue when done.${NC}"
    echo ""
    read -t 120 -p "Press Enter to continue..." || true
    echo ""
fi

#===============================================================================
# Step 7: Install Veriqko platform inside VM
#===============================================================================

step "7/8 — Platform Installation (inside VM)"

log "Running deploy-platform-v2.sh inside VM..."
vm_ssh "sudo bash -c 'source /root/veriqko-env.sh && curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqo/main/infra/deploy-platform-v2.sh | bash'" || \
    error "deploy-platform-v2.sh failed inside VM. Check VM console for details."

log "Platform installation complete"

#===============================================================================
# Step 8: Save credentials and final summary
#===============================================================================

step "8/8 — Final Summary"

# Retrieve credentials from VM
VM_CREDENTIALS=$(vm_ssh "sudo cat /root/veriqko-credentials.txt" 2>/dev/null || echo "")

cat > "$CREDENTIALS_FILE" <<EOF
===============================================================================
VERIQKO DEPLOYMENT — PROXMOX HOST RECORD
Generated: $(date)
===============================================================================

VM ID:      $VMID
VM Name:    $VM_NAME
VM IP:      $VM_IP
Domain:     $VERIQKO_DOMAIN

SSH ACCESS (from this Proxmox host)
-------------------------------------
ssh -i $PROXMOX_SSH_KEY ${VM_USER}@${VM_IP}

Or via Proxmox console:
  qm terminal $VMID

APPLICATION CREDENTIALS
------------------------
Admin Email:    $VERIQKO_ADMIN_EMAIL
Admin Password: $VERIQKO_ADMIN_PASSWORD

DATABASE
--------
Password: $VERIQKO_DB_PASSWORD

JWT SECRET
----------
$VERIQKO_JWT_SECRET

GITHUB DEPLOY KEY (on VM)
--------------------------
/root/.ssh/github_deploy
/opt/veriqko/.ssh/github_deploy

USEFUL COMMANDS (run on VM)
-----------------------------
sudo systemctl status veriqko-api
sudo journalctl -u veriqko-api -f
sudo bash /opt/veriqko/app/infra/update.sh

IMPORTANT: Delete this file after saving credentials elsewhere!
===============================================================================

--- VM CREDENTIALS FILE ---
$VM_CREDENTIALS
EOF

chmod 600 "$CREDENTIALS_FILE"

echo ""
divider
banner "  ✅ VERIQKO DEPLOYMENT COMPLETE"
divider
echo ""
echo "  VM ID:       $VMID"
echo "  VM IP:       $VM_IP"
echo "  App URL:     http://${VM_IP}"
echo "  Domain URL:  http://${VERIQKO_DOMAIN}  (configure DNS to point to $VM_IP)"
echo ""
echo "  Admin email:    $VERIQKO_ADMIN_EMAIL"
echo "  Admin password: $VERIQKO_ADMIN_PASSWORD"
echo ""
echo "  SSH into VM:"
echo "    ssh -i $PROXMOX_SSH_KEY ${VM_USER}@${VM_IP}"
echo ""
echo "  To update the platform (run inside VM):"
echo "    sudo bash /opt/veriqko/app/infra/update.sh"
echo ""
echo "  Credentials saved to: $CREDENTIALS_FILE"
echo ""
echo "  To clean up Proxmox host artifacts from this deployment:"
echo "    bash $(dirname "$0")/proxmox-cleanup.sh"
echo ""
divider
