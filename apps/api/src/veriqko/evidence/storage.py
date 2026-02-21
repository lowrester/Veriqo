"""Evidence file storage."""

import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
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
    absolute_path: Path | str
    size_bytes: int
    sha256_hash: str
    mime_type: str


@dataclass
class StorageConfig:
    """Storage configuration."""

    base_path: Path
    max_file_size_mb: int = 100
    allowed_mime_types: list[str] | None = None
    azure_connection_string: str | None = None
    azure_container_name: str = "veriqko-assets"

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


class Storage(ABC):
    """Abstract storage interface."""

    @abstractmethod
    async def save(
        self,
        file: BinaryIO,
        job_id: str,
        filename: str,
        mime_type: str,
        folder: str = "evidence",
    ) -> StoredFile:
        """Save a file and return storage metadata."""
        pass

    @abstractmethod
    async def get_path(self, relative_path: str) -> Path | str:
        """Get path or URL for a stored file."""
        pass

    @abstractmethod
    async def exists(self, relative_path: str) -> bool:
        """Check if a file exists."""
        pass

    @abstractmethod
    async def delete(self, relative_path: str) -> bool:
        """Delete a file."""
        pass


class AzureBlobStorage(Storage):
    """Azure Blob Storage implementation."""

    def __init__(self, config: StorageConfig):
        self.config = config
        if not config.azure_connection_string:
            raise ValueError("Azure connection string is required")

        # Lazy import to avoid dependency issues if not using Azure
        from azure.storage.blob import BlobServiceClient
        self.client = BlobServiceClient.from_connection_string(config.azure_connection_string)
        self.container_name = config.azure_container_name

    async def save(
        self,
        file: BinaryIO,
        job_id: str,
        filename: str,
        mime_type: str,
        folder: str = "evidence",
    ) -> StoredFile:
        # Validate mime type
        if mime_type not in self.config.allowed_mime_types:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Generate unique filename
        file_uuid = str(uuid4())
        safe_filename = self._sanitize_filename(filename)
        stored_filename = f"{file_uuid}_{safe_filename}"

        # Build blob path: {folder}/YYYY/MM/job_id/
        now = datetime.now(UTC)
        blob_path = f"{folder}/{now.year}/{now.month:02d}/{job_id}/{stored_filename}"

        # Calculate hash while reading
        sha256 = hashlib.sha256()
        content = file.read()
        sha256.update(content)
        size = len(content)

        # Check size limit
        if size > self.config.max_file_size_mb * 1024 * 1024:
            raise ValueError(f"File exceeds maximum size of {self.config.max_file_size_mb}MB")

        # Upload to Azure
        container_client = self.client.get_container_client(self.container_name)
        blob_client = container_client.get_blob_client(blob_path)

        # Simple upload for now, could be optimized for large files
        blob_client.upload_blob(content, overwrite=True, content_settings={"content_type": mime_type})

        return StoredFile(
            stored_filename=stored_filename,
            relative_path=blob_path,
            absolute_path=blob_client.url,
            size_bytes=size,
            sha256_hash=sha256.hexdigest(),
            mime_type=mime_type,
        )

    async def get_path(self, relative_path: str) -> str:
        container_client = self.client.get_container_client(self.container_name)
        blob_client = container_client.get_blob_client(relative_path)
        return blob_client.url

    async def exists(self, relative_path: str) -> bool:
        container_client = self.client.get_container_client(self.container_name)
        blob_client = container_client.get_blob_client(relative_path)
        return blob_client.exists()

    async def delete(self, relative_path: str) -> bool:
        container_client = self.client.get_container_client(self.container_name)
        blob_client = container_client.get_blob_client(relative_path)
        if blob_client.exists():
            blob_client.delete_blob()
            return True
        return False

    def _sanitize_filename(self, filename: str) -> str:
        safe = re.sub(r"[^\w\-.]", "_", filename)
        if "." in safe:
            name, ext = safe.rsplit(".", 1)
            return f"{name[:50]}.{ext}"
        return safe[:50]


class LocalFileStorage(Storage):
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
        folder: str = "evidence",
    ) -> StoredFile:
        """Save a file and return storage metadata."""
        # Validate mime type
        if mime_type not in self.config.allowed_mime_types:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Generate unique filename
        file_uuid = str(uuid4())
        safe_filename = self._sanitize_filename(filename)
        stored_filename = f"{file_uuid}_{safe_filename}"

        # Build path: {folder}/YYYY/MM/job_id/
        now = datetime.now(UTC)
        relative_dir = Path(folder) / str(now.year) / f"{now.month:02d}" / job_id
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


def get_storage() -> Storage:
    """Get storage instance based on settings."""
    from veriqko.config import get_settings

    settings = get_settings()
    config = StorageConfig(
        base_path=settings.storage_base_path,
        max_file_size_mb=settings.storage_max_file_size_mb,
        azure_connection_string=settings.azure_storage_connection_string,
        azure_container_name=settings.azure_storage_container_name,
    )

    if settings.storage_backend == "azure":
        return AzureBlobStorage(config)

    return LocalFileStorage(config)
