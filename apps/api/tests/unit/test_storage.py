import pytest
import os
from pathlib import Path
from io import BytesIO
from unittest.mock import MagicMock, patch

from veriqko.evidence.storage import LocalFileStorage, StorageConfig, StoredFile

@pytest.fixture
def storage_config(tmp_path):
    return StorageConfig(
        base_path=tmp_path,
        max_file_size_mb=1,
        allowed_mime_types=["image/jpeg", "application/pdf"]
    )

@pytest.fixture
def local_storage(storage_config):
    return LocalFileStorage(storage_config)

@pytest.mark.asyncio
async def test_local_storage_save_success(local_storage, tmp_path):
    content = b"fake image content"
    file = BytesIO(content)
    job_id = "job_123"
    filename = "test.jpg"
    mime_type = "image/jpeg"

    stored = await local_storage.save(file, job_id, filename, mime_type)

    assert isinstance(stored, StoredFile)
    assert stored.mime_type == mime_type
    assert stored.size_bytes == len(content)
    assert os.path.exists(stored.absolute_path)
    assert job_id in str(stored.relative_path)

@pytest.mark.asyncio
async def test_local_storage_invalid_mime_type(local_storage):
    file = BytesIO(b"content")
    with pytest.raises(ValueError, match="Unsupported file type"):
        await local_storage.save(file, "job_1", "test.exe", "application/x-msdownload")

@pytest.mark.asyncio
async def test_local_storage_size_limit(local_storage):
    # max_file_size_mb is 1, so 2MB should fail
    content = b"0" * (2 * 1024 * 1024)
    file = BytesIO(content)
    
    with pytest.raises(ValueError, match="File exceeds maximum size"):
        await local_storage.save(file, "job_1", "large.target", "image/jpeg")

@pytest.mark.asyncio
async def test_local_storage_delete(local_storage):
    content = b"content"
    file = BytesIO(content)
    stored = await local_storage.save(file, "job_1", "test.jpg", "image/jpeg")
    
    assert os.path.exists(stored.absolute_path)
    
    success = await local_storage.delete(stored.relative_path)
    assert success is True
    assert not os.path.exists(stored.absolute_path)
    # Check if it was moved to .deleted
    deleted_path = local_storage.base_path / ".deleted" / stored.relative_path
    assert os.path.exists(deleted_path)

def test_sanitize_filename(local_storage):
    assert local_storage._sanitize_filename("hello world!.jpg") == "hello_world_.jpg"
    assert local_storage._sanitize_filename("very/unsafe/path.pdf") == "very_unsafe_path.pdf"
    # Test length limit
    long_name = "a" * 100 + ".jpg"
    sanitized = local_storage._sanitize_filename(long_name)
    assert len(sanitized) <= 60 # 50 + .jpg
