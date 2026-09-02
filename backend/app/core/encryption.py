"""
AES-256-GCM file encryption/decryption.

Matches docs/security-design.md: AES-256-GCM (authenticated encryption,
not an unauthenticated mode), a unique key per file, and no plaintext
ever written to persistent disk on decrypt — decryption happens in
memory and the result is streamed straight to the response.
"""

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE_BYTES = 12  # standard, recommended nonce size for AES-GCM


def generate_key() -> bytes:
    """Generate a fresh random 256-bit (32-byte) AES key."""
    return AESGCM.generate_key(bit_length=256)


def encode_key(key: bytes) -> str:
    return base64.b64encode(key).decode("utf-8")


def decode_key(encoded_key: str) -> bytes:
    return base64.b64decode(encoded_key)


def encrypt_bytes(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt plaintext with AES-256-GCM. Returns nonce || ciphertext, so
    the nonce travels with the ciphertext (it is not secret, only unique
    per encryption) and doesn't need separate storage/bookkeeping.
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE_BYTES)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return nonce + ciphertext


def decrypt_bytes(blob: bytes, key: bytes) -> bytes:
    """Reverse of encrypt_bytes: split off the nonce, then decrypt."""
    aesgcm = AESGCM(key)
    nonce, ciphertext = blob[:NONCE_SIZE_BYTES], blob[NONCE_SIZE_BYTES:]
    return aesgcm.decrypt(nonce, ciphertext, associated_data=None)