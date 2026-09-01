import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_folder_id: uuid.UUID | None = None


class FolderOut(BaseModel):
    id: uuid.UUID
    name: str
    parent_folder_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}