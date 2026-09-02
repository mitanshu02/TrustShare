import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.encryption import decode_key, decrypt_bytes, encode_key, encrypt_bytes, generate_key
from app.core.storage import delete_encrypted_blob, read_encrypted_blob, save_encrypted_blob
from app.models.download import Download
from app.models.file import File
from app.models.file_encryption_key import FileEncryptionKey
from app.models.file_permission import FilePermission
from app.models.user import User


def list_files_for_owner(
    db: Session, owner_id: uuid.UUID, folder_id: uuid.UUID | None = None
) -> list[File]:
    query = db.query(File).filter(File.owner_id == owner_id, File.deleted_at.is_(None))
    if folder_id is not None:
        query = query.filter(File.folder_id == folder_id)
    return query.order_by(File.created_at.desc()).all()


def upload_file(
    db: Session,
    owner_id: uuid.UUID,
    original_name: str,
    content_type: str,
    plaintext: bytes,
    folder_id: uuid.UUID | None,
) -> File:
    """
    Encrypt the file with a fresh AES-256-GCM key, store the ciphertext
    on disk, store the key in its own table, and record metadata + a
    reference to the key (never the key itself) in `files`.
    """
    key = generate_key()
    encrypted_blob = encrypt_bytes(plaintext, key)
    storage_key = save_encrypted_blob(encrypted_blob)

    key_record = FileEncryptionKey(key_material=encode_key(key))
    db.add(key_record)
    db.flush()  # get key_record.id without a separate commit

    file_record = File(
        owner_id=owner_id,
        folder_id=folder_id,
        original_name=original_name,
        content_type=content_type,
        size_bytes=len(plaintext),
        storage_key=storage_key,
        encryption_key_reference=str(key_record.id),
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


def get_file_by_id(db: Session, file_id: uuid.UUID) -> File | None:
    return (
        db.query(File)
        .filter(File.id == file_id, File.deleted_at.is_(None))
        .first()
    )


def get_user_access_level(db: Session, file: File, user_id: uuid.UUID) -> str | None:
    """
    Returns 'owner', 'view', 'download', or None (no access at all).
    """
    if file.owner_id == user_id:
        return "owner"

    permission = (
        db.query(FilePermission)
        .filter(FilePermission.file_id == file.id, FilePermission.user_id == user_id)
        .first()
    )
    if permission is None:
        return None
    if permission.expires_at and permission.expires_at < datetime.now(timezone.utc):
        return None
    return permission.access_level


def decrypt_file_contents(db: Session, file: File) -> bytes:
    key_record = (
        db.query(FileEncryptionKey)
        .filter(FileEncryptionKey.id == uuid.UUID(file.encryption_key_reference))
        .first()
    )
    key = decode_key(key_record.key_material)
    encrypted_blob = read_encrypted_blob(file.storage_key)
    return decrypt_bytes(encrypted_blob, key)


def record_download(db: Session, file_id: uuid.UUID, user_id: uuid.UUID | None) -> None:
    db.add(Download(file_id=file_id, user_id=user_id))
    db.commit()


def soft_delete_file(db: Session, file: File) -> None:
    file.deleted_at = datetime.now(timezone.utc)
    db.add(file)
    db.commit()
    # Ciphertext is intentionally left on disk for now (soft delete, per
    # schema convention) rather than immediately erased.


def share_file(
    db: Session, file: File, emails: list[str], access_level: str, granted_by: uuid.UUID
) -> tuple[list[str], list[str]]:
    """
    Grant access to a file for each resolvable email. Returns
    (shared_with, not_found) email lists. Re-sharing with an already-
    permitted user updates their access level instead of erroring.
    """
    shared_with: list[str] = []
    not_found: list[str] = []

    for email in emails:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            not_found.append(email)
            continue
        if user.id == file.owner_id:
            # Owner already has full access; skip silently.
            continue

        existing = (
            db.query(FilePermission)
            .filter(FilePermission.file_id == file.id, FilePermission.user_id == user.id)
            .first()
        )
        if existing:
            existing.access_level = access_level
            existing.granted_by = granted_by
        else:
            db.add(
                FilePermission(
                    file_id=file.id,
                    user_id=user.id,
                    access_level=access_level,
                    granted_by=granted_by,
                )
            )
        shared_with.append(email)

    db.commit()
    return shared_with, not_found


def list_permissions(db: Session, file_id: uuid.UUID) -> list[FilePermission]:
    return (
        db.query(FilePermission)
        .filter(FilePermission.file_id == file_id)
        .order_by(FilePermission.created_at.desc())
        .all()
    )


def update_permission(
    db: Session, permission: FilePermission, access_level: str
) -> FilePermission:
    permission.access_level = access_level
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


def revoke_permission(db: Session, permission: FilePermission) -> None:
    db.delete(permission)
    db.commit()


def list_files_shared_with_user(db: Session, user_id: uuid.UUID) -> list[dict]:
    rows = (
        db.query(File, FilePermission, User)
        .join(FilePermission, FilePermission.file_id == File.id)
        .join(User, User.id == File.owner_id)
        .filter(
            FilePermission.user_id == user_id,
            File.deleted_at.is_(None),
        )
        .order_by(FilePermission.created_at.desc())
        .all()
    )
    return [
        {
            "file": file,
            "access_level": permission.access_level,
            "shared_by_email": owner.email,
        }
        for file, permission, owner in rows
    ]