from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.events import EventType, NotificationType, SEVERITY_HIGH
from app.models.audit_event import AuditEvent
from app.models.file import File
from app.models.notification import Notification
from app.models.share_link import ShareLink
from app.models.user import User

FAILED_LOGIN_WINDOW_MINUTES = 15
FAILED_LOGIN_THRESHOLD = 5


def create_audit_event(
    db: Session,
    event_type: str,
    actor_user_id: uuid.UUID | None = None,
    target_user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    severity: str = "info",
    ip_address: str | None = None,
    event_metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_type=event_type,
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=severity,
        ip_address=ip_address,
        event_metadata=event_metadata or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_notification(
    db: Session,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    message: str,
    link_url: str | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link_url=link_url,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def notify_admins(
    db: Session,
    notification_type: str,
    title: str,
    message: str,
    link_url: str | None = None,
    exclude_user_id: uuid.UUID | None = None,
) -> int:
    """
    Fans a notification out to every admin account. Returns the number
    of admins notified. Used for platform-wide security events, where
    there is no single "owner" to tell.
    """
    admin_ids = (
        db.query(User.id)
        .filter(User.role == "admin", User.account_status == "active")
        .all()
    )
    count = 0
    for (admin_id,) in admin_ids:
        if exclude_user_id is not None and admin_id == exclude_user_id:
            continue
        create_notification(
            db=db,
            user_id=admin_id,
            notification_type=notification_type,
            title=title,
            message=message,
            link_url=link_url,
        )
        count += 1
    return count


def detect_repeated_failed_logins(
    db: Session,
    ip_address: str | None,
    email: str,
) -> bool:
    """
    Flags 5+ failed logins from the same IP within a 15-minute window.

    Deduplicated: once an alert has fired for an IP, it will not fire
    again until that IP's failure streak ages out of the window —
    otherwise attempt #6, #7, #8... would each spawn their own
    "suspicious activity" event and admin notification.
    """
    if not ip_address:
        return False

    since = datetime.now(timezone.utc) - timedelta(minutes=FAILED_LOGIN_WINDOW_MINUTES)

    last_alert = (
        db.query(AuditEvent.created_at)
        .filter(
            AuditEvent.event_type == EventType.SUSPICIOUS_LOGIN_ACTIVITY,
            AuditEvent.ip_address == ip_address,
            AuditEvent.created_at >= since,
        )
        .order_by(AuditEvent.created_at.desc())
        .first()
    )
    if last_alert is not None:
        # Already alerted for this IP within the current window.
        return False

    count = (
        db.query(func.count(AuditEvent.id))
        .filter(
            AuditEvent.event_type == EventType.LOGIN_FAILED,
            AuditEvent.ip_address == ip_address,
            AuditEvent.created_at >= since,
        )
        .scalar()
    )

    if count < FAILED_LOGIN_THRESHOLD:
        return False

    targeted_user = db.query(User).filter(User.email == email).first()

    create_audit_event(
        db=db,
        event_type=EventType.SUSPICIOUS_LOGIN_ACTIVITY,
        target_user_id=targeted_user.id if targeted_user else None,
        severity=SEVERITY_HIGH,
        ip_address=ip_address,
        event_metadata={
            "reason": f"{FAILED_LOGIN_THRESHOLD}+ failed login attempts within "
            f"{FAILED_LOGIN_WINDOW_MINUTES} minutes",
            "email_attempted": email,
            "attempt_count": count,
        },
    )

    notify_admins(
        db=db,
        notification_type=NotificationType.SECURITY_ALERT,
        title="Suspicious login activity detected",
        message=(
            f"{count} failed login attempts from IP {ip_address} in the last "
            f"{FAILED_LOGIN_WINDOW_MINUTES} minutes (last attempt used email "
            f"'{email}')."
        ),
        link_url="/dashboard/admin",
    )

    # Also tell the account being targeted, if the attempted email belongs
    # to a real user — they're the one best placed to know someone is
    # trying to break into their account right now.
    if targeted_user is not None:
        create_notification(
            db=db,
            user_id=targeted_user.id,
            notification_type=NotificationType.SECURITY_ALERT,
            title="Multiple failed login attempts on your account",
            message=(
                f"{count} failed login attempts were made on your account in the "
                f"last {FAILED_LOGIN_WINDOW_MINUTES} minutes from IP {ip_address}. "
                "If this wasn't you, consider changing your password."
            ),
            link_url="/dashboard/activity",
        )

    return True


def get_user_notifications(
    db: Session, user_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_unread_notification_count(db: Session, user_id: uuid.UUID) -> int:
    return (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .scalar()
        or 0
    )


def mark_notification_read(
    db: Session, notification_id: uuid.UUID, user_id: uuid.UUID
) -> Notification | None:
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .first()
    )

    if notification is None:
        return None

    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)

    return notification


def mark_all_notifications_read(db: Session, user_id: uuid.UUID) -> int:
    now = datetime.now(timezone.utc)
    result = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .update({Notification.read_at: now}, synchronize_session=False)
    )
    db.commit()
    return result


