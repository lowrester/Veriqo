#!/bin/bash
#===============================================================================
# Create Admin User for Veriqko
#
# Usage:
#   ./create-admin.sh [email] [password]
#
# If no arguments provided, uses defaults:
#   Email: admin@veriqko.local
#   Password: admin123
#===============================================================================

set -e

ADMIN_EMAIL="${1:-admin@veriqko.com}"
ADMIN_PASSWORD="${2:-admin123!}"

echo "Creating admin user..."
echo "Email: $ADMIN_EMAIL"

# Navigate to API directory
cd "$(dirname "$0")/../apps/api"

# Generate password hash
PASSWORD_HASH=$(.venv/bin/python3 -c "from veriqko.auth.password import hash_password; print(hash_password('$ADMIN_PASSWORD'))")

# Insert into database
sudo -u postgres psql -d veriqko <<EOF
INSERT INTO users (id, email, password_hash, full_name, role, is_active, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    '$ADMIN_EMAIL',
    '$PASSWORD_HASH',
    'Administrator',
    'admin',
    true,
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;
EOF

echo "✅ Admin user created successfully!"
echo ""
echo "Login credentials:"
echo "  Email: $ADMIN_EMAIL"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "⚠️  IMPORTANT: Change this password after first login!"
