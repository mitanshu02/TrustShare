import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ShareLinkCreate(BaseModel):
    access_level: str = Field(pattern=r"^(view|download)$")
    expires_in_hours: int = Field(gt=0, le=720)  # max 30 days
    max_downloads: int | None = Field(default=None, gt=0)


class ShareLinkCreated(BaseModel):
    """
    Returned exactly once, at creation. The raw token is never
    retrievable again — only its hash is stored.
    """

    id: uuid.UUID
    token: str
    access_level: str
    expires_at: datetime
    max_downloads: int | None
    created_at: datetime


class ShareLinkOut(BaseModel):
    """Owner-facing view of an existing link. Never includes the raw token."""

    id: uuid.UUID
    access_level: str
    expires_at: datetime
    max_downloads: int | None
    download_count: int
    is_active: bool
    created_at: datetime
    revoked_at: datetime | None

    model_config = {"from_attributes": True}


class PublicShareFileInfo(BaseModel):
    """Shown to anyone visiting a share link, before they download."""

    original_name: str
    content_type: str
    size_bytes: int
    access_level: str
    shared_by_name: str