def get_security_analytics(db: Session) -> dict:
    last_24_hours = datetime.now(timezone.utc) - timedelta(hours=24)

    failed_logins = (
        db.query(func.count(AuditEvent.id))
        .filter(
            AuditEvent.event_type == EventType.LOGIN_FAILED,
            AuditEvent.created_at >= last_24_hours,
        )
        .scalar()
        or 0
    )

    suspicious_events = (
        db.query(func.count(AuditEvent.id))
        .filter(
            AuditEvent.severity.in_(["high", "critical"]),
            AuditEvent.created_at >= last_24_hours,
        )
        .scalar()
        or 0
    )

    downloads = (
        db.query(func.count(AuditEvent.id))
        .filter(
            AuditEvent.event_type.in_(
                [EventType.FILE_DOWNLOADED, EventType.PUBLIC_LINK_DOWNLOADED]
            ),
            AuditEvent.created_at >= last_24_hours,
        )
        .scalar()
        or 0
    )

    # Breakdown by event_type, for a richer admin dashboard than three
    # flat counters.
    by_type_rows = (
        db.query(AuditEvent.event_type, func.count(AuditEvent.id))
        .filter(AuditEvent.created_at >= last_24_hours)
        .group_by(AuditEvent.event_type)
        .all()
    )

    recent_high_severity = (
        db.query(AuditEvent)
        .filter(AuditEvent.severity.in_(["high", "critical"]))
        .order_by(AuditEvent.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "failed_logins_24h": failed_logins,
        "suspicious_events_24h": suspicious_events,
        "downloads_24h": downloads,
        "events_by_type_24h": {event_type: count for event_type, count in by_type_rows},
        "recent_high_severity_events": [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "severity": event.severity,
                "ip_address": event.ip_address,
                "created_at": event.created_at,
                "event_metadata": event.event_metadata,
            }
            for event in recent_high_severity
        ],
    }


def get_file_activity_report(db: Session, file_id: uuid.UUID) -> dict:
    """
    Full audit trail for a single file: uploads, downloads, shares,
    permission changes, key rotations, share-link activity — anything
    logged with entity_type='file' and this file's id. Events are
    ordered oldest first, so the list reads like a timeline, and a
    small summary (total events, downloads, temporary links created)
    is included so the report doesn't require reading the whole list
    to answer the obvious first questions.
    """
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_type == "file", AuditEvent.entity_id == str(file_id))
        .order_by(AuditEvent.created_at.asc())
        .all()
    )

    actor_ids = {e.actor_user_id for e in events if e.actor_user_id is not None}
    actors = (
        {u.id: u.email for u in db.query(User).filter(User.id.in_(actor_ids)).all()}
        if actor_ids
        else {}
    )

    download_events = {EventType.FILE_DOWNLOADED, EventType.PUBLIC_LINK_DOWNLOADED}
    downloads = sum(1 for e in events if e.event_type in download_events)
    temporary_links = sum(1 for e in events if e.event_type == EventType.SHARE_LINK_CREATED)

    return {
        "total_events": len(events),
        "downloads": downloads,
        "temporary_links": temporary_links,
        "events": [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "severity": event.severity,
                "actor_email": actors.get(event.actor_user_id),
                "ip_address": event.ip_address,
                "created_at": event.created_at,
                "event_metadata": event.event_metadata,
            }
            for event in events
        ],
    }


