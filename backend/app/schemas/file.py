import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FileMetadataCreate(BaseModel):

    original_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)
    folder_id: uuid.UUID | None = None


class FileOut(BaseModel):
    id: uuid.UUID
    original_name: str
    content_type: str
    size_bytes: int
    folder_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}