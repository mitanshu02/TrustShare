import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.crud.monitoring import (
    get_security_analytics,
    get_unread_notification_count,
    get_user_notifications,
    get_user_security_status,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/api", tags=["monitoring"])


@router.get("/notifications")
def list_notifications(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifications = get_user_notifications(db, current_user.id, limit=limit, offset=offset)

    return [
        {
            "id": str(item.id),
            "notification_type": item.notification_type,
            "title": item.title,
            "message": item.message,
            "link_url": item.link_url,
            "read_at": item.read_at,
            "created_at": item.created_at,
        }
        for item in notifications
    ]


@router.get("/notifications/unread-count")
def unread_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"unread_count": get_unread_notification_count(db, current_user.id)}


@router.patch("/notifications/{notification_id}/read")
def read_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = mark_notification_read(db, notification_id, current_user.id)

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return {"message": "Notification marked as read"}


@router.patch("/notifications/read-all")
def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = mark_all_notifications_read(db, current_user.id)
    return {"message": f"{updated} notification(s) marked as read"}


@router.get("/admin/security-analytics")
def security_analytics(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_security_analytics(db)


@router.get("/security-status")
def security_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Non-admin equivalent of the admin security-analytics endpoint,
    scoped to the caller's own account: recent failed logins against
    their account and whether that crossed the suspicious-activity
    threshold in the last 15 minutes.
    """
    return get_user_security_status(db, current_user.id)
