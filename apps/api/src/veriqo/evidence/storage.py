"""Evidence file storage."""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import aiofiles
import aiofiles.os


@dataclass
class StoredFile:
    """Metadata about a stored file."""

    stored_filename: str
    relative_path: str
    absolute_path: Path
    size_bytes: int
    sha256_hash: str
    mime_type: str


@dataclass
class StorageConfig:
    """Storage configuration."""

    base_path: Path
    max_file_size_mb: int = 100
    allowed_mime_types: list[str] | None = None

    def __post_init__(self):
        if self.allowed_mime_types is None:
            self.allowed_mime_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/gif",
                "video/mp4",
                "video/quicktime",
                "video/webm",
                "application/pdf",
            ]


class LocalFileStorage:
    """
    Local filesystem storage implementation.

    Directory structure:
    {base_path}/
    ├── evidence/
    │   ├── 2024/
    │   │   ├── 01/
    │   │   │   ├── {job_id}/
    │   │   │   │   ├── {uuid}_{original_name}.jpg
    │   │   │   │   └── ...
    │   │   │   └── ...
    │   │   └── ...
    │   └── ...
    └── reports/
        └── {year}/{month}/{job_id}/
            └── {report_id}.pdf
    """

    def __init__(self, config: StorageConfig):
        self.config = config
        self.base_path = config.base_path

    async def save(
        self,
        file: BinaryIO,
        job_id: str,
        filename: str,
        mime_type: str,
    ) -> StoredFile:
        """Save a file and return storage metadata."""
        # Validate mime type
        if mime_type not in self.config.allowed_mime_types:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Generate unique filename
        file_uuid = str(uuid4())
        safe_filename = self._sanitize_filename(filename)
        stored_filename = f"{file_uuid}_{safe_filename}"

        # Build path: evidence/YYYY/MM/job_id/
        now = datetime.now(timezone.utc)
        relative_dir = Path("evidence") / str(now.year) / f"{now.month:02d}" / job_id
        relative_path = relative_dir / stored_filename
        absolute_path = self.base_path / relative_path

        # Ensure directory exists
        await aiofiles.os.makedirs(absolute_path.parent, exist_ok=True)

        # Calculate hash while writing
        sha256 = hashlib.sha256()
        size = 0

        async with aiofiles.open(absolute_path, "wb") as f:
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break

                sha256.update(chunk)
                size += len(chunk)

                # Check size limit
                max_size = self.config.max_file_size_mb * 1024 * 1024
                if size > max_size:
                    await aiofiles.os.remove(absolute_path)
                    raise ValueError(
                        f"File exceeds maximum size of {self.config.max_file_size_mb}MB"
                    )

                await f.write(chunk)

        return StoredFile(
            stored_filename=stored_filename,
            relative_path=str(relative_path),
            absolute_path=absolute_path,
            size_bytes=size,
            sha256_hash=sha256.hexdigest(),
            mime_type=mime_type,
        )

    async def get_path(self, relative_path: str) -> Path:
        """Get absolute path for a stored file."""
        return self.base_path / relative_path

    async def exists(self, relative_path: str) -> bool:
        """Check if a file exists."""
        path = self.base_path / relative_path
        return await aiofiles.os.path.exists(path)

    async def delete(self, relative_path: str) -> bool:
        """Soft delete - move to .deleted/ directory."""
        absolute_path = self.base_path / relative_path
        deleted_path = self.base_path / ".deleted" / relative_path

        if not await aiofiles.os.path.exists(absolute_path):
            return False

        await aiofiles.os.makedirs(deleted_path.parent, exist_ok=True)
        await aiofiles.os.rename(absolute_path, deleted_path)
        return True

    def _sanitize_filename(self, filename: str) -> str:
        """Remove unsafe characters from filename."""
        # Keep only alphanumeric, dots, hyphens, underscores
        safe = re.sub(r"[^\w\-.]", "_", filename)

        # Limit length
        if "." in safe:
            name, ext = safe.rsplit(".", 1)
            return f"{name[:50]}.{ext}"
        return safe[:50]


def get_storage() -> LocalFileStorage:
    """Get storage instance."""
    from veriqo.config import get_settings

    settings = get_settings()
    config = StorageConfig(
        base_path=settings.storage_base_path,
        max_file_size_mb=settings.storage_max_file_size_mb,
    )
    return LocalFileStorage(config)
