import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class FileOut(BaseModel):
    id: uuid.UUID
    original_name: str
    content_type: str
    size_bytes: int
    folder_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SharedFileOut(FileOut):
    """A file shared with the current user, plus who shared it and how."""

    access_level: str
    shared_by_email: str


class ShareRequest(BaseModel):
    emails: list[EmailStr] = Field(min_length=1, max_length=50)
    access_level: str = Field(pattern=r"^(view|download)$")


class ShareResult(BaseModel):
    shared_with: list[str]
    not_found: list[str]


class PermissionOut(BaseModel):
    id: uuid.UUID
    user_email: str
    access_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionUpdate(BaseModel):
    access_level: str = Field(pattern=r"^(view|download)$")


class ActivityEvent(BaseModel):
    type: str  # "upload" | "download" | "share_out" | "share_in"
    file_name: str
    counterpart_email: str | None = None
    access_level: str | None = None
    timestamp: datetime


class StatsOut(BaseModel):
    file_count: int
    total_storage_bytes: int
    files_shared_out: int
    files_shared_with_me: int