from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from veriqko.db.base import Base, TimestampMixin, UUIDMixin


class SystemSetting(Base, UUIDMixin, TimestampMixin):
    """Global system settings stored as key-value pairs."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<SystemSetting {self.key}>"
