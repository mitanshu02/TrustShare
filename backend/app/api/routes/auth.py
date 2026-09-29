import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.core.events import EventType, NotificationType
from app.crud.monitoring import (
    create_audit_event,
    create_notification,
    detect_repeated_failed_logins,
)
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

_FORGOT_PASSWORD_MESSAGE = (
    "If an account exists for that email, a verification code has been sent."
)


def get_client_ip(request: Request) -> str | None:
    """Return the client IP when it is available."""
    return request.client.host if request.client else None


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    existing = get_user_by_email(db, user_in.email)

    if existing is not None:
        create_audit_event(
            db=db,
            event_type=EventType.REGISTRATION_FAILED,
            severity="warning",
            ip_address=get_client_ip(request),
            event_metadata={"reason": "email_already_registered"},
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = create_user(db, user_in)

    create_audit_event(
        db=db,
        event_type=EventType.USER_REGISTERED,
        actor_user_id=user.id,
        entity_type="user",
        entity_id=str(user.id),
        severity="info",
        ip_address=get_client_ip(request),
    )

    return user


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    user = get_user_by_email(db, credentials.email)
    ip_address = get_client_ip(request)

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )

    if user is None or not verify_password(credentials.password, user.password_hash):
        create_audit_event(
            db=db,
            event_type=EventType.LOGIN_FAILED,
            severity="warning",
            ip_address=ip_address,
            event_metadata={"email_attempted": credentials.email},
        )

        detect_repeated_failed_logins(
            db=db,
            ip_address=ip_address,
            email=credentials.email,
        )

        raise invalid_credentials

    if user.account_status != "active":
        create_audit_event(
            db=db,
            event_type=EventType.LOGIN_BLOCKED,
            actor_user_id=user.id,
            entity_type="user",
            entity_id=str(user.id),
            severity="warning",
            ip_address=ip_address,
            event_metadata={"account_status": user.account_status},
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    create_audit_event(
        db=db,
        event_type=EventType.LOGIN_SUCCESS,
        actor_user_id=user.id,
        entity_type="user",
        entity_id=str(user.id),
        severity="info",
        ip_address=ip_address,
    )

    create_notification(
        db=db,
        user_id=user.id,
        notification_type=NotificationType.NEW_LOGIN,
        title="New login to your account",
        message=f"A new login was recorded from IP {ip_address or 'unknown'}.",
        link_url="/dashboard/activity",
    )

    token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role},
    )

    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Protected endpoint used to verify JWT authentication."""
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    user = get_user_by_email(db, payload.email)

    if user is not None:
        raw_otp = create_otp(db, user.id)

        create_audit_event(
            db=db,
            event_type=EventType.PASSWORD_RESET_REQUESTED,
            actor_user_id=user.id,
            entity_type="user",
            entity_id=str(user.id),
            severity="info",
            ip_address=get_client_ip(request),
        )

        # Development only: use console output until an email provider is added.
        # Never return the OTP in the API response.
        if get_settings().ENVIRONMENT == "development":
            logger.warning(
                "DEV ONLY password-reset OTP for %s: %s",
                user.email,
                raw_otp,
            )

    # Generic response prevents account-enumeration attacks.
    return MessageResponse(message=_FORGOT_PASSWORD_MESSAGE)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    user = get_user_by_email(db, payload.email)

    invalid_otp_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification code",
    )

    if user is None:
        create_audit_event(
            db=db,
            event_type=EventType.PASSWORD_RESET_FAILED,
            severity="warning",
            ip_address=get_client_ip(request),
            event_metadata={"reason": "invalid_email_or_otp"},
        )
        raise invalid_otp_error

    if not verify_and_consume_otp(db, user.id, payload.otp):
        create_audit_event(
            db=db,
            event_type=EventType.PASSWORD_RESET_FAILED,
            actor_user_id=user.id,
            entity_type="user",
            entity_id=str(user.id),
            severity="warning",
            ip_address=get_client_ip(request),
            event_metadata={"reason": "invalid_or_expired_otp"},
        )
        raise invalid_otp_error

    update_password(db, user, payload.new_password)

    create_audit_event(
        db=db,
        event_type=EventType.PASSWORD_RESET_SUCCESS,
        actor_user_id=user.id,
        entity_type="user",
        entity_id=str(user.id),
        severity="info",
        ip_address=get_client_ip(request),
    )

    return MessageResponse(
        message="Your password has been reset. You can now log in."
    )