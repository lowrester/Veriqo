#!/bin/bash
#===============================================================================
# Create Admin User for Veriqko
#
# Usage:
#   ./create-admin.sh [email] [password]
#
# If no arguments provided, uses defaults:
#   Email: admin@veriqko.local
#   Password: admin123!
#===============================================================================

set -e

ADMIN_EMAIL="${1:-admin@veriqko.com}"
ADMIN_PASSWORD="${2:-admin123!}"

echo "Creating admin user..."
echo "Email: $ADMIN_EMAIL"

# Navigate to API directory
cd "$(dirname "$0")/../apps/api"

if [ ! -d ".venv" ]; then
    echo "❌ Error: Python virtual environment (.venv) not found in apps/api"
    exit 1
fi

ADMIN_SCRIPT=$(cat <<PYEOF
import asyncio, sys
sys.path.insert(0, 'src')

async def main():
    try:
        from veriqko.db.base import async_session_factory
        from veriqko.auth.password import hash_password
        from veriqko.enums import UserRole
        from sqlalchemy import text
        import uuid, datetime

        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": "$ADMIN_EMAIL"}
            )
            if result.fetchone():
                print("SKIP: Admin user already exists")
                # Just update the password to ensure they can login
                pw_hash = hash_password("$ADMIN_PASSWORD")
                await session.execute(
                    text("UPDATE users SET hashed_password = :pw, role = :role, updated_at = :now WHERE email = :email"),
                    {"email": "$ADMIN_EMAIL", "pw": pw_hash, "role": UserRole.ADMIN.value, "now": datetime.datetime.utcnow()}
                )
                await session.commit()
                print("OK: Admin user password updated.")
                return

            pw_hash = hash_password("$ADMIN_PASSWORD")
            await session.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, full_name, role, is_active, created_at, updated_at)
                    VALUES (:id, :email, :pw, :name, :role, true, :now, :now)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "email": "$ADMIN_EMAIL",
                    "pw": pw_hash,
                    "name": "Administrator",
                    "role": UserRole.ADMIN.value,
                    "now": datetime.datetime.utcnow()
                }
            )
            await session.commit()
            print("OK: Admin user created")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
PYEOF
)

PYTHONPATH="src" .venv/bin/python3 -c "$ADMIN_SCRIPT"

echo ""
echo "✅ Admin user setup script completed!"
echo ""
echo "Login credentials:"
echo "  Email: $ADMIN_EMAIL"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "⚠️  IMPORTANT: Change this password after first login!"
