import uuid

from fastapi import APIRouter, Depends, File as FastAPIFile, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.api.deps import get_current_user
from app.crud.file import (
    decrypt_file_contents,
    get_file_by_id,
    get_user_access_level,
    list_files_for_owner,
    list_files_shared_with_user,
    list_permissions,
    record_download,
    revoke_permission,
    share_file,
    soft_delete_file,
    update_permission,
    upload_file,
)
from app.db.session import get_db
from app.models.file_permission import FilePermission
from app.models.user import User
from app.schemas.file import (
    FileOut,
    PermissionOut,
    PermissionUpdate,
    ShareRequest,
    ShareResult,
    SharedFileOut,
)

router = APIRouter(prefix="/api/files", tags=["files"])

# 100 MB cap for local-disk demo storage. Real cloud storage limits will
# apply once Milestone 2 wires up S3/Azure Blob.
MAX_UPLOAD_BYTES = 100 * 1024 * 1024


def _require_file_and_access(
    db: Session, file_id: uuid.UUID, current_user: User, allowed_levels: set[str]
):
    file = get_file_by_id(db, file_id)
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    access = get_user_access_level(db, file, current_user.id)
    if access is None or access not in allowed_levels:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return file, access


@router.get("", response_model=list[FileOut])
def list_files_endpoint(
    folder_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FileOut]:
    return list_files_for_owner(db, current_user.id, folder_id)


@router.post("/upload", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file_endpoint(
    file: UploadFile = FastAPIFile(...),
    folder_id: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileOut:
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 100 MB local storage limit.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    parsed_folder_id = uuid.UUID(folder_id) if folder_id else None

    return upload_file(
        db,
        owner_id=current_user.id,
        original_name=file.filename or "untitled",
        content_type=file.content_type or "application/octet-stream",
        plaintext=contents,
        folder_id=parsed_folder_id,
    )


@router.get("/shared-with-me", response_model=list[SharedFileOut])
def shared_with_me_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SharedFileOut]:
    rows = list_files_shared_with_user(db, current_user.id)
    return [
        SharedFileOut(
            **FileOut.model_validate(row["file"]).model_dump(),
            access_level=row["access_level"],
            shared_by_email=row["shared_by_email"],
        )
        for row in rows
    ]


@router.get("/{file_id}/download")
def download_file_endpoint(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file, access = _require_file_and_access(db, file_id, current_user, {"owner", "download"})

    plaintext = decrypt_file_contents(db, file)
    record_download(db, file.id, current_user.id)

    return StreamingResponse(
        io.BytesIO(plaintext),
        media_type=file.content_type,
        headers={"Content-Disposition": f'attachment; filename="{file.original_name}"'},
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file_endpoint(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    file, _ = _require_file_and_access(db, file_id, current_user, {"owner"})
    soft_delete_file(db, file)


@router.post("/{file_id}/share", response_model=ShareResult)
def share_file_endpoint(
    file_id: uuid.UUID,
    payload: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShareResult:
    file, _ = _require_file_and_access(db, file_id, current_user, {"owner"})
    shared_with, not_found = share_file(
        db, file, payload.emails, payload.access_level, current_user.id
    )
    return ShareResult(shared_with=shared_with, not_found=not_found)


@router.get("/{file_id}/permissions", response_model=list[PermissionOut])
def list_permissions_endpoint(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PermissionOut]:
    _require_file_and_access(db, file_id, current_user, {"owner"})
    permissions = list_permissions(db, file_id)
    return [
        PermissionOut(
            id=p.id,
            user_email=p.user.email,
            access_level=p.access_level,
            created_at=p.created_at,
        )
        for p in permissions
    ]


@router.patch("/{file_id}/permissions/{permission_id}", response_model=PermissionOut)
def update_permission_endpoint(
    file_id: uuid.UUID,
    permission_id: uuid.UUID,
    payload: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PermissionOut:
    _require_file_and_access(db, file_id, current_user, {"owner"})
    permission = (
        db.query(FilePermission)
        .filter(FilePermission.id == permission_id, FilePermission.file_id == file_id)
        .first()
    )
    if permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    updated = update_permission(db, permission, payload.access_level)
    return PermissionOut(
        id=updated.id,
        user_email=updated.user.email,
        access_level=updated.access_level,
        created_at=updated.created_at,
    )


@router.delete("/{file_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_permission_endpoint(
    file_id: uuid.UUID,
    permission_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _require_file_and_access(db, file_id, current_user, {"owner"})
    permission = (
        db.query(FilePermission)
        .filter(FilePermission.id == permission_id, FilePermission.file_id == file_id)
        .first()
    )
    if permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    revoke_permission(db, permission)