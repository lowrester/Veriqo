import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from veriqko.integrations.models import ApiKey, WebhookSubscription


class KeyGenerator:
    @staticmethod
    def generate() -> tuple[str, str]:
        """
        Generates a new API Key.
        Returns: (raw_key, hashed_key)
        Format: vq_live_<random_32_chars>
        """
        random_part = secrets.token_urlsafe(32)
        raw_key = f"vq_live_{random_part}"
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, hashed_key

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

class IntegrationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_api_key(self, name: str, scopes: list[str], user_id: UUID) -> tuple[ApiKey, str]:
        """Creates a new API Key. Returns model and raw key (to show once)."""
        raw_key, hashed_key = KeyGenerator.generate()

        api_key = ApiKey(
            name=name,
            key_prefix=raw_key[:8],
            hashed_key=hashed_key,
            scopes=scopes,
            created_by_id=user_id
        )
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        return api_key, raw_key

    async def get_api_key_by_hash(self, hashed_key: str) -> ApiKey | None:
        """Retrieves an active API Key by its hash."""
        result = await self.session.execute(
            select(ApiKey).where(
                ApiKey.hashed_key == hashed_key,
                ApiKey.is_active == True
            )
        )
        return result.scalars().first()

    async def list_api_keys(self) -> list[ApiKey]:
        result = await self.session.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))
        return result.scalars().all()

    async def create_webhook(self, url: str, events: list[str], user_id: UUID) -> WebhookSubscription:
        webhook = WebhookSubscription(
            url=url,
            events=events,
            secret_key=secrets.token_hex(24),  # Shared secret for HMAC
            created_by_id=user_id
        )
        self.session.add(webhook)
        await self.session.commit()
        await self.session.refresh(webhook)
        return webhook

    async def list_webhooks(self) -> list[WebhookSubscription]:
        result = await self.session.execute(select(WebhookSubscription))
        return result.scalars().all()
