import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.file import decrypt_file_contents, get_file_by_id, get_user_access_level
from app.crud.share_link import (
    create_share_link,
    get_link_by_id,
    get_valid_link_by_token,
    list_links_for_file,
    record_link_download,
    revoke_link,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.share_link import (
    PublicShareFileInfo,
    ShareLinkCreate,
    ShareLinkCreated,
    ShareLinkOut,
)

router = APIRouter(tags=["share-links"])


def _require_owner(db: Session, file_id: uuid.UUID, current_user: User):
    file = get_file_by_id(db, file_id)
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if get_user_access_level(db, file, current_user.id) != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return file


# --- Owner-facing management (authenticated) ---


@router.post(
    "/api/files/{file_id}/links",
    response_model=ShareLinkCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_link_endpoint(
    file_id: uuid.UUID,
    payload: ShareLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShareLinkCreated:
    file = _require_owner(db, file_id, current_user)
    link, raw_token = create_share_link(db, file, payload, current_user.id)
    return ShareLinkCreated(
        id=link.id,
        token=raw_token,
        access_level=link.access_level,
        expires_at=link.expires_at,
        max_downloads=link.max_downloads,
        created_at=link.created_at,
    )


@router.get("/api/files/{file_id}/links", response_model=list[ShareLinkOut])
def list_links_endpoint(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ShareLinkOut]:
    _require_owner(db, file_id, current_user)
    return list_links_for_file(db, file_id)


@router.delete(
    "/api/files/{file_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT
)
def revoke_link_endpoint(
    file_id: uuid.UUID,
    link_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _require_owner(db, file_id, current_user)
    link = get_link_by_id(db, link_id)
    if link is None or link.file_id != file_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    revoke_link(db, link)


# --- Public access (no authentication required) ---


@router.get("/api/share/{token}", response_model=PublicShareFileInfo)
def public_link_info_endpoint(token: str, db: Session = Depends(get_db)) -> PublicShareFileInfo:
    link = get_valid_link_by_token(db, token)
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This link is invalid, expired, or has been revoked.",
        )
    file = link.file
    return PublicShareFileInfo(
        original_name=file.original_name,
        content_type=file.content_type,
        size_bytes=file.size_bytes,
        access_level=link.access_level,
        shared_by_name=link.creator.full_name,
    )


@router.get("/api/share/{token}/download")
def public_link_download_endpoint(token: str, db: Session = Depends(get_db)):
    link = get_valid_link_by_token(db, token)
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This link is invalid, expired, or has been revoked.",
        )
    if link.access_level != "download":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This link only allows viewing, not downloading.",
        )

    file = link.file
    plaintext = decrypt_file_contents(db, file)
    record_link_download(db, link)

    return StreamingResponse(
        io.BytesIO(plaintext),
        media_type=file.content_type,
        headers={"Content-Disposition": f'attachment; filename="{file.original_name}"'},
    )