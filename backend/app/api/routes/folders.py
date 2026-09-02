import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.folder import create_folder, list_folders_for_owner
from app.db.session import get_db
from app.models.user import User
from app.schemas.folder import FolderCreate, FolderOut

router = APIRouter(prefix="/api/folders", tags=["folders"])


@router.post("", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder_endpoint(
    folder_in: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FolderOut:
    return create_folder(db, current_user.id, folder_in)


@router.get("", response_model=list[FolderOut])
def list_folders_endpoint(
    parent_folder_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[FolderOut]:
    return list_folders_for_owner(db, current_user.id, parent_folder_id)