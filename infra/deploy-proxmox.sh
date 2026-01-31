#!/bin/bash
#===============================================================================
# Veriqo Proxmox Deployment Script
#
# This script creates an Ubuntu VM in Proxmox and deploys the Veriqo platform
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
VMID="${VMID:-200}"
VM_NAME="${VM_NAME:-veriqo}"
VM_MEMORY="${VM_MEMORY:-4096}"
VM_CORES="${VM_CORES:-2}"
VM_DISK="${VM_DISK:-32G}"
VM_BRIDGE="${VM_BRIDGE:-vmbr0}"
STORAGE="${STORAGE:-local-lvm}"

# Ubuntu Cloud Image
UBUNTU_VERSION="jammy"  # Ubuntu 22.04 LTS
CLOUD_IMAGE_URL="https://cloud-images.ubuntu.com/${UBUNTU_VERSION}/current/${UBUNTU_VERSION}-server-cloudimg-amd64.img"

# Veriqo Configuration
VERIQO_DOMAIN="${VERIQO_DOMAIN:-veriqo.local}"
VERIQO_DB_PASSWORD="${VERIQO_DB_PASSWORD:-$(openssl rand -base64 24)}"
VERIQO_JWT_SECRET="${VERIQO_JWT_SECRET:-$(openssl rand -base64 48)}"
VERIQO_ADMIN_EMAIL="${VERIQO_ADMIN_EMAIL:-admin@veriqo.local}"
VERIQO_ADMIN_PASSWORD="${VERIQO_ADMIN_PASSWORD:-$(openssl rand -base64 16)}"

echo "=============================================="
echo "Veriqo Proxmox Deployment"
echo "=============================================="
echo "VM ID: $VMID"
echo "VM Name: $VM_NAME"
echo "Domain: $VERIQO_DOMAIN"
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
hostname: veriqo
manage_etc_hosts: true

users:
  - name: veriqo
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

write_files:
  - path: /opt/veriqo/deploy.sh
    permissions: '0755'
    content: |
      #!/bin/bash
      # This script is generated and executed by cloud-init
      # See deploy-ubuntu.sh for the full deployment script
      curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqo/claude/add-pdf-support-166IR/infra/deploy-ubuntu.sh | bash

runcmd:
  - /opt/veriqo/deploy.sh

final_message: "Veriqo deployment complete after $UPTIME seconds"
CLOUDEOF
)

# Create snippets directory if not exists
mkdir -p /var/lib/vz/snippets

# Write cloud-init config
echo "$CLOUD_INIT_USER" > /var/lib/vz/snippets/veriqo-user.yml

# Set cloud-init
qm set $VMID --cicustom "user=local:snippets/veriqo-user.yml"
qm set $VMID --ciuser veriqo
qm set $VMID --ipconfig0 ip=dhcp

echo ""
echo "=============================================="
echo "VM Created Successfully!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Add your SSH public key to /var/lib/vz/snippets/veriqo-user.yml"
echo "2. Start the VM: qm start $VMID"
echo "3. Get the IP: qm guest cmd $VMID network-get-interfaces"
echo "4. SSH into the VM: ssh veriqo@<IP>"
echo ""
echo "Credentials (save these!):"
echo "  Database Password: $VERIQO_DB_PASSWORD"
echo "  JWT Secret: $VERIQO_JWT_SECRET"
echo "  Admin Email: $VERIQO_ADMIN_EMAIL"
echo "  Admin Password: $VERIQO_ADMIN_PASSWORD"
echo ""
