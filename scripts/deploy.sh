#!/bin/bash
set -e

echo "🚀 Starting Veriqo Deployment..."

# 1. Update Codebase (Force Sync)
echo "📥 Pulling latest changes..."
git fetch origin
git reset --hard origin/main

# 2. Frontend Build
echo "🏗️  Building Frontend..."
cd apps/web
npm install
npm run build
cd ../..

# 3. Backend Update
echo "🐍 Updating Backend..."
cd apps/api
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    python3 -m venv .venv
    source .venv/bin/activate
fi

pip install -r requirements.txt

# 4. Database Migrations
echo "🗄️  Running Migrations..."
# Ensure src is in python path for alembic
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
alembic upgrade head

# 5. Restart Service
echo "🔄 Restarting Service..."
sudo systemctl restart veriqo-api

echo "✅ Deployment Complete!"
