import uuid

from sqlalchemy.orm import Session

from app.models.folder import Folder
from app.schemas.folder import FolderCreate


def create_folder(db: Session, owner_id: uuid.UUID, folder_in: FolderCreate) -> Folder:
    folder = Folder(
        owner_id=owner_id,
        name=folder_in.name,
        parent_folder_id=folder_in.parent_folder_id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def list_folders_for_owner(
    db: Session, owner_id: uuid.UUID, parent_folder_id: uuid.UUID | None = None
) -> list[Folder]:
    query = db.query(Folder).filter(Folder.owner_id == owner_id)
    if parent_folder_id is not None:
        query = query.filter(Folder.parent_folder_id == parent_folder_id)
    return query.order_by(Folder.name).all()