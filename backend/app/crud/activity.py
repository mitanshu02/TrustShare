import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.download import Download
from app.models.file import File
from app.models.file_permission import FilePermission
from app.models.user import User


def get_activity_feed(db: Session, user_id: uuid.UUID, limit: int = 50) -> list[dict]:
    events: list[dict] = []

    # 1. Files I uploaded
    my_files = db.query(File).filter(File.owner_id == user_id).all()
    for f in my_files:
        events.append(
            {
                "type": "upload",
                "file_name": f.original_name,
                "counterpart_email": None,
                "access_level": None,
                "timestamp": f.created_at,
            }
        )

    my_file_ids = [f.id for f in my_files]

    # 2. Downloads of my files by other people
    if my_file_ids:
        downloads_of_mine = (
            db.query(Download, User, File)
            .join(File, File.id == Download.file_id)
            .outerjoin(User, User.id == Download.user_id)
            .filter(Download.file_id.in_(my_file_ids), Download.user_id != user_id)
            .all()
        )
        for download, downloader, f in downloads_of_mine:
            events.append(
                {
                    "type": "download",
                    "file_name": f.original_name,
                    "counterpart_email": downloader.email if downloader else "someone via link",
                    "access_level": None,
                    "timestamp": download.downloaded_at,
                }
            )

    # 3. Files I downloaded (that I don't own)
    my_downloads = (
        db.query(Download, File)
        .join(File, File.id == Download.file_id)
        .filter(Download.user_id == user_id, File.owner_id != user_id)
        .all()
    )
    for download, f in my_downloads:
        events.append(
            {
                "type": "download",
                "file_name": f.original_name,
                "counterpart_email": "you",
                "access_level": None,
                "timestamp": download.downloaded_at,
            }
        )

    # 4. Shares I created (granted to others)
    shares_out = (
        db.query(FilePermission, User, File)
        .join(User, User.id == FilePermission.user_id)
        .join(File, File.id == FilePermission.file_id)
        .filter(FilePermission.granted_by == user_id)
        .all()
    )
    for permission, recipient, f in shares_out:
        events.append(
            {
                "type": "share_out",
                "file_name": f.original_name,
                "counterpart_email": recipient.email,
                "access_level": permission.access_level,
                "timestamp": permission.created_at,
            }
        )

    # 5. Shares granted to me
    shares_in = (
        db.query(FilePermission, User, File)
        .join(User, User.id == FilePermission.granted_by)
        .join(File, File.id == FilePermission.file_id)
        .filter(FilePermission.user_id == user_id)
        .all()
    )
    for permission, granter, f in shares_in:
        events.append(
            {
                "type": "share_in",
                "file_name": f.original_name,
                "counterpart_email": granter.email,
                "access_level": permission.access_level,
                "timestamp": permission.created_at,
            }
        )

    events.sort(key=lambda e: e["timestamp"], reverse=True)
    return events[:limit]