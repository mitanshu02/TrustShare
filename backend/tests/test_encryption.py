import pytest
from cryptography.exceptions import InvalidTag

from app.core.encryption import decrypt_bytes, encrypt_bytes, generate_key


def test_encrypt_decrypt_round_trip():
    key = generate_key()
    plaintext = b"This is a secret TrustShare test file.\x00\x01binary bytes too"

    ciphertext = encrypt_bytes(plaintext, key)
    assert ciphertext != plaintext

    decrypted = decrypt_bytes(ciphertext, key)
    assert decrypted == plaintext


def test_decrypt_fails_with_wrong_key():
    key_a = generate_key()
    key_b = generate_key()
    ciphertext = encrypt_bytes(b"sensitive contents", key_a)

    with pytest.raises(InvalidTag):
        decrypt_bytes(ciphertext, key_b)


def test_decrypt_fails_if_ciphertext_is_tampered_with():
    """
    AES-GCM is authenticated encryption — flipping even one byte of the
    ciphertext must make decryption fail loudly (InvalidTag), not
    silently return corrupted plaintext. This is what makes key
    rotation / storage-layer corruption detectable rather than a quiet
    data-integrity bug.
    """
    key = generate_key()
    ciphertext = bytearray(encrypt_bytes(b"do not tamper with me", key))
    ciphertext[-1] ^= 0xFF  # flip the last byte

    with pytest.raises(InvalidTag):
        decrypt_bytes(bytes(ciphertext), key)


def test_each_file_gets_a_different_key():
    key_a = generate_key()
    key_b = generate_key()
    assert key_a != key_b
