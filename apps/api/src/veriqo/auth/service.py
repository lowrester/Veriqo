"""Authentication service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from veriqo.auth.jwt import create_token_pair, TokenPair
from veriqo.auth.password import verify_password
from veriqo.users.models import User


class AuthService:
    """Authentication service for login and token operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        stmt = select(User).where(
            User.email == email,
            User.deleted_at.is_(None),
            User.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return user

    def create_tokens(self, user: User) -> TokenPair:
        """Create access and refresh tokens for a user."""
        return create_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by ID."""
        stmt = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
