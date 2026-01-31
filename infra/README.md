# Veriqo Deployment Scripts

Deploy Veriqo on Ubuntu Server (with or without Proxmox).

## Quick Start

### Option 1: Direct Ubuntu Server Deployment

Run this on any Ubuntu 22.04/24.04 server:

```bash
curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqo/claude/add-pdf-support-166IR/infra/deploy-ubuntu.sh | sudo bash
```

Or with custom settings:

```bash
export VERIQO_DOMAIN=veriqo.example.com
export VERIQO_ADMIN_EMAIL=admin@example.com
curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqo/claude/add-pdf-support-166IR/infra/deploy-ubuntu.sh | sudo -E bash
```

### Option 2: Proxmox VM Deployment

Run on Proxmox host:

```bash
# Download and customize
wget https://raw.githubusercontent.com/lowrester/Veriqo/claude/add-pdf-support-166IR/infra/deploy-proxmox.sh
chmod +x deploy-proxmox.sh

# Edit configuration (VM ID, name, resources)
nano deploy-proxmox.sh

# Deploy
./deploy-proxmox.sh
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `VERIQO_DOMAIN` | hostname | Domain for the application |
| `VERIQO_DB_PASSWORD` | random | PostgreSQL password |
| `VERIQO_JWT_SECRET` | random | JWT signing secret |
| `VERIQO_ADMIN_EMAIL` | admin@domain | Admin user email |
| `VERIQO_ADMIN_PASSWORD` | random | Admin user password |

## What Gets Installed

- **PostgreSQL 15** - Database
- **Python 3.11** - Backend runtime
- **Node.js 20** - Frontend build
- **Nginx** - Reverse proxy
- **Certbot** - SSL certificates (optional)
- **UFW** - Firewall

## Architecture

```
                    ┌─────────────────┐
                    │     Nginx       │
                    │   (port 80/443) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Static   │  │   API    │  │  /r/     │
        │  Files   │  │ (8000)   │  │ (public) │
        │ (React)  │  │ (FastAPI)│  │          │
        └──────────┘  └────┬─────┘  └──────────┘
                           │
                    ┌──────┴──────┐
                    │ PostgreSQL  │
                    │  (5432)     │
                    └─────────────┘
```

## Post-Installation

### Check Services

```bash
systemctl status veriqo-api
systemctl status nginx
systemctl status postgresql
```

### View Logs

```bash
# API logs
journalctl -u veriqo-api -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### SSL Certificate

If auto-setup failed, run manually:

```bash
sudo certbot --nginx -d your-domain.com
```

### Backup Database

```bash
sudo -u postgres pg_dump veriqo > backup.sql
```

## File Locations

| Path | Description |
|------|-------------|
| `/opt/veriqo/app` | Application code |
| `/opt/veriqo/data` | Evidence & reports |
| `/opt/veriqo/logs` | Application logs |
| `/root/veriqo-credentials.txt` | Generated credentials |

## Troubleshooting

### API not starting

```bash
# Check logs
journalctl -u veriqo-api -n 50

# Test manually
cd /opt/veriqo/app/apps/api
./venv/bin/uvicorn veriqo.main:app --host 127.0.0.1 --port 8000
```

### Database connection issues

```bash
# Test connection
sudo -u postgres psql -d veriqo -c "SELECT 1"

# Check credentials in .env
cat /opt/veriqo/app/apps/api/.env
```

### Nginx errors

```bash
# Test configuration
nginx -t

# Check logs
tail -f /var/log/nginx/error.log
```
