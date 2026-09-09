import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.security import verify_password
from app.crud.admin import (
    change_user_role,
    get_platform_stats,
    get_user_by_id,
    list_all_files,
    list_all_users,
    list_role_audit,
    update_user_status,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminFileOut,
    AdminUserOut,
    PlatformStatsOut,
    RoleChangeAuditOut,
    RoleChangeRequest,
    UserStatusUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserOut])
def list_users_endpoint(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminUserOut]:
    return list_all_users(db)


@router.patch("/users/{user_id}/status", response_model=AdminUserOut)
def update_user_status_endpoint(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserOut:
    target = get_user_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot change their own account status",
        )
    return update_user_status(db, target, payload.account_status)


@router.get("/files", response_model=list[AdminFileOut])
def list_files_endpoint(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminFileOut]:
    return list_all_files(db)


@router.get("/stats", response_model=PlatformStatsOut)
def platform_stats_endpoint(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PlatformStatsOut:
    return PlatformStatsOut(**get_platform_stats(db))



@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
def change_user_role_endpoint(
    user_id: uuid.UUID,
    payload: RoleChangeRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminUserOut:
    # Step-up auth: re-verify the acting admin's current password before
    # allowing a role change, even though they're already authenticated.
    if not verify_password(payload.current_password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    target = get_user_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot change their own role",
        )
    if target.role == payload.new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User already has role '{payload.new_role}'",
        )

    return change_user_role(db, target, payload.new_role, admin)


@router.get("/audit/roles", response_model=list[RoleChangeAuditOut])
def role_audit_endpoint(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[RoleChangeAuditOut]:
    return list_role_audit(db)