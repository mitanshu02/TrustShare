"""
Password hashing, JWT, and one-time-password (OTP) helpers.

- Passwords and OTPs are both hashed with bcrypt before storage. Neither
  plaintext passwords nor raw OTP codes are ever stored or logged.
- JWT access tokens are signed with JWT_SECRET_KEY (HS256 by default).
  See docs/security-design.md.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings

settings = get_settings()


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store the plaintext."""
    password_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), password_hash.encode("utf-8")
    )


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {"sub": subject, "iat": now, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except InvalidTokenError:
        return None


# --- One-time passwords (forgot-password flow) ---

def generate_otp() -> str:
    """Generate a random 6-digit numeric OTP using a CSPRNG."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    """Hash an OTP for storage, same approach as password hashing."""
    return hash_password(otp)


def verify_otp(otp: str, otp_hash: str) -> bool:
    """Check a plaintext OTP against a stored bcrypt hash."""
    return verify_password(otp, otp_hash)