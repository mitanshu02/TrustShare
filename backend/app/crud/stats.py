import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.file import File
from app.models.file_permission import FilePermission


def get_stats(db: Session, user_id: uuid.UUID) -> dict:
    file_count, total_bytes = (
        db.query(func.count(File.id), func.coalesce(func.sum(File.size_bytes), 0))
        .filter(File.owner_id == user_id, File.deleted_at.is_(None))
        .one()
    )

    files_shared_out = (
        db.query(func.count(func.distinct(FilePermission.file_id)))
        .join(File, File.id == FilePermission.file_id)
        .filter(File.owner_id == user_id)
        .scalar()
    )

    files_shared_with_me = (
        db.query(func.count(func.distinct(FilePermission.file_id)))
        .join(File, File.id == FilePermission.file_id)
        .filter(FilePermission.user_id == user_id, File.deleted_at.is_(None))
        .scalar()
    )

    return {
        "file_count": file_count,
        "total_storage_bytes": total_bytes,
        "files_shared_out": files_shared_out or 0,
        "files_shared_with_me": files_shared_with_me or 0,
    }