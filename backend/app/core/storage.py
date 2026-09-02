"""
Local-disk storage for encrypted file blobs.

Stand-in for AWS S3 / Azure Blob Storage (see docs/architecture.md) until
Milestone 2 wires up real cloud storage. Only ever reads/writes
ciphertext — plaintext is never persisted here.
"""

import os
import uuid

from app.core.config import get_settings

settings = get_settings()


def _ensure_storage_dir() -> str:
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    return settings.STORAGE_DIR


def save_encrypted_blob(encrypted_bytes: bytes) -> str:
    """
    Write an encrypted blob to local storage and return its storage key
    (a path-safe identifier, analogous to an S3 object key).
    """
    storage_dir = _ensure_storage_dir()
    storage_key = f"{uuid.uuid4()}.enc"
    path = os.path.join(storage_dir, storage_key)
    with open(path, "wb") as f:
        f.write(encrypted_bytes)
    return storage_key


def read_encrypted_blob(storage_key: str) -> bytes:
    path = os.path.join(settings.STORAGE_DIR, storage_key)
    with open(path, "rb") as f:
        return f.read()


def delete_encrypted_blob(storage_key: str) -> None:
    path = os.path.join(settings.STORAGE_DIR, storage_key)
    if os.path.exists(path):
        os.remove(path)