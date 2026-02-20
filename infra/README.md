# Veriqko Deployment Scripts

Deploy Veriqko on Ubuntu Server (bare-metal or Proxmox VM).

## Two-Step Deployment

### Step 1 — Provision the OS (`deploy-ubuntu.sh`)

Run on a **fresh Ubuntu 22.04/24.04** server (or inside a Proxmox VM):

```bash
curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqko/main/infra/deploy-ubuntu.sh -o /tmp/deploy-ubuntu.sh
sudo bash /tmp/deploy-ubuntu.sh
```

**What it does:**
- Updates system packages
- Installs PostgreSQL 15, Python 3.11, Node.js 20, Nginx, UFW
- Installs and enables **QEMU Guest Agent** (for Proxmox)
- Generates a **server SSH key** (for cloud-init / admin access) — displayed for you to copy
- Generates a **GitHub deploy key** — displayed with a 60-second pause so you can add it to GitHub
- Configures SSH for **SSH-only GitHub access** (no HTTPS)
- Sets up **ssh-agent as a systemd user service** (autostart on boot, no login shell needed)
- Creates the `veriqko` system user and directories
- Saves all credentials to `/root/veriqko-credentials.txt`

> **Important:** When prompted, add the GitHub deploy key to:
> `https://github.com/settings/keys`

---

### Step 2 — Install the Platform (`deploy-platform-v2.sh`)

Run after Step 1 completes:

```bash
curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqko/main/infra/deploy-platform-v2.sh -o /tmp/deploy-platform.sh
sudo bash /tmp/deploy-platform.sh
```

**What it does:**
- Clones the `main` branch via SSH
- Creates Python venv, installs backend dependencies
- Generates `.env` (preserves existing secrets on re-run)
- Runs Alembic migrations (with automatic recovery on dirty state)
- Creates admin user
- Builds the React frontend (`npm ci` with auto-fallback to `npm install`)
- Creates and starts the `veriqko-api` systemd service
- Configures Nginx (handles port 80 conflicts automatically)
- Attempts Let's Encrypt SSL if domain is publicly resolvable
- Runs a health check against `/health`

---

## Proxmox Deployment

Run `deploy-proxmox.sh` on the **Proxmox host** to create the VM:

```bash
wget https://raw.githubusercontent.com/lowrester/Veriqko/main/infra/deploy-proxmox.sh
chmod +x deploy-proxmox.sh
./deploy-proxmox.sh
```

Then SSH into the VM and run Steps 1 and 2 above.

---

## Updating the Platform

```bash
sudo bash /opt/veriqko/app/infra/update.sh
```

**Smart update features:**
- Pulls latest `main` via SSH
- **Dependency diffing** — only reinstalls if `requirements.txt` or `package.json` changed
- **Migration rollback** — reverts DB to previous revision if migration fails
- **node_modules recovery** — auto-wipes and retries if `npm ci` fails
- **Full rollback** — reverts git commit and restarts services if health check fails after update

**Options:**

| Flag | Description |
|------|-------------|
| `--full` | Force full reinstall (wipe node_modules, reinstall all deps) |
| `--api` | Update backend only |
| `--web` | Update frontend only |
| `--no-migrate` | Skip database migrations |
| `--no-rollback` | Disable automatic rollback on failure |

---

## Configuration Variables

Set these as environment variables before running any script:

| Variable | Default | Description |
|----------|---------|-------------|
| `VERIQKO_DOMAIN` | `hostname -f` | Domain for the application |
| `VERIQKO_DB_PASSWORD` | random | PostgreSQL password |
| `VERIQKO_JWT_SECRET` | random | JWT signing secret |
| `VERIQKO_ADMIN_EMAIL` | `admin@<domain>` | Admin user email |
| `VERIQKO_ADMIN_PASSWORD` | random | Admin user password |

Example:
```bash
export VERIQKO_DOMAIN=veriqko.example.com
export VERIQKO_ADMIN_EMAIL=admin@example.com
curl -fsSL https://raw.githubusercontent.com/lowrester/Veriqko/main/infra/deploy-ubuntu.sh -o /tmp/deploy-ubuntu.sh
sudo -E bash /tmp/deploy-ubuntu.sh
```

### Central Configuration (Recommended)

Instead of passing environment variables manually, you can create a `config.env` file in the `infra/` directory. All scripts will automatically source it.

1.  Copy the template: `cp infra/config.env.template infra/config.env`
2.  Edit `infra/config.env` with your desired settings.
3.  Run the scripts; they will now use your pre-configured values.

Example:
```bash
# On your host/VM:
cp infra/config.env.template infra/config.env
nano infra/config.env
sudo bash infra/deploy-ubuntu.sh
```

---

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

## File Locations

| Path | Description |
|------|-------------|
| `/opt/veriqko/app` | Application code |
| `/opt/veriqko/data` | Evidence & reports |
| `/opt/veriqko/logs` | Application logs |
| `/opt/veriqko/.ssh/github_deploy` | GitHub deploy key |
| `/root/veriqko-credentials.txt` | Generated credentials |

## Post-Installation

### Check Services

```bash
systemctl status veriqko-api
systemctl status nginx
systemctl status postgresql
systemctl status qemu-guest-agent
```

### View Logs

```bash
journalctl -u veriqko-api -f
tail -f /opt/veriqko/logs/api-error.log
tail -f /var/log/nginx/error.log
```

### SSH & GitHub

```bash
# View GitHub deploy key
cat /root/.ssh/github_deploy.pub

# Test GitHub SSH connectivity
ssh -T git@github.com -i /opt/veriqko/.ssh/github_deploy

# Check ssh-agent service
systemctl --user status ssh-agent
```

### SSL Certificate

If auto-setup failed, run manually:

```bash
sudo certbot --nginx -d your-domain.com
```

### Backup Database

```bash
sudo -u postgres pg_dump veriqko > /opt/veriqko/backups/backup-$(date +%Y%m%d).sql
```

## Troubleshooting

### API not starting

```bash
journalctl -u veriqko-api -n 50
tail -f /opt/veriqko/logs/api-error.log
# Test manually:
cd /opt/veriqko/app/apps/api
sudo -u veriqko .venv/bin/uvicorn veriqko.main:app --host 127.0.0.1 --port 8000
```

### Git clone fails (SSH)

```bash
# Check key is added to GitHub
cat /root/.ssh/github_deploy.pub
# Test connectivity
ssh -T git@github.com -i /opt/veriqko/.ssh/github_deploy
```

### Database connection issues

```bash
sudo -u postgres psql -d veriqko -c "SELECT 1"
cat /opt/veriqko/app/apps/api/.env
```

### QEMU Guest Agent

```bash
systemctl status qemu-guest-agent
# On Proxmox host:
qm guest cmd <VMID> network-get-interfaces
```
