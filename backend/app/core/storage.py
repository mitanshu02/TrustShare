"""
Object storage backed by Backblaze B2 (S3-compatible API).

Replaces the earlier local-disk stand-in. Only ever reads/writes
ciphertext — plaintext is never persisted here. Function signatures are
unchanged from the local-disk version, so nothing calling this module
(crud/file.py, share link downloads, etc.) needed to change.
"""

import uuid

import boto3
from botocore.client import Config

from app.core.config import get_settings

settings = get_settings()

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.B2_ENDPOINT_URL,
            aws_access_key_id=settings.B2_KEY_ID,
            aws_secret_access_key=settings.B2_APPLICATION_KEY,
            config=Config(signature_version="s3v4"),
        )
    return _client


def save_encrypted_blob(encrypted_bytes: bytes) -> str:
    """
    Upload an encrypted blob to B2 and return its storage key (the
    object's key within the bucket).
    """
    storage_key = f"{uuid.uuid4()}.enc"
    _get_client().put_object(
        Bucket=settings.B2_BUCKET_NAME,
        Key=storage_key,
        Body=encrypted_bytes,
    )
    return storage_key


def read_encrypted_blob(storage_key: str) -> bytes:
    response = _get_client().get_object(
        Bucket=settings.B2_BUCKET_NAME, Key=storage_key
    )
    return response["Body"].read()


def delete_encrypted_blob(storage_key: str) -> None:
    _get_client().delete_object(Bucket=settings.B2_BUCKET_NAME, Key=storage_key)