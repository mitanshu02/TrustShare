import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.events import EventType, NotificationType
from app.core.security import generate_share_token, hash_share_token
from app.crud.monitoring import create_audit_event, create_notification
from app.models.download import Download
from app.models.file import File
from app.models.share_link import ShareLink
from app.schemas.share_link import ShareLinkCreate


def create_share_link(
    db: Session, file: File, payload: ShareLinkCreate, created_by: uuid.UUID
) -> tuple[ShareLink, str]:
    """
    Creates a share link and returns (record, raw_token). The raw token
    is only ever available here, at creation time — only its hash is
    persisted.
    """
    raw_token = generate_share_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours)

    link = ShareLink(
        file_id=file.id,
        created_by=created_by,
        token_hash=hash_share_token(raw_token),
        access_level=payload.access_level,
        expires_at=expires_at,
        max_downloads=payload.max_downloads,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    create_audit_event(
        db=db,
        event_type=EventType.SHARE_LINK_CREATED,
        actor_user_id=created_by,
        entity_type="file",
        entity_id=str(file.id),
        severity="info",
        event_metadata={
            "link_id": str(link.id),
            "access_level": link.access_level,
            "expires_at": link.expires_at.isoformat(),
            "max_downloads": link.max_downloads,
        },
    )

    return link, raw_token


def list_links_for_file(db: Session, file_id: uuid.UUID) -> list[ShareLink]:
    return (
        db.query(ShareLink)
        .filter(ShareLink.file_id == file_id)
        .order_by(ShareLink.created_at.desc())
        .all()
    )


def get_link_by_id(db: Session, link_id: uuid.UUID) -> ShareLink | None:
    return db.query(ShareLink).filter(ShareLink.id == link_id).first()


def revoke_link(db: Session, link: ShareLink, revoked_by: uuid.UUID) -> ShareLink:
    link.is_active = False
    link.revoked_at = datetime.now(timezone.utc)
    db.add(link)
    db.commit()
    db.refresh(link)

    create_audit_event(
        db=db,
        event_type=EventType.SHARE_LINK_REVOKED,
        actor_user_id=revoked_by,
        entity_type="file",
        entity_id=str(link.file_id),
        severity="info",
        event_metadata={"link_id": str(link.id)},
    )

    return link


def get_valid_link_by_token(db: Session, token: str) -> ShareLink | None:
    """
    Looks up a share link by its raw token (hashing it first for the
    lookup) and returns it only if it's currently usable: active, not
    expired, and under its download limit if one is set. The file itself
    must also not be soft-deleted.
    """
    token_hash = hash_share_token(token)
    link = (
        db.query(ShareLink)
        .join(File, File.id == ShareLink.file_id)
        .filter(
            ShareLink.token_hash == token_hash,
            ShareLink.is_active.is_(True),
            File.deleted_at.is_(None),
        )
        .first()
    )
    if link is None:
        return None

    now = datetime.now(timezone.utc)
    link_expires_at = link.expires_at
    if link_expires_at.tzinfo is None:
        # Some backends (e.g. SQLite, used in local testing) don't
        # round-trip timezone info on DateTime columns. Postgres does,
        # so this only matters for tests, but handling it here keeps
        # the comparison correct regardless of backend.
        link_expires_at = link_expires_at.replace(tzinfo=timezone.utc)

    if link_expires_at < now:
        return None
    if link.max_downloads is not None and link.download_count >= link.max_downloads:
        return None

    return link


def record_link_download(db: Session, link: ShareLink) -> None:
    link.download_count += 1
    db.add(link)
    db.add(Download(file_id=link.file_id, share_link_id=link.id, user_id=None))
    db.commit()

    create_audit_event(
        db=db,
        event_type=EventType.PUBLIC_LINK_DOWNLOADED,
        entity_type="file",
        entity_id=str(link.file_id),
        severity="info",
        event_metadata={"link_id": str(link.id)},
    )

    file = link.file
    create_notification(
        db=db,
        user_id=file.owner_id,
        notification_type=NotificationType.FILE_DOWNLOADED,
        title="Your file was downloaded via a share link",
        message=f"'{file.original_name}' was downloaded through a public share link.",
        link_url="/dashboard/activity",
    )