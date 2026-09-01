import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.crud.password_reset import create_otp, verify_and_consume_otp
from app.crud.user import create_user, get_user_by_email, update_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

logger = logging.getLogger("trustshare.auth")

# Generic response used for forgot-password regardless of whether the email
# is registered, so responses never reveal which emails have accounts.
_FORGOT_PASSWORD_MESSAGE = (
    "If an account exists for that email, a verification code has been sent."
)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = get_user_by_email(db, user_in.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    return create_user(db, user_in)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = get_user_by_email(db, credentials.email)

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise invalid_credentials

    if user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Protected endpoint used to verify JWT auth end-to-end."""
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    
   # Request a password-reset OTP.

    user = get_user_by_email(db, payload.email)

    if user is not None:
        raw_otp = create_otp(db, user.id)

        # TODO: replace this with a real email send (see docs/architecture.md
        # — SendGrid is the planned provider). Until email is wired up, the
        # OTP is printed to the backend console for local testing only. It
        # must never be returned in the HTTP response.
        logger.info(
            "Password reset OTP for %s: %s (expires in 10 minutes)",
            user.email,
            raw_otp,
        )
        print(f"[DEV ONLY] Password reset OTP for {user.email}: {raw_otp}")

    return MessageResponse(message=_FORGOT_PASSWORD_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    user = get_user_by_email(db, payload.email)

    invalid_otp_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification code",
    )

    # Same generic error whether the email doesn't exist or the OTP is
    # wrong/expired/locked-out, so this endpoint doesn't reveal which
    # emails are registered either.
    if user is None:
        raise invalid_otp_error

    if not verify_and_consume_otp(db, user.id, payload.otp):
        raise invalid_otp_error

    update_password(db, user, payload.new_password)

    return MessageResponse(message="Your password has been reset. You can now log in.")