import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.file_permission import FilePermission
from app.models.role_change_audit import RoleChangeAudit
from app.models.user import User

def list_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def update_user_status(db: Session, user: User, account_status: str) -> User:
    user.account_status = account_status
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_all_files(db: Session) -> list[dict]:
    rows = (
        db.query(File, User)
        .join(User, User.id == File.owner_id)
        .filter(File.deleted_at.is_(None))
        .order_by(File.created_at.desc())
        .all()
    )
    return [
        {
            "id": f.id,
            "original_name": f.original_name,
            "owner_email": owner.email,
            "size_bytes": f.size_bytes,
            "created_at": f.created_at,
        }
        for f, owner in rows
    ]


def get_platform_stats(db: Session) -> dict:
    total_users = db.query(func.count(User.id)).scalar() or 0

    total_files, total_bytes = (
        db.query(func.count(File.id), func.coalesce(func.sum(File.size_bytes), 0))
        .filter(File.deleted_at.is_(None))
        .one()
    )

    total_shares = db.query(func.count(FilePermission.id)).scalar() or 0

    return {
        "total_users": total_users,
        "total_files": total_files,
        "total_storage_bytes": total_bytes,
        "total_shares": total_shares,
    }


def change_user_role(
    db: Session, target: User, new_role: str, changed_by: User
) -> User:
    """
    Applies a role change and writes an immutable audit record in the
    same transaction. Password verification (step-up auth) happens in
    the route layer before this is called.
    """
    old_role = target.role
    target.role = new_role
    db.add(target)

    db.add(
        RoleChangeAudit(
            changed_by=changed_by.id,
            target_user_id=target.id,
            old_role=old_role,
            new_role=new_role,
        )
    )
    db.commit()
    db.refresh(target)
    return target


def list_role_audit(db: Session, limit: int = 100) -> list[dict]:
    rows = (
        db.query(RoleChangeAudit)
        .order_by(RoleChangeAudit.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "changed_by_email": r.changer.email,
            "target_user_email": r.target_user.email,
            "old_role": r.old_role,
            "new_role": r.new_role,
            "created_at": r.created_at,
        }
        for r in rows
    ]