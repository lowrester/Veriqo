#!/bin/bash
#===============================================================================
# Veriqko Proxmox Deployment Script
#
# This script creates an Ubuntu VM in Proxmox and deploys the Veriqko platform
#
# Usage:
#   1. Run on Proxmox host: ./deploy-proxmox.sh
#   2. Or create VM manually and run the cloud-init script inside
#
# Requirements:
#   - Proxmox VE 7.x or 8.x
#   - Ubuntu Cloud Image (jammy or noble)
#   - Internet access for package downloads
#===============================================================================

set -e

# Configuration - EDIT THESE VALUES
VMID="${VMID:-201}"
VM_NAME="${VM_NAME:-veriqko}"
VM_MEMORY="${VM_MEMORY:-4096}"
VM_CORES="${VM_CORES:-2}"
VM_DISK="${VM_DISK:-32G}"
VM_BRIDGE="${VM_BRIDGE:-vmbr0}"
STORAGE="${STORAGE:-local-lvm}"

# Ubuntu Cloud Image
UBUNTU_VERSION="jammy"  # Ubuntu 22.04 LTS
CLOUD_IMAGE_URL="https://cloud-images.ubuntu.com/${UBUNTU_VERSION}/current/${UBUNTU_VERSION}-server-cloudimg-amd64.img"

# Veriqko Configuration
VERIQKO_BRANCH="${VERIQKO_BRANCH:-main}"
VERIQKO_DOMAIN="${VERIQKO_DOMAIN:-veriqko.local}"
VERIQKO_DB_PASSWORD="${VERIQKO_DB_PASSWORD:-$(openssl rand -base64 24)}"
VERIQKO_JWT_SECRET="${VERIQKO_JWT_SECRET:-$(openssl rand -base64 48)}"
VERIQKO_ADMIN_EMAIL="${VERIQKO_ADMIN_EMAIL:-admin@veriqko.local}"
VERIQKO_ADMIN_PASSWORD="${VERIQKO_ADMIN_PASSWORD:-$(openssl rand -base64 16)}"

echo "=============================================="
echo "Veriqko Proxmox Deployment"
echo "=============================================="
echo "VM ID: $VMID"
echo "VM Name: $VM_NAME"
echo "Domain: $VERIQKO_DOMAIN"
echo ""

# Check if running on Proxmox
if ! command -v qm &> /dev/null; then
    echo "ERROR: This script must be run on a Proxmox host"
    echo "Alternatively, use deploy-ubuntu.sh directly on an Ubuntu server"
    exit 1
fi

# Download Ubuntu Cloud Image if not exists
CLOUD_IMAGE="/var/lib/vz/template/iso/${UBUNTU_VERSION}-server-cloudimg-amd64.img"
if [ ! -f "$CLOUD_IMAGE" ]; then
    echo "Downloading Ubuntu Cloud Image..."
    wget -O "$CLOUD_IMAGE" "$CLOUD_IMAGE_URL"
fi

# Create VM
echo "Creating VM $VMID..."
qm create $VMID --name $VM_NAME --memory $VM_MEMORY --cores $VM_CORES --net0 virtio,bridge=$VM_BRIDGE

# Import disk
echo "Importing disk..."
qm importdisk $VMID "$CLOUD_IMAGE" $STORAGE

# Configure VM
echo "Configuring VM..."
qm set $VMID --scsihw virtio-scsi-pci --scsi0 ${STORAGE}:vm-${VMID}-disk-0
qm set $VMID --ide2 ${STORAGE}:cloudinit
qm set $VMID --boot c --bootdisk scsi0
qm set $VMID --serial0 socket --vga serial0
qm set $VMID --agent enabled=1

# Resize disk
echo "Resizing disk to $VM_DISK..."
qm resize $VMID scsi0 $VM_DISK

# Generate cloud-init user data
CLOUD_INIT_USER=$(cat <<'CLOUDEOF'
#cloud-config
hostname: veriqko
manage_etc_hosts: true

users:
  - name: veriqko
    groups: sudo
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-rsa AAAAB... # Add your SSH public key here

package_update: true
package_upgrade: true

packages:
  - postgresql
  - postgresql-contrib
  - python3.11
  - python3.11-venv
  - python3-pip
  - nodejs
  - npm
  - nginx
  - certbot
  - python3-certbot-nginx
  - git
  - curl
  - htop
  - qemu-guest-agent

write_files:
  - path: /opt/veriqko/deploy.sh
    permissions: '0755'
    content: |
      #!/bin/bash
      # This script is generated and executed by cloud-init
      export VERIQKO_DOMAIN="${VERIQKO_DOMAIN}"
      export VERIQKO_DB_PASSWORD="${VERIQKO_DB_PASSWORD}"
      export VERIQKO_JWT_SECRET="${VERIQKO_JWT_SECRET}"
      export VERIQKO_ADMIN_EMAIL="${VERIQKO_ADMIN_EMAIL}"
      export VERIQKO_ADMIN_PASSWORD="${VERIQKO_ADMIN_PASSWORD}"
      
      # See deploy-ubuntu.sh for the full deployment script
      curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqo/main/infra/deploy-ubuntu.sh | bash

runcmd:
  - /opt/veriqko/deploy.sh

final_message: "Veriqko deployment complete after $UPTIME seconds"
CLOUDEOF
)

# Create snippets directory if not exists
mkdir -p /var/lib/vz/snippets

# Write cloud-init config
echo "$CLOUD_INIT_USER" > /var/lib/vz/snippets/veriqko-user.yml

# Set cloud-init
qm set $VMID --cicustom "user=local:snippets/veriqko-user.yml"
qm set $VMID --ciuser veriqko
qm set $VMID --ipconfig0 ip=dhcp

echo ""
echo "=============================================="
echo "VM Created Successfully!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Add your SSH public key to /var/lib/vz/snippets/veriqko-user.yml"
echo "2. Start the VM: qm start $VMID"
echo "3. Get the IP: qm guest cmd $VMID network-get-interfaces"
echo "4. SSH into the VM: ssh veriqko@<IP>"
echo ""
echo "Credentials (save these!):"
echo "  Database Password: $VERIQKO_DB_PASSWORD"
echo "  JWT Secret: $VERIQKO_JWT_SECRET"
echo "  Admin Email: $VERIQKO_ADMIN_EMAIL"
echo "  Admin Password: $VERIQKO_ADMIN_PASSWORD"
echo ""