def get_storage_analytics(db: Session, owner_id: uuid.UUID) -> dict:
    """
    Storage usage for one user's own files, broken down by a coarse
    "file type" bucket derived from content_type (mirrors slide 8:
    "Storage Statistics (by file type)").
    """
    rows = (
        db.query(File.content_type, File.size_bytes)
        .filter(File.owner_id == owner_id, File.deleted_at.is_(None))
        .all()
    )

    total_files = len(rows)
    total_bytes = sum(size for _, size in rows)

    def _bucket(content_type: str) -> str:
        if content_type.startswith("image/"):
            return "images"
        if content_type == "application/pdf":
            return "pdf"
        if content_type.startswith("video/"):
            return "video"
        if content_type.startswith("text/") or content_type in (
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            return "documents"
        return "other"

    by_type: dict[str, dict[str, int]] = {}
    for content_type, size in rows:
        bucket = _bucket(content_type or "")
        entry = by_type.setdefault(bucket, {"count": 0, "size_bytes": 0})
        entry["count"] += 1
        entry["size_bytes"] += size

    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "by_type": by_type,
    }


EXPIRY_REMINDER_WINDOW_HOURS = 24


def check_expiring_share_links(db: Session) -> int:
    """
    Finds active, non-expired share links that will expire within the
    next EXPIRY_REMINDER_WINDOW_HOURS and sends the owner one reminder
    notification each.

    Dedup strategy: rather than a new "reminder_sent" column (and the
    migration that would require), a link's reminder marker is a
    Notification row whose link_url encodes the share-link's id
    (".../links#<link_id>"). Before creating a reminder we check for
    one already existing, so re-running this job is a no-op for links
    already warned about.

    Intended to be called periodically (see app.core.scheduler), but is
    plain, synchronous, and side-effect-safe to call from anywhere —
    including manually, or from a request handler, if a project prefers
    not to run a background scheduler at all.
    """
    now = datetime.now(timezone.utc)
    soon = now + timedelta(hours=EXPIRY_REMINDER_WINDOW_HOURS)

    expiring_links = (
        db.query(ShareLink)
        .filter(
            ShareLink.is_active.is_(True),
            ShareLink.expires_at > now,
            ShareLink.expires_at <= soon,
        )
        .all()
    )

    sent = 0
    for link in expiring_links:
        marker = f"/dashboard/shared#link-{link.id}"

        already_sent = (
            db.query(Notification.id)
            .filter(
                Notification.notification_type == NotificationType.LINK_EXPIRING_SOON,
                Notification.link_url == marker,
            )
            .first()
        )
        if already_sent is not None:
            continue

        file = link.file
        hours_left = max(1, int((link.expires_at - now).total_seconds() // 3600))

        create_notification(
            db=db,
            user_id=file.owner_id,
            notification_type=NotificationType.LINK_EXPIRING_SOON,
            title="A share link is expiring soon",
            message=(
                f"Your share link for '{file.original_name}' expires in "
                f"about {hours_left} hour(s)."
            ),
            link_url=marker,
        )
        sent += 1

    return sent


def get_audit_log_for_user(
    db: Session,
    user_id: uuid.UUID,
    event_type: str | None = None,
    event_types: list[str] | None = None,
    q: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    A searchable, filterable audit trail scoped to one user: things
    they did (actor), things done to them (target), and activity on
    files they own (so they see who downloaded/shared/revoked access
    to their own files, not only their own actions).

    Filters are applied at the database level (not after fetching a
    page), so `q`/date-range/event-type combined with limit/offset
    paginate correctly instead of silently under-returning matches
    that fall outside the current page.
    """
    owned_file_ids = [
        str(fid) for (fid,) in db.query(File.id).filter(File.owner_id == user_id).all()
    ]

    scope = or_(
        AuditEvent.actor_user_id == user_id,
        AuditEvent.target_user_id == user_id,
    )
    if owned_file_ids:
        scope = or_(
            scope,
            (AuditEvent.entity_type == "file") & AuditEvent.entity_id.in_(owned_file_ids),
        )

    query = db.query(AuditEvent).filter(scope)

    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if event_types:
        query = query.filter(AuditEvent.event_type.in_(event_types))
    if date_from:
        query = query.filter(AuditEvent.created_at >= date_from)
    if date_to:
        query = query.filter(AuditEvent.created_at <= date_to)

    if q:
        matching_file_ids = [
            str(fid)
            for (fid,) in db.query(File.id)
            .filter(File.id.in_([uuid.UUID(fid) for fid in owned_file_ids]) if owned_file_ids else False)
            .filter(File.original_name.ilike(f"%{q}%"))
            .all()
        ] if owned_file_ids else []

        text_filter = AuditEvent.event_type.ilike(f"%{q}%")
        if matching_file_ids:
            text_filter = or_(
                text_filter,
                (AuditEvent.entity_type == "file") & AuditEvent.entity_id.in_(matching_file_ids),
            )
        query = query.filter(text_filter)

    total = query.count()

    events = (
        query.order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    actor_ids = {e.actor_user_id for e in events if e.actor_user_id is not None}
    actors = (
        {u.id: u.email for u in db.query(User).filter(User.id.in_(actor_ids)).all()}
        if actor_ids
        else {}
    )

    file_ids_needed: set[uuid.UUID] = set()
    for e in events:
        if e.entity_type == "file" and e.entity_id:
            try:
                file_ids_needed.add(uuid.UUID(e.entity_id))
            except ValueError:
                pass
    files = (
        {f.id: f.original_name for f in db.query(File).filter(File.id.in_(file_ids_needed)).all()}
        if file_ids_needed
        else {}
    )

    rows = []
    for e in events:
        file_name = None
        if e.entity_type == "file" and e.entity_id:
            try:
                file_name = files.get(uuid.UUID(e.entity_id))
            except ValueError:
                file_name = None

        rows.append(
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "severity": e.severity,
                "actor_email": actors.get(e.actor_user_id),
                "file_name": file_name,
                "ip_address": e.ip_address,
                "created_at": e.created_at,
                "event_metadata": e.event_metadata,
            }
        )

    return {"total": total, "limit": limit, "offset": offset, "events": rows}


def get_user_security_status(db: Session, user_id: uuid.UUID) -> dict:
    """
    A per-user, non-admin view of the same suspicious-login signal the
    admin dashboard sees platform-wide — scoped to attempts made
    against this specific account, using the last 15-minute window.
    """
    since = datetime.now(timezone.utc) - timedelta(minutes=FAILED_LOGIN_WINDOW_MINUTES)

    failed_logins = (
        db.query(func.count(AuditEvent.id))
        .filter(
            AuditEvent.event_type == EventType.LOGIN_FAILED,
            AuditEvent.target_user_id == user_id,
            AuditEvent.created_at >= since,
        )
        .scalar()
        or 0
    )

    latest_alert = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.event_type == EventType.SUSPICIOUS_LOGIN_ACTIVITY,
            AuditEvent.target_user_id == user_id,
            AuditEvent.created_at >= since,
        )
        .order_by(AuditEvent.created_at.desc())
        .first()
    )

    return {
        "failed_logins_15m": failed_logins,
        "suspicious_activity": latest_alert is not None,
        "reason": latest_alert.event_metadata.get("reason") if latest_alert else None,
    }
