import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import generate_otp, hash_otp, verify_otp
from app.models.password_reset_otp import PasswordResetOTP

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


def create_otp(db: Session, user_id: uuid.UUID) -> str:
    """
    Generate a new OTP for a user, store only its hash, and return the raw
    OTP so the caller can deliver it (email, or console in local dev).

    Any previous unused OTPs for this user are invalidated first, so only
    one OTP is ever active at a time.
    """
    now = datetime.now(timezone.utc)

    db.query(PasswordResetOTP).filter(
        PasswordResetOTP.user_id == user_id,
        PasswordResetOTP.used_at.is_(None),
    ).update({"used_at": now})
    db.commit()

    raw_otp = generate_otp()
    expires_at = now + timedelta(minutes=OTP_TTL_MINUTES)

    record = PasswordResetOTP(
        user_id=user_id,
        otp_hash=hash_otp(raw_otp),
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()

    return raw_otp


def verify_and_consume_otp(db: Session, user_id: uuid.UUID, submitted_otp: str) -> bool:
  
    now = datetime.now(timezone.utc)

    record = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.user_id == user_id,
            PasswordResetOTP.used_at.is_(None),
            PasswordResetOTP.expires_at > now,
            PasswordResetOTP.attempts < OTP_MAX_ATTEMPTS,
        )
        .order_by(PasswordResetOTP.created_at.desc())
        .first()
    )

    if record is None:
        return False

    if not verify_otp(submitted_otp, record.otp_hash):
        record.attempts += 1
        db.commit()
        return False

    record.used_at = now
    db.commit()
    return True